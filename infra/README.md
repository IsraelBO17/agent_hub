# Infrastructure (Terraform)

AWS us-east-1, one environment (`dev`) until v1 (D17). Decisions: `docs/ARCHITECTURE.md` D2, D3, D5, D7, D13–D15, D25, D26, §2 and P2.

Names follow `fleet-<environment>-<component>-<type>-<region>` (e.g. `fleet-dev-api-alb-us-east-1`); every resource carries the tags `Owner`, `Project`, `Environment`, `aws-apn-id` and `ManagedBy` (D26).

```
bootstrap/        Created once: Terraform state bucket + Route 53 zone for fleet.qucoon.com. Local state.
envs/dev/         The dev environment. State in the bootstrap bucket (native S3 locking).
modules/
  network/        VPC, 2 public subnets, internet gateway. No NAT gateway.
  ecr/            API image repository (immutable tags, scan on push, keep 15).
  storage/        Private files bucket (uploads, artifacts, exports), CORS for the app origin.
  secrets/        Secrets Manager containers; values are set by hand, never through Terraform.
  alb/            Public ALB: HTTPS (ACM), HTTP→HTTPS, idle timeout 300 s, drain 300 s, api.fleet.qucoon.com.
  service/        ECS cluster, task definition (ARM64, stopTimeout 120 s), service, logs, IAM, task security group.
  amplify/        Amplify app for web/ (branch, GitHub and custom domain come in step 8).
```

## First-time setup

Nothing here is applied without the owner's go-ahead on the plan output.

1. **Pick the AWS profile** for every command below: `export AWS_PROFILE=<profile>` and check it with `aws sts get-caller-identity`.
   Then copy `bootstrap/terraform.tfvars.example` and `envs/dev/terraform.tfvars.example` to `terraform.tfvars` in the same folders and fill in the required tags (`owner`, `aws_apn_id`; D26). Those files are gitignored: the repo is public.
2. **Bootstrap:**
   ```bash
   make infra-plan-bootstrap
   ```
   ```bash
   terraform -chdir=infra/bootstrap apply
   ```
   It prints `name_servers`.
3. **Delegate `fleet` (whoever manages `qucoon.com`, in its Route 53 zone in the other AWS account):** add one record of type `NS`, name `fleet`, with the four `name_servers` values, TTL 3600. Check with `dig +short NS fleet.qucoon.com`. Needed before `enable_api = true` (the API certificate is validated through this zone); it can be done any time before step 8.
4. **Dev environment:** copy `envs/dev/terraform.tfvars.example` to `envs/dev/terraform.tfvars` and fill it in, then:
   ```bash
   make infra-init
   ```
   ```bash
   make infra-plan
   ```
   ```bash
   terraform -chdir=infra/envs/dev apply
   ```
   With `enable_api = false` (the default) this creates the network, ECR, the files bucket, the secrets and the Amplify app; no load balancer and no ECS service.
5. **Secret values** (by hand, never in Terraform or git): for each name in the `secret_names` output,
   ```bash
   aws secretsmanager put-secret-value --secret-id fleet-dev-session-key-secret-us-east-1 --secret-string "$(openssl rand -base64 48)"
   ```
   The two Neon connection strings are set once the Neon project exists (step 8).

## Turning the API on (step 8)

Two switches, so nothing is billed before it's needed:

| Variable | Default | Effect |
|---|---|---|
| `enable_api` | `false` | Creates the ALB, its certificate and `api.fleet.qucoon.com`, the ECS cluster, task definition, service and their IAM roles. Needs step 3 done (the certificate validates through the delegated zone). |
| `api_desired_count` | `0` | Number of API tasks. Set to `1` once an image is in ECR (P7: one task, no autoscaling). |

## Monthly cost, dev (us-east-1, 730 h, checked 2026-09-29)

| Resource | Price | `enable_api = false` | API running |
|---|---|---|---|
| ALB, hourly | $0.0225/h | $0 | $16.43 |
| ALB capacity units | $0.008 per unit-hour | $0 | < $1 |
| Public IPv4 on the ALB (2 zones) | $0.005/h each | $0 | $7.30 |
| Fargate ARM64, 0.25 vCPU / 0.5 GB, one task | $0.03238 vCPU-h + $0.00356 GB-h | $0 | $7.21 |
| Public IPv4 on the task | $0.005/h | $0 | $3.65 |
| Secrets Manager (3) | $0.40 each | $1.20 | $1.20 |
| Route 53 zone | $0.50 + queries | $0.50 | $0.50 |
| ECR, S3, CloudWatch Logs, Amplify | usage | < $1 | < $2 |
| VPC, subnets, internet gateway, security groups, IAM, ECS cluster, ACM, budget | free | $0 | $0 |
| **Total** | | **≈ $2** | **≈ $37** |

The ALB and its two addresses are about two-thirds of the running cost; cheaper setups were weighed and rejected in ARCHITECTURE D2. Budget alarm: 80 % of $50 actual and 100 % forecast, to `budget_alert_email`. Model tokens and Neon are billed separately.

## Everyday

```bash
make infra-validate
```
```bash
make infra-plan
```
