#!/bin/bash
# ==============================================================================
# EC2 USER DATA SCRIPT
# Initializes Ubuntu 24.04 instance for Agentic Search Ops
# ==============================================================================

set -e
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

echo "=== Starting EC2 initialization ==="
echo "Date: $(date)"

# ==============================================================================
# SYSTEM UPDATE
# ==============================================================================

echo "=== Updating system packages ==="
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# ==============================================================================
# INSTALL DEPENDENCIES
# ==============================================================================

echo "=== Installing system dependencies ==="
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    postgresql-client \
    nginx \
    git \
    curl \
    wget \
    unzip \
    jq \
    htop \
    awscli

# ==============================================================================
# CREATE APPLICATION USER
# ==============================================================================

echo "=== Creating application user ==="
if ! id "claude-kb" &>/dev/null; then
    useradd -m -s /bin/bash claude-kb
fi

# ==============================================================================
# CREATE DIRECTORIES
# ==============================================================================

echo "=== Creating application directories ==="
mkdir -p /opt/claude-kb
mkdir -p /var/log/claude-kb
mkdir -p /opt/claude-kb/data/uploads

chown -R claude-kb:claude-kb /opt/claude-kb
chown -R claude-kb:claude-kb /var/log/claude-kb
chmod 755 /opt/claude-kb
chmod 755 /var/log/claude-kb

# ==============================================================================
# CONFIGURE NGINX
# ==============================================================================

echo "=== Configuring Nginx ==="
cat > /etc/nginx/sites-available/claude-kb <<'NGINX'
server {
    listen 80;
    server_name _;

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Root - API docs or redirect
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /var/www/html;
    }
}
NGINX

# Enable site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/claude-kb /etc/nginx/sites-enabled/

# Test and reload nginx
nginx -t
systemctl enable nginx
systemctl restart nginx

# ==============================================================================
# CREATE SYSTEMD SERVICE
# ==============================================================================

echo "=== Creating systemd service ==="
cat > /etc/systemd/system/claude-kb.service <<'SERVICE'
[Unit]
Description=Agentic Search Ops Backend
After=network.target

[Service]
Type=simple
User=claude-kb
Group=claude-kb
WorkingDirectory=/opt/claude-kb/backend
Environment="PATH=/opt/claude-kb/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/claude-kb/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload

# ==============================================================================
# SETUP SWAP (for t2.micro with limited RAM)
# ==============================================================================

echo "=== Setting up swap ==="
if [ ! -f /swapfile ]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# ==============================================================================
# SECURITY HARDENING
# ==============================================================================

echo "=== Applying security hardening ==="

# Disable root SSH
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# ==============================================================================
# CREATE SETUP HELPER SCRIPT
# ==============================================================================

echo "=== Creating helper scripts ==="
cat > /opt/claude-kb/setup.sh <<'SETUP'
#!/bin/bash
# Run this script after cloning the repository

set -e
cd /opt/claude-kb

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Create it first with database credentials."
    echo "See /opt/claude-kb/env.example for template"
    exit 1
fi

# Setup Python virtual environment
cd backend
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start service
sudo systemctl start claude-kb
sudo systemctl enable claude-kb

echo "=== Setup complete! ==="
echo "Check status: sudo systemctl status claude-kb"
echo "View logs: sudo journalctl -u claude-kb -f"
SETUP
chmod +x /opt/claude-kb/setup.sh

# Create env template
cat > /opt/claude-kb/env.example <<'ENVTEMPLATE'
# Database (get from Terraform output)
DATABASE_URL=postgresql://postgres:PASSWORD@RDS_ENDPOINT:5432/agentic_search_ops

# Storage (get from Terraform output)
S3_BUCKET_NAME=your-prefix-kb-storage-xxxx
AWS_REGION=us-east-1

# Frontend URL (CloudFront)
FRONTEND_URL=https://xxxxx.cloudfront.net

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxx

# Agent settings
MAX_JOB_COST_USD=5.0
MAX_JOB_RUNTIME_MINUTES=120

# Document processing
ENABLE_PDF_EXTRACTION=true
ENABLE_DOCX_EXTRACTION=true
ENABLE_EMBEDDINGS=false
ENVTEMPLATE

chown -R claude-kb:claude-kb /opt/claude-kb

# ==============================================================================
# FINISH
# ==============================================================================

echo "=== EC2 initialization complete ==="
echo "Date: $(date)"
echo ""
echo "Next steps:"
echo "1. SSH into the instance"
echo "2. Clone your repository to /opt/claude-kb"
echo "3. Create .env file from template"
echo "4. Run /opt/claude-kb/setup.sh"
