# Created once, by hand, before anything else (D14): the S3 bucket that holds the dev environment's
# Terraform state (native S3 locking, no DynamoDB table). DNS is not here: fleet's names are CNAMEs in
# the qucoon.com zone, managed in another account (D25).
# State for this folder stays local (gitignored). If it is lost, import the bucket.
# Names: <project>-<environment>-<component>-<type>-<region> (D26).

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

locals {
  prefix = "${var.project}-${var.environment}"
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

resource "aws_s3_bucket" "state" {
  bucket = "${local.prefix}-tfstate-s3-${var.region}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.state]
}

resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# The delegated zone (the first design of D25) was deleted outside Terraform and replaced by CNAMEs in the
# qucoon.com zone. Forget it without trying to destroy anything.
removed {
  from = aws_route53_zone.fleet
  lifecycle {
    destroy = false
  }
}
