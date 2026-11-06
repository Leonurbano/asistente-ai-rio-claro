"""
Capa de Guardrails determinística (defensa en profundidad).

No depende del modelo: aplica reglas duras sobre el texto de entrada/salida,
para que los 6 principios de IA responsable no dependan solo de que el
modelo "se porte bien" en el system prompt. Si el modelo falla, estas
funciones son la red de seguridad.
"""
import re

SUCURSALES = ["Guadalajara", "Zapopan", "León", "Querétaro", "Aguascalientes"]

# Palabras que indican que el usuario pregunta por un monto / factura
_FACTURA_KEYWORDS = re.compile(r"\bfactur|\btotal\b|\bmonto\b|\bpagar\b|\bcu[aá]nto\s+(cuesta|debo|se\s+le\s+debe)", re.IGNORECASE)

# Señales de que el dato fuente es dudoso / incompleto
_DUDOSO_KEYWORDS = re.compile(
    r"ileg|borros|no\s+se\s+(ve|lee)|mancha|no\s+est[aá]\s+clar|parcial|incomplet|\$\s*\d+[,.]?\d*_",
    re.IGNORECASE,
)

# Preguntas sobre nómina / sueldos de un tercero
_NOMINA_KEYWORDS = re.compile(r"sueldo|n[oó]mina|cu[aá]nto\s+gana|salario", re.IGNORECASE)

REVISION_HUMANA_MSG = (
    "⚠️ Requiere revisión humana: el dato fuente no es legible o está incompleto. "
    "No se debe inventar la cifra faltante; favor de que Laura (cuentas por pagar) "
    "confirme el monto manualmente antes de cualquier pago."
)

PRIVACIDAD_MSG = (
    "Esa información (nómina/sueldo) es confidencial y solo puede consultarla "
    "la persona autorizada. No puedo compartirla."
)

TRANSPARENCIA_BANNER = "🤖 Estás hablando con un asistente de IA de Distribuidora Río Claro."


def needs_human_review(user_message: str, source_snippet: str = "") -> bool:
    """True si la pregunta es sobre un monto/factura Y la fuente es dudosa."""
    combined = f"{user_message}\n{source_snippet}"
    return bool(_FACTURA_KEYWORDS.search(user_message)) and bool(_DUDOSO_KEYWORDS.search(combined))


def is_payroll_question(user_message: str) -> bool:
    return bool(_NOMINA_KEYWORDS.search(user_message))


def mentions_branch(text: str) -> str | None:
    """Regresa el nombre de la sucursal mencionada, o None si no se menciona ninguna."""
    for s in SUCURSALES:
        if s.lower() in text.lower():
            return s
    return None


def apply_guardrails(user_message: str, agent_reply: str, source_snippet: str = "") -> dict:
    """
    Aplica las reglas duras sobre la respuesta del agente ANTES de devolverla
    al usuario. Regresa un dict con el texto final y banderas de auditoría
    (útiles para la Fase 6 del SOP: evidencia de los 6 principios).
    """
    flags = {
        "human_review_required": False,
        "privacy_blocked": False,
        "equity_branch_mentioned": mentions_branch(user_message),
    }

    if is_payroll_question(user_message):
        flags["privacy_blocked"] = True
        return {"reply": PRIVACIDAD_MSG, "flags": flags}

    if needs_human_review(user_message, source_snippet):
        flags["human_review_required"] = True
        # Se antepone el aviso de revisión humana; nunca se usa la cifra
        # inventada que pudiera traer agent_reply.
        return {"reply": REVISION_HUMANA_MSG, "flags": flags}

    return {"reply": agent_reply, "flags": flags}
