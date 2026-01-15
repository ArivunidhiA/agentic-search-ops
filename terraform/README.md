# Terraform Deployment - Agentic Search Ops

Deploy the complete Knowledge Base system to AWS with a single command.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  CloudFront  │────▶│  S3 Frontend │     │  S3 Storage  │    │
│  │     CDN      │     │   (React)    │     │  (Documents) │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                                         ▲             │
│         │                                         │             │
│         ▼                                         │             │
│  ┌──────────────┐                                │             │
│  │    Users     │                                │             │
│  └──────────────┘                                │             │
│         │                                         │             │
│         ▼                                         │             │
│  ┌──────────────┐     ┌──────────────┐          │             │
│  │   EC2 t2.micro   │────▶│  RDS PostgreSQL │          │             │
│  │   (FastAPI)  │     │   (db.t3.micro) │◀─────────┘             │
│  └──────────────┘     └──────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Terraform** installed:
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   
   # Verify
   terraform version
   ```

2. **AWS CLI** configured:
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (us-east-1)
   ```

3. **SSH Key Pair** in AWS:
   ```bash
   # Create new key pair (if needed)
   aws ec2 create-key-pair --key-name agentic-search-ops-key --query 'KeyMaterial' --output text > ~/.ssh/agentic-search-ops-key.pem
   chmod 400 ~/.ssh/agentic-search-ops-key.pem
   ```

4. **IAM Role** created:
   - Name: `ClaudeKBServiceRole`
   - Permissions: EC2, S3, RDS, Secrets Manager access

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_prefix      = "yourusername"        # Unique prefix for resources
aws_region          = "us-east-1"
ec2_key_pair_name   = "your-key-pair-name"  # Your SSH key pair
allowed_ssh_cidr    = "YOUR_IP/32"          # Your IP address
```

Get your IP:
```bash
curl https://checkip.amazonaws.com
```

### 3. Preview Changes

```bash
terraform plan
```

### 4. Deploy Everything

```bash
terraform apply
```

Type `yes` when prompted. This creates:
- EC2 instance (t2.micro)
- RDS PostgreSQL (db.t3.micro)
- S3 buckets (storage + frontend)
- CloudFront distribution
- Security groups
- Secrets Manager for DB password

### 5. Post-Deployment Setup

```bash
cd ../deploy
chmod +x *.sh
./post_terraform_setup.sh
```

Follow the instructions to:
- Clone the repository to EC2
- Configure environment variables
- Start the backend service

### 6. Deploy Frontend

```bash
./deploy_frontend.sh
```

## Estimated Time

| Step | Duration |
|------|----------|
| Terraform init | 30 seconds |
| Terraform apply | 10-15 minutes |
| Post-setup | 10 minutes |
| **Total** | **20-25 minutes** |

## Estimated Cost

### Free Tier (First 12 months)
- EC2 t2.micro: **750 hours/month FREE**
- RDS db.t3.micro: **750 hours/month FREE**
- S3: **5GB FREE**
- CloudFront: **1TB/month FREE**

**Total: $0/month** (within Free Tier limits)

### After Free Tier
| Service | Monthly Cost |
|---------|-------------|
| EC2 t2.micro | ~$8.50 |
| RDS db.t3.micro | ~$12.50 |
| S3 (5GB) | ~$0.12 |
| CloudFront | ~$0.50 |
| **Total** | **~$22/month** |

## Terraform Outputs

After deployment, get useful information:

```bash
# All outputs
terraform output

# Specific outputs
terraform output ec2_public_ip
terraform output cloudfront_url
terraform output ec2_ssh_command
```

## Common Commands

```bash
# SSH into EC2
ssh -i ~/.ssh/your-key.pem ubuntu@$(terraform output -raw ec2_public_ip)

# View backend logs
sudo journalctl -u claude-kb -f

# Check backend status
sudo systemctl status claude-kb

# Restart backend
sudo systemctl restart claude-kb
```

## Troubleshooting

### EC2 not accessible
- Check security group allows your IP for SSH
- Verify key pair name is correct
- Wait 2-3 minutes after creation for full startup

### RDS connection fails
- RDS is private, only accessible from EC2
- Check security group allows PostgreSQL from EC2 SG
- Verify DATABASE_URL in .env file

### CloudFront showing old content
- Invalidate cache: `aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"`
- Wait 10-15 minutes for propagation

### Backend not starting
```bash
# Check logs
sudo journalctl -u claude-kb -n 100

# Check .env file
cat /opt/claude-kb/.env

# Test manually
cd /opt/claude-kb/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Destroy Resources

**Warning: This deletes ALL resources including data!**

```bash
terraform destroy
```

Type `yes` when prompted.

## Security Notes

- RDS is not publicly accessible (EC2 only)
- S3 storage bucket is private with encryption
- DB password stored in AWS Secrets Manager
- SSH restricted to specified IP range
- All traffic to CloudFront forced to HTTPS

## File Structure

```
terraform/
├── README.md              # This file
├── main.tf                # Provider config, data sources
├── variables.tf           # Input variables
├── outputs.tf             # Resource outputs
├── terraform.tfvars.example # Config template
├── security_groups.tf     # Firewall rules
├── ec2.tf                 # Backend server
├── rds.tf                 # PostgreSQL database
├── s3.tf                  # Storage buckets
├── cloudfront.tf          # CDN distribution
└── user_data.sh           # EC2 initialization script

deploy/
├── post_terraform_setup.sh # Run after terraform apply
├── deploy_backend.sh       # Deploy backend updates
├── deploy_frontend.sh      # Build and deploy frontend
└── backend.service         # Systemd service file
```
