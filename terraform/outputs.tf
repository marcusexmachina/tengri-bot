output "lightsail_public_ip" {
  description = "Public IP of the Lightsail instance"
  value       = aws_lightsail_static_ip.tengri.ip_address
}

output "lightsail_ssh_key_path" {
  description = "Save the private key to a file and chmod 600. Add to GitHub Secrets as SSH_PRIVATE_KEY."
  value       = "terraform output -raw lightsail_private_key > tengri-key.pem && chmod 600 tengri-key.pem"
}

output "lightsail_private_key" {
  description = "Private key for SSH (sensitive)"
  value       = aws_lightsail_key_pair.tengri.private_key
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing images"
  value       = aws_ecr_repository.tengri.repository_url
}

output "ecr_registry" {
  description = "ECR registry ID for login"
  value       = aws_ecr_repository.tengri.registry_id
}

output "s3_backup_bucket" {
  description = "S3 bucket for backups"
  value       = aws_s3_bucket.backups.id
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC"
  value       = aws_iam_role.github_actions.arn
}

output "host_access_key_id" {
  description = "AWS access key for host (ECR pull + S3 backup). Add to host via setup script."
  value       = aws_iam_access_key.host.id
}

output "host_secret_access_key" {
  description = "AWS secret for host (run once: terraform output -raw host_secret_access_key)"
  value       = aws_iam_access_key.host.secret
  sensitive   = true
}
