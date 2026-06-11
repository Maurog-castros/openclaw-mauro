# Terraform

## Layout

```text
modules/platform/          # Recursos compartidos (red, cluster, IAM base)
environments/dev/{aws,gcp,azure}/
environments/prod/{aws,gcp,azure}/
```

Cada entorno cloud incluye:

- `versions.tf` — providers pinneados
- `providers.tf`
- `variables.tf` / `terraform.tfvars.example`
- `main.tf` — llama `module.platform`
- `outputs.tf`
- `backend.tf.example` — estado remoto (obligatorio en prod)

## Convenciones

- Tags: `Project=agentes-ai`, `Environment=dev|prod`, `ManagedBy=terraform`
- Nombres: `aai-<env>-<component>`
- Secretos: solo referencias a ARNs/IDs; valores en Secret Manager + External Secrets Operator
