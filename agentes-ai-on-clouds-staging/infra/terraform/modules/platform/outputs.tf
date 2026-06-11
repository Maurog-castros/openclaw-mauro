output "environment" {
  value = var.environment
}

output "region" {
  value = var.region
}

# Implementar por cloud:
# output "cluster_name" { }
# output "cluster_endpoint" { sensitive = true }
# output "oidc_provider_arn" { }  # AWS IRSA
