variable "region" {
  type    = string
  default = "us-east-1"
}

variable "app_domain" {
  description = "The app's host name; the API is api.<app_domain>. Both are CNAMEs in the qucoon.com zone, which another account manages (D25)."
  type        = string
  default     = "fleet.qucoon.com"
}

variable "project" {
  type    = string
  default = "fleet"
}

variable "environment" {
  type    = string
  default = "dev"
}

# Required internal tags (D26). No defaults: set them in terraform.tfvars (gitignored), never in git.
variable "owner" {
  description = "Owner tag: the responsible person's email."
  type        = string
  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.owner))
    error_message = "owner must be an email address."
  }
}

variable "aws_apn_id" {
  description = "aws-apn-id tag."
  type        = string
  validation {
    condition     = length(var.aws_apn_id) > 0
    error_message = "aws_apn_id is required."
  }
}

variable "enable_api" {
  description = <<-EOT
    Phase 1: creates the API's ACM certificate, whose validation CNAME the qucoon.com owner adds (D25).
    With api_certificate_issued it also creates the ALB and the ECS service (~$24/month for the ALB alone).
  EOT
  type        = bool
  default     = false
}

variable "api_certificate_issued" {
  description = "Phase 2: set true once ACM shows the API certificate as Issued; creates the ALB and the ECS service."
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
  description = "Fleet's AgentCore runtime ARNs the API may invoke. The account is shared, so no wildcard; required when enable_api is true."
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for a in var.agent_runtime_arns : can(regex("^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[A-Za-z0-9_-]+$", a))])
    error_message = "List exact runtime ARNs (arn:aws:bedrock-agentcore:<region>:<account>:runtime/<id>), no wildcards."
  }
}

variable "monthly_budget_usd" {
  description = "Fleet's AWS spend alarm (PRODUCT_PLAN A4, ARCHITECTURE Q8), counting only resources tagged Project=fleet."
  type        = number
  default     = 50
}

variable "budget_alert_email" {
  description = "Where budget alerts go. Set in terraform.tfvars (gitignored). Empty: no budget is created."
  type        = string
  default     = ""
}
