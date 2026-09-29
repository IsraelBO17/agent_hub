terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Partial config: the bucket name comes from infra/bootstrap (`make infra-init`).
  backend "s3" {
    key          = "dev/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true # native S3 locking, no DynamoDB table (D14)
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Owner        = var.owner
      Project      = var.project
      Environment  = var.environment
      "aws-apn-id" = var.aws_apn_id
      ManagedBy    = "terraform"
    }
  }
}
