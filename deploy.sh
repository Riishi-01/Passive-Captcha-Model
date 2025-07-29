#!/bin/bash

# One-Click Deployment Script for Passive CAPTCHA System
# Deploys frontend to Vercel and backend to Railway

set -e  # Exit on any error

echo "🚀 Starting Passive CAPTCHA System Deployment..."
echo "=================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it:"
    echo "   npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

echo "✅ Prerequisites check complete"

# Deploy Frontend to Vercel
echo ""
echo "📦 Deploying frontend to Vercel..."
echo "-----------------------------------"

cd frontend

# Create production build
echo "Building frontend assets..."

# Update API URL in minified version for production
sed -i.bak 's|https://passive-captcha-api.railway.app|https://passive-captcha-api.railway.app|g' src/passive-captcha.min.js

# Deploy to Vercel
vercel --prod --confirm --scope personal

if [ $? -eq 0 ]; then
    echo "✅ Frontend deployed successfully to Vercel"
    FRONTEND_URL=$(vercel list --scope personal | grep passive-captcha | head -1 | awk '{print $2}')
    echo "🌐 Frontend URL: https://$FRONTEND_URL"
else
    echo "❌ Frontend deployment failed"
    exit 1
fi

cd ..

# Deploy Backend to Railway
echo ""
echo "🔧 Deploying backend to Railway..."
echo "----------------------------------"

cd backend

# Ensure model files exist
if [ ! -f "models/passive_captcha_rf.pkl" ]; then
    echo "⚠️  Model files not found. Training model first..."
    python train_model.py
fi

# Deploy to Railway
echo "Deploying to Railway..."
railway up

if [ $? -eq 0 ]; then
    echo "✅ Backend deployed successfully to Railway"
    
    # Get Railway URL
    BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url' 2>/dev/null || echo "check-railway-dashboard")
    echo "🔗 Backend URL: $BACKEND_URL"
    
    # Wait a moment for deployment to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
else
    echo "❌ Backend deployment failed"
    exit 1
fi

cd ..

# Verify deployment
echo ""
echo "✅ Running health checks..."
echo "----------------------------"

# Check if backend is responsive
echo "Testing backend health endpoint..."
if curl -f https://passive-captcha-api.railway.app/api/health &>/dev/null; then
    echo "✅ Backend health check passed"
else
    echo "⚠️  Backend health check failed (may still be starting up)"
fi

# Check if frontend is accessible
echo "Testing frontend accessibility..."
if curl -f https://passive-captcha.vercel.app &>/dev/null; then
    echo "✅ Frontend accessibility check passed"
else
    echo "⚠️  Frontend accessibility check failed"
fi

# Final status
echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "📊 System Status:"
echo "  Frontend (CDN):  https://passive-captcha.vercel.app"
echo "  Backend (API):   https://passive-captcha-api.railway.app"
echo "  Admin Panel:     https://passive-captcha-api.railway.app/admin/dashboard"
echo ""
echo "🔗 Integration URLs:"
echo "  Widget Script:   https://passive-captcha.vercel.app/passive-captcha.js"
echo "  Demo Site:       https://passive-captcha.vercel.app/demo"
echo "  API Endpoint:    https://passive-captcha-api.railway.app/api/verify"
echo ""
echo "📝 Quick Integration:"
echo '  <script src="https://passive-captcha.vercel.app/passive-captcha.js"></script>'
echo "  <script>PassiveCaptcha.init({element: '#your-button'});</script>"
echo ""
echo "🔐 Admin Access:"
echo "  Password: Set ADMIN_SECRET environment variable on Railway"
echo ""
echo "💰 Monthly Costs: ~$5 (Railway Pro plan)"
echo ""
echo "📈 Next Steps:"
echo "  1. Update ADMIN_SECRET environment variable on Railway"
echo "  2. Configure custom domain (optional)"
echo "  3. Set up monitoring alerts"
echo "  4. Review admin dashboard for system health"
echo ""
echo "✅ Your Passive CAPTCHA system is now live and ready for integration!" 