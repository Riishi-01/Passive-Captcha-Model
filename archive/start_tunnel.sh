#!/bin/bash
# Persistent Cloudflare Tunnel for Passive CAPTCHA
set -e

echo "🌐 Starting Cloudflare Tunnel for Passive CAPTCHA"
echo "=================================================="

# Kill any existing cloudflared processes
pkill -f cloudflared 2>/dev/null || true

# Check if localhost is running
if ! curl -s http://localhost:5003/health > /dev/null; then
    echo "❌ Localhost server not running on port 5003"
    echo "Please start the server first:"
    echo "   cd backend && python start_production.py"
    exit 1
fi

echo "✅ Localhost server is running"

# Start the tunnel
echo "🚀 Starting Cloudflare tunnel..."
echo "This will create a new *.trycloudflare.com URL"
echo "Press Ctrl+C to stop the tunnel"
echo

cloudflared tunnel --url http://localhost:5003