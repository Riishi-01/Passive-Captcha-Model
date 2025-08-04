#!/usr/bin/env python3
"""
Robust Authentication Service - Enhanced Security Implementation
Fixes login failures and implements enterprise-grade authentication
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
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from flask import current_app, request
import logging
from contextlib import contextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """Enhanced user roles with granular permissions"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class AuthenticationError(Exception):
    """Authentication-specific errors"""
    pass

class RateLimitError(Exception):
    """Rate limiting errors"""
    pass

class SecurityViolationError(Exception):
    """Security violation errors"""
    pass

@dataclass
class AuthSession:
    """Enhanced authentication session"""
    session_id: str
    user_id: str
    email: str
    role: UserRole
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True
    login_attempts: int = 0
    security_flags: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['role'] = self.role.value
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        data['security_flags'] = self.security_flags or {}
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthSession':
        """Create from dictionary"""
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            email=data['email'],
            role=UserRole(data['role']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            ip_address=data['ip_address'],
            user_agent=data['user_agent'],
            is_active=data.get('is_active', True),
            login_attempts=data.get('login_attempts', 0),
            security_flags=data.get('security_flags', {})
        )

@dataclass
class User:
    """Enhanced user model"""
    user_id: str
    email: str
    password_hash: str
    role: UserRole
    name: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    security_settings: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['role'] = self.role.value
        data['created_at'] = self.created_at.isoformat()
        data['last_login'] = self.last_login.isoformat() if self.last_login else None
        data['account_locked_until'] = self.account_locked_until.isoformat() if self.account_locked_until else None
        data['password_changed_at'] = self.password_changed_at.isoformat() if self.password_changed_at else None
        data['security_settings'] = self.security_settings or {}
        # Don't include password hash in dict
        del data['password_hash']
        return data

