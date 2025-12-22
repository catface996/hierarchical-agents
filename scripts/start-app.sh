#!/bin/bash
# =============================================================================
# Application Startup Script
#
# Starts the hierarchical agents API server directly on the host.
# Database should be running in Docker before starting.
#
# Usage:
#   ./scripts/start-app.sh           # Foreground mode
#   ./scripts/start-app.sh daemon    # Background mode (with gunicorn)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=============================================="
echo "Starting Hierarchical Agents API Server"
echo "=============================================="

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}Loading .env file...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Set defaults
export DB_TYPE=${DB_TYPE:-mysql}
export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-3306}
export DB_NAME=${DB_NAME:-hierarchical_agents}
export DB_USER=${DB_USER:-root}
export DB_PASSWORD=${DB_PASSWORD:-hierarchical123}
export PORT=${PORT:-8080}
export HOST=${HOST:-0.0.0.0}
export AWS_REGION=${AWS_REGION:-us-east-1}
export AWS_BEDROCK_MODEL_ID=${AWS_BEDROCK_MODEL_ID:-us.anthropic.claude-sonnet-4-20250514-v1:0}

# Check if using IAM Role
if [ "${USE_IAM_ROLE}" = "true" ] || [ -z "${AWS_BEDROCK_API_KEY}" ] && [ -z "${AWS_ACCESS_KEY_ID}" ]; then
    echo -e "${GREEN}Using IAM Role authentication${NC}"
    export USE_IAM_ROLE=true
fi

# Check database connection
echo -e "\n${YELLOW}Checking database connection...${NC}"
for i in {1..30}; do
    if python3 -c "
import pymysql
try:
    conn = pymysql.connect(
        host='${DB_HOST}',
        port=${DB_PORT},
        user='${DB_USER}',
        password='${DB_PASSWORD}',
        database='${DB_NAME}'
    )
    conn.close()
    print('OK')
    exit(0)
except Exception as e:
    exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}Database connection successful!${NC}"
        break
    fi

    if [ $i -eq 30 ]; then
        echo -e "${RED}Database connection failed after 30 attempts${NC}"
        echo "Please ensure MySQL is running:"
        echo "  docker-compose -f docker-compose.db-only.yml up -d"
        exit 1
    fi

    echo "Waiting for database... ($i/30)"
    sleep 2
done

# Display configuration
echo -e "\n${GREEN}Configuration:${NC}"
echo "  DB_HOST: $DB_HOST"
echo "  DB_PORT: $DB_PORT"
echo "  DB_NAME: $DB_NAME"
echo "  API_PORT: $PORT"
echo "  AWS_REGION: $AWS_REGION"
echo "  AUTH_MODE: $([ "${USE_IAM_ROLE}" = "true" ] && echo "IAM Role" || echo "API Key/AK-SK")"

# Start application
echo -e "\n${GREEN}Starting server...${NC}"

if [ "$1" = "daemon" ]; then
    # Production mode with gunicorn
    echo "Running in daemon mode with gunicorn..."
    gunicorn \
        --bind ${HOST}:${PORT} \
        --workers 4 \
        --threads 2 \
        --timeout 300 \
        --access-logfile - \
        --error-logfile - \
        --daemon \
        --pid /tmp/hierarchical-agents.pid \
        src.ec2.server:app

    echo -e "${GREEN}Server started in background (PID: $(cat /tmp/hierarchical-agents.pid))${NC}"
    echo ""
    echo "To check status: curl http://localhost:${PORT}/health"
    echo "To view logs: tail -f /var/log/gunicorn/*.log"
    echo "To stop: kill \$(cat /tmp/hierarchical-agents.pid)"
else
    # Development mode
    echo "Running in foreground mode..."
    echo "Press Ctrl+C to stop"
    echo ""
    python3 -m src.ec2.server
fi
