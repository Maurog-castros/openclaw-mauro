# GCP GKE — dev

Copiar estructura desde `../aws/` y adaptar:

- `backend.tf.example` → `backend "gcs" { bucket = "..." }`
- Provider `google` ~> 5.x
- Módulo platform → submódulo GKE + VPC
