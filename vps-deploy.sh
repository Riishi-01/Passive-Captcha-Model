#!/bin/bash

# VPS Deployment Script for Passive CAPTCHA Backend
# Supports local development and permanent Cloudflare tunneling

set -e

echo "🚀 Starting Passive CAPTCHA Backend VPS Deployment..."

# Configuration
PROJECT_NAME="passive-captcha-backend"
PORT=${PORT:-5000}
ENVIRONMENT=${ENVIRONMENT:-production}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check cloudflared
    if ! command -v cloudflared &> /dev/null; then
        print_warning "cloudflared not found. Installing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install cloudflare/cloudflare/cloudflared
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux installation
            curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
            sudo dpkg -i cloudflared.deb
            rm cloudflared.deb
        fi
    fi
    
    print_success "Prerequisites check completed"
}

# Setup Python virtual environment
setup_environment() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Installed Python dependencies"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Validate ML models and database
validate_assets() {
    print_status "Validating ML models and database..."
    
    # Check if ML model exists
    if [ ! -f "models/passive_captcha_rf.pkl" ]; then
        print_error "ML model file not found. Please train the model first."
        exit 1
    fi
    
    if [ ! -f "models/passive_captcha_rf_scaler.pkl" ]; then
        print_error "ML scaler file not found. Please train the model first."
        exit 1
    fi
    
    # Check if database exists or can be created
    if [ ! -f "passive_captcha.db" ]; then
        print_warning "Database not found. Will be created on first run."
    fi
    
    print_success "Asset validation completed"
}

# Configure environment variables
setup_config() {
    print_status "Setting up configuration..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Production Configuration
MODEL_PATH=models/passive_captcha_rf.pkl
SCALER_PATH=models/passive_captcha_rf_scaler.pkl
DATABASE_URL=sqlite:///passive_captcha.db
CONFIDENCE_THRESHOLD=0.6
ADMIN_SECRET=$(openssl rand -hex 32)
RATE_LIMIT_REQUESTS=100
ALLOWED_ORIGINS=*
FLASK_ENV=production
PORT=$PORT
HOST=0.0.0.0
DEBUG=False
EOF
        print_success "Created .env configuration file"
    else
        print_warning ".env file already exists. Using existing configuration."
    fi
}

# Start the Flask application
start_application() {
    print_status "Starting Flask application..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start application in background
    nohup python app.py > app.log 2>&1 &
    APP_PID=$!
    
    # Save PID for later management
    echo $APP_PID > app.pid
    
    # Wait a moment for the app to start
    sleep 3
    
    # Check if application is running
    if ps -p $APP_PID > /dev/null; then
        print_success "Flask application started (PID: $APP_PID)"
        print_status "Application is running on http://localhost:$PORT"
    else
        print_error "Failed to start Flask application"
        cat app.log
        exit 1
    fi
}

# Setup Cloudflare tunnel for permanent access
setup_cloudflare_tunnel() {
    print_status "Setting up Cloudflare tunnel..."
    
    # Check if app is running locally
    if ! curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
        print_error "Application is not running on port $PORT"
        exit 1
    fi
    
    print_status "Creating Cloudflare tunnel..."
    print_warning "This will create a public URL for your application"
    print_warning "The tunnel will remain active until you stop it"
    
    # Start cloudflare tunnel in background
    nohup cloudflared tunnel --url http://localhost:$PORT > tunnel.log 2>&1 &
    TUNNEL_PID=$!
    
    # Save tunnel PID
    echo $TUNNEL_PID > tunnel.pid
    
    # Wait for tunnel to establish
    sleep 5
    
    # Extract the public URL from logs
    if [ -f "tunnel.log" ]; then
        TUNNEL_URL=$(grep -o "https://[a-zA-Z0-9-]*\.trycloudflare\.com" tunnel.log | head -1)
        if [ ! -z "$TUNNEL_URL" ]; then
            print_success "Cloudflare tunnel established!"
            echo ""
            echo "🌐 Public URL: $TUNNEL_URL"
            echo "🔧 Local URL:  http://localhost:$PORT"
            echo ""
            echo "API Endpoints:"
            echo "  Health Check: $TUNNEL_URL/health"
            echo "  Verify:       $TUNNEL_URL/api/verify"
            echo "  Admin:        $TUNNEL_URL/admin"
            echo ""
            
            # Save URL to file
            echo "$TUNNEL_URL" > tunnel_url.txt
        else
            print_error "Failed to extract tunnel URL from logs"
            cat tunnel.log
        fi
    fi
}

