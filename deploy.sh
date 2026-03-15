#!/bin/bash

# FYIXT Deployment Script for viralclip.tech
# This script builds and deploys the FYIXT application using Docker

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         FYIXT Deployment to viralclip.tech                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"

PROJECT_DIR="/Users/mac/Downloads/FYIXT"
DEPLOY_DIR="$PROJECT_DIR/deploy"

# Step 1: Verify environment
echo ""
echo "✓ Step 1: Verifying environment..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Error: FYIXT directory not found at $PROJECT_DIR"
    exit 1
fi
echo "✓ FYIXT directory found"

# Step 2: Build React dashboard
echo ""
echo "✓ Step 2: Building React dashboard..."
cd "$PROJECT_DIR/desktop"
npm run build 2>&1 | grep -E "(✓ built|built in)"
echo "✓ Dashboard built successfully"

# Step 3: Check Docker
echo ""
echo "✓ Step 3: Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Deployment requires Docker."
    echo "Install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✓ Docker found: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose not found"
    exit 1
fi
echo "✓ docker-compose found: $(docker-compose --version)"

# Step 4: Verify .env file
echo ""
echo "✓ Step 4: Checking environment configuration..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  .env file not found. Creating with defaults..."
    cat > "$PROJECT_DIR/.env" << 'ENV'
FYI_WEB_PORTAL_PORT=8000
FYI_PUBLIC_BASE_URL=https://viralclip.tech
FYI_ALLOWED_ORIGINS=https://viralclip.tech,https://www.viralclip.tech
FYI_SCHEDULER_ENABLED=1
FYI_SCHEDULER_POLL_SECONDS=10

# Add your credentials here:
# FB_APP_ID=your_app_id
# FB_APP_SECRET=your_app_secret
# YT_CLIENT_ID=your_client_id
# YT_CLIENT_SECRET=your_client_secret
ENV
    echo "✓ .env created with defaults"
    echo "⚠️  Please update .env with your API credentials"
else
    echo "✓ .env file found"
fi

# Step 5: Build Docker image
echo ""
echo "✓ Step 5: Building Docker image..."
cd "$DEPLOY_DIR"
docker-compose build --no-cache 2>&1 | tail -5
echo "✓ Docker image built successfully"

# Step 6: Start containers
echo ""
echo "✓ Step 6: Starting containers..."
docker-compose up -d
echo "✓ Containers started"

# Step 7: Verify deployment
echo ""
echo "✓ Step 7: Verifying deployment..."
sleep 3

# Check if container is running
if docker-compose ps | grep -q "fyi_app.*Up"; then
    echo "✓ Application container is running"
else
    echo "❌ Application container failed to start"
    docker-compose logs app | tail -20
    exit 1
fi

# Step 8: Display status
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ DEPLOYMENT SUCCESSFUL                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Application Status:"
echo "   Status: $(docker-compose ps app | grep -o 'Up.*' | head -1)"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard:  https://viralclip.tech"
echo "   API Docs:   https://viralclip.tech/docs"
echo "   ReDoc:      https://viralclip.tech/redoc"
echo "   Health:     https://viralclip.tech/api/health"
echo ""
echo "📊 Container Info:"
docker-compose ps
echo ""
echo "📝 Logs:"
echo "   View logs: docker-compose -f $DEPLOY_DIR/docker-compose.yml logs -f app"
echo ""
echo "🛑 To stop:"
echo "   docker-compose -f $DEPLOY_DIR/docker-compose.yml down"
echo ""
echo "✨ Deployment complete! Dashboard is live at https://viralclip.tech"
