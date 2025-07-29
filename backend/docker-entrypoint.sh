#!/bin/bash

# Docker entrypoint script for Passive CAPTCHA Backend
# Manages Flask application and Cloudflare tunnel

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null || true
    fi
    if [ ! -z "$TUNNEL_PID" ]; then
        kill $TUNNEL_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

print_status "Starting Passive CAPTCHA Backend in Docker container..."

# Validate required files
if [ ! -f "models/passive_captcha_rf.pkl" ]; then
    print_error "ML model file not found!"
    exit 1
fi

if [ ! -f "models/passive_captcha_rf_scaler.pkl" ]; then
    print_error "ML scaler file not found!"
    exit 1
fi

# Start Flask application in background
print_status "Starting Flask application..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 5

# Check if Flask is running
if ! curl -f http://localhost:${PORT:-5000}/health > /dev/null 2>&1; then
    print_error "Flask application failed to start"
    exit 1
fi

print_success "Flask application started (PID: $FLASK_PID)"

# Start Cloudflare tunnel if enabled
if [ "${ENABLE_TUNNEL:-true}" = "true" ]; then
    print_status "Starting Cloudflare tunnel..."
    
    # Start tunnel in background
    cloudflared tunnel --url http://localhost:${PORT:-5000} > /tmp/tunnel.log 2>&1 &
    TUNNEL_PID=$!
    
    # Wait for tunnel to establish
    sleep 10
    
    # Extract tunnel URL from logs
    if [ -f "/tmp/tunnel.log" ]; then
        TUNNEL_URL=$(grep -o "https://[a-zA-Z0-9-]*\.trycloudflare\.com" /tmp/tunnel.log | head -1)
        if [ ! -z "$TUNNEL_URL" ]; then
            print_success "Cloudflare tunnel established!"
            echo ""
            echo "🌐 Public URL: $TUNNEL_URL"
            echo "🔧 Local URL:  http://localhost:${PORT:-5000}"
            echo ""
            echo "API Endpoints:"
            echo "  Health Check: $TUNNEL_URL/health"
            echo "  Verify:       $TUNNEL_URL/api/verify"
            echo "  Admin:        $TUNNEL_URL/admin"
            echo ""
            
            # Save URL to file for external access
            echo "$TUNNEL_URL" > /tmp/tunnel_url.txt
        else
            print_warning "Tunnel URL not found in logs, but tunnel may still be working"
            cat /tmp/tunnel.log
        fi
    fi
else
    print_warning "Cloudflare tunnel is disabled"
fi

print_success "🎉 Deployment completed successfully!"

# Keep the container running
print_status "Services running. Press Ctrl+C to stop."

# Wait for processes
wait $FLASK_PID 