#!/bin/bash
# ==============================================================================
# DEPLOY FRONTEND SCRIPT
# Builds React app and deploys to S3 + invalidates CloudFront cache
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform"
FRONTEND_DIR="${SCRIPT_DIR}/../frontend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Deploying Frontend ===${NC}"

# ==============================================================================
# GET TERRAFORM OUTPUTS
# ==============================================================================

cd "$TERRAFORM_DIR"

FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name 2>/dev/null || echo "")
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name 2>/dev/null || echo "")
EC2_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")

if [ -z "$FRONTEND_BUCKET" ]; then
    echo -e "${RED}ERROR: Could not get frontend bucket from Terraform${NC}"
    exit 1
fi

echo -e "${YELLOW}Frontend Bucket: ${FRONTEND_BUCKET}${NC}"
echo -e "${YELLOW}CloudFront ID: ${CLOUDFRONT_ID}${NC}"
echo -e "${YELLOW}Backend API: http://${EC2_IP}${NC}"
echo ""

# ==============================================================================
# BUILD FRONTEND
# ==============================================================================

cd "$FRONTEND_DIR"

echo -e "${YELLOW}Installing dependencies...${NC}"
npm install

echo -e "${YELLOW}Creating production .env...${NC}"
cat > .env.production << EOF
VITE_API_URL=http://${EC2_IP}/api/v1
EOF

echo -e "${YELLOW}Building production bundle...${NC}"
npm run build

# Verify build output
if [ ! -d "dist" ]; then
    echo -e "${RED}ERROR: Build failed - dist directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}Build complete!${NC}"
ls -la dist/

# ==============================================================================
# UPLOAD TO S3
# ==============================================================================

echo ""
echo -e "${YELLOW}Uploading to S3...${NC}"

# Sync files to S3
aws s3 sync dist/ "s3://${FRONTEND_BUCKET}/" \
    --delete \
    --cache-control "max-age=31536000" \
    --exclude "index.html"

# Upload index.html with no-cache (for SPA routing)
aws s3 cp dist/index.html "s3://${FRONTEND_BUCKET}/index.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

echo -e "${GREEN}S3 upload complete!${NC}"

# ==============================================================================
# INVALIDATE CLOUDFRONT CACHE
# ==============================================================================

echo ""
echo -e "${YELLOW}Invalidating CloudFront cache...${NC}"

INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${GREEN}Invalidation created: ${INVALIDATION_ID}${NC}"
echo -e "${YELLOW}Cache invalidation takes 5-10 minutes to propagate globally${NC}"

# ==============================================================================
# VERIFY DEPLOYMENT
# ==============================================================================

echo ""
echo -e "${GREEN}=== Frontend Deployed Successfully! ===${NC}"
echo ""
echo -e "  ${BLUE}Frontend URL:${NC}  https://${CLOUDFRONT_DOMAIN}"
echo -e "  ${BLUE}S3 Bucket:${NC}     ${FRONTEND_BUCKET}"
echo -e "  ${BLUE}Backend API:${NC}   http://${EC2_IP}/api/v1"
echo ""
echo -e "${YELLOW}Note: It may take 5-10 minutes for CloudFront to update globally${NC}"
