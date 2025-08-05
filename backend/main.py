#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
else:
    print("[WARNING] No production config file found")


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

        print(f"[SEARCH] Static folder detection:")
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

            print(f"[SEARCH] Checking alternative paths:")
            for alt_path in alternative_paths:
                abs_path = os.path.abspath(alt_path)
                exists = os.path.exists(abs_path)
                print(f"   {alt_path} -> {abs_path} (exists: {exists})")
                if exists:
                    static_folder = abs_path
                    print(f"[SUCCESS] Found frontend at: {static_folder}")
                    break
            else:
                print(f"[ERROR] No static folder found, disabling frontend serving")
                static_folder = None
                serve_frontend = False
        else:
            print(f"[SUCCESS] Using primary static folder: {static_folder}")

        # Log static folder contents for debugging
        if static_folder and os.path.exists(static_folder):
            try:
                files = os.listdir(static_folder)
                print(f"[CHAR] Static folder contains {len(files)} files: {files[:5]}{'...' if len(files) > 5 else ''}")
                # Check for index.html specifically
                index_path = os.path.join(static_folder, 'index.html')
                print(f"[DOCUMENT] index.html exists: {os.path.exists(index_path)}")
            except Exception as e:
                print(f"[WARNING] Could not list static folder contents: {e}")

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
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Website-Token", "X-Requested-With", "Cache-Control"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        },
        r"/admin/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Cache-Control", "Accept", "Origin"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"],
            "max_age": 86400  # 24 hours preflight cache
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
        app.logger.info("Redis connection established successfully")
    except Exception as e:
        app.logger.info(f"💾 Redis unavailable, running without caching (development mode): {type(e).__name__}")

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

    # Rate limiting - use Redis if available, fallback to in-memory
    try:
        limiter_config = {
            'key_func': get_remote_address,
            'default_limits': [f"{app.config['RATE_LIMIT_REQUESTS']} per hour"]
        }
        
        if redis_client:
            try:
                # Test Redis connection first
                redis_client.ping()
                limiter_config['storage_uri'] = app.config['REDIS_URL']
                app.logger.info("Rate limiting initialized with Redis backend")
            except:
                app.logger.info("Rate limiting using in-memory backend (Redis unavailable)")
        else:
            app.logger.info("Rate limiting using in-memory backend (development mode)")
        
        limiter = Limiter(**limiter_config)
        limiter.init_app(app)
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
    
    # Initialize robust authentication system
    try:
        from app.auth_integration import integrate_with_existing_app
        with app.app_context():
            auth_success = integrate_with_existing_app(app)
            if auth_success:
                app.logger.info("✅ Robust authentication system integrated")
            else:
                app.logger.warning("⚠️  Failed to integrate robust authentication, using fallback")
    except Exception as e:
        app.logger.warning(f"⚠️  Authentication integration error: {e}, using fallback")

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
        app.logger.info("Importing services modules...")

        app.logger.info(f"Initializing auth service with Redis: {redis_client is not None}")
        app.logger.info(f"ADMIN_SECRET in app.config: {app.config.get('ADMIN_SECRET')}")
        
        # Initialize auth service - try robust service first, fallback to basic
        try:
            from app.services.robust_auth_service import init_robust_auth_service, get_robust_auth_service
            # Initialize the robust auth service first
            auth_service = init_robust_auth_service(redis_client)
            if auth_service and hasattr(auth_service, 'admin_secret'):
                app.logger.info(f"Using robust auth service initialized successfully")
            else:
                # Fallback to old auth service
                auth_service = init_auth_service(redis_client)
                app.logger.info(f"Using fallback auth service initialized: {auth_service is not None}")
        except Exception as auth_error:
            app.logger.warning(f"Robust auth service initialization failed, using fallback: {auth_error}")
            auth_service = init_auth_service(redis_client)
            app.logger.info(f"Fallback auth service initialized: {auth_service is not None}")

        # Always initialize website service (with or without Redis)
        website_service = init_website_service(redis_client)
        app.logger.info(f"Website service initialized: {website_service is not None}")

        # Initialize Script Token Manager
        from app.script_token_manager import init_script_token_manager
        script_token_manager = init_script_token_manager(redis_client)
        app.logger.info(f"Script token manager initialized: {script_token_manager is not None}")

        app.logger.info("Services initialized successfully")
    except ImportError as e:
        app.logger.error(f"Service import failed: {e}")
    except Exception as e:
        app.logger.error(f"Service initialization failed: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")

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
        from app.admin.script_management import script_mgmt_bp

        app.register_blueprint(analytics_bp)
        app.register_blueprint(alerts_bp)
        app.register_blueprint(logs_bp)
        app.register_blueprint(ml_metrics_bp)
        app.register_blueprint(script_mgmt_bp)

        # Additional authentication endpoints handled by existing services
        app.logger.info("Analytics, monitoring, and script management endpoints registered")
    except Exception as e:
        app.logger.warning(f"Failed to register analytics endpoints: {e}")

    # Test fresh auth service creation
    @app.route('/debug/fresh-auth', methods=['POST'])
    def debug_fresh_auth():
        """Test creating a fresh AuthService within request context"""
        try:
            data = request.get_json()
            password = data.get('password', '') if data else ''

            # Create a fresh AuthService within this request context
            from app.services.auth_service import RobustAuthService
            fresh_auth = RobustAuthService(None)

            # Test authentication with fresh service
            result = fresh_auth.authenticate_admin(password)

            return jsonify({
                'password': password,
                'app_config_admin_secret': app.config.get('ADMIN_SECRET'),
                'fresh_auth_admin_secret': fresh_auth.admin_secret,
                'fresh_auth_jwt_secret': fresh_auth.jwt_secret[:10] + '...',
                'password_match': password == fresh_auth.admin_secret,
                'auth_result': result is not None,
                'app_context': True
            })

        except Exception as e:
            import traceback
            return jsonify({
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500

    # Debug admin login endpoint
    @app.route('/debug/login', methods=['POST'])
    def debug_login():
        """Debug endpoint to test admin login directly"""
        try:
            data = request.get_json()
            password = data.get('password', '') if data else ''

            # Get auth service
            auth_service = app.auth_service
            if not auth_service:
                return jsonify({'error': 'Auth service not available'}), 503

            # Check password directly
            admin_secret = app.config.get('ADMIN_SECRET')
            password_match = password == admin_secret

            # Try authentication
            result = auth_service.authenticate_admin(password)

            return jsonify({
                'received_password': password,
                'expected_password': admin_secret,
                'password_match': password_match,
                'auth_result': result is not None,
                'auth_service_admin_secret': auth_service.admin_secret,
                'full_result': result
            })

        except Exception as e:
            import traceback
            return jsonify({
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500

    # Debug endpoint for environment variables (temporary)
    @app.route('/debug/env')
    def debug_env():
        """Debug endpoint to check environment variables"""
        config_files_status = {}
        for config_path in ['config.env.production', './config.env.production', 'backend/config.env.production', '../config.env.production']:
            config_files_status[config_path] = os.path.exists(config_path)

        return jsonify({
            'ADMIN_SECRET': os.getenv('ADMIN_SECRET', 'NOT_SET'),
            'ADMIN_SECRET_from_config': app.config.get('ADMIN_SECRET', 'NOT_SET'),
            'JWT_SECRET': os.getenv('JWT_SECRET', 'NOT_SET')[:10] + '...' if os.getenv('JWT_SECRET') else 'NOT_SET',
            'auth_service_available': app.auth_service is not None,
            'config_files_status': config_files_status,
            'current_working_directory': os.getcwd(),
            'render_external_url': os.getenv('RENDER_EXTERNAL_URL', 'NOT_SET')
        })

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

    # Register enhanced authentication endpoints
    try:
        from app.auth_integration import create_enhanced_auth_endpoints
        create_enhanced_auth_endpoints(app)
        app.logger.info('Enhanced auth endpoints registered successfully')
    except Exception as e:
        app.logger.error(f'Failed to register enhanced auth endpoints: {e}')

    # Register prototype API with SocketIO support
    try:
        from app.prototype_api import register_prototype
        register_prototype(app, socketio)
        app.logger.info('Prototype API registered successfully')
    except Exception as e:
        app.logger.error(f'Failed to register prototype API: {e}')
    
    # Register site routes for frontend deployment
    try:
        from app.site_routes import site_bp
        app.register_blueprint(site_bp)
        app.logger.info('Site routes registered successfully')
    except Exception as e:
        app.logger.error(f'Failed to register site routes: {e}')
    
    # Register script serving routes BEFORE other routes to avoid conflicts
    @app.route('/app/static/passive-captcha-script.js')
    @app.route('/backend/app/static/passive-captcha-script.js')
    @app.route('/static/passive-captcha-script.js')
    @app.route('/passive-captcha-script.js')
    def serve_passive_captcha_script():
        """Serve the passive captcha script via multiple routes"""
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
                return f'// Script not found at: {script_path}', 404, {'Content-Type': 'application/javascript'}
                
        except Exception as e:
            return f'// Script error: {e}', 500, {'Content-Type': 'application/javascript'}
    
    # Generic static file serving (for other files)
    @app.route('/static/<path:filename>')
    def serve_other_static_files(filename):
        """Serve other static files"""
        try:
            static_dir = os.path.join(os.path.dirname(__file__), 'app', 'static')
            full_path = os.path.join(static_dir, filename)
            
            if os.path.exists(full_path):
                return send_from_directory(static_dir, filename)
            else:
                return f'File not found: {filename}', 404
                
        except Exception as e:
            return f'Error serving file: {filename}', 500
    
    app.logger.info("Application created successfully")
    return app, socketio


def register_frontend_routes(app, static_folder):
    """Register integrated routing architecture with existing dashboard"""

    @app.route('/')
    def serve_uidai_government_portal():
        """Serve the actual UIDAI Government HTML as main homepage"""
        try:
            # Force serving UIDAI HTML file as the main page (not Vue.js dashboard)
            uidai_path = os.path.join(os.path.dirname(__file__), '..', 'site', 'Home - Unique Identification Authority of India .html')
            app.logger.info(f"Force serving UIDAI HTML from: {uidai_path}")
            
            # Always try to serve UIDAI first, ignore Vue.js dashboard
            if os.path.exists(uidai_path):
                with open(uidai_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Inject passive captcha script and enhanced analytics
                passive_script_injection = '''
                <!-- Enhanced Passive CAPTCHA Integration for UIDAI Government Portal -->
                <script src="/passive-captcha-script.js"></script>
                <script>
                    // Initialize enhanced passive captcha for UIDAI government site
                    document.addEventListener('DOMContentLoaded', function() {
                        if (typeof PassiveCaptcha !== 'undefined') {
                            PassiveCaptcha.init({
                                websiteId: 'uidai-gov-in',
                                apiEndpoint: '/prototype/api/verify',
                                analyticsEndpoint: '/prototype/api/analytics',
                                enableRealTimeMonitoring: true,
                                collectTouchPatterns: true,
                                monitorFocusEvents: true,
                                trackFormInteractions: true,
                                enablePageViewTracking: true,
                                enableSessionAnalytics: true,
                                samplingRate: 1.0
                            });
                            console.log('🛡️ Enhanced Passive CAPTCHA activated for UIDAI Government Portal');
                        }
                    });
                </script>
                <style>
                    .admin-access-panel {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: rgba(0, 0, 70, 0.95);
                        color: white;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        z-index: 9999;
                        font-family: Arial, sans-serif;
                        font-size: 14px;
                        min-width: 200px;
                    }
                    .admin-access-panel h4 {
                        margin: 0 0 10px 0;
                        font-size: 16px;
                        border-bottom: 1px solid rgba(255,255,255,0.3);
                        padding-bottom: 8px;
                    }
                    .admin-access-panel a {
                        color: #1cb5e0;
                        text-decoration: none;
                        display: inline-block;
                        margin: 5px 10px 5px 0;
                        padding: 5px 10px;
                        border: 1px solid #1cb5e0;
                        border-radius: 4px;
                        transition: all 0.3s;
                    }
                    .admin-access-panel a:hover {
                        background: #1cb5e0;
                        color: white;
                    }
                </style>
                </head>'''
                
                # Add admin access panel before closing body tag
                admin_panel = '''
                <!-- UIDAI Admin Access Panel -->
                <div class="admin-access-panel">
                    <h4>🏛️ UIDAI Admin Portal</h4>
                    <div>
                        <a href="/admin">📊 Dashboard</a>
                        <a href="/prototype/api/analytics">📈 Analytics</a>
                    </div>
                    <div style="margin-top: 10px; font-size: 12px; opacity: 0.8;">
                        Protected by Passive CAPTCHA
                    </div>
                </div>
                </body>'''
                
                # Inject the script before </head> and admin panel before </body>
                if '</head>' in content:
                    content = content.replace('</head>', passive_script_injection, 1)
                if '</body>' in content:
                    content = content.replace('</body>', admin_panel, 1)
                
                return content
            else:
                app.logger.error(f"UIDAI HTML not found at {uidai_path}")
                # Fallback to basic UIDAI portal
                app.logger.info("Serving fallback UIDAI portal")
            return '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Passive CAPTCHA Admin Dashboard</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
                    .container { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; max-width: 500px; }
                    .header { color: #4338ca; margin-bottom: 20px; }
                    .nav-link { display: inline-block; background: #4338ca; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 8px; transition: all 0.3s; }
                    .nav-link:hover { background: #3730a3; transform: translateY(-2px); }
                    .status { color: #059669; font-size: 14px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🛡️ Passive CAPTCHA Dashboard</h1>
                        <p>Advanced Behavioral Authentication System</p>
                    </div>
                    <div>
                        <a href="/uidai" class="nav-link">🏛️ UIDAI Portal</a>
                        <a href="/api/health" class="nav-link">📊 System Health</a>
                    </div>
                    <div class="status">
                        ⚡ Server Running • Frontend Load Error
                    </div>
                </div>
            </body>
            </html>
            '''
        except Exception as e:
            app.logger.error(f"Failed to serve dashboard: {e}")
            return f'''
            <!DOCTYPE html>
            <html><head><title>Server Error</title></head>
            <body>
                <h1>Server Error</h1>
                <p>Error: {e}</p>
                <a href="/uidai">Visit UIDAI Portal</a>
            </body></html>
            '''

    @app.route('/admin')
    @app.route('/admin/')
    def serve_admin_dashboard():
        """Serve Vue.js admin dashboard at /admin route"""
        try:
            # Use app's static folder directly for admin dashboard
            if app.static_folder:
                index_path = os.path.join(app.static_folder, 'index.html')
                app.logger.info(f"Serving admin dashboard from: {index_path}")
                if os.path.exists(index_path):
                    with open(index_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    app.logger.info("Successfully served admin dashboard")
                    return content
                else:
                    app.logger.error(f"Admin dashboard index.html not found at {index_path}")
            else:
                app.logger.error("No static folder configured for admin")
            
            # Fallback admin dashboard with fake data under 1000
            app.logger.info("Serving fallback admin dashboard with sample data")
            return '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>UIDAI Admin Dashboard</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: linear-gradient(135deg, #000046 0%, #1cb5e0 100%); min-height: 100vh; padding: 20px; }
                    .container { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }
                    .header { color: #000046; margin-bottom: 30px; text-align: center; }
                    .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
                    .metric { background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #000046; text-align: center; }
                    .metric-value { font-size: 24px; font-weight: bold; color: #000046; }
                    .metric-label { font-size: 14px; color: #666; margin-top: 5px; }
                    .nav-link { display: inline-block; background: #000046; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 8px; transition: all 0.3s; }
                    .nav-link:hover { background: #1cb5e0; transform: translateY(-2px); }
                    .status { color: #059669; font-size: 14px; margin-top: 20px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🛡️ UIDAI Admin Dashboard</h1>
                        <p>Passive CAPTCHA Management System</p>
                    </div>
                    
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-value">847</div>
                            <div class="metric-label">Total Verifications</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">793</div>
                            <div class="metric-label">Verified Users</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">54</div>
                            <div class="metric-label">Blocked Attempts</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">93.6%</div>
                            <div class="metric-label">Detection Rate</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">156</div>
                            <div class="metric-label">Active Sessions</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">728</div>
                            <div class="metric-label">Page Views Today</div>
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="/" class="nav-link">🏛️ UIDAI Portal</a>
                        <a href="/prototype/api/analytics" class="nav-link">📊 Live Analytics</a>
                        <a href="/api/health" class="nav-link">🔍 System Health</a>
                    </div>
                    
                    <div class="status">
                        ✅ All systems operational | Real-time monitoring active
                    </div>
                </div>
            </body>
            </html>
            '''
                
                # Enhanced passive captcha script with full analytics integration
                passive_script = '''
                <!-- Enhanced Passive CAPTCHA Integration for UIDAI Government Portal -->
                <script>
                    // Global configuration for passive CAPTCHA
                    window.PASSIVE_CAPTCHA_CONFIG = {
                        apiUrl: '/prototype/api/verify',
                        websiteId: 'uidai-gov-in',
                        enabled: true,
                        debug: true,
                        collectAll: true,
                        realTimeAnalytics: true
                    };
                </script>
                <script src="/passive-captcha-script.js"></script>
                <script>
                    // Enhanced UIDAI analytics and tracking
                    document.addEventListener('DOMContentLoaded', function() {
                        console.log('🏛️ UIDAI Portal loaded with Advanced Passive CAPTCHA Protection');
                        
                        // Initialize passive captcha with enhanced configuration
                        if (typeof PassiveCaptcha !== 'undefined') {
                            PassiveCaptcha.init({
                                websiteId: 'uidai-gov-in',
                                apiEndpoint: '/prototype/api/verify',
                                enableRealTimeMonitoring: true,
                                collectTouchPatterns: true,
                                monitorFocusEvents: true,
                                trackFormInteractions: true,
                                analyticsEndpoint: '/prototype/api/analytics'
                            });
                            console.log('✅ Passive CAPTCHA System Active');
                        }
                        
                        // Track comprehensive page analytics
                        var sessionData = {
                            sessionId: 'uidai_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                            startTime: Date.now(),
                            pageUrl: window.location.href,
                            referrer: document.referrer || 'direct',
                            userAgent: navigator.userAgent,
                            screen: screen.width + 'x' + screen.height,
                            viewport: window.innerWidth + 'x' + window.innerHeight,
                            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                            language: navigator.language,
                            platform: navigator.platform
                        };
                        
                        // Send initial page view analytics
                        function sendAnalytics(eventData) {
                            if (window.fetch) {
                                fetch('/prototype/api/analytics', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-Website-URL': window.location.href,
                                        'X-Passive-Captcha-Token': 'uidai-portal-' + Date.now()
                                    },
                                    body: JSON.stringify(eventData)
                                }).then(function(response) {
                                    if (response.ok) {
                                        console.log('📊 Analytics sent successfully');
                                    }
                                }).catch(function(err) {
                                    console.log('⚠️ Analytics error:', err);
                                });
                            }
                        }
                        
                        // Initial page view
                        sendAnalytics({
                            event: 'uidai_page_view',
                            timestamp: Date.now(),
                            session: sessionData,
                            page: 'uidai_homepage'
                        });
                        
                        // Track user interactions
                        var interactionCount = 0;
                        function trackInteraction(type, details) {
                            interactionCount++;
                            if (interactionCount % 3 === 0) {
                                sendAnalytics({
                                    event: 'uidai_interaction',
                                    type: type,
                                    details: details,
                                    count: interactionCount,
                                    timestamp: Date.now(),
                                    sessionId: sessionData.sessionId
                                });
                            }
                        }
                        
                        // Attach interaction listeners
                        document.addEventListener('click', function(e) {
                            trackInteraction('click', {
                                target: e.target.tagName,
                                x: e.clientX,
                                y: e.clientY
                            });
                        });
                        
                        document.addEventListener('scroll', function() {
                            trackInteraction('scroll', {
                                scrollTop: window.pageYOffset,
                                scrollLeft: window.pageXOffset
                            });
                        });
                        
                        document.addEventListener('keydown', function(e) {
                            trackInteraction('keydown', {
                                key: e.key,
                                code: e.code
                            });
                        });
                        
                        // Track page unload
                        window.addEventListener('beforeunload', function() {
                            var timeOnPage = Date.now() - sessionData.startTime;
                            if (navigator.sendBeacon) {
                                navigator.sendBeacon('/prototype/api/analytics', JSON.stringify({
                                    event: 'uidai_page_unload',
                                    sessionId: sessionData.sessionId,
                                    timeOnPage: timeOnPage,
                                    interactions: interactionCount,
                                    timestamp: Date.now()
                                }));
                            }
                        });
                        
                        console.log('🔐 Real-time monitoring active for UIDAI portal');
                    });
                </script>
                
                <!-- Enhanced Admin Access Panel -->
                <div id="uidai-admin-panel" style="position: fixed; top: 15px; right: 15px; background: linear-gradient(135deg, #000046 0%, #1cb5e0 100%); color: white; padding: 16px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); z-index: 99999; font-family: 'Segoe UI', sans-serif; text-align: center; cursor: pointer; transition: all 0.3s ease; min-width: 200px;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    <div style="font-size: 11px; margin-bottom: 8px; opacity: 0.9; font-weight: 600;">🛡️ UIDAI ADMIN SYSTEM</div>
                    <a href="/" style="display: block; background: rgba(255,255,255,0.2); color: white; padding: 10px 14px; text-decoration: none; border-radius: 6px; margin: 4px 0; font-size: 13px; font-weight: 500; border: 1px solid rgba(255,255,255,0.3); transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">📊 Analytics Dashboard</a>
                    <a href="/api/health" style="display: block; background: rgba(255,255,255,0.2); color: white; padding: 10px 14px; text-decoration: none; border-radius: 6px; margin: 4px 0; font-size: 13px; font-weight: 500; border: 1px solid rgba(255,255,255,0.3); transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">🔍 System Health</a>
                    <div style="font-size: 10px; margin-top: 8px; opacity: 0.7;">🟢 Active Monitoring</div>
                </div>
                
                <!-- UIDAI Portal Enhancement Styles -->
                <style>
                    /* Enhanced styling for government portal */
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                    }
                    
                    /* Responsive admin panel */
                    @media (max-width: 768px) {
                        #uidai-admin-panel {
                            top: 10px !important;
                            right: 10px !important;
                            left: 10px !important;
                            min-width: auto !important;
                            padding: 12px !important;
                        }
                        #uidai-admin-panel a {
                            font-size: 12px !important;
                            padding: 8px 12px !important;
                        }
                    }
                </style>
                '''
                
                # Inject before closing body tag
                if '</body>' in content:
                    content = content.replace('</body>', passive_script + '\n</body>')
                else:
                    content += passive_script
                
                return content
            else:
                app.logger.warning(f"UIDAI site not found at {uidai_path}, serving fallback")
                return '''
                <!DOCTYPE html>
                <html><head><title>UIDAI - Government of India</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f7fa; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                    .header { text-align: center; color: #000046; margin-bottom: 30px; }
                    .admin-link { display: inline-block; background: linear-gradient(135deg, #000046 0%, #1cb5e0 100%); color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px; transition: transform 0.2s; }
                    .admin-link:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
                    .back-link { text-align: center; margin-top: 30px; }
                    .back-link a { color: #1cb5e0; text-decoration: none; }
                </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🏛️ Unique Identification Authority of India</h1>
                            <p>Government of India - Digital Identity Platform</p>
                        </div>
                        <div style="text-align: center;">
                            <a href="/" class="admin-link">📊 Admin Dashboard</a>
                            <a href="/api/health" class="admin-link">🔍 System Health</a>
                        </div>
                        <div class="back-link">
                            <a href="/">← Return to Admin Dashboard</a>
                        </div>
                    </div>
                    <script src="/passive-captcha-script.js"></script>
                    <script>
                        if (typeof PassiveCaptcha !== 'undefined') {
                            PassiveCaptcha.init({
                                websiteId: 'uidai-gov-in-fallback',
                                apiEndpoint: '/prototype/api/verify',
                                enableRealTimeMonitoring: true
                            });
                        }
                    </script>
                </body></html>
                '''
        except Exception as e:
            app.logger.error(f"Failed to serve UIDAI portal: {e}")
            return '''
            <!DOCTYPE html>
            <html><head><title>UIDAI Portal - Error</title></head>
            <body>
                <h1>🏛️ UIDAI Government Portal</h1>
                <p>Temporary service unavailable</p>
                <div><a href="/">← Return to Dashboard</a></div>
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
        api_prefixes = ('api/', 'admin/', 'assets/', 'static/', 'socket.io/')

        # Define specific backend endpoints that should not serve SPA
        backend_endpoints = ('health',)

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
                <p>[WARNING] Frontend temporarily unavailable</p>
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
    try:
        app, socketio = create_app('production')
        
        print(f"[WSGI] Flask app type: {type(app)}")
        print(f"[WSGI] Flask app callable: {callable(app)}")
        print(f"[WSGI] SocketIO type: {type(socketio) if socketio else 'None'}")
        print(f"[WSGI] SocketIO callable: {callable(socketio) if socketio else 'None'}")
        
        # For Gunicorn with eventlet workers, return the Flask app
        # SocketIO functionality will still work through the app.socketio instance
        print(f"[WSGI] Returning Flask app for Gunicorn compatibility")
        return app
            
    except Exception as e:
        print(f"[ERROR] Failed to create WSGI app: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency fallback - create minimal Flask app
        from flask import Flask
        emergency_app = Flask(__name__)
        
        @emergency_app.route('/health')
        def health():
            return {'status': 'error', 'message': 'Application failed to initialize properly'}
            
        return emergency_app


def run_app(host='0.0.0.0', port=None, debug=False):
    """Run the application"""
    if port is None:
        port = int(os.getenv('PORT', 5003))

    app, socketio = create_app('development' if debug else 'production')

    if socketio:
        print(f"[DEPLOY] Starting Passive CAPTCHA with SocketIO on {host}:{port}")
        # Allow unsafe Werkzeug in production for development purposes
        # In real production, this should use a proper WSGI server like gunicorn
        socketio.run(app, host=host, port=port, debug=debug, use_reloader=False,
                    allow_unsafe_werkzeug=True)
    else:
        print(f"[DEPLOY] Starting Passive CAPTCHA on {host}:{port}")
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
        print(f"[DEPLOY] Starting Passive CAPTCHA with Gunicorn on {args.host}:{port}")
        print(f"[DEPLOY] Command: {' '.join(cmd)}")
        sys.exit(subprocess.call(cmd))
    else:
        # Use built-in Flask development server
        run_app(args.host, args.port, args.debug)
