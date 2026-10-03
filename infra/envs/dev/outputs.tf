output "api_url" {
  value = "https://${local.api_domain}"
}

output "app_url" {
  value = local.app_origin
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "files_bucket" {
  value = module.storage.bucket_name
}

output "secret_names" {
  description = "Set each value by hand: aws secretsmanager put-secret-value --secret-id <name> --secret-string '...'"
  value       = module.secrets.names
}

output "api_enabled" {
  value = var.enable_api
}

output "ecs_cluster" {
  value = one(module.api[*].cluster_name)
}

output "ecs_service" {
  value = one(module.api[*].service_name)
}

output "api_log_group" {
  value = one(module.api[*].log_group)
}

output "amplify_app_id" {
  value = module.web.app_id
}

output "alb_dns_name" {
  value = one(module.alb[*].dns_name)
}

output "api_certificate_status" {
  value = one(aws_acm_certificate.api[*].status)
}

output "dns_records_for_qucoon" {
  description = "CNAME records for the owner of the qucoon.com zone to add (D25). Keep the validation record: ACM renews with it."
  value = concat(
    [for o in flatten([for c in aws_acm_certificate.api : c.domain_validation_options]) : {
      purpose = "certificate validation for ${o.domain_name}"
      name    = o.resource_record_name
      type    = o.resource_record_type
      value   = o.resource_record_value
    }],
    [for dns in module.alb[*].dns_name : {
      purpose = "the API"
      name    = "${local.api_domain}."
      type    = "CNAME"
      value   = dns
    }],
  )
}