class RobustAuthService:
    """Enterprise-grade authentication service"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.jwt_secret = self._get_jwt_secret()
        self.session_timeout = timedelta(hours=24)
        self.max_login_attempts = 5
        self.account_lockout_duration = timedelta(minutes=30)
        self.rate_limit_window = timedelta(minutes=15)
        self.rate_limit_max_attempts = 10
        
        # Add admin_secret for backward compatibility
        self.admin_secret = os.getenv('ADMIN_SECRET', 'Admin123')
        
        # In-memory storage fallback when Redis is not available
        self._memory_users = {}  # email -> User dict
        self._memory_sessions = {}  # session_id -> AuthSession dict
        self._memory_rate_limits = {}  # key -> (count, expire_time)
        
        # Initialize default admin user
        self._ensure_default_admin()
    
    def _get_jwt_secret(self) -> str:
        """Get or generate JWT secret"""
        secret = os.getenv('JWT_SECRET_KEY')
        if not secret:
            secret = secrets.token_urlsafe(64)
            logger.warning("JWT_SECRET_KEY not set, using generated secret (not persistent)")
        return secret
    
    def _ensure_default_admin(self):
        """Ensure default admin user exists"""
        try:
            admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@passivecaptcha.com')
            # Use admin_secret as default password for consistency
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', self.admin_secret)
            
            existing_user = self.get_user_by_email(admin_email)
            if not existing_user:
                admin_user = self.create_user(
                    email=admin_email,
                    password=admin_password,
                    name="Default Admin",
                    role=UserRole.SUPER_ADMIN
                )
                logger.info(f"Created default admin user: {admin_email} with password: {admin_password}")
            else:
                logger.info(f"Default admin user already exists: {admin_email}")
                
        except Exception as e:
            logger.error(f"Failed to ensure default admin: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return f"sess_{secrets.token_urlsafe(32)}"
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID"""
        return f"user_{secrets.token_urlsafe(16)}"
    
    def _get_redis_key(self, key_type: str, identifier: str) -> str:
        """Generate Redis keys"""
        return f"auth:{key_type}:{identifier}"
    
    def _check_rate_limit(self, identifier: str, max_attempts: int = None) -> bool:
        """Check rate limiting"""
        if not self.redis:
            return True  # No rate limiting without Redis
        
        max_attempts = max_attempts or self.rate_limit_max_attempts
        key = self._get_redis_key("rate_limit", identifier)
        
        try:
            current_attempts = self.redis.get(key)
            if current_attempts is None:
                self.redis.setex(key, int(self.rate_limit_window.total_seconds()), 1)
                return True
            
            current_attempts = int(current_attempts)
            if current_attempts >= max_attempts:
                return False
            
            self.redis.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error
    
    def _store_user(self, user: User):
        """Store user in Redis or memory fallback"""
        try:
            data = user.to_dict()
            data['password_hash'] = user.password_hash  # Include for storage
            
            if self.redis:
                key = self._get_redis_key("user", user.email)
                self.redis.setex(key, int(timedelta(days=30).total_seconds()), json.dumps(data, default=str))
            else:
                # Fallback to in-memory storage
                self._memory_users[user.email] = data
                logger.debug(f"Stored user {user.email} in memory (Redis unavailable)")
                
        except Exception as e:
            logger.error(f"Failed to store user: {e}")
    
    def _store_session(self, session: AuthSession):
        """Store session in Redis or memory fallback"""
        try:
            session_data = session.to_dict()
            
            if self.redis:
                key = self._get_redis_key("session", session.session_id)
                self.redis.setex(
                    key, 
                    int(self.session_timeout.total_seconds()), 
                    json.dumps(session_data, default=str)
                )
                
                # Also store by email for lookup
                email_key = self._get_redis_key("session_by_email", session.email)
                self.redis.setex(
                    email_key,
                    int(self.session_timeout.total_seconds()),
                    session.session_id
                )
            else:
                # Fallback to in-memory storage
                expiry_time = datetime.utcnow() + self.session_timeout
                self._memory_sessions[session.session_id] = {
                    'data': session_data,
                    'expires_at': expiry_time,
                    'email': session.email
                }
                logger.debug(f"Stored session {session.session_id} in memory (Redis unavailable)")
                
        except Exception as e:
            logger.error(f"Failed to store session: {e}")
    
    def create_user(self, email: str, password: str, name: str, role: UserRole = UserRole.ADMIN) -> User:
        """Create new user"""
        if self.get_user_by_email(email):
            raise AuthenticationError(f"User with email {email} already exists")
        
        # Validate password strength
        if len(password) < 8:
            raise AuthenticationError("Password must be at least 8 characters long")
        
        user = User(
            user_id=self._generate_user_id(),
            email=email.lower().strip(),
            password_hash=self._hash_password(password),
            role=role,
            name=name,
            created_at=datetime.utcnow(),
            password_changed_at=datetime.utcnow(),
            security_settings={
                'password_expiry_days': 90,
                'require_password_change': False,
                'mfa_enabled': False
            }
        )
        
        self._store_user(user)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from Redis or memory fallback"""
        email = email.lower().strip()
        
        try:
            user_data = None
            
            if self.redis:
                key = self._get_redis_key("user", email)
                data = self.redis.get(key)
                if data:
                    user_data = json.loads(data)
            else:
                # Fallback to in-memory storage
                user_data = self._memory_users.get(email)
            
            if user_data:
                return User(
                    user_id=user_data['user_id'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    role=UserRole(user_data['role']),
                    name=user_data['name'],
                    created_at=datetime.fromisoformat(user_data['created_at']),
                    last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None,
                    is_active=user_data.get('is_active', True),
                    failed_login_attempts=user_data.get('failed_login_attempts', 0),
                    account_locked_until=datetime.fromisoformat(user_data['account_locked_until']) if user_data.get('account_locked_until') else None,
                    password_changed_at=datetime.fromisoformat(user_data['password_changed_at']) if user_data.get('password_changed_at') else None,
                    security_settings=user_data.get('security_settings', {})
                )
                
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
        
        return None
    
    def authenticate_user(self, email: str, password: str, ip_address: str = None, user_agent: str = None) -> Tuple[bool, Optional[AuthSession], Optional[str]]:
        """Authenticate user and create session"""
        email = email.lower().strip()
        ip_address = ip_address or request.remote_addr if request else "unknown"
        user_agent = user_agent or request.headers.get('User-Agent', 'unknown') if request else "unknown"
        
        # Rate limiting
        rate_limit_key = f"{email}:{ip_address}"
        if not self._check_rate_limit(rate_limit_key):
            return False, None, "Too many login attempts. Please try again later."
        
        # Get user
        user = self.get_user_by_email(email)
        if not user:
            return False, None, "Invalid email or password"
        
        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            return False, None, f"Account locked until {user.account_locked_until.strftime('%H:%M:%S')}"
        
        # Check if user is active
        if not user.is_active:
            return False, None, "Account is disabled"
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.max_login_attempts:
                user.account_locked_until = datetime.utcnow() + self.account_lockout_duration
                logger.warning(f"Account locked for user {email} due to failed attempts")
            
            self._store_user(user)
            return False, None, "Invalid email or password"
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        self._store_user(user)
        
        # Create session
        session = AuthSession(
            session_id=self._generate_session_id(),
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            security_flags={
                'login_method': 'password',
                'ip_address': ip_address,
                'user_agent_hash': hashlib.sha256(user_agent.encode()).hexdigest()[:16]
            }
        )
        
        self._store_session(session)
        
        logger.info(f"User {email} authenticated successfully from {ip_address}")
        return True, session, None
    
    def validate_session(self, session_id: str, update_activity: bool = True) -> Optional[AuthSession]:
        """Validate and optionally update session from Redis or memory fallback"""
        if not session_id:
            return None
        
        try:
            session_data = None
            
            if self.redis:
                key = self._get_redis_key("session", session_id)
                data = self.redis.get(key)
                if data:
                    session_data = json.loads(data)
            else:
                # Fallback to in-memory storage
                memory_session = self._memory_sessions.get(session_id)
                if memory_session:
                    # Check if session is expired
                    if memory_session['expires_at'] < datetime.utcnow():
                        # Remove expired session
                        del self._memory_sessions[session_id]
                        return None
                    session_data = memory_session['data']
            
            if not session_data:
                return None
            
            session = AuthSession.from_dict(session_data)
            
            # Check if session is expired (double check for Redis sessions)
            if session.last_activity + self.session_timeout < datetime.utcnow():
                self.invalidate_session(session_id)
                return None
            
            # Update last activity if requested
            if update_activity:
                session.last_activity = datetime.utcnow()
                self._store_session(session)
            
            return session
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    def generate_jwt_token(self, session: AuthSession) -> str:
        """Generate JWT token for session"""
        payload = {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'email': session.email,
            'role': session.role.value,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + self.session_timeout
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Validate session still exists
            session = self.validate_session(payload['session_id'])
            if not session:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None
    
    def invalidate_session(self, session_id: str):
        """Invalidate session"""
        if not self.redis:
            return
        
        try:
            # Get session to find email
            session = self.validate_session(session_id, update_activity=False)
            if session:
                email_key = self._get_redis_key("session_by_email", session.email)
                self.redis.delete(email_key)
            
            # Delete session
            key = self._get_redis_key("session", session_id)
            self.redis.delete(key)
            
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user by invalidating session"""
        try:
            self.invalidate_session(session_id)
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Cleanup expired sessions (run periodically)"""
        if not self.redis:
            return
        
        try:
            # This is automatically handled by Redis TTL, but we can add cleanup logic here
            logger.info("Session cleanup completed")
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
    
    def get_user_sessions(self, email: str) -> List[AuthSession]:
        """Get all active sessions for a user"""
        sessions = []
        if not self.redis:
            return sessions
        
        try:
            # In a production system, you'd maintain a set of session IDs per user
            # For now, we'll return the current session if it exists
            email_key = self._get_redis_key("session_by_email", email)
            session_id = self.redis.get(email_key)
            if session_id:
                session = self.validate_session(session_id.decode(), update_activity=False)
                if session:
                    sessions.append(session)
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
        
        return sessions
    
    def require_role(self, required_role: UserRole, session: AuthSession) -> bool:
        """Check if session has required role"""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.OPERATOR: 2,
            UserRole.ADMIN: 3,
            UserRole.SUPER_ADMIN: 4
        }
        
        user_level = role_hierarchy.get(session.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        return user_level >= required_level
    
    def change_password(self, email: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_user_by_email(email)
        if not user:
            return False
        
        if not self._verify_password(old_password, user.password_hash):
            return False
        
        if len(new_password) < 8:
            raise AuthenticationError("New password must be at least 8 characters long")
        
        user.password_hash = self._hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        self._store_user(user)
        
        return True
    
    def authenticate_admin(self, password: str) -> bool:
        """Backward compatible admin authentication"""
        # Check against admin_secret for backward compatibility
        if password == self.admin_secret:
            return True
        
        # Also check against default admin user
        default_admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@passivecaptcha.com')
        success, session, error = self.authenticate_user(
            email=default_admin_email,
            password=password,
            ip_address="127.0.0.1",
            user_agent="admin"
        )
        
        return success

# Global instance
robust_auth_service = None

def init_robust_auth_service(redis_client: redis.Redis = None):
    """Initialize the robust authentication service"""
    global robust_auth_service
    robust_auth_service = RobustAuthService(redis_client)
    return robust_auth_service

def get_robust_auth_service() -> Optional[RobustAuthService]:
    """Get the robust authentication service instance"""
    return robust_auth_service