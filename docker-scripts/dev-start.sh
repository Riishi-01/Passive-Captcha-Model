#!/bin/bash
# Development Environment Startup Script

set -e

echo "🐳 Starting Passive CAPTCHA Development Environment"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/logs
mkdir -p backend/tmp
mkdir -p frontend/dist

# Copy environment files if they don't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << EOF
# Development Environment Variables
FLASK_ENV=development
ADMIN_SECRET=Admin123
DATABASE_URL=postgresql://captcha_user:captcha_pass@postgres:5432/passive_captcha
REDIS_URL=redis://redis:6379/0
POSTGRES_DB=passive_captcha
POSTGRES_USER=captcha_user
POSTGRES_PASSWORD=captcha_pass
VITE_API_URL=http://localhost:5003
VITE_WS_URL=ws://localhost:5003
EOF
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose down --remove-orphans
docker-compose build --parallel
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check service health
echo "🏥 Checking service health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose ps | grep -q "Up (healthy)"; then
        echo "✅ Services are healthy!"
        break
    elif [ $attempt -eq $max_attempts ]; then
        echo "❌ Services failed to become healthy within timeout"
        docker-compose logs --tail=50
        exit 1
    else
        echo "   Attempt $attempt/$max_attempts - waiting for services..."
        sleep 2
        ((attempt++))
    fi
done

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Development URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:5003"
echo "   Backend Health: http://localhost:5003/health"
echo "   Admin Login: http://localhost:5003/admin/login"
echo ""
echo "📊 Database Info:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "🔧 Useful Commands:"
echo "   View logs: docker-compose logs -f [service_name]"
echo "   Stop services: docker-compose down"
echo "   Rebuild: docker-compose build --no-cache"
echo ""
echo "✅ Development environment is ready!"