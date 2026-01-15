# ==============================================================================
# EC2 SECURITY GROUP
# ==============================================================================

resource "aws_security_group" "ec2" {
  name        = "${var.project_prefix}-kb-ec2-sg"
  description = "Security group for Agentic Search Ops backend"
  vpc_id      = data.aws_vpc.default.id

  # SSH access (restricted to specified CIDR)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "SSH access from allowed CIDR"
  }

  # HTTP access (for backend API)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access for API"
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }

  # Backend API port (8000/8001)
  ingress {
    from_port   = 8000
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Backend API ports"
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_prefix}-kb-ec2-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ==============================================================================
# RDS SECURITY GROUP
# ==============================================================================

resource "aws_security_group" "rds" {
  name        = "${var.project_prefix}-kb-rds-sg"
  description = "Security group for Agentic Search Ops RDS"
  vpc_id      = data.aws_vpc.default.id

  # PostgreSQL access from EC2 only (more secure)
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
    description     = "PostgreSQL access from EC2 instances"
  }

  # No outbound rules needed for RDS (it's a managed service)
  
  tags = {
    Name = "${var.project_prefix}-kb-rds-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}
