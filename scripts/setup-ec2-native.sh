#!/bin/bash
# =============================================================================
# EC2 Native Setup Script
#
# Sets up EC2 for running:
# - MySQL in Docker
# - Application directly on host with Python
#
# This is the recommended setup for IAM Role authentication.
#
# Usage:
#   chmod +x scripts/setup-ec2-native.sh
#   ./scripts/setup-ec2-native.sh
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "=============================================="
echo "   EC2 Native Setup for Hierarchical Agents"
echo "=============================================="
echo -e "${NC}"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi

echo -e "${YELLOW}[1/6] Installing system dependencies...${NC}"

if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ] || [ "$OS" = "centos" ]; then
    # Amazon Linux / RHEL / CentOS
    sudo yum update -y
    sudo yum install -y docker git python3 python3-pip
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker $(whoami)

    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    # Ubuntu / Debian
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose git python3 python3-pip python3-venv
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker $(whoami)
fi

echo -e "${GREEN}System dependencies installed${NC}"

# Check IAM Role
echo -e "\n${YELLOW}[2/6] Checking IAM Role...${NC}"
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    IAM_ROLE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>/dev/null || echo "")
else
    IAM_ROLE=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>/dev/null || echo "")
fi

if [ -z "$IAM_ROLE" ]; then
    echo -e "${RED}Warning: No IAM Role attached to this instance!${NC}"
    echo "Please attach an IAM Role with Bedrock permissions."
else
    echo -e "${GREEN}IAM Role found: $IAM_ROLE${NC}"
fi

# Install Python dependencies
echo -e "\n${YELLOW}[3/6] Installing Python dependencies...${NC}"
pip3 install --user -r requirements.txt
echo -e "${GREEN}Python dependencies installed${NC}"

# Create .env file
echo -e "\n${YELLOW}[4/6] Creating .env file...${NC}"
cat > .env << 'EOF'
# Database Configuration (MySQL in Docker)
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=hierarchical_agents
DB_USER=root
DB_PASSWORD=hierarchical123

# AWS Configuration - IAM Role
USE_IAM_ROLE=true
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# Server Configuration
PORT=8080
HOST=0.0.0.0
DEBUG=false
EOF
echo -e "${GREEN}.env file created${NC}"

# Start MySQL
echo -e "\n${YELLOW}[5/6] Starting MySQL database...${NC}"

# Need to use newgrp or restart shell for docker group
if ! groups | grep -q docker; then
    echo -e "${YELLOW}Note: You may need to log out and back in for docker group to take effect${NC}"
    echo "Or run: newgrp docker"
fi

# Try to start MySQL
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        docker-compose -f docker-compose.db-only.yml up -d
        echo -e "${GREEN}MySQL started${NC}"
    else
        echo -e "${YELLOW}Docker daemon not accessible. After re-login, run:${NC}"
        echo "  docker-compose -f docker-compose.db-only.yml up -d"
    fi
else
    echo -e "${YELLOW}Docker not found. Please install Docker first.${NC}"
fi

# Summary
echo -e "\n${YELLOW}[6/6] Setup complete!${NC}"
echo ""
echo -e "${CYAN}=============================================="
echo "   Setup Complete!"
echo "=============================================="
echo -e "${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. If you just added yourself to the docker group, log out and back in:"
echo "   exit"
echo ""
echo "2. Start the database:"
echo "   docker-compose -f docker-compose.db-only.yml up -d"
echo ""
echo "3. Start the application:"
echo "   ./scripts/start-app.sh"
echo ""
echo "   Or in daemon mode:"
echo "   ./scripts/start-app.sh daemon"
echo ""
echo "4. Test the service:"
echo "   curl http://localhost:8080/health"
echo ""
echo "5. Run the stream test:"
echo "   python3 test_stream.py 'Your question here'"
echo ""
