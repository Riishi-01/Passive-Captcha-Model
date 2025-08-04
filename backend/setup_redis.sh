#!/bin/bash
# Redis Setup Script for Development
# Run this script to set up Redis for local development

echo "🔧 Setting up Redis for Passive CAPTCHA development..."

# Check if Redis is installed
if command -v redis-server &> /dev/null; then
    echo "✅ Redis is already installed"
else
    echo "📦 Installing Redis..."
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            echo "❌ Homebrew not found. Please install Redis manually:"
            echo "   https://redis.io/docs/getting-started/installation/install-redis-on-mac-os/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install redis-server
        elif command -v yum &> /dev/null; then
            sudo yum install redis
        else
            echo "❌ Package manager not supported. Please install Redis manually:"
            echo "   https://redis.io/docs/getting-started/installation/install-redis-on-linux/"
            exit 1
        fi
    else
        echo "❌ OS not supported. Please install Redis manually:"
        echo "   https://redis.io/docs/getting-started/installation/"
        exit 1
    fi
fi

# Start Redis server
echo "🚀 Starting Redis server..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS with Homebrew
    brew services start redis
    echo "✅ Redis started as a service"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    echo "✅ Redis started and enabled"
fi

# Test connection
echo "🔍 Testing Redis connection..."
sleep 2
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running and accessible"
    echo ""
    echo "🎉 Redis setup complete!"
    echo "   • Redis server: localhost:6379"
    echo "   • Test command: redis-cli ping"
    echo "   • Stop command: redis-cli shutdown (or brew services stop redis on macOS)"
    echo ""
    echo "Now you can restart your Passive CAPTCHA app to use Redis!"
else
    echo "❌ Redis setup failed. Please check the installation manually."
    exit 1
fi