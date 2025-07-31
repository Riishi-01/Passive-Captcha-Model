#!/bin/bash

# Render.com Build Script for Passive CAPTCHA
echo "🚀 Starting Render Build Process..."

# Install Python dependencies (cloud-optimized)
echo "📦 Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements-render.txt

# Build frontend if package.json exists
if [ -f "../frontend/package.json" ]; then
    echo "🏗️ Building frontend..."
    cd ../frontend
    npm install --silent
    npm run build --silent
    echo "✅ Frontend build complete"
    cd ../backend
else
    echo "⚠️ Frontend package.json not found, skipping frontend build"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs uploads
touch logs/app.log

# Set executable permissions
chmod +x render_start.py

echo "✅ Build completed successfully!"
echo "🚀 Ready for deployment"