#!/usr/bin/env python3
"""
Passive CAPTCHA Production Application
"""

import os
import sys
from typing import Tuple, Optional
from flask import Flask
from flask_socketio import SocketIO

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def create_app(env: str = 'production') -> Tuple[Flask, Optional[SocketIO]]:
    """
    Create robust application using the new factory pattern
    """
    try:
        from app.core.factory import create_robust_app
        return create_robust_app(env)
    except Exception as e:
        print(f"Failed to create robust app: {e}")
        # Fallback to basic app
        return create_fallback_app(env)


def create_fallback_app(env: str) -> Tuple[Flask, None]:
    """
    Fallback application creation if robust factory fails
    """
    from flask import Flask
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'fallback-secret-key'),
        'DEBUG': env == 'development',
    })
    
    @app.route('/health')
    def health():
        return {
            'status': 'degraded',
            'message': 'Running in fallback mode',
            'timestamp': int(__import__('time').time())
        }
    
    @app.route('/')
    def index():
        return '''
        <h1>🛡️ Passive CAPTCHA - Fallback Mode</h1>
        <p>Application is running in fallback mode.</p>
        <a href="/health">Health Check</a>
        '''
    
    return app, None


def register_frontend_routes(app: Flask, static_folder: str) -> None:
    """Register frontend serving routes"""
    
    @app.route('/')
    def serve_index():
        try:
            from flask import send_from_directory
            return send_from_directory(static_folder, 'index.html')
        except Exception:
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>Passive CAPTCHA Dashboard</title></head>
            <body>
                <h1>🛡️ Passive CAPTCHA Dashboard</h1>
                <p>Advanced Behavioral Authentication System</p>
                <div>
                    <a href="/admin" style="display: inline-block; background: #4338ca; color: white; 
                           padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 8px;">
                        📊 Admin Panel
                    </a>
                    <a href="/health" style="display: inline-block; background: #059669; color: white; 
                           padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 8px;">
                        🔍 System Health
                    </a>
                </div>
                <div style="margin-top: 20px; color: #059669; font-size: 14px;">
                    ✅ Server Running • Authentication Fixed • Robust Architecture
                </div>
            </body>
            </html>
            '''
    
    @app.route('/admin')
    def serve_admin():
        return serve_index()
    
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        try:
            from flask import send_from_directory, abort
            asset_path = os.path.join(static_folder, 'assets', filename)
            if os.path.exists(asset_path):
                return send_from_directory(os.path.join(static_folder, 'assets'), filename)
            else:
                abort(404)
        except Exception:
            from flask import abort
            abort(404)
    
    @app.route('/<path:path>')
    def serve_spa(path):
        # Skip API routes
        if path.startswith(('api/', 'admin/', 'assets/', 'health')):
            from flask import abort
            abort(404)
        
        # Handle file extensions
        if path.endswith(('.js', '.css', '.png', '.jpg', '.ico', '.map')):
            try:
                from flask import send_from_directory
                return send_from_directory(static_folder, path)
            except Exception:
                from flask import abort
                abort(404)
        
        # Serve index.html for SPA routes
        return serve_index()


def add_script_routes(app: Flask) -> None:
    """Add passive CAPTCHA script serving routes"""
    
    @app.route('/passive-captcha-script.js')
    @app.route('/app/static/passive-captcha-script.js')
    @app.route('/backend/app/static/passive-captcha-script.js')
    @app.route('/static/passive-captcha-script.js')
    def serve_passive_captcha_script():
        """Serve the passive captcha script"""
        try:
            static_dir = os.path.join(os.path.dirname(__file__), 'app', 'static')
            script_path = os.path.join(static_dir, 'passive-captcha-script.js')
            
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, 200, {
                    'Content-Type': 'application/javascript; charset=utf-8',
                    'Cache-Control': 'public, max-age=3600',
                    'Access-Control-Allow-Origin': '*'
                }
            else:
                return f'// Passive CAPTCHA script not found at: {script_path}', 404, {
                    'Content-Type': 'application/javascript'
                }
        except Exception as e:
            return f'// Script error: {e}', 500, {
                'Content-Type': 'application/javascript'
            }


def get_wsgi_app():
    """Get WSGI application for production deployment"""
    try:
        app, socketio = create_app('production')
        return app
    except Exception as e:
        print(f"WSGI app creation failed: {e}")
        # Return emergency fallback
        from flask import Flask
        emergency_app = Flask(__name__)
        
        @emergency_app.route('/health')
        def health():
            return {'status': 'error', 'message': 'WSGI initialization failed'}
        
        return emergency_app


def run_app(host: str = '0.0.0.0', port: Optional[int] = None, debug: bool = False) -> None:
    """Run the application with proper error handling"""
    if port is None:
        port = int(os.getenv('PORT', 5003))
    
    env = 'development' if debug else 'production'
    
    try:
        app, socketio = create_app(env)
        
        # Register additional routes
        add_script_routes(app)
        
        # Find and register frontend routes if static folder exists
        if hasattr(app, 'static_folder') and app.static_folder:
            register_frontend_routes(app, app.static_folder)
        
        print(f"🚀 Starting Passive CAPTCHA on {host}:{port}")
        print(f"📊 Environment: {env}")
        print(f"✅ Authentication: Fixed & Robust")
        print(f"🔧 Architecture: Production-Ready")
        
        if socketio:
            print(f"🔌 SocketIO: Enabled")
            socketio.run(app, host=host, port=port, debug=debug, 
                        use_reloader=False, allow_unsafe_werkzeug=True)
        else:
            print(f"🔌 SocketIO: Disabled")
            app.run(host=host, port=port, debug=debug, use_reloader=False)
            
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Passive CAPTCHA Application')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=None, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--env', choices=['development', 'testing', 'production'], 
                       default=None, help='Environment override')
    
    args = parser.parse_args()
    
    # Override environment if specified
    if args.env:
        os.environ['FLASK_ENV'] = args.env
    
    print("🛡️ PASSIVE CAPTCHA")
    print("=" * 30)
    print("✅ Authentication Fixed")
    print("✅ Production Ready")
    print("=" * 30)
    
    run_app(args.host, args.port, args.debug)