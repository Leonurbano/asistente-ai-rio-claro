"""
Azure Function (HTTP trigger) — backend intermedio del chat de Río Claro.

Recibe {"session_id": str, "message": str}, llama al agente de Foundry
(vía AgentClient), aplica los guardrails deterministas, y regresa:
{
  "banner": "...",       # aviso de transparencia (mostrar siempre en el frontend)
  "reply": "...",        # respuesta final (ya pasó por guardrails)
  "citation": "...",     # de qué sección de la base de conocimiento salió
  "flags": {...}         # evidencia para la Fase 6 (auditoría de los 6 principios)
}
"""
import json
import logging

import azure.functions as func

from agent_client import AgentClient
from guardrails import TRANSPARENCIA_BANNER, apply_guardrails

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
_agent_client = None


def _get_client() -> AgentClient:
    global _agent_client
    if _agent_client is None:
        _agent_client = AgentClient()
    return _agent_client


@app.route(route="chat", methods=["POST"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "JSON inválido"}), status_code=400, mimetype="application/json")

    message = (body or {}).get("message", "").strip()
    session_id = (body or {}).get("session_id", "anon")

    if not message:
        return func.HttpResponse(json.dumps({"error": "falta 'message'"}), status_code=400, mimetype="application/json")

    client = _get_client()
    agent_result = client.send_message(session_id, message)
    guarded = apply_guardrails(message, agent_result["reply"], agent_result.get("source_snippet", ""))

    response = {
        "banner": TRANSPARENCIA_BANNER,
        "reply": guarded["reply"],
        "citation": agent_result.get("source_snippet", "") if not guarded["flags"]["human_review_required"] else "",
        "flags": guarded["flags"],
    }
    logging.info("chat ok session=%s flags=%s", session_id, guarded["flags"])
    return func.HttpResponse(json.dumps(response, ensure_ascii=False), status_code=200, mimetype="application/json")
