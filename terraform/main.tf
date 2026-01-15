# ==============================================================================
# TERRAFORM CONFIGURATION
# ==============================================================================

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# ==============================================================================
# AWS PROVIDER
# ==============================================================================

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "agentic-search-ops"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ==============================================================================
# DATA SOURCES
# ==============================================================================

# Get default VPC (using default for Free Tier simplicity)
data "aws_vpc" "default" {
  default = true
}

# Get default subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Get at least 2 availability zones for RDS subnet group
data "aws_availability_zones" "available" {
  state = "available"
}

# Get latest Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get current region
data "aws_region" "current" {}

# ==============================================================================
# RANDOM RESOURCES
# ==============================================================================

# Generate random password for RDS
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Generate random suffix for globally unique S3 bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# ==============================================================================
# SECRETS MANAGER
# ==============================================================================

# Store RDS password securely
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project_prefix}-kb-db-password-${random_id.bucket_suffix.hex}"
  description             = "Database password for Agentic Search Ops"
  recovery_window_in_days = 0 # Allow immediate deletion for dev
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "postgres"
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = 5432
    dbname   = "agentic_search_ops"
  })
}

# ==============================================================================
# DB SUBNET GROUP (Required for RDS)
# ==============================================================================

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_prefix}-kb-db-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name = "${var.project_prefix}-kb-db-subnet-group"
  }
}
