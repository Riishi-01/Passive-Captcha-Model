#!/bin/bash
# Deployment validation script

echo "🚀 Starting Passive CAPTCHA Deployment"

# Check Python version
python3 --version

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r backend/requirements-render.txt

# Test imports
echo "🧪 Testing critical imports..."
cd backend
python3 -c "
try:
    import flask
    import flask_cors
    import redis
    import jwt
    print('✅ All critical imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Test syntax
echo "🔍 Testing Python syntax..."
python3 -m py_compile main.py
if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax errors found"
    exit 1
fi

echo "🎯 Deployment validation complete"
