# Developer Guide - Agent Framework on Azure

Esta guía documenta todos los pasos necesarios para configurar el entorno de desarrollo y desplegar la infraestructura del proyecto.

## 📋 Tabla de Contenidos

1. [Autenticación en Azure](#1-autenticación-en-azure)
2. [Configuración de Terraform](#2-configuración-de-terraform)
3. [Despliegue de Infraestructura](#3-despliegue-de-infraestructura)
4. [Configuración del Entorno Python](#4-configuración-del-entorno-python)
5. [Resolución de Problemas](#5-resolución-de-problemas)

---

## 1. Autenticación en Azure

### Paso 1.1: Login con Azure CLI

En un entorno de Dev Container/Codespaces, ejecuta:

```bash
az login
```

El sistema te pedirá que abras una página web y ingreses un código de dispositivo para autenticarte.

### Paso 1.2: Verificar la suscripción activa

Una vez autenticado, verifica tu suscripción:

```bash
az account show
```

Deberías ver algo como:

```json
{
  "id": "22d9ab23-2ad4-42a9-88c8-34d3a30d316a",
  "name": "Hackathon",
  "tenantId": "a0298061-c663-48a2-b380-434076c64949"
}
```

### Paso 1.3: Guardar IDs importantes

```bash
export AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
export AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
```

---

## 2. Configuración de Terraform

### Problema común: Terraform no detecta la suscripción automáticamente

En entornos de contenedores (Codespaces, Dev Containers), Terraform puede no detectar automáticamente las credenciales de Azure CLI aunque hayas hecho `az login` correctamente.

**Síntoma del error:**

```
Error: building account: unable to configure ResourceManagerAccount: 
subscription ID could not be determined and was not specified
```

### Solución: Especificar el Subscription ID explícitamente

Edita el archivo `infra/providers.tf` y agrega el `subscription_id`:

```terraform
provider "azurerm" {
  features {}
  subscription_id = "22d9ab23-2ad4-42a9-88c8-34d3a30d316a"  # Tu subscription ID
}
```

**¿Por qué ocurre esto?**

1. **Contexto de contenedor**: Las credenciales de Azure CLI no siempre se propagan correctamente a otras herramientas
2. **Múltiples métodos de autenticación**: Terraform intenta varios métodos en orden:
   - Variables de entorno (`ARM_SUBSCRIPTION_ID`)
   - Configuración explícita en el provider ✅ (la que usamos)
   - Azure CLI (falla en algunos contenedores)
   - Managed Identity

### Paso 2.1: Inicializar Terraform

```bash
cd infra
terraform init
```

---

## 3. Despliegue de Infraestructura

### Paso 3.1: Planificar el despliegue (opcional)

Para ver qué recursos se crearán sin aplicarlos:

```bash
terraform plan
```

### Paso 3.2: Aplicar la configuración

```bash
terraform apply -auto-approve
```

### Recursos creados

El despliegue crea los siguientes recursos en Azure:

| Recurso | Nombre | Descripción |
|---------|--------|-------------|
| Resource Group | `rg-dev-swe-ai-ag-b443` | Contenedor de todos los recursos |
| Azure AI Foundry | `aif-dev-swe-ai-ag-b443` | Servicio de AI con capacidad multi-modelo |
| AI Project | `proj-dev-swe-ai-ag-b443` | Proyecto de agentes AI |
| Storage Account | `stdevsweaiagb443` | Almacenamiento para archivos de entrenamiento |
| Storage Container | `training-files` | Contenedor de blobs para datos |
| Log Analytics | `log-dev-swe-ai-ag-b443` | Workspace de logs y métricas |
| Application Insights | `appi-dev-swe-ai-ag-b443` | Monitoreo de aplicaciones |
| Chat Model Deployment | `chatmodel` | Deployment de GPT-4.1-mini |
| Role Assignments | 3 asignaciones | Permisos para el usuario |

### Paso 3.3: Verificar la salida

```bash
terraform output
```

Salida esperada:

```
resource_group_name = "rg-dev-swe-ai-ag-b443"
```

### Paso 3.4: Verificar recursos creados por consola

Puedes verificar todos los recursos desplegados usando Azure CLI:

#### Ver todos los recursos del Resource Group

```bash
az resource list --resource-group rg-dev-swe-ai-ag-b443 --output table
```

#### Ver detalles de recursos específicos

**Azure AI Foundry:**
```bash
az cognitiveservices account show \
  --name aif-dev-swe-ai-ag-b443 \
  --resource-group rg-dev-swe-ai-ag-b443
```

**Modelo deployado (GPT-4.1-mini):**
```bash
az cognitiveservices account deployment list \
  --name aif-dev-swe-ai-ag-b443 \
  --resource-group rg-dev-swe-ai-ag-b443 \
  --output table
```

**Storage Account y Container:**
```bash
# Ver storage account
az storage account show \
  --name stdevsweaiagb443 \
  --resource-group rg-dev-swe-ai-ag-b443

# Ver containers
az storage container list \
  --account-name stdevsweaiagb443 \
  --auth-mode login \
  --output table
```

**Application Insights:**
```bash
az monitor app-insights component show \
  --app appi-dev-swe-ai-ag-b443 \
  --resource-group rg-dev-swe-ai-ag-b443
```

**Log Analytics:**
```bash
az monitor log-analytics workspace show \
  --workspace-name log-dev-swe-ai-ag-b443 \
  --resource-group rg-dev-swe-ai-ag-b443
```

**Role Assignments (permisos):**
```bash
az role assignment list \
  --scope "/subscriptions/22d9ab23-2ad4-42a9-88c8-34d3a30d316a/resourceGroups/rg-dev-swe-ai-ag-b443" \
  --output table
```

**Exportar todo a JSON para análisis:**
```bash
az resource list \
  --resource-group rg-dev-swe-ai-ag-b443 \
  --output json > recursos.json
```

---

## 4. Configuración del Entorno Python

### Problema común: Error de permisos con uv sync

**Síntoma del error:**

```bash
uv sync --active
# error: failed to create directory `/vscode/venvs/agent-framework-on-azure`: 
# Permission denied (os error 13)
```

**Causa**: `uv` intenta crear el entorno virtual en `/vscode/venvs/` donde no tienes permisos de escritura.

### Solución: Crear entorno virtual local

### Paso 4.1: Crear el entorno virtual

```bash
cd src
uv venv .venv
```

### Paso 4.2: Activar el entorno

```bash
source .venv/bin/activate
```

### Paso 4.3: Instalar dependencias

```bash
uv sync --active
```

Esto instalará ~80 paquetes incluyendo:
- `agent-framework-azure-ai`
- `agent-framework-core`
- `azure-ai-agents`
- `azure-ai-projects`
- `openai`
- `fastapi`
- Y muchos más...

### Paso 4.4: Crear archivo de configuración .env

Crea el archivo `src/.env` con las siguientes variables:

```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=22d9ab23-2ad4-42a9-88c8-34d3a30d316a
AZURE_TENANT_ID=a0298061-c663-48a2-b380-434076c64949
RESOURCE_GROUP_NAME=rg-dev-swe-ai-ag-b443

# Azure AI Foundry Project (completar después de obtener los valores)
# PROJECT_CONNECTION_STRING=<your-project-connection-string>
# AZURE_OPENAI_ENDPOINT=<your-foundry-endpoint>
```

### Paso 4.5: Obtener valores adicionales del proyecto

Para obtener el connection string del proyecto:

```bash
# Listar proyectos en el resource group
az resource list \
  --resource-group rg-dev-swe-ai-ag-b443 \
  --resource-type Microsoft.CognitiveServices/accounts/projects \
  --query "[].{name:name, id:id}" -o table
```

### Paso 4.6: Configurar VS Code

Asegúrate de que VS Code use el entorno virtual correcto:

1. Presiona `Ctrl+Shift+P` (o `Cmd+Shift+P` en Mac)
2. Escribe "Python: Select Interpreter"
3. Selecciona el intérprete en `.venv` (`./src/.venv/bin/python`)

---

## 5. Resolución de Problemas

### Problema: `az login` funciona pero Terraform no encuentra la suscripción

**Solución**: Especifica `subscription_id` explícitamente en `providers.tf` (ver sección 2).

### Problema: Error de permisos con `uv sync`

**Solución**: Crea el entorno virtual localmente con `uv venv .venv` (ver sección 4).

### Problema: Terraform init falla con `chmod operation not permitted`

Esto ocurre cuando el repo está en un mount de Windows. **Solución**:

```bash
cd infra
mkdir -p /vscode/tfdata/plugin-cache

export TF_DATA_DIR=/vscode/tfdata/infra
export TF_PLUGIN_CACHE_DIR=/vscode/tfdata/plugin-cache

terraform init
```

### Problema: No puedo instalar dependencias de Python

**Verificaciones**:

1. ¿Estás en el directorio `src`?
2. ¿Activaste el entorno virtual?
3. ¿Tienes acceso a internet?

```bash
cd src
source .venv/bin/activate
uv pip list  # Verificar paquetes instalados
```

---

## 📊 Resumen del Estado Actual

✅ **Autenticación Azure**: Completada  
✅ **Terraform configurado**: Subscription ID especificado  
✅ **Infraestructura desplegada**: 15 recursos creados  
✅ **Entorno Python**: Configurado con .venv local  
✅ **Dependencias instaladas**: 80 paquetes  
✅ **Archivo .env**: Creado con credenciales básicas  

---

## 🚀 Próximos Pasos

1. Completar las variables del proyecto en `.env`
2. Ejecutar el script de creación de datos: `python src/create_data.py`
3. Iniciar el agente principal: `python src/main.py`
4. Seguir los laboratorios en `docs/workshop.md`

---

## 📚 Referencias

- [Azure CLI Documentation](https://learn.microsoft.com/cli/azure/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [uv Package Manager](https://github.com/astral-sh/uv)
- [Model Context Protocol with Foundry Agents](https://learn.microsoft.com/en-us/agent-framework/user-guide/model-context-protocol/using-mcp-with-foundry-agents?pivots=programming-language-python)

---

**Última actualización**: 16 de diciembre de 2025  
**Suscripción**: Hackathon (22d9ab23-2ad4-42a9-88c8-34d3a30d316a)  
**Resource Group**: rg-dev-swe-ai-ag-b443
