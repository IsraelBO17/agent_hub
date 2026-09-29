# VPC with public subnets only: no NAT gateway (ARCHITECTURE §2). Tasks get public IPs; security groups do the fencing.

variable "prefix" {
  description = "<project>-<environment>, e.g. fleet-dev (D26)."
  type        = string
}

variable "region" {
  type = string
}

variable "cidr" {
  type = string
}

variable "az_count" {
  description = "An ALB needs at least two availability zones."
  type        = number
  default     = 2
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block           = var.cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.prefix}-main-vpc-${var.region}" }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.prefix}-main-igw-${var.region}" }
}

resource "aws_subnet" "public" {
  count                   = var.az_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = false # ECS assigns public IPs per task; nothing else lives here
  tags                    = { Name = "${var.prefix}-public-${substr(data.aws_availability_zones.available.names[count.index], -1, 1)}-subnet-${var.region}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
  tags = { Name = "${var.prefix}-public-rt-${var.region}" }
}

resource "aws_route_table_association" "public" {
  count          = var.az_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "vpc_cidr" {
  value = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}
