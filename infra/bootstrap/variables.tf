variable "region" {
  type    = string
  default = "us-east-1"
}

variable "zone_name" {
  description = "The delegated subdomain (D25)."
  type        = string
  default     = "fleet.programmeos.com"
}
