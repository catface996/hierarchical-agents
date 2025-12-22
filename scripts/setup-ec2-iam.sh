#!/bin/bash
# =============================================================================
# EC2 IAM Role Setup Script
#
# This script configures an EC2 instance for running the hierarchical agents
# system with IAM Role authentication.
#
# Usage:
#   chmod +x scripts/setup-ec2-iam.sh
#   ./scripts/setup-ec2-iam.sh
# =============================================================================

set -e

echo "=============================================="
echo "EC2 IAM Role Setup for Hierarchical Agents"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get instance ID
echo -e "\n${YELLOW}[1/5] Getting instance ID...${NC}"
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    # IMDSv2
    INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "")
else
    # IMDSv1 fallback
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "")
fi

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}Error: Could not get instance ID. Are you running on EC2?${NC}"
    exit 1
fi
echo -e "${GREEN}Instance ID: $INSTANCE_ID${NC}"

# Check current IAM Role
echo -e "\n${YELLOW}[2/5] Checking IAM Role...${NC}"
if [ -n "$TOKEN" ]; then
    IAM_ROLE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>/dev/null || echo "")
else
    IAM_ROLE=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>/dev/null || echo "")
fi

if [ -z "$IAM_ROLE" ]; then
    echo -e "${RED}Error: No IAM Role attached to this instance!${NC}"
    echo -e "${YELLOW}Please attach an IAM Role with Bedrock permissions to this EC2 instance.${NC}"
    echo ""
    echo "Required permissions:"
    echo "  - bedrock:InvokeModel"
    echo "  - bedrock:InvokeModelWithResponseStream"
    exit 1
fi
echo -e "${GREEN}IAM Role: $IAM_ROLE${NC}"

# Test Bedrock access
echo -e "\n${YELLOW}[3/5] Testing Bedrock access...${NC}"
AWS_REGION=${AWS_REGION:-us-east-1}
if aws bedrock list-foundation-models --region $AWS_REGION --query 'modelSummaries[0].modelId' --output text 2>/dev/null; then
    echo -e "${GREEN}Bedrock access confirmed!${NC}"
else
    echo -e "${RED}Warning: Could not access Bedrock. Please verify IAM Role permissions.${NC}"
fi

# Update IMDSv2 hop limit for Docker
echo -e "\n${YELLOW}[4/5] Configuring IMDSv2 hop limit for Docker...${NC}"
CURRENT_HOP_LIMIT=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].MetadataOptions.HttpPutResponseHopLimit' \
    --output text 2>/dev/null || echo "1")

echo "Current hop limit: $CURRENT_HOP_LIMIT"

if [ "$CURRENT_HOP_LIMIT" -lt 2 ]; then
    echo "Updating hop limit to 2 for Docker container access..."
    aws ec2 modify-instance-metadata-options \
        --instance-id $INSTANCE_ID \
        --http-put-response-hop-limit 2 \
        --http-endpoint enabled
    echo -e "${GREEN}Hop limit updated to 2${NC}"
else
    echo -e "${GREEN}Hop limit already >= 2${NC}"
fi

# Create .env file
echo -e "\n${YELLOW}[5/5] Creating .env file...${NC}"
cat > .env << EOF
# Database Configuration
DB_TYPE=mysql
DB_HOST=127.0.0.1
DB_PORT=13306
DB_NAME=hierarchical_agents
DB_USER=root
DB_PASSWORD=hierarchical123

# AWS Configuration - IAM Role
USE_IAM_ROLE=true
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_BEDROCK_MODEL_ID=${AWS_BEDROCK_MODEL_ID:-us.anthropic.claude-sonnet-4-20250514-v1:0}

# Server Configuration
PORT=8080
DEBUG=false
EOF
echo -e "${GREEN}.env file created${NC}"

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Start the services:"
echo "     docker-compose -f docker-compose.ec2.yml up -d"
echo ""
echo "  2. Verify the service:"
echo "     curl http://localhost:8080/health"
echo ""
echo "  3. Run a test:"
echo "     python3 test_stream.py 'Your question here'"
echo ""
