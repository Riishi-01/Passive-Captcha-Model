#!/usr/bin/env python3
"""
Simple production deployment script for Passive CAPTCHA
Single port deployment with frontend and backend
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def main():
    print("🚀 Passive CAPTCHA - Single Port Production Deployment")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    os.environ['ADMIN_SECRET'] = 'Admin123'
    os.environ['PORT'] = '5003'
    os.environ['HOST'] = '0.0.0.0'
    
    print("📋 Environment Configuration:")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Admin Password: {os.environ['ADMIN_SECRET']}")
    print(f"   Port: {os.environ['PORT']}")
    print(f"   Host: {os.environ['HOST']}")
    
    # Check frontend build
    frontend_dist = project_root / 'frontend' / 'dist'
    if frontend_dist.exists():
        print(f"✅ Frontend build found at: {frontend_dist}")
        print(f"   Files: {list(os.listdir(frontend_dist))}")
    else:
        print(f"❌ Frontend build not found at: {frontend_dist}")
        print("   Building frontend...")
        
        # Build frontend
        result = subprocess.run(['npm', 'run', 'build'], 
                               cwd=project_root / 'frontend',
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Frontend build failed: {result.stderr}")
            return False
        print("✅ Frontend built successfully")
    
    # Start the production server
    try:
        print("\n🚀 Starting Production Server...")
        print("=" * 60)
        
        # Change to backend directory and start server
        os.chdir(project_root / 'backend')
        
        # Load production environment
        if os.path.exists('config.env.production'):
            from dotenv import load_dotenv
            load_dotenv('config.env.production')
            print("✅ Loaded production environment")
        
        # Import and start the production app
        from app.production_app import create_production_app
        
        print("Creating production Flask application...")
        app, socketio = create_production_app('production')
        
        port = int(os.environ['PORT'])
        host = os.environ['HOST']
        
        print(f"\n{'='*60}")
        print(f"🎉 PASSIVE CAPTCHA PRODUCTION SERVER READY")
        print(f"{'='*60}")
        print(f"🌐 Server: http://{host}:{port}")
        print(f"🏠 Frontend: http://{host}:{port}/")
        print(f"🔍 Health: http://{host}:{port}/health")
        print(f"🔑 Admin: Use password '{os.environ['ADMIN_SECRET']}'")
        print(f"🔐 Login API: POST http://{host}:{port}/admin/login")
        print(f"{'='*60}")
        print(f"Press Ctrl+C to stop the server")
        print(f"{'='*60}")
        
        # Store start time
        app.start_time = time.time()
        
        # Start server
        if socketio:
            socketio.run(app, host=host, port=port, debug=False, use_reloader=False)
        else:
            app.run(host=host, port=port, debug=False, use_reloader=False)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)