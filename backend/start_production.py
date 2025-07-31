#!/usr/bin/env python3
"""
Production startup script for Passive CAPTCHA
Builds frontend and starts the production server on a single port
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def run_command(cmd, cwd=None, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}")
    
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ Error: {description} failed with exit code {result.returncode}")
        return False
    print(f"✅ {description} completed successfully")
    return True

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js is not installed")
            return False
    except FileNotFoundError:
        print("❌ Node.js is not installed")
        return False
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm: {result.stdout.strip()}")
        else:
            print("❌ npm is not installed")
            return False
    except FileNotFoundError:
        print("❌ npm is not installed")
        return False
    
    return True

def setup_backend():
    """Setup backend environment"""
    print("\n🚀 Setting up backend...")
    
    # Ensure required directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", description="Installing Python dependencies"):
        return False
    
    return True

def build_frontend():
    """Build the frontend"""
    frontend_dir = Path(__file__).parent.parent / 'frontend'
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    print(f"\n🏗️ Building frontend in {frontend_dir}")
    
    # Install dependencies
    if not run_command("npm install", cwd=frontend_dir, description="Installing frontend dependencies"):
        return False
    
    # Build for production
    if not run_command("npm run build", cwd=frontend_dir, description="Building frontend for production"):
        return False
    
    # Check if dist folder was created
    dist_dir = frontend_dir / 'dist'
    if not dist_dir.exists():
        print("❌ Frontend build failed - dist directory not found")
        return False
    
    print(f"✅ Frontend built successfully at {dist_dir}")
    return True

def start_redis():
    """Start Redis server if not running"""
    print("\n📦 Starting Redis server...")
    
    # Check if Redis is already running
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == 'PONG':
            print("✅ Redis is already running")
            return True
    except FileNotFoundError:
        pass
    
    # Try to start Redis
    try:
        # Start Redis in background
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # Give Redis time to start
        
        # Check if it started
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == 'PONG':
            print("✅ Redis started successfully")
            return True
        else:
            print("⚠️ Redis may not be available - continuing without caching")
            return True  # Continue without Redis
    except FileNotFoundError:
        print("⚠️ Redis not found - continuing without caching")
        return True  # Continue without Redis

def start_production_server():
    """Start the production server"""
    print("\n🚀 Starting production server...")
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    
    # Start the server
    try:
        from app.production_app import create_production_app
        
        print("Creating production application...")
        app, socketio = create_production_app('production')
        
        port = int(os.getenv('PORT', 5003))
        host = os.getenv('HOST', '0.0.0.0')
        
        print(f"\n{'='*60}")
        print(f"🎉 PASSIVE CAPTCHA PRODUCTION SERVER")
        print(f"{'='*60}")
        print(f"🌐 Server: http://{host}:{port}")
        print(f"🏠 Dashboard: http://{host}:{port}/")
        print(f"🔍 Health Check: http://{host}:{port}/health")
        print(f"🔑 Admin Login: Use password 'Admin123'")
        print(f"{'='*60}")
        print(f"Press Ctrl+C to stop the server")
        print(f"{'='*60}\n")
        
        # Store start time for health check
        app.start_time = time.time()
        
        if socketio:
            socketio.run(app, host=host, port=port, debug=False, use_reloader=False)
        else:
            app.run(host=host, port=port, debug=False, use_reloader=False)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main function"""
    print("🚀 Passive CAPTCHA Production Setup")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir(Path(__file__).parent)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        sys.exit(1)
    
    # Build frontend
    if not build_frontend():
        sys.exit(1)
    
    # Start Redis (optional)
    start_redis()
    
    # Start production server
    if not start_production_server():
        sys.exit(1)

if __name__ == '__main__':
    main()