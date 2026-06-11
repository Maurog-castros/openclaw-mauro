# agentes-ai-on-clouds

Plataforma de despliegue multi-cloud (AWS EKS, GCP GKE, Azure AKS) para el stack de agentes IA de Mauro.

**Origen operativo:** `/home/mauro/openclaw-mauro` (servidor Ubuntu + desarrollo local).

## Estructura

| Directorio | Contenido |
|------------|-----------|
| `apps/openclaw/` | Gateway, agentes, scripts Python, Docker |
| `apps/litellm/` | Proxy de modelos |
| `apps/open-webui/` | UI opcional |
| `apps/memory-services/` | Postgres pgvector + Redis |
| `infra/terraform/` | Módulos por cloud |
| `infra/k8s/` | Manifests base + overlays |
| `cicd/jenkins/` | Pipelines |
| `docs/inventory/` | Inventario del legacy |
| `secrets.example/` | Plantillas sin secretos |

## Primer paso

Leer [docs/inventory/INVENTARIO-OPENCLAW-MAURO.md](docs/inventory/INVENTARIO-OPENCLAW-MAURO.md).

## Estado

- [x] Estructura de directorios
- [x] Inventario servidor
- [ ] Sync Fase 1 desde `openclaw-mauro`
- [ ] Plantillas K8s / Terraform
