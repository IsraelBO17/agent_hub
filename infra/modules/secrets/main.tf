# Secret containers only (D15). Values are set by hand (`aws secretsmanager put-secret-value`) and never pass
# through Terraform, so they never land in state.

variable "prefix" {
  description = "e.g. agent-hub/dev"
  type        = string
}

variable "secrets" {
  description = "Secret short name => description."
  type        = map(string)
}

resource "aws_secretsmanager_secret" "this" {
  for_each                = var.secrets
  name                    = "${var.prefix}/${each.key}"
  description             = each.value
  recovery_window_in_days = 7
}

output "arns" {
  description = "Short name => ARN."
  value       = { for k, s in aws_secretsmanager_secret.this : k => s.arn }
}

output "names" {
  value = { for k, s in aws_secretsmanager_secret.this : k => s.name }
}
