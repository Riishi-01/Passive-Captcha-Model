#!/bin/bash
set -e

echo "🔨 Simple Render Build Process"
echo "================================"

# Install Node.js 18 if not available
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

echo "✅ Node.js version: $(node -v)"
echo "✅ NPM version: $(npm -v)"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements-render.txt

# Build frontend
echo "🏗️ Building frontend..."
cd frontend
npm install --no-audit --no-fund
npm run build
cd ..

echo "✅ Build completed successfully!"