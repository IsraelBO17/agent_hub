variable "region" {
  type    = string
  default = "us-east-1"
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
