output "state_bucket" {
  description = "Pass to `terraform init -backend-config=bucket=...` in infra/envs/*."
  value       = aws_s3_bucket.state.bucket
}
