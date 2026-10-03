# The dev environment, the only one until v1 (D17). Apply order and the manual steps: infra/README.md.

locals {
  prefix     = "${var.project}-${var.environment}" # names: <prefix>-<component>-<type>-<region> (D26)
  app_domain = var.app_domain                      # https://fleet.qucoon.com (Amplify)
  api_domain = var.api_domain                      # https://api-fleet.qucoon.com (ALB)
  app_origin = "https://${local.app_domain}"
  api_port   = 8000
  # The account is shared: the API may invoke only fleet's own runtimes, listed explicitly.
  runtime_arns = var.agent_runtime_arns
}

module "network" {
  source = "../../modules/network"
  prefix = local.prefix
  region = var.region
  cidr   = "10.20.0.0/16"
}

module "ecr" {
  source = "../../modules/ecr"
  name   = "${local.prefix}-api-ecr-${var.region}"
}

module "storage" {
  source       = "../../modules/storage"
  bucket_name  = "${local.prefix}-files-s3-${var.region}"
  cors_origins = [local.app_origin, "http://localhost:5173"] # 5173: Vite dev server
}

module "secrets" {
  source = "../../modules/secrets"
  prefix = local.prefix
  region = var.region
  secrets = {
    "database-url"        = "Neon pooled connection string, used by the API (D3)"
    "database-url-direct" = "Neon direct connection string, used by migrations (D3)"
    "session-key"         = "Signs the API's access tokens (D8). Random, at least 32 bytes."
  }
}

# The API uses qucoon's shared wildcard certificate (*.qucoon.com), owned by the qucoon cloud team and
# referenced by ARN only, so Terraform never changes or deletes it (D25). The first design created its own
# certificate; that one was deleted outside Terraform: forget it.
removed {
  from = aws_acm_certificate.api
  lifecycle {
    destroy = false
  }
}

module "alb" {
  count             = var.enable_api ? 1 : 0
  source            = "../../modules/alb"
  prefix            = "${local.prefix}-api"
  region            = var.region
  vpc_id            = module.network.vpc_id
  vpc_cidr          = module.network.vpc_cidr
  subnet_ids        = module.network.public_subnet_ids
  certificate_arn   = var.api_certificate_arn
  container_port    = local.api_port
  health_check_path = "/v1/health"
}

module "api" {
  count                 = var.enable_api ? 1 : 0
  source                = "../../modules/service"
  prefix                = "${local.prefix}-api"
  region                = var.region
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.public_subnet_ids
  alb_security_group_id = module.alb[0].security_group_id
  target_group_arn      = module.alb[0].target_group_arn
  image                 = "${module.ecr.repository_url}:${var.api_image_tag}"
  desired_count         = var.api_desired_count
  container_port        = local.api_port
  files_bucket_arn      = module.storage.bucket_arn
  agent_runtime_arns    = local.runtime_arns

  environment = {
    APP_ENV          = "dev"
    PORT             = tostring(local.api_port)
    APP_ORIGIN       = local.app_origin
    FILES_BUCKET     = module.storage.bucket_name
    GOOGLE_CLIENT_ID = var.google_client_id
    AWS_REGION       = var.region
  }

  secrets = {
    DATABASE_URL        = module.secrets.arns["database-url"]
    DATABASE_URL_DIRECT = module.secrets.arns["database-url-direct"]
    SESSION_SIGNING_KEY = module.secrets.arns["session-key"]
  }
}

module "web" {
  source = "../../modules/amplify"
  name   = "${local.prefix}-web-amplify-${var.region}"
  environment_variables = {
    VITE_API_URL          = "https://${local.api_domain}"
    VITE_GOOGLE_CLIENT_ID = var.google_client_id
  }
}

resource "aws_budgets_budget" "monthly" {
  count        = var.budget_alert_email == "" ? 0 : 1
  name         = "${local.prefix}-monthly-budget-${var.region}"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # The account is shared with other projects: count only resources tagged Project=fleet (D26).
  # Needs `Project` activated as a cost allocation tag in the organization's management account;
  # until then this budget sees $0.
  cost_filter {
    name   = "TagKeyValue"
    values = [format("user:Project$%s", var.project)] # user:Project$fleet
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}
