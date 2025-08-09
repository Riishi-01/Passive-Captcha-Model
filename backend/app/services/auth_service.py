# -*- coding: utf-8 -*-
"""
Unified Authentication Service
Consolidates all authentication functionality into a single, working service
"""

import os
import jwt
import hashlib
import secrets
import time
import bcrypt
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
from flask import current_app, has_app_context, request
import logging

# Setup logging
logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class RateLimitError(Exception):
    """Rate limiting error"""
    pass


@dataclass
class AuthenticatedUser:
    """Authenticated user data structure"""
    id: str
    email: str
    name: str
    role: UserRole
    last_login: datetime
    login_count: int = 0
    failed_attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value,
            'last_login': self.last_login.isoformat(),
            'login_count': self.login_count,
            'failed_attempts': self.failed_attempts
        }


class AuthService:
    """Unified authentication service with comprehensive security"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.session_prefix = "session:"
        self.token_prefix = "token:"
        self.rate_limit_prefix = "rate_limit:"
        self.blocked_ip_prefix = "blocked_ip:"
        
        # Security settings
        self.session_ttl = 86400  # 24 hours
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.rate_limit_requests = 10  # requests per minute
        self.rate_limit_window = 60  # seconds
        
        # JWT configuration
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 
                                   os.getenv('JWT_SECRET', 
                                            self._generate_jwt_secret()))
        self.jwt_algorithm = 'HS256'
        
        # Admin credentials - CRITICAL: This fixes the missing admin_secret issue
        self.admin_secret = os.getenv('ADMIN_SECRET', 'Admin123')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'admin@passive-captcha.com')
        self.admin_password_hash = self._generate_default_admin_hash()
        
        logger.info("AuthService initialized successfully")
        
    def _generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(64)
    
    def _generate_default_admin_hash(self) -> str:
        """Generate default admin password hash"""
        try:
            # Use admin_secret as the password for consistency
            password = self.admin_secret
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate admin hash: {e}")
            return ""
    
    def _get_client_ip(self) -> str:
        """Get client IP address with proxy support"""
        if not request:
            return 'unknown'
            
        # Check for forwarded IP (for proxies/load balancers)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """Check if identifier is rate limited"""
        if not self.redis:
            return False
        
        try:
            key = f"{self.rate_limit_prefix}{identifier}"
            current_count = self.redis.get(key)
            
            if current_count is None:
                # First request in window
                self.redis.setex(key, self.rate_limit_window, 1)
                return False
            
            count = int(current_count)
            if count >= self.rate_limit_requests:
                return True
            
            # Increment counter
            self.redis.incr(key)
            return False
            
        except Exception:
            # Silently fail when Redis is not available
            return False
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        if not self.redis:
            return False
        
        try:
            blocked_key = f"{self.blocked_ip_prefix}{ip_address}"
            return self.redis.exists(blocked_key)
        except Exception:
            return False
    
    def _block_ip(self, ip_address: str, duration: int = None) -> None:
        """Block IP address for specified duration"""
        if not self.redis:
            return
        
        try:
            blocked_key = f"{self.blocked_ip_prefix}{ip_address}"
            block_duration = duration or self.lockout_duration
            self.redis.setex(blocked_key, block_duration, 1)
            
            if has_app_context():
                current_app.logger.warning(f"Blocked IP {ip_address} for {block_duration} seconds")
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"Failed to block IP: {e}")
    
    def _record_failed_attempt(self, ip_address: str) -> None:
        """Record failed login attempt"""
        if not self.redis:
            return
        
        try:
            attempts_key = f"failed_attempts:{ip_address}"
            current_attempts = self.redis.get(attempts_key)
            
            if current_attempts is None:
                attempts = 1
            else:
                attempts = int(current_attempts) + 1
            
            # Store with expiration
            self.redis.setex(attempts_key, self.lockout_duration, attempts)
            
            # Block IP if too many attempts
            if attempts >= self.max_login_attempts:
                self._block_ip(ip_address)
                
        except Exception:
            # Silently fail when Redis is not available
            pass
    
    def _validate_admin_credentials(self, email: str, password: str) -> bool:
        """Validate admin credentials with secure password checking"""
        # Check email first
        if email and email != self.admin_email:
            return False
        
        # Check against plain text admin_secret (primary method)
        if password == self.admin_secret:
            return True
        
        # Also check against hashed password if available
        try:
            if self.admin_password_hash:
                return bcrypt.checkpw(password.encode('utf-8'), 
                                    self.admin_password_hash.encode('utf-8'))
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"Password validation error: {e}")
        
        return False
    
    def authenticate_admin(self, password: str, email: str = None) -> Optional[Dict[str, Any]]:
        """
        Unified admin authentication method
        Supports both old (password only) and new (email+password) signatures
        """
        ip_address = self._get_client_ip()
        
        # Check if IP is blocked
        if self._is_ip_blocked(ip_address):
            raise AuthenticationError("IP address is temporarily blocked due to failed login attempts")
        
        # Check rate limiting
        if self._check_rate_limit(ip_address):
            raise RateLimitError("Too many requests. Please try again later")
        
        # Validate credentials
        if not password:
            self._record_failed_attempt(ip_address)
            raise AuthenticationError("Password is required")
        
        # If email is provided, validate both, otherwise just password
        if email:
            if not self._validate_admin_credentials(email, password):
                self._record_failed_attempt(ip_address)
                raise AuthenticationError("Invalid email or password")
            user_email = email
        else:
            # Backward compatibility: just password
            if password != self.admin_secret:
                self._record_failed_attempt(ip_address)
                raise AuthenticationError("Invalid password")
            user_email = self.admin_email
        
        # Create authenticated user
        user = AuthenticatedUser(
            id="admin",
            email=user_email,
            name="Administrator",
            role=UserRole.ADMIN,
            last_login=datetime.utcnow(),
            login_count=1
        )
        
        # Create session
        return self._create_secure_session(user, False, ip_address)
    
    def _create_secure_session(self, user: AuthenticatedUser, remember_me: bool, ip_address: str) -> Dict[str, Any]:
        """Create secure session with JWT token"""
        now = datetime.utcnow()
        session_id = secrets.token_urlsafe(32)
        
        # Set token expiration
        if remember_me:
            exp_time = now + timedelta(days=30)
            ttl = 30 * 24 * 3600
        else:
            # Extend default session to reduce near-immediate expiry issues
            exp_time = now + timedelta(seconds=max(self.session_ttl, 86400))
            ttl = max(self.session_ttl, 86400)
        
        # Create JWT token
        token_payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'session_id': session_id,
            'ip_address': ip_address,
            'iat': int(now.timestamp()),
            'exp': int(exp_time.timestamp())
        }
        
        try:
            token = jwt.encode(token_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"JWT encoding error: {e}")
            raise AuthenticationError("Failed to create authentication token")
        
        # Store session data
        session_data = {
            'user': user.to_dict(),
            'token': token,
            'created_at': now.isoformat(),
            'expires_at': exp_time.isoformat(),
            'ip_address': ip_address,
            'remember_me': remember_me
        }
        
        if self.redis:
            try:
                session_key = f"{self.session_prefix}{session_id}"
                self.redis.setex(session_key, ttl, json.dumps(session_data, default=str))
                
                # Store token mapping
                token_key = f"{self.token_prefix}{token}"
                self.redis.setex(token_key, ttl, session_id)
                
                if has_app_context():
                    current_app.logger.info(f"Session created for {user.email}")
            except Exception as e:
                if has_app_context():
                    current_app.logger.warning(f"Failed to store session in Redis: {e}")
        
        return {
            'token': token,
            'user': user.to_dict(),
            'expires_in': ttl,
            'timestamp': now.isoformat(),
            'session_id': session_id
        }
    
    def validate_token(self, token: str) -> Optional[AuthenticatedUser]:
        """
        Enhanced token validation with comprehensive checks
        """
        if not token:
            return None
        
        try:
            # If Redis is available, check session storage
            if self.redis:
                try:
                    token_key = f"{self.token_prefix}{token}"
                    session_id = self.redis.get(token_key)
                    
                    if not session_id:
                        return None
                    
                    # Handle bytes or str from Redis
                    if isinstance(session_id, (bytes, bytearray)):
                        session_id = session_id.decode()
                    session_key = f"{self.session_prefix}{session_id}"
                    session_data = self.redis.get(session_key)
                    
                    if not session_data:
                        return None
                    
                    if isinstance(session_data, (bytes, bytearray)):
                        session_data = session_data.decode()
                    session_info = json.loads(session_data)
                    user_data = session_info['user']
                    
                    return AuthenticatedUser(
                        id=user_data['id'],
                        email=user_data['email'],
                        name=user_data['name'],
                        role=UserRole(user_data['role']),
                        last_login=datetime.fromisoformat(user_data['last_login']),
                        login_count=user_data.get('login_count', 0),
                        failed_attempts=user_data.get('failed_attempts', 0)
                    )
                    
                except Exception as e:
                    if has_app_context():
                        current_app.logger.warning(f"Redis session validation failed: {e}")
            
            # Fallback to JWT validation
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
                
                # Check expiration
                exp_timestamp = payload.get('exp')
                if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
                    return None
                
                # Create user from payload
                return AuthenticatedUser(
                    id=payload['user_id'],
                    email=payload['email'],
                    name="Administrator",
                    role=UserRole(payload['role']),
                    last_login=datetime.utcnow()
                )
                
            except jwt.ExpiredSignatureError:
                return None
            except jwt.InvalidTokenError:
                return None
                
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"Token validation error: {e}")
            return None
    
    def logout(self, token: str) -> bool:
        """Enhanced logout with session cleanup"""
        if not token:
            return False
        
    def refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Refresh an existing token by creating a new session for the same user"""
        try:
            # Try to get user from existing session via Redis
            user: Optional[AuthenticatedUser] = None
            remember_me = False
            ip_address = self._get_client_ip()

            if self.redis:
                try:
                    token_key = f"{self.token_prefix}{token}"
                    session_id = self.redis.get(token_key)
                    if session_id:
                        session_key = f"{self.session_prefix}{session_id}"
                        session_data_raw = self.redis.get(session_key)
                        if session_data_raw:
                            session_info = json.loads(session_data_raw)
                            user_data = session_info.get('user', {})
                            remember_me = session_info.get('remember_me', False)
                            ip_address = session_info.get('ip_address', ip_address)
                            user = AuthenticatedUser(
                                id=user_data.get('id', 'admin'),
                                email=user_data.get('email', ''),
                                name=user_data.get('name', 'Administrator'),
                                role=UserRole(user_data.get('role', 'admin')),
                                last_login=datetime.utcnow(),
                                login_count=user_data.get('login_count', 0),
                                failed_attempts=user_data.get('failed_attempts', 0)
                            )
                except Exception:
                    pass

            # Fallback: validate JWT and extract user info
            if not user:
                user_obj = self.validate_token(token)
                if not user_obj:
                    return None
                user = user_obj

            # Issue new session and token
            return self._create_secure_session(user, remember_me, ip_address)

        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"Token refresh error: {e}")
            return None

        try:
            if self.redis:
                # Remove from Redis
                token_key = f"{self.token_prefix}{token}"
                session_id = self.redis.get(token_key)
                
                if session_id:
                    if isinstance(session_id, (bytes, bytearray)):
                        session_id = session_id.decode()
                    session_key = f"{self.session_prefix}{session_id}"
                    self.redis.delete(session_key)
                    self.redis.delete(token_key)
                    
                    if has_app_context():
                        current_app.logger.info("User logged out successfully")
                
            return True
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"Logout error: {e}")
            return False
    
    def get_session_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information"""
        if not token or not self.redis:
            return None
        
        try:
            token_key = f"{self.token_prefix}{token}"
            session_id = self.redis.get(token_key)
            
            if not session_id:
                return None
            
            if isinstance(session_id, (bytes, bytearray)):
                session_id = session_id.decode()
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.redis.get(session_key)
            
            if not session_data:
                return None
            
            if isinstance(session_data, (bytes, bytearray)):
                session_data = session_data.decode()
            return json.loads(session_data)
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"Session info error: {e}")
            return None


# Alias for backward compatibility
RobustAuthService = AuthService

# Global auth service instance
auth_service = None


def init_auth_service(redis_client: Optional[redis.Redis] = None) -> AuthService:
    """Initialize the authentication service"""
    global auth_service
    auth_service = AuthService(redis_client)
    logger.info("AuthService initialized and ready")
    return auth_service


def get_auth_service() -> Optional[AuthService]:
    """Get the current authentication service instance"""
    return auth_service


def require_admin_auth(f):
    """Decorator for requiring admin authentication"""
    from functools import wraps
    from flask import request, jsonify
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }), 401
        
        token = auth_header.split(' ')[1]
        auth_svc = get_auth_service()
        
        if not auth_svc:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_SERVICE_UNAVAILABLE',
                    'message': 'Authentication service not available'
                }
            }), 503
        
        user = auth_svc.validate_token(token)
        if not user or user.role != UserRole.ADMIN:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'Admin access required'
                }
            }), 403
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function