provider "aws" {
  region = var.region

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
    })
  }
}
