# Proyecto 2 (AI-901) — Asistente de Río Claro

Asistente de IA para Distribuidora Río Claro: resuelve dudas de empleados y clientes sobre facturas, inventario, políticas y pedidos, aplicando los 6 principios de IA responsable del brief.

## Demo en vivo

**Chat público:** https://strioclarofe28102.z14.web.core.windows.net/

## Arquitectura

| Componente | Recurso Azure | Qué hace |
|---|---|---|
| Agente de IA | Azure AI Foundry (`gpt-5-mini` + File Search) | Responde con base en la base de conocimiento, siguiendo las reglas de `agent/system_prompt.md` |
| Backend | Azure Function (Python) | Expone `/api/chat`, invoca al agente vía Managed Identity y aplica guardrails antes de responder |
| Frontend | Storage Account con sitio web estático | Interfaz de chat web |
| Identidad | Managed Identity (sin API Keys) | Autenticación entre el backend y el agente |

Todo el stack corre en Azure, sin dependencias de ninguna máquina local.

## Principios de IA responsable aplicados

- **Transparencia:** banner de IA desde el primer mensaje; cada respuesta cita la sección de la que salió.
- **Confiabilidad:** si un dato (ej. el total de una factura) no está claro, se marca para revisión humana en vez de inventarse.
- **Equidad:** las respuestas sobre inventario/ventas consideran las 5 sucursales de forma pareja.
- **Rendición de cuentas:** el agente nunca autoriza el pago de una factura; recomienda que un humano la apruebe.
- **Privacidad:** los datos de nómina/sueldos están bloqueados ante cualquier pregunta.
- **Inclusión:** respuestas breves y claras, pensadas para alguien sin experiencia técnica.
- **Alcance estricto:** el agente solo responde temas de Distribuidora Río Claro y redirige cualquier otra pregunta.

## Pruebas automatizadas

```bash
pip install -r backend/requirements.txt
pytest backend/tests/
```

18 pruebas cubren guardrails, seguridad de credenciales y el flujo completo del endpoint `/chat` en modo simulado (`MOCK_MODE=true`), sin necesitar Azure real.

> `frontend/index.html` usa un placeholder para `FUNCTION_URL` por seguridad — no se publica la clave real del backend en este repositorio.

## Estructura del proyecto

```
knowledge/caso-rio-claro.md     # base de conocimiento
agent/system_prompt.md          # instrucciones del agente
backend/
  function_app.py               # endpoint HTTP /chat
  agent_client.py                # cliente del agente
  guardrails.py                  # reglas deterministas
  tests/                         # pruebas automatizadas
frontend/index.html             # chat web
infra/                          # scripts de aprovisionamiento y estimación de costo
```

## Autor

Leonel Urbano Ramírez Espejel. Certificación IA-ATDT, Proyecto 2 (AI-901).
