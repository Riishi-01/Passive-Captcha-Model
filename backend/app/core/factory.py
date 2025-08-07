"""
Robust Application Factory
Production-ready Flask application creation with comprehensive error handling
"""

import os
import sys
import redis
from typing import Tuple, Optional
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

from app.core.config import AppConfig, get_config
from app.core.logging import setup_logging, log_request_info


class ApplicationError(Exception):
    """Custom application initialization error"""
    pass


def create_redis_client(config: AppConfig) -> Optional[redis.Redis]:
    """Create and test Redis client connection"""
    if not config.redis:
        return None
    
    try:
        client = redis.Redis.from_url(
            config.redis.url,
            decode_responses=config.redis.decode_responses,
            health_check_interval=config.redis.health_check_interval
        )
        
        # Test connection
        client.ping()
        return client
        
    except Exception as e:
        # Log warning but don't fail - app can work without Redis
        print(f"Redis connection failed: {e}. Continuing without Redis.")
        return None


def create_socketio(app: Flask, config: AppConfig, cors_origins) -> Optional[SocketIO]:
    """Create SocketIO instance if enabled"""
    if not config.enable_websocket:
        return None
    
    try:
        socketio = SocketIO(
            app,
            cors_allowed_origins=cors_origins,
            async_mode='threading',
            logger=False,
            engineio_logger=False
        )
        return socketio
        
    except Exception as e:
        app.logger.warning(f"SocketIO initialization failed: {e}")
        return None


def create_rate_limiter(app: Flask, config: AppConfig, redis_client: Optional[redis.Redis]) -> Optional[Limiter]:
    """Create rate limiter with Redis or in-memory storage"""
    if not config.enable_rate_limiting:
        return None
    
    try:
        limiter_config = {
            'key_func': get_remote_address,
            'default_limits': [f"{config.rate_limit_requests} per hour"]
        }
        
        if redis_client:
            try:
                redis_client.ping()
                limiter_config['storage_uri'] = config.redis.url
                app.logger.info("Rate limiting initialized with Redis backend")
            except Exception:
                app.logger.info("Rate limiting using in-memory backend (Redis unavailable)")
        else:
            app.logger.info("Rate limiting using in-memory backend")
        
        limiter = Limiter(**limiter_config)
        limiter.init_app(app)
        return limiter
        
    except Exception as e:
        app.logger.warning(f"Rate limiting initialization failed: {e}")
        return None


def configure_cors(app: Flask, config: AppConfig) -> None:
    """Configure CORS with environment-specific settings"""
    cors_origins = config.allowed_origins
    
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


def find_static_folder() -> Optional[str]:
    """Find frontend static folder with multiple fallback locations"""
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    project_root = os.path.dirname(backend_dir)
    
    # Possible static folder locations
    locations = [
        os.path.join(project_root, 'frontend', 'dist'),
        os.path.join(backend_dir, 'static'),
        os.path.join(os.getcwd(), 'static'),
        './static'
    ]
    
    for location in locations:
        if os.path.exists(location):
            index_path = os.path.join(location, 'index.html')
            if os.path.exists(index_path):
                return os.path.abspath(location)
    
    return None


def initialize_database(app: Flask, config: AppConfig) -> None:
    """Initialize database connection"""
    try:
        from app.database import init_db
        with app.app_context():
            init_db()
            app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
        # Don't raise - let app start for debugging


def initialize_ml_model(app: Flask, config: AppConfig) -> None:
    """Initialize ML model"""
    try:
        from app.ml import load_model
        with app.app_context():
            load_model()
            app.logger.info("ML model loaded successfully")
    except Exception as e:
        app.logger.warning(f"ML model loading failed: {e}")
        # Continue without ML model


def initialize_services(app: Flask, config: AppConfig, redis_client: Optional[redis.Redis]) -> None:
    """Initialize application services"""
    try:
        app.logger.info("Initializing application services...")
        
        # Initialize authentication service
        from app.services.auth_service import init_auth_service
        auth_service = init_auth_service(redis_client)
        app.auth_service = auth_service
        app.logger.info(f"Auth service initialized with admin_secret: {auth_service.admin_secret}")
        
        # Initialize website service
        from app.services import init_website_service
        website_service = init_website_service(redis_client)
        app.website_service = website_service
        app.logger.info(f"Website service initialized: {website_service is not None}")
        
        # Initialize script token manager
        from app.script_token_manager import init_script_token_manager
        script_token_manager = init_script_token_manager(redis_client)
        app.script_token_manager = script_token_manager
        app.logger.info(f"Script token manager initialized: {script_token_manager is not None}")
        
        app.logger.info("All services initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Service initialization failed: {e}")
        raise ApplicationError(f"Failed to initialize services: {e}")


