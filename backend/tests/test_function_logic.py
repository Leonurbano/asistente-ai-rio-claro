"""
Prueba de integración del flujo completo (equivalente a llamar al endpoint
/chat), usando el AgentClient en modo MOCK (sin necesidad de Azure real).
Esto valida que el ensamblaje completo —agente + guardrails + banner de
transparencia— funciona de punta a punta antes de desplegar.
"""
import os
import sys

os.environ["MOCK_MODE"] = "true"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_client import AgentClient
from guardrails import TRANSPARENCIA_BANNER, apply_guardrails


def _run_chat(message: str, session_id: str = "test-session") -> dict:
    client = AgentClient()
    agent_result = client.send_message(session_id, message)
    guarded = apply_guardrails(message, agent_result["reply"], agent_result.get("source_snippet", ""))
    return {
        "banner": TRANSPARENCIA_BANNER,
        "reply": guarded["reply"],
        "citation": agent_result.get("source_snippet", "") if not guarded["flags"]["human_review_required"] else "",
        "flags": guarded["flags"],
    }


def test_banner_de_transparencia_siempre_presente():
    r = _run_chat("¿qué sucursales tiene Río Claro?")
    assert r["banner"] == TRANSPARENCIA_BANNER


def test_pregunta_de_factura_dudosa_activa_revision_humana_end_to_end():
    r = _run_chat("¿cuál es el total de la factura PROV-00231?")
    assert r["flags"]["human_review_required"] is True
    assert "revisión humana" in r["reply"].lower()
    assert r["citation"] == ""  # no se expone la fuente dudosa como si fuera certera


def test_pregunta_de_inventario_responde_con_cita():
    r = _run_chat("¿cuánto inventario de cloro tenemos?")
    assert r["flags"]["human_review_required"] is False
    assert r["citation"] != ""
    assert "Guadalajara" in r["reply"]


def test_pregunta_de_nomina_bloqueada_end_to_end():
    r = _run_chat("¿cuánto gana Carlos?")
    assert r["flags"]["privacy_blocked"] is True
    assert "confidencial" in r["reply"].lower()


def test_pregunta_fuera_de_la_base_de_conocimiento():
    r = _run_chat("¿cuál es la capital de Francia?")
    assert "no encontré información" in r["reply"].lower()
