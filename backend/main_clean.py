#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passive CAPTCHA - Clean Application Entry Point
Fixed authentication system and simplified structure
"""

import os
import sys
import redis
from flask import Flask, request, jsonify, send_from_directory, abort
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
production_config_paths = [
    'config.env.production',
    './config.env.production',
    'backend/config.env.production',
    '../config.env.production'
]

for config_path in production_config_paths:
    if os.path.exists(config_path):
        load_dotenv(config_path, override=True)
        print(f"[SUCCESS] Loaded production config from: {config_path}")
        break


def create_app(config_name='production'):
    """
    Clean application factory with fixed authentication
    """
    # Determine if we need to serve static files
    serve_frontend = os.getenv('SERVE_FRONTEND', 'true').lower() == 'true'
    static_folder = None

    if serve_frontend:
        # Configure Flask app to serve static frontend files
        backend_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(backend_dir)
        static_folder = os.path.join(project_root, 'frontend', 'dist')

        if not os.path.exists(static_folder):
            # Check alternative locations
            alternative_paths = [
                os.path.join(backend_dir, 'static'),
                os.path.join(os.getcwd(), 'static'),
                './static'
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    static_folder = alt_path
                    break
            else:
                static_folder = None
                serve_frontend = False

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
        'DEBUG': config_name == 'development',
        'TESTING': config_name == 'testing',
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
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
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
            "supports_credentials": True
        },
        r"/health": {
            "origins": cors_origins,
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Initialize Redis client (optional)
    redis_client = None
    try:
        redis_client = redis.Redis.from_url(app.config['REDIS_URL'], decode_responses=True)
        redis_client.ping()
        app.logger.info("✅ Redis connection established successfully")
    except Exception as e:
        app.logger.info(f"💾 Redis unavailable, running without caching: {type(e).__name__}")

    # Initialize SocketIO (optional)
    socketio = None
    try:
        socketio = SocketIO(
            app,
            cors_allowed_origins=cors_origins,
            async_mode='threading',
            logger=False,
            engineio_logger=False
        )
        app.logger.info("✅ SocketIO initialized successfully")
    except Exception as e:
        app.logger.warning(f"⚠️ SocketIO initialization failed: {e}")

    # Rate limiting
    limiter = None
    try:
        limiter_config = {
            'key_func': get_remote_address,
            'default_limits': [f"{app.config['RATE_LIMIT_REQUESTS']} per hour"]
        }
        
        if redis_client:
            limiter_config['storage_uri'] = app.config['REDIS_URL']
            app.logger.info("✅ Rate limiting with Redis backend")
        else:
            app.logger.info("✅ Rate limiting with in-memory backend")
        
        limiter = Limiter(**limiter_config)
        limiter.init_app(app)
    except Exception as e:
        app.logger.warning(f"⚠️ Rate limiting disabled: {e}")

    # Initialize database
    try:
        from app.database import init_db
        with app.app_context():
            init_db()
            app.logger.info("✅ Database initialized successfully")
    except Exception as e:
        app.logger.error(f"❌ Database initialization failed: {e}")

    # Initialize ML model
    try:
        from app.ml import load_model
        with app.app_context():
            load_model()
            app.logger.info("✅ ML model loaded successfully")
    except Exception as e:
        app.logger.warning(f"⚠️ ML model loading failed: {e}")

    # Initialize unified authentication service
    auth_service = None
    website_service = None
    try:
        app.logger.info("🔐 Initializing unified authentication service...")
        
        # Initialize unified auth service
        from app.services.auth_service import init_auth_service
        auth_service = init_auth_service(redis_client)
        app.logger.info(f"✅ Auth service initialized with admin_secret: {auth_service.admin_secret}")

        # Initialize website service
        from app.services import init_website_service
        website_service = init_website_service(redis_client)
        app.logger.info(f"✅ Website service initialized: {website_service is not None}")

        # Initialize Script Token Manager
        from app.script_token_manager import init_script_token_manager
        script_token_manager = init_script_token_manager(redis_client)
        app.logger.info(f"✅ Script token manager initialized: {script_token_manager is not None}")

    except Exception as e:
        app.logger.error(f"❌ Service initialization failed: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")

    # Register core API blueprints
    try:
        from app.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        app.logger.info("✅ Core API endpoints registered")
    except Exception as e:
        app.logger.error(f"❌ Failed to register core API: {e}")

    # Register admin API blueprints
    try:
        from app.api.admin_endpoints import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.logger.info("✅ Admin API endpoints registered")
    except Exception as e:
        app.logger.error(f"❌ Failed to register admin API: {e}")

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint"""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': int(__import__('time').time()),
                'version': '2.0.0-clean',
                'components': {
                    'database': 'unknown',
                    'redis': 'available' if redis_client else 'disabled',
                    'ml_model': 'unknown',
                    'auth_service': 'available' if auth_service else 'disabled',
                    'rate_limiting': 'available' if limiter else 'disabled',
                    'websocket': 'available' if socketio else 'disabled'
                }
            }

            # Test database
            try:
                from app.database import get_db_session
                session = get_db_session()
                session.execute(__import__('sqlalchemy').text('SELECT 1'))
                session.close()
                health_status['components']['database'] = 'healthy'
            except Exception:
                health_status['components']['database'] = 'error'
                health_status['status'] = 'degraded'

            # Test ML model
            try:
                from app.ml import model_loaded
                health_status['components']['ml_model'] = 'healthy' if model_loaded else 'unavailable'
            except Exception:
                health_status['components']['ml_model'] = 'unavailable'

            return jsonify(health_status)

        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': int(__import__('time').time())
            }), 500

    # Static file serving
    @app.route('/passive-captcha-script.js')
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
                return f'// Script not found at: {script_path}', 404, {
                    'Content-Type': 'application/javascript'
                }
        except Exception as e:
            return f'// Script error: {e}', 500, {
                'Content-Type': 'application/javascript'
            }

    # Frontend serving (if enabled)
    if serve_frontend and static_folder and os.path.exists(static_folder):
        register_frontend_routes(app, static_folder)

    # Store references for external access
    app.redis_client = redis_client
    app.socketio = socketio
    app.auth_service = auth_service
    app.website_service = website_service
    app.limiter = limiter
    app.start_time = int(__import__('time').time())

    app.logger.info("✅ Application created successfully")
    return app, socketio