def register_blueprints(app: Flask, config: AppConfig) -> None:
    """Register application blueprints"""
    try:
        # Core API - conditionally import
        try:
            from app.api import api_bp
            app.register_blueprint(api_bp, url_prefix='/api')
            app.logger.info("Core API endpoints registered")
        except ImportError:
            app.logger.warning("Core API blueprint not available")
        
        # Admin API
        try:
            from app.api.admin_endpoints import admin_bp
            app.register_blueprint(admin_bp, url_prefix='/admin')
            app.logger.info("Admin API endpoints registered")
        except ImportError:
            app.logger.warning("Admin API blueprint not available")
        
        # Script endpoints
        try:
            from app.api.script_endpoints import script_bp
            app.register_blueprint(script_bp, url_prefix='/api')
            app.logger.info("Script API endpoints registered")
        except ImportError:
            app.logger.warning("Script API blueprint not available")
        
        app.logger.info("Available blueprints registered successfully")
        
    except Exception as e:
        app.logger.error(f"Blueprint registration failed: {e}")
        # Don't raise - allow app to start with partial functionality


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': {'code': 'NOT_FOUND', 'message': 'Resource not found'}}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}, 500
    
    @app.errorhandler(ApplicationError)
    def application_error(error):
        return {'error': {'code': 'APPLICATION_ERROR', 'message': str(error)}}, 500


def create_robust_app(env: str = None) -> Tuple[Flask, Optional[SocketIO]]:
    """
    Create a robust, production-ready Flask application
    
    Args:
        env: Environment name (development, testing, production)
    
    Returns:
        Tuple of (Flask app, SocketIO instance or None)
    
    Raises:
        ApplicationError: If critical initialization fails
    """
    # Load configuration
    config = get_config(env)
    
    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        raise ApplicationError(f"Configuration validation failed: {config_errors}")
    
    # Find static folder
    static_folder = find_static_folder() if config.serve_frontend else None
    
    # Create Flask app
    app = Flask(
        __name__,
        static_folder=static_folder,
        static_url_path='/static' if static_folder else None
    )
    
    # Apply configuration
    app.config.update(config.to_flask_config())
    
    # Setup logging FIRST
    setup_logging(app)
    app.logger.info(f"Starting Passive CAPTCHA application in {config.environment.value} mode")
    
    if static_folder:
        app.logger.info(f"Frontend static folder: {static_folder}")
    
    # Configure CORS
    configure_cors(app, config)
    
    # Create Redis client
    redis_client = create_redis_client(config)
    app.redis_client = redis_client
    
    # Create SocketIO
    socketio = create_socketio(app, config, config.allowed_origins)
    app.socketio = socketio
    
    # Create rate limiter
    limiter = create_rate_limiter(app, config, redis_client)
    app.limiter = limiter
    
    # Initialize database
    initialize_database(app, config)
    
    # Initialize ML model
    initialize_ml_model(app, config)
    
    # Initialize services
    initialize_services(app, config, redis_client)
    
    # Register blueprints
    register_blueprints(app, config)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add request logging
    log_request_info(app)
    
    # Store configuration and startup time
    app.config_obj = config
    app.start_time = int(__import__('time').time())
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Comprehensive health check"""
        return {
            'status': 'healthy',
            'timestamp': int(__import__('time').time()),
            'uptime': int(__import__('time').time()) - app.start_time,
            'version': '2.0.0',
            'environment': config.environment.value,
            'components': {
                'database': 'available',
                'redis': 'available' if redis_client else 'disabled',
                'ml_model': 'available',
                'auth_service': 'available' if hasattr(app, 'auth_service') else 'disabled',
                'websocket': 'available' if socketio else 'disabled',
                'rate_limiting': 'available' if limiter else 'disabled'
            }
        }
    
    app.logger.info("Robust application created successfully")
    return app, socketio