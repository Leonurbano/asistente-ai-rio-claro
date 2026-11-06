"""
Automatiza la Fase 2 del SOP (crear el agente, cargar la base de
conocimiento y el system prompt) vía SDK en vez de clics manuales en el
portal — ejecútalo TÚ, en tu máquina, después de `az login` y de haber
creado el proyecto de Foundry y desplegado gpt-4o-mini (Fase 1).

Uso:
  pip install azure-ai-projects azure-identity
  python provision_agent.py --endpoint https://<tu-proyecto>.services.ai.azure.com --model gpt-4o-mini
"""
import argparse
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

HERE = os.path.dirname(__file__)
SYSTEM_PROMPT_PATH = os.path.join(HERE, "..", "agent", "system_prompt.md")
KNOWLEDGE_PATH = os.path.join(HERE, "..", "knowledge", "caso-rio-claro.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True, help="Project endpoint de Azure AI Foundry")
    parser.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args()

    with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        system_prompt = f.read()

    client = AIProjectClient(endpoint=args.endpoint, credential=DefaultAzureCredential())

    print("Subiendo base de conocimiento...")
    uploaded_file = client.agents.files.upload_and_poll(file_path=KNOWLEDGE_PATH, purpose="assistants")
    vector_store = client.agents.vector_stores.create_and_poll(file_ids=[uploaded_file.id])

    print("Creando agente con File Search + Guardrails básicos...")
    from azure.ai.projects.models import FileSearchTool

    file_search = FileSearchTool(vector_store_ids=[vector_store.id])
    agent = client.agents.create_agent(
        model=args.model,
        name="asistente-rio-claro",
        instructions=system_prompt,
        tools=file_search.definitions,
        tool_resources=file_search.resources,
    )

    print("\n== Listo ==")
    print(f"PROJECT_ENDPOINT={args.endpoint}")
    print(f"AGENT_ID={agent.id}")
    print("\nConfigura estas dos variables en tu Function App (ver infra/deploy.sh, paso 4).")


if __name__ == "__main__":
    main()
