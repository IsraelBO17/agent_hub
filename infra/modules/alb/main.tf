# Public ALB for the API (D2, D5, P2). Its certificate and DNS live outside: the names are CNAMEs in the
# qucoon.com zone, managed by its owner in another account (D25).
# Idle timeout and deregistration delay are explicit because SSE and deploy draining depend on them.

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

variable "vpc_cidr" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "certificate_arn" {
  description = "ACM certificate for the API host name, validated by a CNAME in the qucoon.com zone."
  type        = string
}

variable "container_port" {
  type = number
}

variable "health_check_path" {
  type = string
}

variable "idle_timeout_seconds" {
  description = "Well above the 15 s SSE keep-alive (D5)."
  type        = number
  default     = 300
}

variable "deregistration_delay_seconds" {
  description = "Lets open streams finish during a deploy (P2)."
  type        = number
  default     = 300
}

resource "aws_security_group" "alb" {
  name        = "${var.prefix}-alb-sg-${var.region}"
  description = "Public HTTPS to the API load balancer"
  vpc_id      = var.vpc_id
  tags        = { Name = "${var.prefix}-alb-sg-${var.region}" }
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.alb.id
  description       = "Redirected to HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "to_tasks" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "tcp"
  from_port         = var.container_port
  to_port           = var.container_port
}

resource "aws_lb" "this" {
  name                       = "${var.prefix}-alb-${var.region}" # 32-character limit
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.alb.id]
  subnets                    = var.subnet_ids
  idle_timeout               = var.idle_timeout_seconds
  drop_invalid_header_fields = true
}

resource "aws_lb_target_group" "api" {
  name                 = "${var.prefix}-tg-${var.region}" # 32-character limit
  vpc_id               = var.vpc_id
  target_type          = "ip"
  protocol             = "HTTP"
  port                 = var.container_port
  deregistration_delay = var.deregistration_delay_seconds

  health_check {
    path                = var.health_check_path
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

# Waits until the certificate is ISSUED (its validation CNAME is in place), so the HTTPS listener
# never references a pending certificate.
resource "aws_acm_certificate_validation" "api" {
  certificate_arn = var.certificate_arn
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.api.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      protocol    = "HTTPS"
      port        = "443"
      status_code = "HTTP_301"
    }
  }
}

output "security_group_id" {
  value = aws_security_group.alb.id
}

output "target_group_arn" {
  value = aws_lb_target_group.api.arn
}

output "https_listener_arn" {
  value = aws_lb_listener.https.arn
}

output "dns_name" {
  value = aws_lb.this.dns_name
}
