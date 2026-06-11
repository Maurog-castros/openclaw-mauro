# Deployment (cloud)

## Orden recomendado

1. **Red + cluster** — `infra/terraform/environments/<env>/<cloud>/`
2. **Add-ons** — ingress, cert-manager, external-secrets (según cloud)
3. **Data plane** — Postgres pgvector, Redis (managed o `infra/k8s/base/memory/`)
4. **LiteLLM** — `apps/litellm` + secretos API
5. **OpenClaw gateway** — imagen `apps/openclaw/docker/openclaw-with-ssh`, ConfigMap desde `apps/openclaw/config/`
6. **Jobs/Cron** — pipelines finanzas, líder (desde `apps/openclaw/scripts/`)
7. **Canales** — WhatsApp/Telegram tokens vía External Secrets

## Volúmenes persistentes

| Dato | Legacy path | Cloud |
|------|-------------|-------|
| Movimientos / CSV | `data/*.csv` | PVC o DB (fase 2) |
| Inbox boletas | `data/inbox/` | PVC S3/GCS compatible |
| Sesiones OpenClaw | `data/config/agents/*/sessions/` | PVC efímero o reset por deploy |

**No** migrar sesiones `.jsonl` al repo Git.

## Imagen OpenClaw

Build desde `apps/openclaw/docker/openclaw-with-ssh/Dockerfile` (base OpenClaw + wrappers).

Registry: ECR / Artifact Registry / ACR según cloud.

## Validación post-deploy

```bash
kubectl -n openclaw get pods
kubectl -n openclaw logs deploy/openclaw-gateway --tail=50
curl -sSf https://<litellm>/health
```
