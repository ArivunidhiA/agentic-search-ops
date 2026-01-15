# ==============================================================================
# REQUIRED VARIABLES
# ==============================================================================

variable "project_prefix" {
  description = "Unique prefix for resource names (e.g., your-username). Must be lowercase."
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_prefix))
    error_message = "Project prefix must be lowercase alphanumeric with hyphens only."
  }
}

variable "ec2_key_pair_name" {
  description = "Name of existing EC2 key pair for SSH access"
  type        = string
}

# ==============================================================================
# AWS CONFIGURATION
# ==============================================================================

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be production, staging, or development."
  }
}

# ==============================================================================
# EC2 CONFIGURATION
# ==============================================================================

variable "ec2_instance_type" {
  description = "EC2 instance type (t2.micro is Free Tier eligible)"
  type        = string
  default     = "t2.micro"
}

variable "ec2_root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 20
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH (use YOUR_IP/32 for security)"
  type        = string
  default     = "0.0.0.0/0"
}

# ==============================================================================
# RDS CONFIGURATION
# ==============================================================================

variable "rds_instance_class" {
  description = "RDS instance class (db.t3.micro is Free Tier eligible)"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS storage allocation in GB (20 GB is Free Tier)"
  type        = number
  default     = 20
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "rds_backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

# ==============================================================================
# APPLICATION CONFIGURATION
# ==============================================================================

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude (will be stored in Secrets Manager)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "max_job_cost_usd" {
  description = "Maximum cost per job in USD"
  type        = number
  default     = 5.0
}

# ==============================================================================
# TAGS
# ==============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
