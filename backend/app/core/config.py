"""
Comprehensive Configuration Management
Environment-based configuration with validation
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = -1


@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str
    decode_responses: bool = True
    health_check_interval: int = 30


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    jwt_secret_key: str
    admin_secret: str
    admin_email: str
    session_timeout: int = 3600
    max_login_attempts: int = 5
    lockout_duration: int = 900


@dataclass
class MLConfig:
    """Machine Learning configuration"""
    model_path: str
    scaler_path: str
    confidence_threshold: float = 0.6
    model_reload_interval: int = 3600


@dataclass
class AppConfig:
    """Main application configuration"""
    environment: Environment
    debug: bool
    testing: bool
    database: DatabaseConfig
    security: SecurityConfig
    ml: MLConfig
    host: str = "0.0.0.0"
    port: int = 5003
    
    # Optional component configs
    redis: Optional[RedisConfig] = None
    
    # Application settings
    serve_frontend: bool = True
    enable_websocket: bool = True
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 1000
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 10
    
    # CORS
    allowed_origins: list = None
    
    @classmethod
    def from_environment(cls, env: str = None) -> 'AppConfig':
        """Create configuration from environment variables"""
        if env is None:
            env = os.getenv('FLASK_ENV', 'production')
        
        environment = Environment(env)
        
        # Database configuration
        db_url = os.getenv('DATABASE_URL', 'sqlite:///passive_captcha_production.db')
        database = DatabaseConfig(url=db_url)
        
        # Redis configuration (optional)
        redis_url = os.getenv('REDIS_URL')
        redis_config = RedisConfig(url=redis_url) if redis_url else None
        
        # Security configuration
        security = SecurityConfig(
            secret_key=os.getenv('SECRET_KEY', 'production-secret-key-16chars'),
            jwt_secret_key=os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-16chars'),
            admin_secret=os.getenv('ADMIN_SECRET', 'SecureAdmin2024'),
            admin_email=os.getenv('ADMIN_EMAIL', 'admin@passive-captcha.com'),
            session_timeout=int(os.getenv('SESSION_TIMEOUT', '3600')),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            lockout_duration=int(os.getenv('LOCKOUT_DURATION', '900'))
        )
        
        # ML configuration
        ml = MLConfig(
            model_path=os.getenv('MODEL_PATH', 'models/passive_captcha_rf.pkl'),
            scaler_path=os.getenv('SCALER_PATH', 'models/passive_captcha_rf_scaler.pkl'),
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.6'))
        )
        
        # CORS origins
        origins_str = os.getenv('ALLOWED_ORIGINS', '')
        allowed_origins = origins_str.split(',') if origins_str and origins_str != '*' else ["*"]
        
        return cls(
            environment=environment,
            debug=environment == Environment.DEVELOPMENT,
            testing=environment == Environment.TESTING,
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5003')),
            database=database,
            redis=redis_config,
            security=security,
            ml=ml,
            serve_frontend=os.getenv('SERVE_FRONTEND', 'true').lower() == 'true',
            enable_websocket=os.getenv('ENABLE_WEBSOCKET', 'true').lower() == 'true',
            enable_rate_limiting=os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true',
            rate_limit_requests=int(os.getenv('RATE_LIMIT_REQUESTS', '1000')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', 'logs/app.log'),
            allowed_origins=allowed_origins
        )
    
    def to_flask_config(self) -> Dict[str, Any]:
        """Convert to Flask configuration dictionary"""
        return {
            'DEBUG': self.debug,
            'TESTING': self.testing,
            'SECRET_KEY': self.security.secret_key,
            'JWT_SECRET_KEY': self.security.jwt_secret_key,
            'ADMIN_SECRET': self.security.admin_secret,
            'ADMIN_EMAIL': self.security.admin_email,
            'DATABASE_URL': self.database.url,
            'REDIS_URL': self.redis.url if self.redis else None,
            'MODEL_PATH': self.ml.model_path,
            'SCALER_PATH': self.ml.scaler_path,
            'CONFIDENCE_THRESHOLD': self.ml.confidence_threshold,
            'RATE_LIMIT_REQUESTS': self.rate_limit_requests,
            'LOG_LEVEL': self.log_level,
            'LOG_FILE': self.log_file,
            'LOG_MAX_SIZE': self.log_max_size,
            'LOG_BACKUP_COUNT': self.log_backup_count,
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': True
        }
    
    def validate(self) -> list:
        """Validate configuration and return any errors"""
        errors = []
        
        # Check required files exist
        if not os.path.exists(self.ml.model_path):
            errors.append(f"ML model not found: {self.ml.model_path}")
        
        if not os.path.exists(self.ml.scaler_path):
            errors.append(f"ML scaler not found: {self.ml.scaler_path}")
        
        # Validate security settings
        if len(self.security.secret_key) < 16:
            errors.append("SECRET_KEY should be at least 16 characters long")
        
        if len(self.security.jwt_secret_key) < 16:
            errors.append("JWT_SECRET_KEY should be at least 16 characters long")
        
        # Validate port
        if not (1 <= self.port <= 65535):
            errors.append(f"Invalid port number: {self.port}")
        
        return errors


def get_config(env: str = None) -> AppConfig:
    """Get application configuration"""
    return AppConfig.from_environment(env)