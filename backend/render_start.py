#!/usr/bin/env python3
"""
Render.com Production Startup Script
Optimized for cloud deployment with minimal dependencies
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup environment for Render deployment"""
    print("🚀 Passive CAPTCHA - Render Deployment")
    print("=" * 50)
    
    # Set production environment variables
    os.environ.update({
        'FLASK_ENV': 'production',
        'ADMIN_SECRET': 'Admin123',
        'PORT': str(os.environ.get('PORT', 5003)),
        'HOST': '0.0.0.0'
    })
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    print(f"✅ Environment configured")
    print(f"   PORT: {os.environ.get('PORT')}")
    print(f"   HOST: {os.environ.get('HOST')}")

def start_application():
    """Start the Flask application"""
    try:
        from app.production_app import create_production_app
        
        app = create_production_app()
        port = int(os.environ.get('PORT', 5003))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🌐 Starting server on {host}:{port}")
        
        # Use Gunicorn if available, otherwise Flask dev server
        try:
            import gunicorn.app.base
            
            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    config = {key: value for key, value in self.options.items()
                             if key in self.cfg.settings and value is not None}
                    for key, value in config.items():
                        self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application
            
            options = {
                'bind': f'{host}:{port}',
                'workers': 1,
                'timeout': 120,
                'keepalive': 5,
                'max_requests': 1000,
                'max_requests_jitter': 100,
                'loglevel': 'info'
            }
            
            StandaloneApplication(app, options).run()
            
        except ImportError:
            print("⚠️  Gunicorn not available, using Flask dev server")
            app.run(
                host=host,
                port=port,
                debug=False,
                threaded=True
            )
            
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    setup_environment()
    start_application()