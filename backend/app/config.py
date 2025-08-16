# -*- coding: utf-8 -*-
"""
Application Configuration Management
Centralized configuration for the passive CAPTCHA system
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Config:
    """Base configuration class"""
    
    # Security Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'admin123')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@passive-captcha.com')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or os.getenv('JWT_SECRET') or ADMIN_SECRET
    JWT_ALGORITHM = 'HS256'
    
    # Session Configuration
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '86400'))  # 24 hours
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    LOCKOUT_DURATION = int(os.getenv('LOCKOUT_DURATION', '900'))  # 15 minutes
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///passive_captcha.db')
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    PORT = int(os.getenv('PORT', '5003'))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', f'http://localhost:{PORT}')
    
    # ML Model Settings
    ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'app/ml/models/')
    ML_CONFIDENCE_THRESHOLD = float(os.getenv('ML_CONFIDENCE_THRESHOLD', '0.8'))
    
    # Security Thresholds
    AUTOMATION_THRESHOLD = float(os.getenv('AUTOMATION_THRESHOLD', '0.5'))
    MIN_INTERACTION_TIME = int(os.getenv('MIN_INTERACTION_TIME', '3000'))  # milliseconds
    
    # Static Files
    STATIC_FOLDER = os.getenv('STATIC_FOLDER', 'app/static')
    FRONTEND_BUILD_PATH = os.getenv('FRONTEND_BUILD_PATH', '../frontend/dist')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Production vs Development
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT.lower() == 'development'
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'url': cls.DATABASE_URL,
            'echo': cls.DEBUG,
            'pool_pre_ping': True,
            'pool_recycle': 300
        }
    
    @classmethod
    def get_redis_config(cls) -> Optional[Dict[str, Any]]:
        """Get Redis configuration if enabled"""
        if not cls.REDIS_ENABLED:
            return None
        
        return {
            'url': cls.REDIS_URL,
            'decode_responses': True,
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
            'retry_on_timeout': True
        }
    
    @classmethod
    def get_security_config(cls) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'session_timeout': cls.SESSION_TIMEOUT,
            'max_login_attempts': cls.MAX_LOGIN_ATTEMPTS,
            'lockout_duration': cls.LOCKOUT_DURATION,
            'jwt_secret': cls.JWT_SECRET_KEY,
            'jwt_algorithm': cls.JWT_ALGORITHM,
            'admin_secret': cls.ADMIN_SECRET,
            'admin_email': cls.ADMIN_EMAIL,
            'ml_confidence_threshold': cls.ML_CONFIDENCE_THRESHOLD,
            'automation_threshold': cls.AUTOMATION_THRESHOLD,
            'min_interaction_time': cls.MIN_INTERACTION_TIME
        }
    
    @classmethod
    def setup_logging(cls):
        """Setup application logging"""
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=cls.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log') if cls.is_production() else logging.NullHandler()
            ]
        )
        
        # Suppress noisy third-party loggers in production
        if cls.is_production():
            logging.getLogger('werkzeug').setLevel(logging.WARNING)
            logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate critical configuration settings"""
        errors = []
        
        # Check required settings
        if cls.is_production():
            if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
                errors.append("SECRET_KEY must be changed in production")
            
            if cls.ADMIN_SECRET == 'admin123':
                errors.append("ADMIN_SECRET should be changed in production")
        
        # Check numeric settings
        try:
            if cls.PORT < 1 or cls.PORT > 65535:
                errors.append(f"Invalid PORT: {cls.PORT}")
        except (ValueError, TypeError):
            errors.append("PORT must be a valid integer")
        
        try:
            if cls.SESSION_TIMEOUT < 300:  # 5 minutes minimum
                errors.append("SESSION_TIMEOUT should be at least 300 seconds")
        except (ValueError, TypeError):
            errors.append("SESSION_TIMEOUT must be a valid integer")
        
        # Log validation results
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        logger.info("Configuration validation passed")
        return True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENVIRONMENT = 'development'
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENVIRONMENT = 'production'
    LOG_LEVEL = 'INFO'
    
    # Stricter security in production
    ML_CONFIDENCE_THRESHOLD = 0.85
    AUTOMATION_THRESHOLD = 0.4
    MIN_INTERACTION_TIME = 5000  # 5 seconds


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    ENVIRONMENT = 'testing'
    DATABASE_URL = 'sqlite:///:memory:'
    REDIS_ENABLED = False
    LOG_LEVEL = 'WARNING'


def get_config_class():
    """Get configuration class based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(env, DevelopmentConfig)


def get_config() -> Config:
    """Get current configuration instance"""
    config_class = get_config_class()
    return config_class()