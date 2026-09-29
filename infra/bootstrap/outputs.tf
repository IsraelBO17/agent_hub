output "state_bucket" {
  description = "Pass to `terraform init -backend-config=bucket=...` in infra/envs/*."
  value       = aws_s3_bucket.state.bucket
}

output "zone_id" {
  value = aws_route53_zone.fleet.zone_id
}

output "name_servers" {
  description = "Add one NS record named `fleet` per value in GoDaddy DNS for programmeos.com."
  value       = aws_route53_zone.fleet.name_servers
}
