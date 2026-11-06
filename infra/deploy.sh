#!/usr/bin/env bash
# Script con el que aprovisioné la infraestructura del proyecto: Storage
# (con sitio web estático para el frontend), Function App y Managed Identity,
# dentro de mi suscripción de Azure for Students.
#
# Región: Azure for Students solo permite crear recursos en 5 regiones;
# usé North Central US (las otras son Norway East, West US, Chile Central
# y Brazil South).

set -euo pipefail

RESOURCE_GROUP="rg-proyecto2-rioclaro"
LOCATION="northcentralus"
FUNCTION_APP_NAME="func-rioclaro-$RANDOM"
STORAGE_ACCOUNT_NAME="strioclaro$RANDOM"

echo "== Verificando sesión de Azure =="
az account show --query "{subscription:name, id:id}" -o table

echo "== Creando cuenta de almacenamiento =="
az storage account create \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS

echo "== Habilitando sitio web estático (hospeda el frontend, sin Static Web Apps) =="
az storage blob service-properties update \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --static-website --index-document index.html

echo "== Creando Function App (plan de Consumo) =="
az functionapp create \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT_NAME" \
  --consumption-plan-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4

echo "== Habilitando Managed Identity (System Assigned) en la Function App =="
az functionapp identity assign \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP"

IDENTITY_PRINCIPAL_ID=$(az functionapp identity show \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query principalId -o tsv)
echo "Managed Identity creada. principalId: $IDENTITY_PRINCIPAL_ID"

cat <<EOF

== Lo que seguí haciendo manualmente después de este script ==
1. Creé el proyecto de Foundry en https://ai.azure.com (mismo grupo de
   recursos y región) y desplegué el modelo gpt-5-mini.
2. Creé el agente (nombre, instrucciones de agent/system_prompt.md y la
   base de conocimiento) desde el portal.
3. Le di permiso a la Managed Identity sobre Foundry con el rol "Foundry
   User" (es el único que cubre resolver agentes por nombre):
   az role assignment create \\
     --assignee "$IDENTITY_PRINCIPAL_ID" \\
     --role "Foundry User" \\
     --scope "<resource-id-de-la-cuenta-de-foundry>"
4. Configuré la Function App (sin API key):
   az functionapp config appsettings set --name "$FUNCTION_APP_NAME" \\
     --resource-group "$RESOURCE_GROUP" \\
     --settings MOCK_MODE=false PROJECT_ENDPOINT="<...>" AGENT_ID="<nombre-del-agente>"
5. Publiqué el backend: cd backend && func azure functionapp publish "$FUNCTION_APP_NAME"
6. Subí el frontend (con FUNCTION_URL ya actualizado) al contenedor \$web:
   az storage blob upload --account-name "$STORAGE_ACCOUNT_NAME" --auth-mode key \\
     -c '$web' -f frontend/index.html -n index.html
7. Habilité CORS en la Function App para el origen del sitio estático:
   az functionapp cors add --name "$FUNCTION_APP_NAME" --resource-group "$RESOURCE_GROUP" \\
     --allowed-origins "https://$STORAGE_ACCOUNT_NAME.z*.web.core.windows.net"

Recursos creados: $FUNCTION_APP_NAME, $STORAGE_ACCOUNT_NAME
Identidad administrada (principalId): $IDENTITY_PRINCIPAL_ID
EOF
