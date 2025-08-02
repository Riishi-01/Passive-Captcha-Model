"""
Production-Grade Passive CAPTCHA Application
Integrates all components: ML endpoints, WebSocket, logs pipeline, caching
"""

import os
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Load production environment if available
if os.path.exists('config.env.production'):
    load_dotenv('config.env.production', override=True)


def create_production_app(config_name='production'):
    """
    Production application factory with all integrated components
    """
    # Configure Flask app to serve static frontend files
    # Get the absolute path to the frontend dist folder
    backend_dir = os.path.dirname(os.path.dirname(__file__))  # app/ parent directory
    project_root = os.path.dirname(backend_dir)  # backend/ parent directory  
    static_folder = os.path.join(project_root, 'frontend', 'dist')
    
    print(f"Backend dir: {backend_dir}")
    print(f"Project root: {project_root}")
    print(f"Static folder: {static_folder}")
    print(f"Static folder exists: {os.path.exists(static_folder)}")
    
    # Additional path checking for Render environment
    if not os.path.exists(static_folder):
        # Try alternative paths for Render deployment
        alternative_paths = [
            os.path.join(backend_dir, '..', 'frontend', 'dist'),
            os.path.join(os.getcwd(), 'frontend', 'dist'),
            os.path.join(os.path.dirname(os.getcwd()), 'frontend', 'dist'),
            '/opt/render/project/src/frontend/dist'
        ]
        
        for alt_path in alternative_paths:
            abs_alt_path = os.path.abspath(alt_path)
            print(f"Checking alternative path: {abs_alt_path}")
            if os.path.exists(abs_alt_path):
                static_folder = abs_alt_path
                print(f"Found frontend at alternative path: {static_folder}")
                break
        else:
            static_folder = None
            print("Static folder not found in any location, serving without frontend")
    
    # Log static folder contents if found
    if static_folder and os.path.exists(static_folder):
        try:
            files = os.listdir(static_folder)
            print(f"Static folder contains {len(files)} files: {files[:5]}{'...' if len(files) > 5 else ''}")
        except Exception as e:
            print(f"Could not list static folder contents: {e}")
    
    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    
    # Production Configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'passive-captcha-production-secret'),
        'MODEL_PATH': os.getenv('MODEL_PATH', 'models/passive_captcha_rf.pkl'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///passive_captcha_production.db'),
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'CONFIDENCE_THRESHOLD': float(os.getenv('CONFIDENCE_THRESHOLD', '0.6')),
        'ADMIN_SECRET': os.getenv('ADMIN_SECRET', 'Admin123'),
        'RATE_LIMIT_REQUESTS': int(os.getenv('RATE_LIMIT_REQUESTS', '1000')),
        'API_BASE_URL': os.getenv('API_BASE_URL', 'http://localhost:5003'),
        'WEBSOCKET_URL': os.getenv('WEBSOCKET_URL', 'ws://localhost:5003'),
        'DEBUG': config_name == 'development',
        'TESTING': False,
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
    
    # CORS configuration for production
    default_origins = 'http://localhost:3000,https://passive-captcha.onrender.com,http://frontend:80,http://localhost:5003'
    allowed_origins = os.getenv('ALLOWED_ORIGINS', default_origins)
    cors_origins = allowed_origins.split(',') if allowed_origins != '*' else "*"
    
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
    
    # Initialize Redis client
    try:
        redis_client = redis.Redis.from_url(app.config['REDIS_URL'], decode_responses=True)
        redis_client.ping()  # Test connection
        app.logger.info("Redis connection established successfully")
    except Exception as e:
        app.logger.warning(f"Redis unavailable, using in-memory fallback: {e}")
        redis_client = None
    
    # Initialize SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins=cors_origins,
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        logger=False,  # Disable SocketIO logging to avoid conflicts
        engineio_logger=False
    )
    
    # Rate limiting with Redis backend
    if redis_client:
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{app.config['RATE_LIMIT_REQUESTS']} per hour"],
            storage_uri=app.config['REDIS_URL']
        )
    else:
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{app.config['RATE_LIMIT_REQUESTS']} per hour"]
        )
    
    limiter.init_app(app)
    
    # Initialize database
    from app.database import init_db
    with app.app_context():
        try:
            init_db()
            app.logger.info("Database initialized successfully")
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            raise
    
    # Initialize ML model
    from app.ml import load_model
    with app.app_context():
        try:
            load_model()
            app.logger.info("ML model loaded successfully")
        except Exception as e:
            app.logger.error(f"ML model loading failed: {e}")
            # Don't raise - app can still function without ML model
    
    # Initialize logs pipeline
    from app.logs_pipeline import init_logs_pipeline
    logs_pipeline = None
    if redis_client:
        try:
            logs_pipeline = init_logs_pipeline(app, socketio, redis_client)
            app.logger.info("Logs pipeline initialized successfully")
        except Exception as e:
            app.logger.error(f"Logs pipeline initialization failed: {e}")
    
    # Initialize WebSocket server
    from app.websocket_server import init_websocket_server
    websocket_manager = None
    if redis_client:
        try:
            websocket_manager = init_websocket_server(app, socketio, redis_client)
            app.logger.info("WebSocket server initialized successfully")
        except Exception as e:
            app.logger.error(f"WebSocket server initialization failed: {e}")
    
    # Initialize script token manager
    from app.script_token_manager import init_script_token_manager
    script_token_manager = None
    if redis_client:
        try:
            script_token_manager = init_script_token_manager(redis_client)
            app.logger.info("Script token manager initialized successfully")
        except Exception as e:
            app.logger.error(f"Script token manager initialization failed: {e}")

    # Initialize centralized services (always)
    from app.services import init_auth_service, init_website_service
    auth_service = None
    website_service = None
    
    try:
        # Always initialize auth service (works with or without Redis)
        auth_service = init_auth_service(redis_client)
        if redis_client:
            website_service = init_website_service(redis_client)
            app.logger.info("Centralized services initialized successfully with Redis")
        else:
            app.logger.info("Authentication service initialized in standalone mode")
    except Exception as e:
        app.logger.error(f"Service initialization failed: {e}")

    # Initialize endpoint modules with Redis client (legacy support)
    from app.admin.ml_endpoints import init_ml_endpoints
    from app.admin.dashboard_endpoints import init_dashboard_endpoints
    from app.admin.config_endpoints import init_config_endpoints
    from app.admin.script_management import init_script_management
    
    if redis_client:
        init_ml_endpoints(redis_client)
        init_dashboard_endpoints(redis_client)
        init_config_endpoints(redis_client)
        init_script_management(redis_client)
        app.logger.info("All endpoint modules initialized with Redis caching")
    
    # Register blueprints (avoid duplicates)
    from app.api import api_bp
    from app.api.admin_endpoints import admin_bp as admin_api_bp
    from app.api.script_endpoints import script_bp
    
    # Register main API endpoints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(script_bp)
    app.logger.info("Core API endpoints registered")
    
    # Register modern admin API endpoints (primary)
    app.register_blueprint(admin_api_bp, url_prefix='/admin')
    app.logger.info("Admin API endpoints registered")
    
    # Register supporting analytics endpoints (non-conflicting)
    from app.admin.analytics_endpoints import analytics_bp
    from app.admin.alerts_endpoints import alerts_bp
    from app.admin.logs_endpoints import logs_bp
    from app.admin.ml_metrics_endpoints import ml_metrics_bp
    app.register_blueprint(analytics_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(ml_metrics_bp)
    app.logger.info("Analytics and monitoring endpoints registered")
    
    # Skip legacy endpoints that conflict with modern admin API
    # (ml_bp, dashboard_bp, config_bp, script_mgmt_bp have duplicate routes with admin_api_bp)
    app.logger.info("Skipped legacy conflicting blueprints to avoid route conflicts")
    
    # Register temporary endpoint fixes for testing
    try:
        from app.temp_endpoints import missing_bp
        app.register_blueprint(missing_bp)
        app.logger.info("Temporary endpoint fixes registered")
    except ImportError:
        app.logger.debug("No temporary endpoint fixes found")
    
    app.logger.info("All blueprints registered successfully")
    
    # Production health check endpoint
    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint"""
        try:
            from app.ml import model_loaded
            import time
            
            # Check database
            db_status = 'healthy'
            try:
                from app.database import get_db_session
                session = get_db_session()
                session.execute('SELECT 1')
                session.close()
            except:
                db_status = 'error'
            
            # Check Redis
            redis_status = 'healthy' if redis_client else 'disabled'
            if redis_client:
                try:
                    redis_client.ping()
                except:
                    redis_status = 'error'
            
            # Check WebSocket
            ws_status = 'healthy' if websocket_manager else 'disabled'
            if websocket_manager:
                try:
                    stats = websocket_manager.get_connection_stats()
                    ws_connections = stats['total_connections']
                except:
                    ws_status = 'error'
                    ws_connections = 0
            else:
                ws_connections = 0
            
            # Check logs pipeline
            logs_status = 'healthy' if logs_pipeline else 'disabled'
            
            # Overall status
            critical_components = [db_status]
            if any(status == 'error' for status in critical_components):
                overall_status = 'unhealthy'
            elif any(status == 'error' for status in [redis_status, ws_status, logs_status]):
                overall_status = 'degraded'
            else:
                overall_status = 'healthy'
            
            return {
                'status': overall_status,
                'timestamp': int(time.time()),
                'version': '2.0.0',
                'components': {
                    'database': db_status,
                    'ml_model': 'healthy' if model_loaded else 'error',
                    'redis': redis_status,
                    'websocket': ws_status,
                    'logs_pipeline': logs_status
                },
                'metrics': {
                    'websocket_connections': ws_connections,
                    'uptime_seconds': int(time.time() - app.start_time) if hasattr(app, 'start_time') else 0
                }
            }
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    # Frontend serving routes (must be registered last to avoid conflicts)
    def register_frontend_routes():
        @app.route('/')
        def serve_root():
            """Serve Vue.js frontend root"""
            if static_folder and os.path.exists(static_folder):
                try:
                    return app.send_static_file('index.html')
                except Exception as e:
                    app.logger.error(f"Failed to serve index.html: {e}")
                    # Fallback to reading file directly
                    try:
                        index_path = os.path.join(static_folder, 'index.html')
                        if os.path.exists(index_path):
                            with open(index_path, 'r', encoding='utf-8') as f:
                                return f.read()
                    except Exception as e2:
                        app.logger.error(f"Failed to read index.html directly: {e2}")
            
            # Fallback HTML with better styling
            return '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <title>Passive CAPTCHA Admin</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .api-link { display: inline-block; margin: 10px; padding: 10px 20px; background: #007cba; color: white; text-decoration: none; border-radius: 5px; }
                    .api-link:hover { background: #005a85; }
                    .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <h1>🔐 Passive CAPTCHA Admin Dashboard</h1>
                <div class="status">
                    <p><strong>✅ API Server Running</strong></p>
                    <p>Frontend build pending or failed. API endpoints are fully functional:</p>
                </div>
                <div>
                    <a href="/health" class="api-link">❤️ Health Check</a>
                    <a href="/admin/login" class="api-link">🔑 Admin Login API</a>
                    <a href="/admin/analytics" class="api-link">📊 Analytics API</a>
                </div>
                <h3>Quick Test:</h3>
                <pre>curl -X POST /admin/login -H "Content-Type: application/json" -d '{"password": "Admin123"}'</pre>
                <h3>Available Endpoints:</h3>
                <ul>
                    <li><a href="/health">System Health</a></li>
                    <li><a href="/admin/analytics/summary">Analytics Summary</a></li>
                    <li><a href="/admin/ml/metrics">ML Metrics</a></li>
                    <li><a href="/admin/websites">Websites</a></li>
                </ul>
            </body>
            </html>
            '''
        
        # Remove conflicting /login route - let Vue.js handle frontend routes
        # API login is handled by /admin/login endpoint
        
        @app.route('/<path:path>')
        def serve_static_files(path):
            """Serve static assets or fallback to index.html for SPA routing"""
            if static_folder and os.path.exists(static_folder):
                try:
                    file_path = os.path.join(static_folder, path)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        return app.send_static_file(path)
                    else:
                        # For Vue.js router - serve index.html for all routes
                        # But only for routes that look like frontend routes (not API endpoints)
                        if not path.startswith(('api', 'admin', 'health')):
                            try:
                                return app.send_static_file('index.html')
                            except Exception as e:
                                app.logger.error(f"Failed to serve index.html for SPA route {path}: {e}")
                                # Try reading file directly
                                index_path = os.path.join(static_folder, 'index.html')
                                if os.path.exists(index_path):
                                    with open(index_path, 'r', encoding='utf-8') as f:
                                        return f.read()
                        # Return 404 for API-like routes
                        return {'error': {'code': 'NOT_FOUND', 'message': f'Endpoint /{path} not found'}, 'success': False}, 404
                except Exception as e:
                    app.logger.error(f"Error serving static file {path}: {e}")
                    return {'error': {'code': 'SERVER_ERROR', 'message': 'Static file serving error'}, 'success': False}, 500
            else:
                # Return 404 for unknown routes when frontend not available
                return {'error': {'code': 'NOT_FOUND', 'message': f'Endpoint /{path} not found (frontend not available)'}, 'success': False}, 404
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Invalid request format or parameters'
            }
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Endpoint not found'
            }
        }), 404
    
    @app.errorhandler(422)
    def validation_error(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Request validation failed'
            }
        }), 422
    
    @app.errorhandler(429)
    def rate_limit_handler(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'RATE_LIMITED',
                'message': 'Too many requests. Please try again later.',
                'retry_after': getattr(error, 'retry_after', None)
            }
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred. Please try again later.'
            }
        }), 500
    
    # Handle JSON parsing errors
    @app.errorhandler(Exception)
    def handle_json_error(error):
        if 'JSON' in str(error) or 'json' in str(error).lower():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_JSON',
                    'message': 'Invalid JSON in request body'
                }
            }), 400
        # Re-raise if it's not a JSON error
        raise error
    
    # Set application start time for uptime calculation
    import time
    app.start_time = time.time()
    
    # Store references for access in other modules
    app.redis_client = redis_client
    app.socketio = socketio
    app.logs_pipeline = logs_pipeline
    app.websocket_manager = websocket_manager
    app.script_token_manager = script_token_manager
    app.auth_service = auth_service
    app.website_service = website_service
    
    # Register frontend routes (must be last to avoid conflicts)
    register_frontend_routes()
    
    app.logger.info("Production application created successfully")
    return app, socketio


def setup_logging(app):
    """Setup comprehensive logging for production"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set log level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    app.logger.setLevel(log_level)
    
    # Create file handler with rotation
    if not app.config['DEBUG']:
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_SIZE'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        
        file_handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to app logger
        app.logger.addHandler(file_handler)
        
        # Also set up root logger for other modules
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    app.logger.info("Logging configured successfully")


def run_production_server():
    """Run the production server with SocketIO"""
    app, socketio = create_production_app('production')
    
    port = int(os.getenv('PORT', 5003))
    host = os.getenv('HOST', '0.0.0.0')
    
    app.logger.info(f"Starting production server on {host}:{port}")
    
    # Run with SocketIO
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        log_output=False
    )


if __name__ == '__main__':
    run_production_server()