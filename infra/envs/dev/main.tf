# The dev environment, the only one until v1 (D17). Apply order and the manual steps: infra/README.md.

data "aws_caller_identity" "current" {}

data "aws_route53_zone" "fleet" {
  name = var.zone_name
}

locals {
  prefix     = "${var.project}-${var.environment}" # names: <prefix>-<component>-<type>-<region> (D26)
  app_domain = var.zone_name                       # https://fleet.qucoon.com (Amplify, step 8)
  api_domain = "api.${var.zone_name}"              # https://api.fleet.qucoon.com (ALB)
  app_origin = "https://${local.app_domain}"
  api_port   = 8000
  account_id = data.aws_caller_identity.current.account_id
  runtime_arns = length(var.agent_runtime_arns) > 0 ? var.agent_runtime_arns : [
    "arn:aws:bedrock-agentcore:${var.region}:${local.account_id}:runtime/*",
  ]
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

module "alb" {
  count             = var.enable_api ? 1 : 0
  source            = "../../modules/alb"
  prefix            = "${local.prefix}-api"
  region            = var.region
  vpc_id            = module.network.vpc_id
  vpc_cidr          = module.network.vpc_cidr
  subnet_ids        = module.network.public_subnet_ids
  zone_id           = data.aws_route53_zone.fleet.zone_id
  domain            = local.api_domain
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
