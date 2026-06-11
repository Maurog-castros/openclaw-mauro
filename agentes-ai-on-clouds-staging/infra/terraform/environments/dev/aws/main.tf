module "platform" {
  source = "../../../modules/platform"

  project_name = var.project_name
  environment  = var.environment
  region       = var.region
  tags         = var.tags
}
