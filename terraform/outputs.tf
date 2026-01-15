# ==============================================================================
# EC2 OUTPUTS
# ==============================================================================

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.backend.id
}

output "ec2_public_ip" {
  description = "EC2 instance public IP (Elastic IP)"
  value       = aws_eip.backend.public_ip
}

output "ec2_private_ip" {
  description = "EC2 instance private IP"
  value       = aws_instance.backend.private_ip
}

output "ec2_ssh_command" {
  description = "SSH command to connect to EC2"
  value       = "ssh -i ~/.ssh/${var.ec2_key_pair_name}.pem ubuntu@${aws_eip.backend.public_ip}"
}

# ==============================================================================
# RDS OUTPUTS
# ==============================================================================

output "rds_endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "RDS instance address (host only)"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "database_url" {
  description = "Full database connection URL (password hidden)"
  value       = "postgresql://postgres:PASSWORD@${aws_db_instance.postgres.endpoint}/agentic_search_ops"
  sensitive   = true
}

# ==============================================================================
# S3 OUTPUTS
# ==============================================================================

output "storage_bucket_name" {
  description = "S3 storage bucket name"
  value       = aws_s3_bucket.storage.id
}

output "storage_bucket_arn" {
  description = "S3 storage bucket ARN"
  value       = aws_s3_bucket.storage.arn
}

output "frontend_bucket_name" {
  description = "S3 frontend bucket name"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_website_endpoint" {
  description = "S3 frontend bucket website endpoint"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

# ==============================================================================
# CLOUDFRONT OUTPUTS
# ==============================================================================

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_url" {
  description = "CloudFront URL (frontend)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

# ==============================================================================
# SECRETS MANAGER OUTPUTS
# ==============================================================================

output "db_password_secret_name" {
  description = "AWS Secrets Manager secret name for DB password"
  value       = aws_secretsmanager_secret.db_password.name
}

output "db_password_secret_arn" {
  description = "AWS Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.db_password.arn
}

# ==============================================================================
# SECURITY GROUP OUTPUTS
# ==============================================================================

output "ec2_security_group_id" {
  description = "EC2 security group ID"
  value       = aws_security_group.ec2.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

# ==============================================================================
# APPLICATION URLS
# ==============================================================================

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${aws_eip.backend.public_ip}"
}

output "backend_api_url" {
  description = "Backend API base URL"
  value       = "http://${aws_eip.backend.public_ip}/api/v1"
}

output "frontend_url" {
  description = "Frontend URL (CloudFront)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

# ==============================================================================
# DEPLOYMENT INFO
# ==============================================================================

output "deployment_info" {
  description = "Summary of deployment information"
  value = {
    region                = var.aws_region
    environment           = var.environment
    ec2_ip                = aws_eip.backend.public_ip
    rds_endpoint          = aws_db_instance.postgres.endpoint
    storage_bucket        = aws_s3_bucket.storage.id
    frontend_bucket       = aws_s3_bucket.frontend.id
    cloudfront_domain     = aws_cloudfront_distribution.frontend.domain_name
    db_password_secret    = aws_secretsmanager_secret.db_password.name
  }
}

# ==============================================================================
# HELPFUL COMMANDS
# ==============================================================================

output "helpful_commands" {
  description = "Useful commands for managing the deployment"
  value = <<-EOT
    
    # SSH into EC2:
    ssh -i ~/.ssh/${var.ec2_key_pair_name}.pem ubuntu@${aws_eip.backend.public_ip}
    
    # Get DB password:
    aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.db_password.name} --query SecretString --output text | jq -r .password
    
    # Deploy frontend:
    cd frontend && npm run build && aws s3 sync dist/ s3://${aws_s3_bucket.frontend.id} --delete
    
    # Invalidate CloudFront cache:
    aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.frontend.id} --paths "/*"
    
    # View backend logs:
    ssh -i ~/.ssh/${var.ec2_key_pair_name}.pem ubuntu@${aws_eip.backend.public_ip} "sudo journalctl -u claude-kb -f"
    
  EOT
}
