#!/usr/bin/env python3
"""
Passive CAPTCHA - Consolidated Application Factory
Single entry point for all environments (development, production, testing)
"""

import os
import sys
import redis
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Load environment variables
load_dotenv()

# Load production environment if available
if os.path.exists('config.env.production'):
    load_dotenv('config.env.production', override=True)


def create_app(config_name='production'):
    """
    Consolidated application factory for all environments
    """
    
    # Determine if we need to serve static files
    serve_frontend = os.getenv('SERVE_FRONTEND', 'true').lower() == 'true'
    static_folder = None
    
    if serve_frontend:
        # Configure Flask app to serve static frontend files
        backend_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(backend_dir)
        static_folder = os.path.join(project_root, 'frontend', 'dist')
        
        print(f"🔍 Static folder detection:")
        print(f"   Backend dir: {backend_dir}")
        print(f"   Project root: {project_root}")
        print(f"   Primary static path: {static_folder}")
        print(f"   Primary path exists: {os.path.exists(static_folder)}")
        
        # Check for alternative static folder locations (Render-optimized)
        if not os.path.exists(static_folder):
            alternative_paths = [
                # Render build process copies here
                os.path.join(backend_dir, 'static'),
                # Alternative project structures
                os.path.join(project_root, 'frontend', 'dist'),
                os.path.join(os.getcwd(), 'static'),
                os.path.join(os.getcwd(), 'frontend', 'dist'),
                # Render deployment paths
                '/opt/render/project/src/backend/static',
                '/opt/render/project/src/frontend/dist',
                # Relative fallbacks
                './static',
                './frontend/dist',
                '../frontend/dist'
            ]
            
            print(f"🔍 Checking alternative paths:")
            for alt_path in alternative_paths:
                abs_path = os.path.abspath(alt_path)
                exists = os.path.exists(abs_path)
                print(f"   {alt_path} -> {abs_path} (exists: {exists})")
                if exists:
                    static_folder = abs_path
                    print(f"✅ Found frontend at: {static_folder}")
                    break
            else:
                print(f"❌ No static folder found, disabling frontend serving")
                static_folder = None
                serve_frontend = False
        else:
            print(f"✅ Using primary static folder: {static_folder}")
        
        # Log static folder contents for debugging
        if static_folder and os.path.exists(static_folder):
            try:
                files = os.listdir(static_folder)
                print(f"📁 Static folder contains {len(files)} files: {files[:5]}{'...' if len(files) > 5 else ''}")
                # Check for index.html specifically
                index_path = os.path.join(static_folder, 'index.html')
                print(f"📄 index.html exists: {os.path.exists(index_path)}")
            except Exception as e:
                print(f"⚠️ Could not list static folder contents: {e}")
    
    # Create Flask app
    app = Flask(__name__, 
                static_folder=static_folder if serve_frontend else None,
                static_url_path='/static' if serve_frontend else None)
    
    # Configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'passive-captcha-production-secret'),
        'MODEL_PATH': os.getenv('MODEL_PATH', 'models/passive_captcha_rf.pkl'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///passive_captcha_production.db'),
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'CONFIDENCE_THRESHOLD': float(os.getenv('CONFIDENCE_THRESHOLD', '0.6')),
        'ADMIN_SECRET': os.getenv('ADMIN_SECRET', 'Admin123'),
        'RATE_LIMIT_REQUESTS': int(os.getenv('RATE_LIMIT_REQUESTS', '1000')),
        'API_BASE_URL': os.getenv('API_BASE_URL', os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:5003')),
        'WEBSOCKET_URL': os.getenv('WEBSOCKET_URL', os.getenv('RENDER_EXTERNAL_URL', 'ws://localhost:5003').replace('https://', 'wss://').replace('http://', 'ws://')),
        'DEBUG': config_name == 'development',
        'TESTING': config_name == 'testing',
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
        
        # WebSocket configuration
        'SOCKETIO_ASYNC_MODE': 'threading',
        'SOCKETIO_CORS_ALLOWED_ORIGINS': "*",
        
        # Logging configuration
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'LOG_FILE': os.getenv('LOG_FILE', 'logs/app.log'),
        'LOG_MAX_SIZE': int(os.getenv('LOG_MAX_SIZE', '10485760')),  # 10MB
        'LOG_BACKUP_COUNT': int(os.getenv('LOG_BACKUP_COUNT', '10'))
    })
    
    # Setup logging
    setup_logging(app)
    
    # CORS configuration
    render_url = os.getenv('RENDER_EXTERNAL_URL', '')
    default_origins = [
        'http://localhost:3000',
        'http://localhost:5003',
        'http://frontend:80',
        'https://passive-captcha.onrender.com'
    ]
    
    if render_url and render_url not in default_origins:
        default_origins.append(render_url)
    
    allowed_origins_str = os.getenv('ALLOWED_ORIGINS', ','.join(default_origins))
    cors_origins = allowed_origins_str.split(',') if allowed_origins_str != '*' else "*"
    
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["POST", "GET", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Website-Token"],
            "supports_credentials": True
        },
        r"/admin/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        },
        r"/health": {
            "origins": cors_origins,
            "methods": ["GET"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Initialize Redis client (optional)
    redis_client = None
    try:
        redis_client = redis.Redis.from_url(app.config['REDIS_URL'], decode_responses=True)
        redis_client.ping()
        app.logger.info("Redis connection established successfully")
    except Exception as e:
        app.logger.warning(f"Redis unavailable, running without caching: {e}")
    
    # Initialize SocketIO (optional)
    socketio = None
    try:
        socketio = SocketIO(
            app,
            cors_allowed_origins=cors_origins,
            async_mode=app.config['SOCKETIO_ASYNC_MODE'],
            logger=False,
            engineio_logger=False
        )
        app.logger.info("SocketIO initialized successfully")
    except Exception as e:
        app.logger.warning(f"SocketIO initialization failed: {e}")
    
    # Rate limiting - use in-memory by default, Redis if specifically available
    try:
        # Always use in-memory rate limiting to avoid Redis connection issues
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{app.config['RATE_LIMIT_REQUESTS']} per hour"]
        )
        limiter.init_app(app)
        app.logger.info("Rate limiting initialized with in-memory backend")
    except Exception as e:
        app.logger.warning(f"Rate limiting initialization failed, disabling: {e}")
        # Continue without rate limiting if everything fails
        limiter = None
    
    # Initialize database
    try:
        from app.database import init_db
        with app.app_context():
            init_db()
            app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
        # Don't raise - let app start without database for debugging
    
    # Initialize ML model (optional)
    try:
        from app.ml import load_model
        with app.app_context():
            load_model()
            app.logger.info("ML model loaded successfully")
    except Exception as e:
        app.logger.warning(f"ML model loading failed: {e}")
    
    # Initialize services
    auth_service = None
    website_service = None
    try:
        from app.services import init_auth_service, init_website_service
        auth_service = init_auth_service(redis_client)
        if redis_client:
            website_service = init_website_service(redis_client)
        app.logger.info("Services initialized successfully")
    except Exception as e:
        app.logger.warning(f"Service initialization failed: {e}")
    
    # Register core API blueprints
    try:
        from app.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        app.logger.info("Core API endpoints registered")
    except Exception as e:
        app.logger.error(f"Failed to register core API: {e}")
    
    # Register consolidated admin blueprint
    try:
        from app.api.admin_endpoints import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.logger.info("Admin API endpoints registered")
    except Exception as e:
        app.logger.error(f"Failed to register admin API: {e}")
    
    # Register analytics and monitoring endpoints (non-conflicting)
    try:
        from app.admin.analytics_endpoints import analytics_bp
        from app.admin.alerts_endpoints import alerts_bp
        from app.admin.logs_endpoints import logs_bp
        from app.admin.ml_metrics_endpoints import ml_metrics_bp
        
        app.register_blueprint(analytics_bp)
        app.register_blueprint(alerts_bp)
        app.register_blueprint(logs_bp)
        app.register_blueprint(ml_metrics_bp)
        app.logger.info("Analytics and monitoring endpoints registered")
    except Exception as e:
        app.logger.warning(f"Failed to register analytics endpoints: {e}")
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint"""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': int(__import__('time').time()),
                'version': '2.0.0',
                'components': {
                    'database': 'unknown',
                    'redis': 'available' if redis_client else 'disabled',
                    'ml_model': 'unknown',
                    'services': 'available' if auth_service else 'disabled',
                    'rate_limiting': 'available' if hasattr(app, 'limiter') and app.limiter else 'disabled',
                    'websocket': 'available' if socketio else 'disabled'
                },
                'metrics': {
                    'uptime_seconds': int(__import__('time').time()) - app.start_time if hasattr(app, 'start_time') else 0,
                    'websocket_connections': 0  # TODO: Get actual count from SocketIO
                }
            }
            
            # Test database
            try:
                from app.database import get_db_session
                session = get_db_session()
                # Try different SQL formats for compatibility
                try:
                    session.execute(__import__('sqlalchemy').text('SELECT 1'))
                except:
                    # Fallback for older SQLAlchemy versions
                    session.execute('SELECT 1')
                session.close()
                health_status['components']['database'] = 'healthy'
            except Exception as db_error:
                health_status['components']['database'] = 'error'
                health_status['status'] = 'unhealthy'
            
            # Test ML model
            try:
                from app.ml import model_loaded
                health_status['components']['ml_model'] = 'healthy' if model_loaded else 'unavailable'
            except Exception:
                health_status['components']['ml_model'] = 'unavailable'
            
            # Test Redis connection if client exists
            if redis_client:
                try:
                    redis_client.ping()
                    health_status['components']['redis'] = 'healthy'
                except Exception:
                    health_status['components']['redis'] = 'error'
            
            return jsonify(health_status)
            
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': int(__import__('time').time())
            }), 500
    
    # Frontend serving (if enabled)
    if serve_frontend and static_folder and os.path.exists(static_folder):
        register_frontend_routes(app, static_folder)
    
    # Store references for external access
    app.redis_client = redis_client
    app.socketio = socketio
    app.auth_service = auth_service
    app.website_service = website_service
    app.limiter = limiter if 'limiter' in locals() else None
    app.start_time = int(__import__('time').time())
    
    app.logger.info("Application created successfully")
    return app, socketio


def register_frontend_routes(app, static_folder):
    """Register frontend serving routes"""
    
    @app.route('/')
    def serve_root():
        """Serve Vue.js frontend root"""
        try:
            return app.send_static_file('index.html')
        except Exception as e:
            app.logger.error(f"Failed to serve index.html: {e}")
            return '''
            <!DOCTYPE html>
            <html><head><title>Passive CAPTCHA</title></head>
            <body>
                <h1>🔐 Passive CAPTCHA API</h1>
                <p>✅ API Server Running</p>
                <div>
                    <a href="/health">❤️ Health Check</a> |
                    <a href="/admin/login">🔑 Admin Login</a>
                </div>
            </body></html>
            '''
    
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Serve Vue.js build assets"""
        try:
            asset_path = os.path.join(static_folder, 'assets', filename)
            if os.path.exists(asset_path):
                mimetype = 'application/javascript' if filename.endswith('.js') else \
                          'text/css' if filename.endswith('.css') else \
                          'application/json' if filename.endswith('.map') else \
                          'application/octet-stream'
                
                with open(asset_path, 'rb') as f:
                    response = app.response_class(
                        f.read(),
                        mimetype=mimetype,
                        headers={'Cache-Control': 'public, max-age=31536000, immutable'}
                    )
                    return response
            else:
                abort(404)
        except Exception as e:
            app.logger.error(f"Error serving asset {filename}: {e}")
            abort(500)
    
    @app.route('/<path:path>')
    def serve_spa(path):
        """Enhanced SPA route handler for Vue.js application"""
        
        # Define API and backend routes that should NOT serve the SPA
        api_prefixes = ('api/', 'assets/', 'static/', 'socket.io/')
        
        # Define specific backend endpoints that should not serve SPA
        backend_endpoints = ('health', 'admin/login', 'admin/logout', 'admin/health', 'admin/statistics')
        
        # Define file extensions that should be served directly or return 404
        file_extensions = ('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.map', '.txt', '.xml', '.json')
        
        # Log the request for debugging
        app.logger.info(f"SPA route handler: /{path}")
        
        # 1. Skip API routes - these should be handled by their respective blueprints
        if path.startswith(api_prefixes) or path in backend_endpoints:
            app.logger.info(f"Skipping API/backend route: /{path}")
            abort(404)
        
        # 2. Handle direct file requests
        if path.endswith(file_extensions):
            file_path = os.path.join(static_folder, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                app.logger.debug(f"Serving static file: {path}")
                return app.send_static_file(path)
            else:
                app.logger.debug(f"Static file not found: {path}")
                abort(404)
        
        # 3. Serve Vue.js SPA for all other routes (dashboard, login, websites, etc.)
        # This includes routes like: dashboard, login, websites, analytics, settings, etc.
        try:
            app.logger.debug(f"Serving SPA for route: /{path}")
            index_path = os.path.join(static_folder, 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    response = app.response_class(
                        content,
                        mimetype='text/html',
                        headers={
                            'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache',
                            'Expires': '0'
                        }
                    )
                    return response
            else:
                app.logger.error(f"index.html not found at {index_path}")
                abort(404)
        except Exception as e:
            app.logger.error(f"Error serving SPA for route /{path}: {e}")
            # Fallback to basic error page
            return f'''
            <!DOCTYPE html>
            <html>
            <head><title>Passive CAPTCHA</title></head>
            <body>
                <h1>🔐 Passive CAPTCHA</h1>
                <p>⚠️ Frontend temporarily unavailable</p>
                <p><a href="/admin/login">Admin API Login</a></p>
                <p><a href="/health">System Health</a></p>
            </body>
            </html>
            ''', 503


def setup_logging(app):
    """Setup logging for the application"""
    if app.config.get('DEBUG'):
        return  # Use default logging in debug mode
    
    # Create logs directory
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set log level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    app.logger.setLevel(log_level)
    
    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_SIZE'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        
        file_handler.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")


def get_wsgi_app():
    """Get WSGI application for production servers like gunicorn"""
    app, socketio = create_app('production')
    return socketio if socketio else app


def run_app(host='0.0.0.0', port=None, debug=False):
    """Run the application"""
    if port is None:
        port = int(os.getenv('PORT', 5003))
    
    app, socketio = create_app('development' if debug else 'production')
    
    if socketio:
        print(f"🚀 Starting Passive CAPTCHA with SocketIO on {host}:{port}")
        # Allow unsafe Werkzeug in production for development purposes
        # In real production, this should use a proper WSGI server like gunicorn
        socketio.run(app, host=host, port=port, debug=debug, use_reloader=False, 
                    allow_unsafe_werkzeug=True)
    else:
        print(f"🚀 Starting Passive CAPTCHA on {host}:{port}")
        app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Passive CAPTCHA Application')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=None, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--gunicorn', action='store_true', help='Use gunicorn for production (requires gunicorn installed)')
    
    args = parser.parse_args()
    
    if args.gunicorn and not args.debug:
        # Use gunicorn for production
        import subprocess
        import sys
        port = args.port or int(os.getenv('PORT', 5003))
        cmd = [
            'gunicorn',
            '--worker-class', 'eventlet',
            '--workers', '1',
            '--bind', f'{args.host}:{port}',
            '--timeout', '120',
            '--keep-alive', '2',
            'main:get_wsgi_app()'
        ]
        print(f"🚀 Starting Passive CAPTCHA with Gunicorn on {args.host}:{port}")
        subprocess.run(cmd)
    else:
        run_app(host=args.host, port=args.port, debug=args.debug)