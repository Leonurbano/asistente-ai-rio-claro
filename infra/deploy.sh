#!/usr/bin/env bash
# Script de despliegue — Fases 1, 3 (publicación) y 5 del SOP.
#
# IMPORTANTE: este script lo debes ejecutar TÚ, en tu propia máquina o en la
# terminal de Cloud Shell de tu cuenta de Azure for Students, después de
# `az login`. No se ejecutó en este entorno de desarrollo porque aquí no
# hay (ni debe haber) credenciales de tu cuenta de Azure.
#
# Requisitos previos (Fase 0 del SOP, ya deberías tenerlos):
#   - Grupo de recursos creado (ej. rg-proyecto2-rioclaro)
#   - Presupuesto con alertas configurado
#   - Región confirmada con disponibilidad de gpt-4o-mini en Foundry

set -euo pipefail

RESOURCE_GROUP="rg-proyecto2-rioclaro"
LOCATION="westus"              # cambia si tu Fase 0 eligió otra región
FUNCTION_APP_NAME="func-rioclaro-$RANDOM"
STORAGE_ACCOUNT_NAME="strioclaro$RANDOM"
STATIC_WEB_APP_NAME="swa-rioclaro"
KEY_VAULT_NAME="kv-rioclaro-$RANDOM"

echo "== Verificando sesión de Azure =="
az account show --query "{subscription:name, id:id}" -o table

echo "== Creando cuenta de almacenamiento (requerida por Azure Functions) =="
az storage account create \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS

echo "== Creando Function App (plan de Consumo — costo \$0 dentro de la capa gratuita) =="
az functionapp create \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT_NAME" \
  --consumption-plan-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4

echo "== Creando Key Vault =="
az keyvault create \
  --name "$KEY_VAULT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "== Creando Static Web App (plan gratuito) =="
az staticwebapp create \
  --name "$STATIC_WEB_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Free

echo "== Habilitando Managed Identity (System Assigned) en la Function App =="
# Esto reemplaza el uso de una API Key en texto plano: la Function App se
# autentica contra Foundry con una identidad administrada por Azure,
# sin ningún secreto que guardar, rotar o filtrar.
az functionapp identity assign \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP"

# Guarda el principalId para el role assignment del paso manual de abajo
# (se necesita el ID del recurso de Foundry, que aún no existe en este punto
# del script — por eso el role assignment se deja como paso 4, después de
# crear el proyecto de Foundry en el portal).
IDENTITY_PRINCIPAL_ID=$(az functionapp identity show \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query principalId -o tsv)
echo "Managed Identity creada. principalId: $IDENTITY_PRINCIPAL_ID"

cat <<EOF

== Siguiente paso MANUAL (requiere el portal de Foundry, Fase 1-2 del SOP) ==
1. Ve a https://ai.azure.com, crea el proyecto de Foundry en este mismo
   grupo de recursos ($RESOURCE_GROUP) y región ($LOCATION).
2. Despliega el modelo gpt-4o-mini.
3. Corre infra/provision_agent.py (en tu máquina, con 'az login' activo)
   para crear el agente con la base de conocimiento y el system prompt
   ya preparados en este proyecto — automatiza la Fase 2 completa.
4. Dale a la Managed Identity de la Function App permiso sobre el proyecto
   de Foundry (sustituye API Key por RBAC — sin secretos):
   az role assignment create \\
     --assignee "$IDENTITY_PRINCIPAL_ID" \\
     --role "Azure AI Developer" \\
     --scope "<resource-id-del-proyecto-de-foundry>"
   (El resource ID lo obtienes con:
     az resource show --resource-group "$RESOURCE_GROUP" \\
       --resource-type "Microsoft.CognitiveServices/accounts/projects" \\
       --name "<nombre-del-proyecto>" --query id -o tsv)
5. Copia el PROJECT_ENDPOINT y AGENT_ID que te regrese provision_agent.py y
   configúralos como variables de entorno de tu Function App — SIN API KEY,
   la autenticación ya la resuelve la Managed Identity + el role assignment
   del paso 4:
   az functionapp config appsettings set --name "$FUNCTION_APP_NAME" \\
     --resource-group "$RESOURCE_GROUP" \\
     --settings MOCK_MODE=false PROJECT_ENDPOINT="<...>" AGENT_ID="<...>"
6. Publica el código: cd backend && func azure functionapp publish "$FUNCTION_APP_NAME"
7. Publica el frontend: az staticwebapp deploy ... (o desde el portal, conectando este repo)
8. Actualiza FUNCTION_URL en frontend/index.html con la URL real de tu función.

Recursos creados: $FUNCTION_APP_NAME, $STORAGE_ACCOUNT_NAME, $KEY_VAULT_NAME, $STATIC_WEB_APP_NAME
Identidad administrada (principalId): $IDENTITY_PRINCIPAL_ID
EOF
