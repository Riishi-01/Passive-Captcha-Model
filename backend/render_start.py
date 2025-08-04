#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render.com Production Startup Script
Optimized for cloud deployment with minimal dependencies
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup environment for Render deployment"""
    print("[DEPLOY] Passive CAPTCHA - Render Deployment")
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

    print(f"[SUCCESS] Environment configured")
    print(f"   PORT: {os.environ.get('PORT')}")
    print(f"   HOST: {os.environ.get('HOST')}")

def start_application():
    """Start the Flask application"""
    try:
        from main import create_app  # Using consolidated application factory

        app, socketio = create_app('production')
        port = int(os.environ.get('PORT', 5003))
        host = os.environ.get('HOST', '0.0.0.0')

        print(f"[NETWORK] Starting server on {host}:{port}")
        print(f"[SIGNAL] Server will be accessible on port {port}")

        if socketio:
            print("[CHAR] Using SocketIO server")
            socketio.run(
                app,
                host=host,
                port=port,
                debug=False,
                use_reloader=False,
                log_output=True,
                allow_unsafe_werkzeug=True
            )
        else:
            print("[CHAR] Using standard Flask server")
            app.run(
                host=host,
                port=port,
                debug=False,
                use_reloader=False
            )

    except Exception as e:
        print(f"[ERROR] Application startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    setup_environment()
    start_application()
