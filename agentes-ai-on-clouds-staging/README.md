# agentes-ai-on-clouds

Plataforma **GitOps-ready** para desplegar el stack de agentes IA (OpenClaw, LiteLLM, memoria vectorial y automatizaciones) en **AWS EKS**, **GCP GKE** y **Azure AKS**, sin alterar el entorno legacy en bare-metal.

| | |
|---|---|
| **Legacy (producción hoy)** | `/home/mauro/openclaw-mauro` — no tocar en deploy |
| **Este repo** | Copia versionada + IaC para cloud |
| **Sincronización** | `scripts/sync-from-openclaw-mauro.sh` (solo lectura en origen) |

---

## Arquitectura

```text
                    ┌─────────────────────────────────────────┐
                    │           Cloud (EKS / GKE / AKS)        │
                    │  Terraform → VPC → Cluster → Add-ons     │
                    └──────────────────┬──────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
  ┌──────────────┐              ┌──────────────┐              ┌──────────────┐
  │  OpenClaw    │              │   LiteLLM    │              │   Memory     │
  │  Gateway     │◄────────────►│   Proxy      │              │ PG+Redis     │
  └──────┬───────┘              └──────────────┘              └──────────────┘
         │ channels (WA/TG)
         ▼
  ┌──────────────┐     CronJobs / Jobs
  │ Agentes      │     finanzas · content · intel · sales · …
  │ + scripts/   │
  └──────────────┘
```

| Componente | Ruta en repo | Rol |
|------------|--------------|-----|
| OpenClaw | `apps/openclaw/` | Gateway, agentes, scripts Python, Docker |
| LiteLLM | `apps/litellm/` | Proxy de modelos (`OPENAI_API_KEY`, `LITELLM_MASTER_KEY`) |
| Memoria | `apps/memory-services/` | Postgres pgvector + Redis |
| Open WebUI | `apps/open-webui/` | UI opcional |
| Kubernetes | `infra/k8s/` | Manifests base + overlays dev/prod |
| Terraform | `infra/terraform/` | Módulos por cloud |
| CI/CD | `cicd/jenkins/` | Pipelines de referencia |
| Secretos | `secrets.example/` | Plantillas — **nunca** valores reales |

---

## Estructura del repositorio

```text
agentes-ai-on-clouds/
├── apps/
│   ├── openclaw/
│   │   ├── agents/          # SOUL.md por agente (finanzas, content, …)
│   │   ├── config/          # JSON/MD de configuración versionable
│   │   ├── docker/          # compose, Dockerfile custom, overrides
│   │   ├── scripts/         # Lógica Python/shell (finanzas, IG, líder, …)
│   │   └── workspaces/skills/
│   ├── litellm/
│   ├── memory-services/
│   └── open-webui/
├── infra/
│   ├── terraform/
│   │   ├── modules/platform/    # VPC, cluster, IRSA/Workload Identity
│   │   └── environments/{dev,prod}/{aws,gcp,azure}/
│   └── k8s/
│       ├── base/
│       └── overlays/{dev,prod}/
├── cicd/jenkins/
├── docs/
│   ├── inventory/
│   ├── runbooks/
│   └── architecture/
├── scripts/
│   └── sync-from-openclaw-mauro.sh
└── secrets.example/
```

---

## Agentes incluidos

| ID | Dominio | Canales / triggers |
|----|---------|-------------------|
| `finanzas` | Gastos, banco, boletas, transferencias | WhatsApp, Telegram |
| `content` | Instagram, borradores | Delegación desde finanzas |
| `intel` | Investigación / briefs | Cron / orquestador |
| `sales` | Leads | Workspace marketing |
| `pyme-chile` | Proyecto PYME | Workspace dedicado |
| `lider` | Boletas supermercado (scripts) | Cron email |
| `linkedin-jobs` | Empleo (config en repo) | Pendiente cloud |

Detalle: [`docs/inventory/AGENTES-RESUMEN.md`](docs/inventory/AGENTES-RESUMEN.md).

---

## Inicio rápido (operador)

### 1. Sincronizar desde legacy (opcional, idempotente)

```bash
export OPENCLAW_LEGACY_ROOT=/home/mauro/openclaw-mauro
./scripts/sync-from-openclaw-mauro.sh
```

El script **no modifica** el directorio origen; solo actualiza este repo.

### 2. Secretos

```bash
cp secrets.example/litellm.env.example secrets.example/litellm.env   # local, gitignored
# Rellenar y subir a Secret Manager / K8s External Secrets
```

Ver [`secrets.example/README.md`](secrets.example/README.md).

### 3. Terraform (ejemplo AWS dev)

```bash
cd infra/terraform/environments/dev/aws
cp backend.tf.example backend.tf    # bucket S3 + DynamoDB lock
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

### 4. Kubernetes

```bash
kubectl apply -k infra/k8s/overlays/dev
```

---

## DevSecOps

| Práctica | Implementación |
|----------|----------------|
| **Separación legacy / cloud** | Producción sigue en `openclaw-mauro`; este repo es la fuente de despliegue cloud |
| **Sin secretos en Git** | `secrets.example/`, `.gitignore`, `openclaw.example.json` redactado |
| **Estado Terraform remoto** | `backend.tf.example` por cloud (S3, GCS, Azure Storage) |
| **Menor privilegio** | IRSA (AWS), Workload Identity (GCP), managed identity (Azure) en módulos |
| **Entornos** | `dev` / `prod` con overlays Kustomize y tfvars separados |
| **Auditoría** | Inventario en `docs/inventory/`, cron snapshot en `docs/operations/` |

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [docs/inventory/INVENTARIO-OPENCLAW-MAURO.md](docs/inventory/INVENTARIO-OPENCLAW-MAURO.md) | Inventario completo del legacy |
| [docs/architecture/DEPLOYMENT.md](docs/architecture/DEPLOYMENT.md) | Flujo de despliegue cloud |
| [docs/runbooks/](docs/runbooks/) | READMEs por agente/script |

---

## Licencia

Ver [LICENSE](LICENSE).
