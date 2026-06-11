variable "project_name" {
  description = "Nombre corto del proyecto (ej. agentes-ai)"
  type        = string
  default     = "agentes-ai"
}

variable "environment" {
  description = "Entorno: dev | prod"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment debe ser dev o prod."
  }
}

variable "region" {
  description = "Region cloud principal"
  type        = string
}

variable "cluster_version" {
  description = "Version del plano de control Kubernetes"
  type        = string
  default     = "1.29"
}

variable "node_instance_types" {
  description = "Tipos de instancia para node pool (cloud-specific en implementacion)"
  type        = list(string)
  default     = ["t3.large"]
}

variable "tags" {
  description = "Tags comunes"
  type        = map(string)
  default     = {}
}
