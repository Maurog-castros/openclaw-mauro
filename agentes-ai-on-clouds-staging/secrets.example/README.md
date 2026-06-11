# Secretos (plantillas)

**Nunca** commitear valores reales. `.gitignore` excluye `.env` y `secrets/`.

| Archivo | Uso |
|---------|-----|
| `litellm.env.example` | API keys para LiteLLM |
| `openclaw.env.example` | Gateway OpenClaw |
| `whatsapp_allow_from.example.txt` | Números E.164 autorizados |
| `santander_cartola.env.example` | PDF cartola Santander |
| `gmail_credentials.json.example` | OAuth Gmail (crear desde Google Cloud Console) |

## Cloud

- **AWS:** Secrets Manager + [External Secrets Operator](https://external-secrets.io/)
- **GCP:** Secret Manager + Workload Identity
- **Azure:** Key Vault + CSI driver

Mapear a `Secret` de Kubernetes: `litellm-secrets`, `openclaw-secrets`, `postgres-memory-secrets`.