def register_frontend_routes(app, static_folder):
    """Register frontend routes for serving Vue.js application"""
    
    @app.route('/')
    def serve_index():
        """Serve Vue.js frontend"""
        try:
            index_path = os.path.join(static_folder, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder, 'index.html')
            else:
                # Fallback dashboard
                return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>🛡️ Passive CAPTCHA Dashboard</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                               margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                               min-height: 100vh; display: flex; align-items: center; justify-content: center; }
                        .container { background: white; padding: 40px; border-radius: 16px; 
                                   box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; max-width: 500px; }
                        .nav-link { display: inline-block; background: #4338ca; color: white; 
                                  padding: 12px 24px; text-decoration: none; border-radius: 8px; 
                                  margin: 8px; transition: all 0.3s; }
                        .nav-link:hover { background: #3730a3; transform: translateY(-2px); }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🛡️ Passive CAPTCHA Dashboard</h1>
                        <p>Advanced Behavioral Authentication System</p>
                        <div>
                            <a href="/admin" class="nav-link">📊 Admin Panel</a>
                            <a href="/health" class="nav-link">🔍 System Health</a>
                        </div>
                        <div style="margin-top: 20px; color: #059669; font-size: 14px;">
                            ✅ Server Running • Authentication Fixed
                        </div>
                    </div>
                </body>
                </html>
                '''
        except Exception as e:
            app.logger.error(f"Failed to serve frontend: {e}")
            return jsonify({'error': 'Frontend service unavailable'}), 503

    @app.route('/admin')
    def serve_admin():
        """Serve admin dashboard"""
        try:
            return serve_index()  # Same as main index for SPA routing
        except Exception as e:
            app.logger.error(f"Failed to serve admin: {e}")
            return jsonify({'error': 'Admin dashboard unavailable'}), 503

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Serve Vue.js build assets"""
        try:
            asset_path = os.path.join(static_folder, 'assets', filename)
            if os.path.exists(asset_path):
                return send_from_directory(os.path.join(static_folder, 'assets'), filename)
            else:
                abort(404)
        except Exception as e:
            app.logger.error(f"Error serving asset {filename}: {e}")
            abort(500)

    @app.route('/<path:path>')
    def serve_spa(path):
        """Serve SPA routes"""
        # Skip API routes
        if path.startswith(('api/', 'admin/', 'assets/', 'static/', 'health')):
            abort(404)
        
        # Handle file extensions
        if path.endswith(('.js', '.css', '.png', '.jpg', '.ico', '.map')):
            try:
                return send_from_directory(static_folder, path)
            except Exception:
                abort(404)
        
        # Serve index.html for SPA routes
        return serve_index()


def setup_logging(app):
    """Setup logging for the application"""
    if app.config.get('DEBUG'):
        return

    # Create logs directory
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set log level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    app.logger.setLevel(log_level)

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
    """Get WSGI application for production servers"""
    try:
        app, socketio = create_app('production')
        print(f"[WSGI] Returning Flask app for production deployment")
        return app
    except Exception as e:
        print(f"[ERROR] Failed to create WSGI app: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency fallback
        from flask import Flask
        emergency_app = Flask(__name__)
        
        @emergency_app.route('/health')
        def health():
            return {'status': 'error', 'message': 'Application failed to initialize'}
            
        return emergency_app


def run_app(host='0.0.0.0', port=None, debug=False):
    """Run the application"""
    if port is None:
        port = int(os.getenv('PORT', 5003))

    app, socketio = create_app('development' if debug else 'production')

    if socketio:
        print(f"[DEPLOY] 🚀 Starting Passive CAPTCHA with SocketIO on {host}:{port}")
        socketio.run(app, host=host, port=port, debug=debug, 
                    use_reloader=False, allow_unsafe_werkzeug=True)
    else:
        print(f"[DEPLOY] 🚀 Starting Passive CAPTCHA on {host}:{port}")
        app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Passive CAPTCHA Application')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=None, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print("🛡️ Passive CAPTCHA - Clean Version with Fixed Authentication")
    print("=" * 60)
    run_app(args.host, args.port, args.debug)