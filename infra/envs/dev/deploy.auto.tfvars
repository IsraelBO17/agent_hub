# Deploy values for dev, committed on purpose: none of them is secret (D27: runtime ARNs aren't secret).
# Tag values and other private inputs stay in the gitignored terraform.tfvars (D26).
# Terraform loads *.auto.tfvars after terraform.tfvars, so these win.

enable_api        = true
api_desired_count = 1
api_image_tag     = "dcb9559" # git SHA of the commit the image was built from (ECR tags are immutable)

agent_runtime_arns = [
  "arn:aws:bedrock-agentcore:us-east-1:992382810653:runtime/fleet_dev_research_analyst_runtime_us_east_1-J5QFpm41XD",
]

# Phase 1 creates only the certificate; set true once ACM shows it Issued (D25, infra/README.md).
api_certificate_issued = false
