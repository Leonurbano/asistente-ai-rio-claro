"""
Cliente del agente de Azure AI Foundry.

MOCK_MODE=true (default): respuestas simuladas, para probar el flujo completo
(guardrails, citas, endpoint HTTP) sin necesitar Azure.

MOCK_MODE=false: usa el SDK real (azure-ai-projects) vía Managed Identity.
Requiere PROJECT_ENDPOINT y AGENT_ID (ver infra/deploy.sh).
"""
import os

MOCK_MODE = os.environ.get("MOCK_MODE", "true").lower() == "true"

_MOCK_RESPONSES = {
    "sueldo": "Según la sección 5, Carlos es responsable de sistemas, pero no tengo autorizado compartir montos de nómina.",
    "factura": (
        "Según la sección 8 de la base de conocimiento, la factura PROV-00231 de "
        "'Limpiadores del Bajío' tiene el total parcialmente cubierto por una mancha "
        "('$4,8__.00'), por lo que no puedo confirmar el monto exacto."
    ),
    "inventario": (
        "Según la sección 6 (catálogo normalizado), el stock de Cloro líquido 1L es: "
        "Guadalajara 120, Zapopan 85, León 60, Querétaro 95, Aguascalientes 40."
    ),
    "devoluciones": (
        "Según la sección 7, un cliente puede devolver producto cerrado dentro de 15 "
        "días naturales con factura o nota de remisión."
    ),
}


def _mock_reply(message: str) -> tuple[str, str]:
    """Regresa (respuesta, fragmento_fuente) simulados según palabras clave."""
    lower = message.lower()
    if "sueldo" in lower or "nómina" in lower or "nomina" in lower or "gana" in lower:
        return _MOCK_RESPONSES["sueldo"], "sección 5"
    if "factura" in lower or "total" in lower or "pagar" in lower:
        return _MOCK_RESPONSES["factura"], "sección 8 (dato ilegible, mancha, total incompleto)"
    if "inventario" in lower or "stock" in lower or "cloro" in lower:
        return _MOCK_RESPONSES["inventario"], "sección 6"
    if "devoluci" in lower:
        return _MOCK_RESPONSES["devoluciones"], "sección 7"
    return (
        "No encontré información específica sobre eso en la base de conocimiento del caso Río Claro.",
        "",
    )


class AgentClient:
    def __init__(self):
        if MOCK_MODE:
            self._mode = "mock"
        else:
            self._mode = "real"
            self._init_real_client()

    def _init_real_client(self):
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        endpoint = os.environ["PROJECT_ENDPOINT"]
        self.agent_name = os.environ["AGENT_ID"]  # nombre del agente, no un "asst_..." id

        self.project_client = AIProjectClient(
            endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True
        )
        self.openai_client = self.project_client.get_openai_client(agent_name=self.agent_name)

    def send_message(self, session_id: str, message: str) -> dict:
        """Regresa {"reply": str, "source_snippet": str}."""
        if self._mode == "mock":
            reply, source = _mock_reply(message)
            return {"reply": reply, "source_snippet": source}

        response = self.openai_client.responses.create(input=message)
        reply = response.output_text

        # Mejor esfuerzo: extraer la cita de File Search; si no viene, usamos
        # la respuesta misma como texto para los guardrails (defensa en profundidad).
        source_snippet = ""
        try:
            for item in getattr(response, "output", []) or []:
                for content in getattr(item, "content", []) or []:
                    for ann in getattr(content, "annotations", []) or []:
                        quote = getattr(ann, "quote", None) or getattr(ann, "text", None)
                        if quote:
                            source_snippet = quote
                            break
                    if source_snippet:
                        break
                if source_snippet:
                    break
        except Exception:
            pass

        if not source_snippet:
            source_snippet = reply

        return {"reply": reply, "source_snippet": source_snippet}
