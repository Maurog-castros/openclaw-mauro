# Módulo platform — implementación por cloud en environments/*/aws|gcp|azure.
# Este stub documenta la interfaz; extender con submódulos:
#   - network (VPC/VNet)
#   - kubernetes (EKS/GKE/AKS)
#   - iam (IRSA / Workload Identity)

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

# placeholder — reemplazar en PR por recursos reales del cloud elegido
