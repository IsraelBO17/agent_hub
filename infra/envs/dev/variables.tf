variable "region" {
  type    = string
  default = "us-east-1"
}

variable "zone_name" {
  description = "Delegated subdomain created in infra/bootstrap (D25)."
  type        = string
  default     = "fleet.programmeos.com"
}

variable "enable_api" {
  description = <<-EOT
    Creates the ALB (with its certificate and api. DNS record) and the ECS service. Off until step 8 so the
    ALB's fixed ~$24/month doesn't start before there is an API to serve.
  EOT
  type        = bool
  default     = false
}

variable "api_image_tag" {
  description = "Image tag in ECR to run (a git SHA). Unused while api_desired_count is 0."
  type        = string
  default     = "bootstrap"
}

variable "api_desired_count" {
  description = "0 until step 8 pushes the first API image; then 1 (P7)."
  type        = number
  default     = 0
}

variable "google_client_id" {
  description = "Google OAuth client ID (not secret; D15). Empty until it is created in the Google Cloud console."
  type        = string
  default     = ""
}

variable "agent_runtime_arns" {
  description = "AgentCore runtimes the API may invoke. Defaults to every runtime in this account and region."
  type        = list(string)
  default     = []
}

variable "monthly_budget_usd" {
  description = "AWS spend alarm (PRODUCT_PLAN A4, ARCHITECTURE Q8), excluding model tokens billed elsewhere."
  type        = number
  default     = 50
}

variable "budget_alert_email" {
  description = "Where budget alerts go. Set in terraform.tfvars (gitignored). Empty: no budget is created."
  type        = string
  default     = ""
}
