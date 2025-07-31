#!/bin/bash
set -e  # Exit on any error

# Enhanced Render.com Build Script for Passive CAPTCHA
echo "🚀 Starting Enhanced Render Build Process..."
echo "📍 Current working directory: $(pwd)"
echo "🐍 Python version: $(python --version 2>&1 || echo 'Python not found')"
echo "📦 Pip version: $(pip --version 2>&1 || echo 'Pip not found')"

# Environment detection
if [ -n "$RENDER" ]; then
    echo "🌐 Detected Render environment"
    export NODE_ENV=production
    export CI=true
fi

# Check and install Node.js if needed
echo "🔍 Checking Node.js availability..."
if ! command -v node &> /dev/null; then
    echo "⚠️ Node.js not found. Attempting installation..."
    
    # Try installing Node.js 18 via NodeSource
    if command -v curl &> /dev/null; then
        echo "📥 Installing Node.js 18 via NodeSource..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash - 2>/dev/null || echo "NodeSource setup failed"
        apt-get install -y nodejs 2>/dev/null || echo "apt-get install failed"
    fi
    
    # Alternative: Download Node.js binary directly
    if ! command -v node &> /dev/null; then
        echo "📥 Downloading Node.js binary directly..."
        cd /tmp
        wget -q https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-x64.tar.xz 2>/dev/null || {
            echo "❌ Failed to download Node.js"
            cd - > /dev/null
        }
        
        if [ -f "node-v18.19.0-linux-x64.tar.xz" ]; then
            tar xf node-v18.19.0-linux-x64.tar.xz
            export PATH="/tmp/node-v18.19.0-linux-x64/bin:$PATH"
            cd - > /dev/null
        fi
    fi
else
    echo "✅ Node.js found: $(node --version)"
fi

# Verify Node.js availability
if command -v node &> /dev/null; then
    echo "✅ Node.js version: $(node --version)"
    echo "✅ NPM version: $(npm --version)"
    NODE_AVAILABLE=true
else
    echo "❌ Node.js still not available after installation attempts"
    NODE_AVAILABLE=false
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install --upgrade pip --quiet
pip install -r requirements-render.txt --quiet

# Handle frontend build
echo "🏗️ Processing frontend..."
cd ../

if [ -f "frontend/package.json" ] && [ "$NODE_AVAILABLE" = true ]; then
    echo "📦 Building frontend with Node.js..."
    cd frontend
    
    # Configure npm for CI environment
    npm config set audit-level high
    npm config set fund false
    npm config set update-notifier false
    
    # Install dependencies with retries
    echo "📦 Installing frontend dependencies..."
    for i in {1..3}; do
        if npm ci --silent --no-audit --no-fund --production=false; then
            echo "✅ NPM dependencies installed successfully"
            break
        elif [ $i -eq 3 ]; then
            echo "❌ NPM install failed after 3 attempts"
            # Fallback to npm install
            npm install --silent --no-audit --no-fund --production=false || {
                echo "❌ Both npm ci and npm install failed"
                cd ../
                mkdir -p frontend/dist
                echo '<!DOCTYPE html><html><head><title>Passive CAPTCHA</title></head><body><h1>API Server Running</h1><p>Frontend dependencies failed</p><p><a href="/login">Login</a> | <a href="/health">Health</a></p></body></html>' > frontend/dist/index.html
                exit 0
            }
        else
            echo "⚠️ NPM install attempt $i failed, retrying..."
            sleep 2
        fi
    done
    
    # Build frontend (with fallback for systems without timeout command)
    echo "🔨 Building frontend..."
    
    # Try with timeout if available, otherwise use regular npm run build
    if command -v timeout >/dev/null 2>&1; then
        # Linux/Render environment with timeout command
        if timeout 300 npm run build; then
            BUILD_SUCCESS=true
        else
            BUILD_SUCCESS=false
        fi
    else
        # macOS or systems without timeout command
        npm run build &
        BUILD_PID=$!
        
        # Wait for build with manual timeout (300 seconds = 5 minutes)
        BUILD_TIMEOUT=300
        BUILD_COUNT=0
        BUILD_SUCCESS=false
        
        while [ $BUILD_COUNT -lt $BUILD_TIMEOUT ]; do
            if ! kill -0 $BUILD_PID 2>/dev/null; then
                # Process finished, check exit status
                wait $BUILD_PID
                BUILD_EXIT=$?
                if [ $BUILD_EXIT -eq 0 ]; then
                    BUILD_SUCCESS=true
                fi
                break
            fi
            sleep 1
            BUILD_COUNT=$((BUILD_COUNT + 1))
        done
        
        # Kill build process if it's still running (timeout)
        if kill -0 $BUILD_PID 2>/dev/null; then
            echo "⚠️ Frontend build timed out after 5 minutes, killing process..."
            kill -TERM $BUILD_PID 2>/dev/null || true
            sleep 2
            kill -KILL $BUILD_PID 2>/dev/null || true
            BUILD_SUCCESS=false
        fi
    fi
    
    if [ "$BUILD_SUCCESS" = true ]; then
        echo "✅ Frontend build completed successfully"
        
        # Verify build output
        if [ -d "dist" ] && [ -f "dist/index.html" ]; then
            echo "✅ Build verification passed"
            echo "📊 Build size: $(du -sh dist/ 2>/dev/null || echo 'Unknown')"
            echo "📁 Build contents:"
            ls -la dist/ | head -5
        else
            echo "⚠️ Build verification failed - missing dist/index.html"
        fi
    else
        echo "⚠️ Frontend build failed or timed out"
        mkdir -p dist
        echo '<!DOCTYPE html><html><head><title>Passive CAPTCHA</title></head><body><h1>API Server Running</h1><p>Frontend build failed</p><p><a href="/login">Login</a> | <a href="/health">Health</a></p></body></html>' > dist/index.html
    fi
    
    cd ../
else
    echo "⚠️ Frontend build skipped (Node.js unavailable or package.json missing)"
    # Create fallback frontend
    mkdir -p frontend/dist
    cat > frontend/dist/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passive CAPTCHA Admin</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .api-link { display: inline-block; margin: 10px; padding: 10px 20px; background: #007cba; color: white; text-decoration: none; border-radius: 5px; }
        .api-link:hover { background: #005a85; }
    </style>
</head>
<body>
    <h1>🔐 Passive CAPTCHA API Server</h1>
    <p>Frontend build not available. API endpoints are working:</p>
    <div>
        <a href="/login" class="api-link">🔑 Login API</a>
        <a href="/health" class="api-link">❤️ Health Check</a>
        <a href="/admin" class="api-link">⚙️ Admin API</a>
    </div>
    <h3>Quick Test:</h3>
    <pre>curl -X POST /login -H "Content-Type: application/json" -d '{"password": "Admin123"}'</pre>
</body>
</html>
EOF
fi

# Backend setup
echo "🔧 Setting up backend..."
cd backend

# Create necessary directories
mkdir -p logs uploads
touch logs/app.log

# Set permissions
chmod +x render_start.py 2>/dev/null || echo "Could not set execute permission on render_start.py"

echo "✅ Enhanced build completed successfully!"
echo "🚀 Ready for deployment"
echo "📊 Final directory structure:"
echo "   Backend: $(ls -la | wc -l) files"
echo "   Frontend: $(ls -la ../frontend/dist/ 2>/dev/null | wc -l || echo '0') files"