# ==============================================================================
# RDS POSTGRESQL INSTANCE
# ==============================================================================

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_prefix}-kb-db"
  
  # Engine configuration
  engine         = "postgres"
  engine_version = var.rds_engine_version
  
  # Instance configuration (Free Tier eligible)
  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true
  
  # Database configuration
  db_name  = "agentic_search_ops"
  username = "postgres"
  password = random_password.db_password.result
  port     = 5432
  
  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false # More secure - only accessible from EC2
  
  # Backup configuration
  backup_retention_period = var.rds_backup_retention_period
  backup_window          = "03:00-04:00"        # 3-4 AM UTC
  maintenance_window     = "mon:04:00-mon:05:00" # Monday 4-5 AM UTC
  
  # Snapshot configuration
  skip_final_snapshot       = true # Set to false for production
  final_snapshot_identifier = "${var.project_prefix}-kb-db-final-snapshot"
  delete_automated_backups  = true
  
  # Performance configuration
  performance_insights_enabled = false # Costs extra
  
  # Deletion protection (enable for production)
  deletion_protection = false
  
  # Apply changes immediately (set to false for production)
  apply_immediately = true
  
  # Enable auto minor version upgrades
  auto_minor_version_upgrade = true

  tags = {
    Name = "${var.project_prefix}-kb-db"
  }

  lifecycle {
    ignore_changes = [password] # Don't recreate on password changes
  }
}
