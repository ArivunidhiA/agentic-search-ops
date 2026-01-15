#!/bin/bash
# ==============================================================================
# DEPLOY BACKEND SCRIPT
# Updates the backend code on EC2 and restarts the service
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Deploying Backend ===${NC}"

# ==============================================================================
# GET EC2 INFO
# ==============================================================================

cd "$TERRAFORM_DIR"

EC2_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")
KEY_PAIR=$(terraform output -raw ec2_ssh_command 2>/dev/null | grep -oP '(?<=-i ~/.ssh/)[^.]+' || echo "your-key")

if [ -z "$EC2_IP" ]; then
    echo -e "${RED}ERROR: Could not get EC2 IP from Terraform${NC}"
    exit 1
fi

SSH_KEY="$HOME/.ssh/${KEY_PAIR}.pem"
SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP"

echo -e "${YELLOW}EC2 IP: ${EC2_IP}${NC}"
echo -e "${YELLOW}SSH Key: ${SSH_KEY}${NC}"
echo ""

# ==============================================================================
# DEPLOY
# ==============================================================================

echo -e "${YELLOW}Connecting to EC2 and deploying...${NC}"

$SSH_CMD << 'REMOTE_SCRIPT'
set -e

echo "=== Pulling latest code ==="
cd /opt/claude-kb
sudo -u claude-kb git pull origin main

echo "=== Installing dependencies ==="
cd /opt/claude-kb/backend
sudo -u claude-kb bash -c 'source venv/bin/activate && pip install -r requirements.txt'

echo "=== Restarting service ==="
sudo systemctl restart claude-kb

echo "=== Checking status ==="
sleep 3
sudo systemctl status claude-kb --no-pager

echo "=== Testing health endpoint ==="
curl -s http://localhost:8000/health | jq .

echo "=== Deployment complete ==="
REMOTE_SCRIPT

echo ""
echo -e "${GREEN}=== Backend Deployed Successfully! ===${NC}"
echo -e "Backend URL: http://${EC2_IP}"
echo -e "Health Check: http://${EC2_IP}/health"