# Create systemd service for permanent deployment (Linux VPS)
create_systemd_service() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Creating systemd service for permanent deployment..."
        
        # Get current directory
        CURRENT_DIR=$(pwd)
        USER=$(whoami)
        
        # Create systemd service file
        sudo tee /etc/systemd/system/passive-captcha.service > /dev/null << EOF
[Unit]
Description=Passive CAPTCHA Backend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        # Create cloudflare tunnel service
        sudo tee /etc/systemd/system/passive-captcha-tunnel.service > /dev/null << EOF
[Unit]
Description=Passive CAPTCHA Cloudflare Tunnel
After=passive-captcha.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:$PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd and enable services
        sudo systemctl daemon-reload
        sudo systemctl enable passive-captcha.service
        sudo systemctl enable passive-captcha-tunnel.service
        
        print_success "Systemd services created and enabled"
        print_status "Use 'sudo systemctl start passive-captcha' to start the service"
        print_status "Use 'sudo systemctl start passive-captcha-tunnel' to start the tunnel"
    fi
}

# Health check function
health_check() {
    print_status "Performing health check..."
    
    # Check local application
    if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
        print_success "✅ Local application is healthy"
    else
        print_error "❌ Local application health check failed"
        return 1
    fi
    
    # Check tunnel if URL exists
    if [ -f "tunnel_url.txt" ]; then
        TUNNEL_URL=$(cat tunnel_url.txt)
        if curl -f "$TUNNEL_URL/health" > /dev/null 2>&1; then
            print_success "✅ Tunnel is accessible"
            echo "   Public URL: $TUNNEL_URL"
        else
            print_warning "⚠️  Tunnel may still be connecting..."
        fi
    fi
}

# Stop all services
stop_services() {
    print_status "Stopping services..."
    
    # Stop Flask app
    if [ -f "app.pid" ]; then
        APP_PID=$(cat app.pid)
        if ps -p $APP_PID > /dev/null; then
            kill $APP_PID
            print_success "Stopped Flask application"
        fi
        rm -f app.pid
    fi
    
    # Stop tunnel
    if [ -f "tunnel.pid" ]; then
        TUNNEL_PID=$(cat tunnel.pid)
        if ps -p $TUNNEL_PID > /dev/null; then
            kill $TUNNEL_PID
            print_success "Stopped Cloudflare tunnel"
        fi
        rm -f tunnel.pid
    fi
}

# Show status
show_status() {
    print_status "Service Status:"
    
    # Check Flask app
    if [ -f "app.pid" ]; then
        APP_PID=$(cat app.pid)
        if ps -p $APP_PID > /dev/null; then
            print_success "Flask app is running (PID: $APP_PID)"
        else
            print_warning "Flask app is not running"
        fi
    else
        print_warning "Flask app PID file not found"
    fi
    
    # Check tunnel
    if [ -f "tunnel.pid" ]; then
        TUNNEL_PID=$(cat tunnel.pid)
        if ps -p $TUNNEL_PID > /dev/null; then
            print_success "Cloudflare tunnel is running (PID: $TUNNEL_PID)"
            if [ -f "tunnel_url.txt" ]; then
                echo "   Public URL: $(cat tunnel_url.txt)"
            fi
        else
            print_warning "Cloudflare tunnel is not running"
        fi
    else
        print_warning "Tunnel PID file not found"
    fi
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            setup_environment
            validate_assets
            setup_config
            start_application
            setup_cloudflare_tunnel
            create_systemd_service
            health_check
            print_success "🎉 Deployment completed successfully!"
            show_status
            ;;
        "start")
            start_application
            setup_cloudflare_tunnel
            health_check
            ;;
        "stop")
            stop_services
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "tunnel-only")
            setup_cloudflare_tunnel
            ;;
        *)
            echo "Usage: $0 {deploy|start|stop|status|health|tunnel-only}"
            echo ""
            echo "Commands:"
            echo "  deploy      - Full deployment with tunnel setup"
            echo "  start       - Start application and tunnel"
            echo "  stop        - Stop all services"
            echo "  status      - Show service status"
            echo "  health      - Perform health check"
            echo "  tunnel-only - Setup only Cloudflare tunnel"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap stop_services EXIT

# Run main function
main "$@" 