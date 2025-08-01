#!/bin/bash
# Production Deployment Script for Docker

set -e

echo "🚀 Passive CAPTCHA Production Deployment"
echo "========================================"

# Parse command line arguments
ENVIRONMENT=${1:-production}
BUILD_FRONTEND=${2:-true}

echo "📋 Deployment Configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Build Frontend: $BUILD_FRONTEND"
echo ""

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Set environment variables for production
export FLASK_ENV=production
export NODE_ENV=production

# Load environment variables if .env.production exists
if [ -f .env.production ]; then
    echo "📝 Loading production environment variables..."
    source .env.production
else
    echo "⚠️  No .env.production file found. Using defaults."
fi

# Create production directories
echo "📁 Creating production directories..."
mkdir -p backend/logs
mkdir -p backend/tmp
mkdir -p nginx/ssl

# Build frontend if requested
if [ "$BUILD_FRONTEND" = "true" ]; then
    echo "🔨 Building frontend for production..."
    cd frontend
    
    # Install dependencies
    npm ci --only=production --no-audit --no-fund
    
    # Build with production settings
    export VITE_API_URL=${VITE_API_URL:-https://passive-captcha.onrender.com}
    export VITE_WS_URL=${VITE_WS_URL:-wss://passive-captcha.onrender.com}
    npm run build
    
    echo "✅ Frontend built successfully"
    cd ..
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.production.yml down --remove-orphans

# Build production images
echo "🔨 Building production images..."
docker-compose -f docker-compose.production.yml build --parallel --no-cache

# Start production services
echo "🚀 Starting production services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Health check
echo "🏥 Performing health checks..."
max_attempts=60
attempt=1

while [ $attempt -le $max_attempts ]; do
    # Check backend health
    if curl -f http://localhost:5003/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    elif [ $attempt -eq $max_attempts ]; then
        echo "❌ Backend health check failed"
        docker-compose -f docker-compose.production.yml logs backend
        exit 1
    else
        echo "   Attempt $attempt/$max_attempts - checking backend health..."
        sleep 2
        ((attempt++))
    fi
done

# Test admin login
echo "🔐 Testing admin authentication..."
if curl -s -X POST -H "Content-Type: application/json" \
   -d '{"password": "Admin123"}' \
   http://localhost:5003/admin/login | grep -q "token"; then
    echo "✅ Admin authentication working!"
else
    echo "❌ Admin authentication failed"
    exit 1
fi

# Show deployment status
echo ""
echo "📊 Production Deployment Status:"
docker-compose -f docker-compose.production.yml ps

echo ""
echo "🌐 Production URLs:"
echo "   Application: http://localhost (if nginx is configured)"
echo "   Backend API: http://localhost:5003"
echo "   Frontend: http://localhost:3000"
echo ""
echo "📋 Quick Commands:"
echo "   View logs: docker-compose -f docker-compose.production.yml logs -f [service]"
echo "   Stop: docker-compose -f docker-compose.production.yml down"
echo "   Restart: docker-compose -f docker-compose.production.yml restart [service]"
echo ""
echo "✅ Production deployment completed successfully!"

# Optional: Save deployment info
cat > deployment_info.json << EOF
{
  "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "frontend_built": $BUILD_FRONTEND,
  "services": $(docker-compose -f docker-compose.production.yml ps --format json)
}
EOF

echo "📝 Deployment info saved to deployment_info.json"