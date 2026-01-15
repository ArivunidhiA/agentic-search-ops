#!/bin/bash
# ==============================================================================
# POST-TERRAFORM SETUP SCRIPT
# Run this after 'terraform apply' completes
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Post-Terraform Setup ===${NC}"
echo ""

# ==============================================================================
# CHECK PREREQUISITES
# ==============================================================================

if [ ! -d "$TERRAFORM_DIR" ]; then
    echo -e "${RED}ERROR: Terraform directory not found at $TERRAFORM_DIR${NC}"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Check if terraform state exists
if [ ! -f "terraform.tfstate" ]; then
    echo -e "${RED}ERROR: terraform.tfstate not found. Run 'terraform apply' first.${NC}"
    exit 1
fi

# ==============================================================================
# EXTRACT TERRAFORM OUTPUTS
# ==============================================================================

echo -e "${YELLOW}Extracting Terraform outputs...${NC}"

EC2_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")
RDS_ENDPOINT=$(terraform output -raw rds_endpoint 2>/dev/null || echo "")
RDS_ADDRESS=$(terraform output -raw rds_address 2>/dev/null || echo "")
STORAGE_BUCKET=$(terraform output -raw storage_bucket_name 2>/dev/null || echo "")
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name 2>/dev/null || echo "")
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name 2>/dev/null || echo "")
SECRET_NAME=$(terraform output -raw db_password_secret_name 2>/dev/null || echo "")
KEY_PAIR=$(terraform output -raw ec2_ssh_command 2>/dev/null | grep -oP '(?<=-i )[^ ]+' | sed 's/.pem$//' || echo "your-key")

if [ -z "$EC2_IP" ]; then
    echo -e "${RED}ERROR: Could not get EC2 IP. Is terraform apply complete?${NC}"
    exit 1
fi

# ==============================================================================
# GET DATABASE PASSWORD
# ==============================================================================

echo -e "${YELLOW}Retrieving database password from Secrets Manager...${NC}"

DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --query SecretString \
    --output text 2>/dev/null | jq -r '.password' || echo "")

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}ERROR: Could not retrieve database password${NC}"
    echo "Make sure AWS CLI is configured and has access to Secrets Manager"
    exit 1
fi

# ==============================================================================
# DISPLAY DEPLOYMENT INFO
# ==============================================================================

echo ""
echo -e "${GREEN}=== Deployment Information ===${NC}"
echo ""
echo -e "  ${BLUE}EC2 IP:${NC}           $EC2_IP"
echo -e "  ${BLUE}RDS Endpoint:${NC}     $RDS_ENDPOINT"
echo -e "  ${BLUE}Storage Bucket:${NC}   $STORAGE_BUCKET"
echo -e "  ${BLUE}Frontend Bucket:${NC}  $FRONTEND_BUCKET"
echo -e "  ${BLUE}CloudFront URL:${NC}   https://$CLOUDFRONT_DOMAIN"
echo ""

# ==============================================================================
# GENERATE ENV FILE CONTENT
# ==============================================================================

ENV_CONTENT="# Database
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@${RDS_ENDPOINT}/agentic_search_ops

# Storage
S3_BUCKET_NAME=${STORAGE_BUCKET}
AWS_REGION=us-east-1

# Frontend URL
FRONTEND_URL=https://${CLOUDFRONT_DOMAIN}

# Anthropic API (add your key)
ANTHROPIC_API_KEY=

# Agent settings
MAX_JOB_COST_USD=5.0
MAX_JOB_RUNTIME_MINUTES=120

# Document processing
ENABLE_PDF_EXTRACTION=true
ENABLE_DOCX_EXTRACTION=true
ENABLE_EMBEDDINGS=false"

# ==============================================================================
# OUTPUT INSTRUCTIONS
# ==============================================================================

echo -e "${GREEN}=== Next Steps ===${NC}"
echo ""
echo -e "${YELLOW}1. SSH into EC2:${NC}"
echo "   ssh -i ~/.ssh/${KEY_PAIR}.pem ubuntu@${EC2_IP}"
echo ""
echo -e "${YELLOW}2. Clone repository:${NC}"
echo "   cd /opt/claude-kb"
echo "   sudo chown -R claude-kb:claude-kb ."
echo "   sudo -u claude-kb git clone https://github.com/YOUR_USERNAME/agentic-search-ops.git ."
echo ""
echo -e "${YELLOW}3. Create .env file:${NC}"
echo "   sudo -u claude-kb tee /opt/claude-kb/.env << 'EOF'"
echo "$ENV_CONTENT"
echo "EOF"
echo ""
echo -e "${YELLOW}4. Add your Anthropic API key:${NC}"
echo "   sudo -u claude-kb nano /opt/claude-kb/.env"
echo ""
echo -e "${YELLOW}5. Run setup script:${NC}"
echo "   sudo -u claude-kb /opt/claude-kb/setup.sh"
echo ""
echo -e "${YELLOW}6. Check backend status:${NC}"
echo "   sudo systemctl status claude-kb"
echo "   sudo journalctl -u claude-kb -f"
echo ""
echo -e "${YELLOW}7. Deploy frontend (from local machine):${NC}"
echo "   cd deploy && ./deploy_frontend.sh"
echo ""

# ==============================================================================
# SAVE DEPLOYMENT INFO
# ==============================================================================

cat > "${SCRIPT_DIR}/deployment_info.txt" << EOF
=== Agentic Search Ops Deployment Info ===
Generated: $(date)

EC2 IP: $EC2_IP
RDS Endpoint: $RDS_ENDPOINT
Storage Bucket: $STORAGE_BUCKET
Frontend Bucket: $FRONTEND_BUCKET
CloudFront URL: https://$CLOUDFRONT_DOMAIN
Secrets Manager: $SECRET_NAME

SSH Command: ssh -i ~/.ssh/${KEY_PAIR}.pem ubuntu@${EC2_IP}
Backend URL: http://${EC2_IP}
Frontend URL: https://${CLOUDFRONT_DOMAIN}
EOF

echo -e "${GREEN}Deployment info saved to: ${SCRIPT_DIR}/deployment_info.txt${NC}"
echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
