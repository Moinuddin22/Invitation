locals {
  base_url = local.use_domain ? "https://${local.hostname}" : "https://${aws_apprunner_service.app.service_url}"
}

output "ecr_repository_url" { value = aws_ecr_repository.app.repository_url }
output "db_endpoint" { value = aws_db_instance.this.endpoint }
output "base_url" { value = local.base_url }

output "invitation_links" {
  value = {
    nikah  = "${local.base_url}/nikah"
    valima = "${local.base_url}/valima"
  }
}
