# The API on ECS Fargate: cluster, task definition, service, logs, IAM and the task security group (D2, P2, P7).
# One task, no autoscaling in v1 (P7). desired_count stays 0 until step 8 pushes the first image.

variable "prefix" {
  description = "<project>-<environment>-<component>, e.g. fleet-dev-api. Names end with -<type>-<region> (D26)."
  type        = string
}

variable "region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "target_group_arn" {
  type = string
}

variable "image" {
  description = "Full image reference, e.g. <ecr url>:<git sha>."
  type        = string
}

variable "desired_count" {
  type = number
}

variable "cpu" {
  type    = number
  default = 256
}

variable "memory" {
  type    = number
  default = 512
}

variable "container_port" {
  type = number
}

variable "environment" {
  description = "Plain environment variables."
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Environment variable name => Secrets Manager ARN, injected at task start (D15)."
  type        = map(string)
  default     = {}
}

variable "files_bucket_arn" {
  type = string
}

variable "agent_runtime_arns" {
  description = "AgentCore runtimes the API may invoke."
  type        = list(string)
}

variable "log_retention_days" {
  type    = number
  default = 14
}

locals {
  container_name = "api"
}

# ---- Logs
resource "aws_cloudwatch_log_group" "api" {
  name              = "${var.prefix}-logs-${var.region}"
  retention_in_days = var.log_retention_days
}

# ---- IAM: execution role (pull image, write logs, read secrets at start)
data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.prefix}-exec-role-${var.region}"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "execution_secrets" {
  count = length(var.secrets) > 0 ? 1 : 0
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = values(var.secrets)
  }
}

resource "aws_iam_role_policy" "execution_secrets" {
  count  = length(var.secrets) > 0 ? 1 : 0
  name   = "read-secrets"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution_secrets[0].json
}

# ---- IAM: task role (what the API itself may do)
resource "aws_iam_role" "task" {
  name               = "${var.prefix}-task-role-${var.region}"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

data "aws_iam_policy_document" "task" {
  statement {
    sid       = "Files"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.files_bucket_arn}/u/*"]
  }
  statement {
    sid     = "InvokeAgents"
    actions = ["bedrock-agentcore:InvokeAgentRuntime", "bedrock-agentcore:StopRuntimeSession"]
    # Exact ARNs only (D27): each runtime, and its DEFAULT endpoint, which a call with
    # qualifier=DEFAULT may also be authorised against.
    resources = concat(
      var.agent_runtime_arns,
      [for arn in var.agent_runtime_arns : "${arn}/runtime-endpoint/DEFAULT"],
    )
  }
}

resource "aws_iam_role_policy" "task" {
  name   = "api"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task.json
}

# ---- Network
resource "aws_security_group" "task" {
  name        = "${var.prefix}-task-sg-${var.region}"
  description = "API tasks: inbound only from the ALB"
  vpc_id      = var.vpc_id
  tags        = { Name = "${var.prefix}-task-sg-${var.region}" }
}

resource "aws_vpc_security_group_ingress_rule" "from_alb" {
  security_group_id            = aws_security_group.task.id
  referenced_security_group_id = var.alb_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = var.container_port
  to_port                      = var.container_port
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.task.id
  description       = "Neon, Google, AgentCore, AWS APIs (no NAT, ARCHITECTURE section 2)" # EC2 rejects characters such as §
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# ---- ECS
resource "aws_ecs_cluster" "this" {
  name = "${var.prefix}-ecs-${var.region}"
  setting {
    name  = "containerInsights"
    value = "disabled" # cost; revisit with monitoring in step 9
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.prefix}-task-${var.region}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64" # Graviton: cheaper; images are built on arm64
  }

  container_definitions = jsonencode([{
    name         = local.container_name
    image        = var.image
    essential    = true
    stopTimeout  = 120 # ECS maximum: finish open streams after SIGTERM (P2)
    portMappings = [{ containerPort = var.container_port, protocol = "tcp" }]
    environment  = [for k, v in var.environment : { name = k, value = v }]
    secrets      = [for k, arn in var.secrets : { name = k, valueFrom = arn }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.api.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "api"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name                              = "${var.prefix}-svc-${var.region}"
  cluster                           = aws_ecs_cluster.this.id
  task_definition                   = aws_ecs_task_definition.api.arn
  desired_count                     = var.desired_count
  launch_type                       = "FARGATE"
  health_check_grace_period_seconds = 30
  enable_ecs_managed_tags           = true
  propagate_tags                    = "SERVICE" # tasks carry the required tags too (D26)

  # Rolling deploy: the new task starts before the old one drains (P2, B3).
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.task.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = local.container_name
    container_port   = var.container_port
  }
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "service_name" {
  value = aws_ecs_service.api.name
}

output "task_role_arn" {
  value = aws_iam_role.task.arn
}

output "execution_role_arn" {
  value = aws_iam_role.execution.arn
}

output "log_group" {
  value = aws_cloudwatch_log_group.api.name
}
