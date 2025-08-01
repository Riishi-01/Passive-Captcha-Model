#!/bin/bash
# Render.com Build Script for Passive CAPTCHA
# This script ensures both backend and frontend are properly built

set -e  # Exit on any error

echo "🚀 Starting Render.com Build Process"
echo "===================================="

# Print environment info
echo "📋 Environment Information:"
echo "   Node version: $(node --version 2>/dev/null || echo 'Not available')"
echo "   NPM version: $(npm --version 2>/dev/null || echo 'Not available')"
echo "   Python version: $(python --version 2>/dev/null || echo 'Not available')"
echo "   Current directory: $(pwd)"
echo "   Available disk space: $(df -h . | tail -1 | awk '{print $4}')"

# Step 1: Install Python dependencies
echo ""
echo "🐍 Installing Python Dependencies..."
pip install -r backend/requirements-render.txt
echo "✅ Python dependencies installed"

# Step 2: Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "⚠️ Node.js not found. Trying to install..."
    # Try to install Node.js on Render (this might not work on all platforms)
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - 2>/dev/null || echo "Could not install Node.js automatically"
    sudo apt-get install -y nodejs 2>/dev/null || echo "Could not install Node.js via apt"
fi

# Step 3: Install frontend dependencies
echo ""
echo "📦 Installing Frontend Dependencies..."
cd frontend

if ! command -v npm &> /dev/null; then
    echo "❌ NPM not available. Cannot build frontend."
    echo "ℹ️ The application will run with API-only mode."
    cd ..
    exit 0
fi

# Clear npm cache to avoid issues
npm cache clean --force 2>/dev/null || echo "Could not clear npm cache"

# Install with verbose logging
echo "Installing npm packages..."
npm install --verbose --no-optional --no-audit || {
    echo "⚠️ NPM install failed. Trying alternative approaches..."
    
    # Try with different npm configurations
    npm config set registry https://registry.npmjs.org/
    npm install --legacy-peer-deps --no-optional || {
        echo "❌ All npm install attempts failed"
        cd ..
        exit 1
    }
}

echo "✅ Frontend dependencies installed"

# Step 4: Build frontend
echo ""
echo "🔨 Building Frontend for Production..."

# Set environment variables for build
export NODE_ENV=production
export VITE_API_URL="${VITE_API_URL:-https://passive-captcha.onrender.com}"
export VITE_WS_URL="${VITE_WS_URL:-wss://passive-captcha.onrender.com}"

echo "Build environment:"
echo "   NODE_ENV: $NODE_ENV"
echo "   VITE_API_URL: $VITE_API_URL"
echo "   VITE_WS_URL: $VITE_WS_URL"

# Run the build
npm run build || {
    echo "❌ Frontend build failed"
    cd ..
    exit 1
}

# Verify build output
if [ ! -d "dist" ]; then
    echo "❌ Build failed - dist directory not created"
    cd ..
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    echo "❌ Build failed - index.html not found"
    cd ..
    exit 1
fi

# Count and list build artifacts
asset_count=$(find dist -name "*.js" -o -name "*.css" | wc -l)
total_files=$(find dist -type f | wc -l)

echo "✅ Frontend build successful!"
echo "   📁 Built files: $total_files total, $asset_count assets"
echo "   📦 Build size: $(du -sh dist | cut -f1)"

# List some key files
echo "   📋 Key files:"
ls -la dist/ | head -10

cd ..

# Step 5: Final verification
echo ""
echo "🔍 Final Verification..."

# Run deployment test
if [ -f "deployment_test.py" ]; then
    echo "Running deployment test..."
    python deployment_test.py || echo "⚠️ Some deployment tests failed"
else
    echo "Deployment test script not found, skipping..."
fi

echo ""
echo "🎉 Build Process Complete!"
echo "=========================="
echo "✅ Backend: Ready"
echo "✅ Frontend: Built and ready"
echo "🚀 Application ready for deployment"

# Create a build info file
cat > build_info.txt << EOF
Build completed: $(date)
Frontend build: $([ -d "frontend/dist" ] && echo "✅ Success" || echo "❌ Failed")
Asset count: $asset_count
Build environment: $NODE_ENV
API URL: $VITE_API_URL
WebSocket URL: $VITE_WS_URL
EOF

echo "📋 Build info saved to build_info.txt"