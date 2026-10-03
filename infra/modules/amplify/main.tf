# Amplify Hosting for the SPA in web/ (D13, D24, WEB_PROFILE Hosting): the app with its monorepo build spec, SPA
# rewrite and security headers, the branch it deploys, and the custom domain.
#
# The GitHub connection is made once outside Terraform (infra/README.md): Amplify's GitHub App is installed on
# the repository, and `aws amplify update-app --repository ... --access-token ...` hands Amplify a short-lived
# token it doesn't keep. Terraform only records the repository URL, so no token is ever in state.

variable "name" {
  description = "Full app name (D26), e.g. fleet-dev-web-amplify-us-east-1."
  type        = string
}

variable "environment_variables" {
  description = "Build-time settings for the SPA (VITE_*). Not secret: they ship to the browser."
  type        = map(string)
  default     = {}
}

variable "repository" {
  description = "The GitHub repository Amplify builds, e.g. https://github.com/owner/repo. Empty: not connected yet."
  type        = string
  default     = ""
}

variable "branch" {
  description = "The branch Amplify builds and deploys on every push. Created only once the repository is connected."
  type        = string
  default     = "main"
}

variable "domain" {
  description = "The custom domain, e.g. fleet.qucoon.com. Empty: the Amplify default domain only."
  type        = string
  default     = ""
}

variable "content_security_policy" {
  description = "The Content-Security-Policy header for every response (web standard §19)."
  type        = string
}

locals {
  connected = var.repository != ""
}

resource "aws_amplify_app" "this" {
  name       = var.name
  platform   = "WEB"
  repository = local.connected ? var.repository : null

  # Monorepo (web/): Node from web/.nvmrc, a clean install from the lockfile, the git SHA as the release.
  build_spec = <<-YAML
    version: 1
    applications:
      - appRoot: web
        frontend:
          phases:
            preBuild:
              commands:
                - nvm install "$(cat .nvmrc)"
                - nvm use "$(cat .nvmrc)"
                - npm ci --cache .npm --prefer-offline
            build:
              commands:
                - export VITE_RELEASE="$AWS_COMMIT_ID"
                - npm run build
          artifacts:
            baseDirectory: dist
            files:
              - '**/*'
          cache:
            paths:
              - .npm/**/*
  YAML

  # Empty values are left out (Amplify rejects them), e.g. the Google client ID before it exists.
  environment_variables = merge(
    { AMPLIFY_MONOREPO_APP_ROOT = "web" },
    { for k, v in var.environment_variables : k => v if v != "" },
  )

  # SPA: every path without a file extension serves index.html (React Router).
  custom_rule {
    source = "</^[^.]+$|\\.(?!(css|gif|ico|jpg|jpeg|js|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>"
    target = "/index.html"
    status = "200"
  }

  # Web standard §19 and §24: security headers everywhere, long caching for hashed assets, none for the page.
  custom_headers = <<-YAML
    customHeaders:
      - pattern: '**'
        headers:
          - key: Content-Security-Policy
            value: "${var.content_security_policy}"
          - key: Strict-Transport-Security
            value: max-age=31536000; includeSubDomains
          - key: X-Content-Type-Options
            value: nosniff
          - key: Referrer-Policy
            value: strict-origin-when-cross-origin
          - key: Permissions-Policy
            value: camera=(), geolocation=(), microphone=(self), payment=(), usb=()
          - key: Cache-Control
            value: no-cache
      - pattern: '/assets/**'
        headers:
          - key: Cache-Control
            value: public, max-age=31536000, immutable
  YAML
}

resource "aws_amplify_branch" "this" {
  count             = local.connected ? 1 : 0
  app_id            = aws_amplify_app.this.id
  branch_name       = var.branch
  stage             = "DEVELOPMENT" # one environment, dev, until v1 (D17)
  framework         = "React"
  enable_auto_build = true
}

# fleet.qucoon.com is a CNAME in the qucoon.com zone, which another account manages (D25), so Terraform doesn't
# wait for verification: it outputs the records, and the zone's owner adds them.
resource "aws_amplify_domain_association" "this" {
  count                  = local.connected && var.domain != "" ? 1 : 0
  app_id                 = aws_amplify_app.this.id
  domain_name            = var.domain
  enable_auto_sub_domain = false
  wait_for_verification  = false

  certificate_settings {
    type = "AMPLIFY_MANAGED"
  }

  sub_domain {
    branch_name = aws_amplify_branch.this[0].branch_name
    prefix      = ""
  }
}

output "app_id" {
  value = aws_amplify_app.this.id
}

output "default_domain" {
  value = aws_amplify_app.this.default_domain
}

output "branch_url" {
  description = "The branch on the Amplify default domain, e.g. https://main.<app id>.amplifyapp.com."
  value       = local.connected ? "https://${var.branch}.${aws_amplify_app.this.default_domain}" : null
}

# The records Amplify needs, for the zone's owner. Amplify reports each as "name CNAME value"; the root of the
# association (prefix "") has no name, and a sub-domain's name is relative to the domain.
locals {
  dns_raw = flatten([
    for d in aws_amplify_domain_association.this : concat(
      [{ purpose = "the web app's certificate", parts = split(" ", trimspace(d.certificate_verification_dns_record)) }],
      [for s in d.sub_domain : { purpose = "the web app", parts = split(" ", trimspace(s.dns_record)) }],
    )
  ])
}

output "dns_records" {
  value = [for r in local.dns_raw : {
    purpose = r.purpose
    name    = upper(r.parts[0]) == "CNAME" ? "${var.domain}." : endswith(r.parts[0], ".") ? r.parts[0] : "${r.parts[0]}.${var.domain}."
    type    = "CNAME"
    value   = r.parts[length(r.parts) - 1]
  } if length(r.parts) >= 2]
}
