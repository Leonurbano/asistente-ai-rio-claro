"""
Prueba de seguridad: confirma que la autenticación contra Azure AI Foundry
se hace con Managed Identity (DefaultAzureCredential) y NUNCA con una API
Key en texto plano dentro del código fuente del backend.

Esto se agregó al revisar el material oficial del curso (tutoriales de
Function+Storage+AppService+Foundry): el patrón enseñado ahí usa una
FOUNDRY_API_KEY guardada en app settings. Para Río Claro se decidió no
adoptar ese patrón y mantener Managed Identity + RBAC (ya implementado
desde el inicio en agent_client.py), por ser la opción sin secretos que
rotar ni filtrar. Esta prueba evita que alguien reintroduzca una API key
por accidente en una modificación futura.
"""
import os

HERE = os.path.dirname(__file__)
AGENT_CLIENT_PATH = os.path.join(HERE, "..", "agent_client.py")


def _read_source() -> str:
    with open(AGENT_CLIENT_PATH, encoding="utf-8") as f:
        return f.read()


def test_no_se_usa_foundry_api_key_como_credencial():
    source = _read_source()
    assert "FOUNDRY_API_KEY" not in source
    assert "api_key" not in source.lower()


def test_se_usa_default_azure_credential():
    source = _read_source()
    assert "DefaultAzureCredential" in source
