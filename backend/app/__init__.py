"""
Passive CAPTCHA Backend Application Factory
Initializes Flask app with ML model, database, and API endpoints
"""

import os
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_app(config_name='development'):
    """
    Application factory pattern for Flask app creation
    """
    app = Flask(__name__)
    
    # Configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'passive-captcha-secret-key'),
        'MODEL_PATH': os.getenv('MODEL_PATH', 'models/passive_captcha_rf.pkl'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///passive_captcha.db'),
        'CONFIDENCE_THRESHOLD': float(os.getenv('CONFIDENCE_THRESHOLD', '0.6')),
        'ADMIN_SECRET': os.getenv('ADMIN_SECRET', 'admin-secret-key'),
        'RATE_LIMIT_REQUESTS': int(os.getenv('RATE_LIMIT_REQUESTS', '100')),
        'DEBUG': config_name == 'development'
    })
    
    # CORS configuration - Allow Render.com domains
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
    if allowed_origins == '*':
        cors_origins = "*"
    else:
        cors_origins = allowed_origins.split(',')
    
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["POST", "GET", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        },
        r"/admin/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        },
        r"/health": {
            "origins": cors_origins,
            "methods": ["GET"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{app.config['RATE_LIMIT_REQUESTS']} per hour"]
    )
    limiter.init_app(app)
    
    # Initialize database
    from app.database import init_db
    with app.app_context():
        init_db()
    
    # Initialize ML model
    from app.ml import load_model
    with app.app_context():
        load_model()
    
    # Register blueprints
    from app.api import api_bp
    from app.admin import admin_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            from app.ml import model_loaded
            return {
                'status': 'healthy',
                'timestamp': int(time.time()) if 'time' in globals() else 'unknown',
                'version': '1.0.0',
                'model_loaded': model_loaded
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 