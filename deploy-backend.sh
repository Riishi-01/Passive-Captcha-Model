#!/bin/bash

# Deploy Passive CAPTCHA Backend to Render.com using CLI
# This script provides deployment instructions after successful testing

echo "🚀 Deploying Passive CAPTCHA Backend to Render.com..."

# Run pre-deployment tests
echo "🧪 Running pre-deployment tests..."
cd backend
python -m pytest test_units.py test_model.py test_deployment.py::TestDeploymentReadiness -q

if [ $? -eq 0 ]; then
    echo "✅ All tests passed! Ready for deployment."
else
    echo "❌ Tests failed. Please fix issues before deployment."
    exit 1
fi

cd ..

echo "⚠️  Blueprint deployment via CLI is not directly supported."
echo "📋 Please use one of these options:"
echo ""
echo "Option 1: Web Interface Blueprint (Recommended)"
echo "1. Go to https://render.com/dashboard"
echo "2. Click 'New' → 'Blueprint'"
echo "3. Connect repository: https://github.com/Riishi-01/Passive-captcha.git"
echo "4. Render will detect render.yaml and deploy automatically"
echo ""
echo "Option 2: Manual Service Creation"
echo "Use the Render dashboard to create services manually with these settings:"
echo ""
echo "Backend Service:"
echo "- Name: passive-captcha-backend"
echo "- Repository: https://github.com/Riishi-01/Passive-captcha.git"
echo "- Root Directory: backend"
echo "- Runtime: Python 3"
echo "- Build Command: pip install --upgrade pip && pip install -r requirements-deploy.txt"
echo "- Start Command: gunicorn app:app --bind 0.0.0.0:\$PORT --workers 2 --timeout 120"
echo ""
echo "Frontend Service:"
echo "- Name: passive-captcha-frontend"
echo "- Type: Static Site"
echo "- Repository: https://github.com/Riishi-01/Passive-captcha.git"
echo "- Root Directory: frontend"
echo "- Build Command: npm ci && npm run build"
echo "- Publish Directory: dist"
echo ""
echo "🔑 Environment Variables (copy from render.env.example):"
echo "- FLASK_ENV=production"
echo "- MODEL_PATH=models/passive_captcha_rf.pkl"
echo "- DATABASE_URL=sqlite:///passive_captcha.db"
echo "- CONFIDENCE_THRESHOLD=0.6"
echo "- SECRET_KEY=<generate in Render>"
echo "- ADMIN_SECRET=<generate in Render>"
echo ""
echo "✅ All configuration files are ready in your repository!"
echo "🧪 Testing Status: PASSED"
echo "📊 Deployment Readiness: READY"
echo "📚 See RENDER_DEPLOYMENT_GUIDE.md for detailed instructions" 