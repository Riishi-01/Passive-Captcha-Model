#!/bin/bash
# Cloudflare Tunnel Setup for Passive CAPTCHA Production
set -e

echo "🌐 Cloudflare Tunnel Setup for Passive CAPTCHA"
echo "=================================================="

# Check if the production server is running
if ! curl -s http://localhost:5003/health > /dev/null; then
    echo "❌ Production server is not running on port 5003"
    echo "Please run: python deploy_production.py"
    exit 1
fi

echo "✅ Production server is running on port 5003"

# Test admin login
echo "🔐 Testing admin login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5003/admin/login \
    -H "Content-Type: application/json" \
    -d '{"password": "Admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "token"; then
    echo "✅ Admin login successful"
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token')
    echo "   Token: ${TOKEN:0:50}..."
else
    echo "❌ Admin login failed:"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

# Test health endpoint
echo "🏥 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:5003/health)
echo "   Health Status: $(echo "$HEALTH_RESPONSE" | jq -r '.status')"

echo ""
echo "🚀 PRODUCTION SERVER READY FOR CLOUDFLARE TUNNEL"
echo "=================================================="
echo "✅ Backend API: http://localhost:5003"
echo "✅ Admin Login: POST http://localhost:5003/admin/login"
echo "✅ Health Check: http://localhost:5003/health"
echo "✅ Password: Admin123"
echo ""
echo "📋 CLOUDFLARE TUNNEL SETUP INSTRUCTIONS:"
echo "=================================================="
echo ""
echo "1. Install Cloudflare Tunnel (cloudflared):"
echo "   curl -L --output cloudflared.pkg https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.pkg"
echo "   sudo installer -pkg cloudflared.pkg -target /"
echo ""
echo "2. Login to Cloudflare:"
echo "   cloudflared tunnel login"
echo ""
echo "3. Create a tunnel:"
echo "   cloudflared tunnel create passive-captcha"
echo ""
echo "4. Configure the tunnel (create config.yml):"
echo "   tunnel: <tunnel-id>"
echo "   credentials-file: /Users/$(whoami)/.cloudflared/<tunnel-id>.json"
echo "   ingress:"
echo "     - hostname: yourdomain.com"
echo "       service: http://localhost:5003"
echo "     - service: http_status:404"
echo ""
echo "5. Route DNS:"
echo "   cloudflared tunnel route dns passive-captcha yourdomain.com"
echo ""
echo "6. Run the tunnel:"
echo "   cloudflared tunnel run passive-captcha"
echo ""
echo "🔥 QUICK START COMMAND:"
echo "   cloudflared tunnel --url http://localhost:5003"
echo ""
echo "This will create a temporary tunnel and give you a *.trycloudflare.com URL"
echo "Perfect for testing!"
echo ""
echo "📝 API TESTING COMMANDS:"
echo "=================================================="
echo ""
echo "# Test login (replace YOUR_TUNNEL_URL):"
echo "curl -X POST https://YOUR_TUNNEL_URL/admin/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"password\": \"Admin123\"}'"
echo ""
echo "# Test health:"
echo "curl https://YOUR_TUNNEL_URL/health"
echo ""
echo "# Access dashboard:"
echo "open https://YOUR_TUNNEL_URL/"
echo ""

# If cloudflared is available, offer to start tunnel
if command -v cloudflared &> /dev/null; then
    echo "🎉 cloudflared is already installed!"
    echo ""
    read -p "Do you want to start a temporary tunnel now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting temporary Cloudflare tunnel..."
        echo "This will give you a *.trycloudflare.com URL"
        echo "Press Ctrl+C to stop the tunnel"
        cloudflared tunnel --url http://localhost:5003
    fi
else
    echo "💡 Install cloudflared to continue with tunnel setup"
    echo "   brew install cloudflared"
    echo "   or download from: https://github.com/cloudflare/cloudflared/releases"
fi