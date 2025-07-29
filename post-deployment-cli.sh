#!/bin/bash

# Post-deployment CLI management for Passive CAPTCHA on Render.com
echo "🔧 Passive CAPTCHA - Post-Deployment CLI Management"
echo ""

echo "📊 View all services:"
echo "render services"
echo ""

echo "🚀 Deploy updates to backend:"
echo "render deploy --service=passive-captcha-backend"
echo ""

echo "🚀 Deploy updates to frontend:"
echo "render deploy --service=passive-captcha-frontend"
echo ""

echo "📜 View backend logs:"
echo "render logs --service=passive-captcha-backend"
echo ""

echo "📜 View frontend logs:"
echo "render logs --service=passive-captcha-frontend"
echo ""

echo "🔄 Restart backend service:"
echo "render restart --service=passive-captcha-backend"
echo ""

echo "🔄 Restart frontend service:"
echo "render restart --service=passive-captcha-frontend"
echo ""

echo "👤 Check current user:"
echo "render whoami"
echo ""

echo "🌍 Check workspace:"
echo "render workspace current"
echo ""

echo "💾 Check database status (if PostgreSQL added):"
echo "render services | grep -i postgres"
echo ""

echo "🧪 Test deployed backend:"
echo "curl https://passive-captcha-backend.onrender.com/health"
echo ""

echo "🌐 Open frontend:"
echo "open https://passive-captcha-frontend.onrender.com"
echo ""

echo "✅ After deployment, run any of these commands to manage your services!" 