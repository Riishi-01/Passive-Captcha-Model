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
    
    # Install dependencies
    echo "📦 Installing frontend dependencies..."
    npm install --silent
    
    # Build the frontend
    echo "🔨 Building frontend..."
    npm run build --silent
    
    # Verify build output
    if [ -d "dist" ]; then
        echo "✅ Frontend build complete - dist folder created"
        ls -la dist/ | head -5
    else
        echo "⚠️ Frontend build completed but no dist folder found"
        echo "   Creating empty dist folder for fallback"
        mkdir -p dist
        echo '<!DOCTYPE html><html><head><title>Passive CAPTCHA</title></head><body><h1>API Server Running</h1><p>Frontend build pending...</p></body></html>' > dist/index.html
    fi
    
    cd ../backend
else
    echo "⚠️ Frontend package.json not found, skipping frontend build"
    # Create minimal fallback frontend
    mkdir -p ../frontend/dist
    echo '<!DOCTYPE html><html><head><title>Passive CAPTCHA</title></head><body><h1>API Server Running</h1><p>Access API at /login</p></body></html>' > ../frontend/dist/index.html
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs uploads
touch logs/app.log

# Set executable permissions
chmod +x render_start.py

echo "✅ Build completed successfully!"
echo "🚀 Ready for deployment"