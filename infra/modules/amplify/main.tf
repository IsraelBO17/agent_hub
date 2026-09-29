# Amplify Hosting app for the SPA in web/ (D13, D24). The branch, the GitHub connection and the custom domain
# (fleet.programmeos.com) are added in step 8, when web/ exists.

variable "name" {
  type = string
}

variable "environment_variables" {
  description = "Build-time settings for the SPA (VITE_*). Not secret: they ship to the browser."
  type        = map(string)
  default     = {}
}

resource "aws_amplify_app" "this" {
  name     = var.name
  platform = "WEB"

  build_spec = <<-YAML
    version: 1
    applications:
      - appRoot: web
        frontend:
          phases:
            preBuild:
              commands:
                - npm ci
            build:
              commands:
                - npm run build
          artifacts:
            baseDirectory: dist
            files:
              - '**/*'
          cache:
            paths:
              - node_modules/**/*
  YAML

  environment_variables = merge({ AMPLIFY_MONOREPO_APP_ROOT = "web" }, var.environment_variables)

  # SPA: every path without a file extension serves index.html (React Router).
  custom_rule {
    source = "</^[^.]+$|\\.(?!(css|gif|ico|jpg|jpeg|js|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>"
    target = "/index.html"
    status = "200"
  }
}

output "app_id" {
  value = aws_amplify_app.this.id
}

output "default_domain" {
  value = aws_amplify_app.this.default_domain
}
