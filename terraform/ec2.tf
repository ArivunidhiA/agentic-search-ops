# ==============================================================================
# EC2 INSTANCE
# ==============================================================================

resource "aws_instance" "backend" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  key_name               = var.ec2_key_pair_name
  vpc_security_group_ids = [aws_security_group.ec2.id]
  
  # IAM instance profile for S3 and Secrets Manager access
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
  
  # User data script for initial setup
  user_data = file("${path.module}/user_data.sh")
  
  # Root volume configuration
  root_block_device {
    volume_size           = var.ec2_root_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
    
    tags = {
      Name = "${var.project_prefix}-kb-backend-root"
    }
  }

  # Monitoring
  monitoring = false # Detailed monitoring costs extra

  # Metadata options (IMDSv2 for security)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "${var.project_prefix}-kb-backend"
  }

  lifecycle {
    ignore_changes = [ami] # Don't recreate on AMI updates
  }
}

# ==============================================================================
# ELASTIC IP (Stable public IP)
# ==============================================================================

resource "aws_eip" "backend" {
  instance = aws_instance.backend.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_prefix}-kb-backend-eip"
  }

  depends_on = [aws_instance.backend]
}

# ==============================================================================
# IAM INSTANCE PROFILE (Optional - for S3/Secrets access)
# ==============================================================================

# Create IAM role for EC2
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_prefix}-kb-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.project_prefix}-kb-ec2-role"
  }
}

# Policy for S3 access
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_prefix}-kb-s3-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.storage.arn,
          "${aws_s3_bucket.storage.arn}/*"
        ]
      }
    ]
  })
}

# Policy for Secrets Manager access
resource "aws_iam_role_policy" "secrets_access" {
  name = "${var.project_prefix}-kb-secrets-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn
        ]
      }
    ]
  })
}

# Instance profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_prefix}-kb-ec2-profile"
  role = aws_iam_role.ec2_role.name
}
