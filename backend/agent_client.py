"""
Cliente del agente de Azure AI Foundry.

Tiene dos modos, controlados por la variable de entorno MOCK_MODE:

- MOCK_MODE=true  (default si no hay credenciales): regresa respuestas
  simuladas, para poder desarrollar y probar TODO el flujo (guardrails,
  citas, endpoint HTTP) sin necesitar una suscripción de Azure activa.
  Así es como se validó este proyecto en este entorno.

- MOCK_MODE=false: usa el SDK real de Azure AI Foundry (azure-ai-projects)
  para llamar al agente desplegado. Requiere las variables de entorno
  PROJECT_ENDPOINT y AGENT_ID (ver infra/deploy.sh y README.md). Esta
  rama SOLO puede probarse con una suscripción de Azure real — no se
  ejecutó en este entorno porque este entorno no tiene ni debe tener
  las credenciales de la cuenta de Leo.
"""
import os

MOCK_MODE = os.environ.get("MOCK_MODE", "true").lower() == "true"

# Respuestas simuladas para los casos de prueba del SOP (Fase 6).
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
        # Importa el SDK real solo si hace falta, para no requerirlo en modo mock.
        from azure.ai.projects import AIProjectClient

        endpoint = os.environ["PROJECT_ENDPOINT"]
        # NOTA: en este proyecto el agente se creó desde el portal de Foundry
        # (no con provision_agent.py), por lo que no existe un "asst_..." id
        # clásico. El recurso se referencia por su NOMBRE. La variable de
        # entorno AGENT_ID guarda ese nombre (ej. "asistente-rio-claro") para
        # no tener que cambiar el resto del checklist/infra.
        self.agent_name = os.environ["AGENT_ID"]

        # Autenticación: preferimos API key (FOUNDRY_API_KEY) porque, al día de
        # hoy, ningún rol RBAC estándar de Azure otorga el permiso de "plano de
        # datos" (dataAction) que requiere el servicio de Agents en preview
        # (Microsoft.CognitiveServices/accounts/AIServices/agents/write). Si no
        # hay API key configurada, caemos de regreso a Managed Identity/Entra ID
        # (DefaultAzureCredential) por si en el futuro Azure agrega ese permiso
        # a un rol built-in.
        api_key = os.environ.get("FOUNDRY_API_KEY")
        if api_key:
            from azure.core.credentials import AzureKeyCredential

            self._credential = AzureKeyCredential(api_key)
        else:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()

        self.project_client = AIProjectClient(
            endpoint=endpoint, credential=self._credential, allow_preview=True
        )
        self.openai_client = self.project_client.get_openai_client(agent_name=self.agent_name)

    def send_message(self, session_id: str, message: str) -> dict:
        """Regresa {"reply": str, "source_snippet": str}."""
        if self._mode == "mock":
            reply, source = _mock_reply(message)
            return {"reply": reply, "source_snippet": source}

        # Rama real: usa la API de Responses del agente (gpt-5-mini + File Search).
        response = self.openai_client.responses.create(input=message)
        reply = response.output_text

        # Mejor esfuerzo: extraer el fragmento citado por File Search, si viene
        # en las anotaciones de la respuesta. Si no viene, usamos la propia
        # respuesta del agente como texto a inspeccionar por los guardrails
        # (defensa en profundidad: así "dudoso"/"ilegible" se detecta aunque
        # el SDK no exponga la cita en este formato de respuesta).
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
