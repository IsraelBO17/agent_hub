# Deploy values for dev, committed on purpose: none of them is secret (D27: runtime ARNs aren't secret).
# Tag values and other private inputs stay in the gitignored terraform.tfvars (D26).
# Terraform loads *.auto.tfvars after terraform.tfvars, so these win.

enable_api        = true
api_desired_count = 1
api_image_tag     = "8440c4f" # git SHA the image was built from; after the rebase onto main the same api/ tree is commit 57f7f02 (also tagged in ECR)

# qucoon's shared wildcard certificate (*.qucoon.com), owned by the qucoon cloud team (D25).
api_certificate_arn = "arn:aws:acm:us-east-1:992382810653:certificate/14063ea3-87d8-4f3e-bd3e-6f76dc640b81"

agent_runtime_arns = [
  "arn:aws:bedrock-agentcore:us-east-1:992382810653:runtime/fleet_dev_research_analyst_runtime_us_east_1-J5QFpm41XD",
]
