"""
Authentication Service
Centralized authentication and authorization logic
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
from flask import current_app, has_app_context
import redis
import json


class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


@dataclass
class AuthenticatedUser:
    """Authenticated user data structure"""
    id: str
    email: str
    name: str
    role: UserRole
    last_login: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value,
            'last_login': self.last_login.isoformat()
        }


class AuthService:
    """Centralized authentication service"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.session_prefix = "session:"
        self.token_prefix = "token:"
        self.session_ttl = 86400  # 24 hours
        
        # Get configuration from Flask app context if available, fallback to env vars
        if has_app_context():
            from flask import current_app
            self.jwt_secret = current_app.config.get('JWT_SECRET', os.getenv('JWT_SECRET', 'your-secret-key'))
            self.admin_secret = current_app.config.get('ADMIN_SECRET', os.getenv('ADMIN_SECRET', 'Admin123'))
        else:
            # Fallback to environment variables if no app context
            self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key')
            self.admin_secret = os.getenv('ADMIN_SECRET', 'Admin123')
        
    def authenticate_admin(self, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate admin user with password
        """
        # Simple password check for admin
        if password != self.admin_secret:
            current_app.logger.warning(f"Failed admin login attempt")
            return None
        
        # Generate JWT token
        now = datetime.utcnow()
        exp_time = now + timedelta(seconds=self.session_ttl)
        
        payload = {
            'admin': True,
            'iat': int(now.timestamp()),
            'exp': int(exp_time.timestamp())
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
        # Create user object
        user = AuthenticatedUser(
            id='admin',
            email='admin@passivecaptcha.com',
            name='Administrator',
            role=UserRole.ADMIN,
            last_login=now
        )
        
        # Store session in Redis (if available)
        session_id = self._generate_session_id()
        session_data = {
            'user': user.to_dict(),
            'token': token,
            'created_at': now.isoformat(),
            'expires_at': exp_time.isoformat()
        }
        
        if self.redis:
            try:
                session_key = f"{self.session_prefix}{session_id}"
                self.redis.setex(session_key, self.session_ttl, json.dumps(session_data, default=str))
                
                # Store token mapping
                token_key = f"{self.token_prefix}{token}"
                self.redis.setex(token_key, self.session_ttl, session_id)
                current_app.logger.info("Session stored in Redis")
            except Exception as e:
                current_app.logger.warning(f"Failed to store session in Redis: {e}")
        else:
            current_app.logger.info("Session created without Redis storage")
        
        current_app.logger.info(f"Admin login successful")
        
        return {
            'token': token,
            'user': user.to_dict(),
            'expires_in': self.session_ttl,
            'timestamp': now.isoformat()
        }
    
    def validate_token(self, token: str) -> Optional[AuthenticatedUser]:
        """
        Validate JWT token and return user if valid
        """
        try:
            # If Redis is available, check session storage
            if self.redis:
                try:
                    # Check if token exists in Redis
                    token_key = f"{self.token_prefix}{token}"
                    session_id = self.redis.get(token_key)
                    
                    if not session_id:
                        return None
                    
                    # Get session data
                    session_key = f"{self.session_prefix}{session_id.decode()}"
                    session_data = self.redis.get(session_key)
                    
                    if not session_data:
                        return None
                    
                    session_info = json.loads(session_data)
                except Exception as e:
                    current_app.logger.warning(f"Redis validation failed, falling back to JWT-only: {e}")
                    # Fall through to JWT-only validation
            
            # JWT-only validation (no Redis required)
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check if token is expired
            if payload['exp'] < datetime.utcnow().timestamp():
                return None
            
            # For admin tokens, create user object
            if payload.get('admin'):
                return AuthenticatedUser(
                    id='admin',
                    email='admin@passivecaptcha.com',
                    name='Administrator',
                    role=UserRole.ADMIN,
                    last_login=datetime.utcnow()
                )
            
            return None
            
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, KeyError, ValueError) as e:
            current_app.logger.warning(f"Token validation failed: {e}")
            return None
    
    def logout(self, token: str) -> bool:
        """
        Logout user and invalidate session
        """
        try:
            # Get session ID from token
            token_key = f"{self.token_prefix}{token}"
            session_id = self.redis.get(token_key)
            
            if session_id:
                self._cleanup_session(session_id.decode(), token)
                current_app.logger.info("User logged out successfully")
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Logout error: {e}")
            return False
    
    def refresh_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh user session and extend expiration
        """
        user = self.validate_token(token)
        if not user:
            return None
        
        try:
            # Get current session
            token_key = f"{self.token_prefix}{token}"
            session_id = self.redis.get(token_key)
            
            if not session_id:
                return None
            
            session_key = f"{self.session_prefix}{session_id.decode()}"
            session_data = self.redis.get(session_key)
            
            if not session_data:
                return None
            
            session_info = json.loads(session_data)
            
            # Extend session expiration
            now = datetime.utcnow()
            exp_time = now + timedelta(seconds=self.session_ttl)
            
            session_info['expires_at'] = exp_time.isoformat()
            
            # Update Redis entries
            self.redis.setex(session_key, self.session_ttl, json.dumps(session_info, default=str))
            self.redis.setex(token_key, self.session_ttl, session_id)
            
            return {
                'token': token,
                'user': user.to_dict(),
                'expires_in': self.session_ttl,
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Session refresh error: {e}")
            return None
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all active sessions (admin function)
        """
        try:
            sessions = []
            pattern = f"{self.session_prefix}*"
            
            for key in self.redis.scan_iter(match=pattern):
                session_data = self.redis.get(key)
                if session_data:
                    try:
                        session_info = json.loads(session_data)
                        sessions.append({
                            'session_id': key.decode().replace(self.session_prefix, ''),
                            'user': session_info['user'],
                            'created_at': session_info['created_at'],
                            'expires_at': session_info['expires_at']
                        })
                    except json.JSONDecodeError:
                        continue
            
            return sessions
            
        except Exception as e:
            current_app.logger.error(f"Error getting active sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        """
        try:
            cleaned = 0
            now = datetime.utcnow()
            pattern = f"{self.session_prefix}*"
            
            for key in self.redis.scan_iter(match=pattern):
                session_data = self.redis.get(key)
                if session_data:
                    try:
                        session_info = json.loads(session_data)
                        expires_at = datetime.fromisoformat(session_info['expires_at'])
                        
                        if expires_at < now:
                            session_id = key.decode().replace(self.session_prefix, '')
                            token = session_info.get('token')
                            self._cleanup_session(session_id, token)
                            cleaned += 1
                            
                    except (json.JSONDecodeError, ValueError, KeyError):
                        # Clean up malformed session data
                        self.redis.delete(key)
                        cleaned += 1
            
            return cleaned
            
        except Exception as e:
            current_app.logger.error(f"Session cleanup error: {e}")
            return 0
    
    def get_auth_statistics(self) -> Dict[str, Any]:
        """
        Get authentication statistics
        """
        try:
            active_sessions = len(self.get_active_sessions())
            total_tokens = len(list(self.redis.scan_iter(match=f"{self.token_prefix}*")))
            
            return {
                'active_sessions': active_sessions,
                'total_tokens': total_tokens,
                'session_ttl': self.session_ttl,
                'cleanup_last_run': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting auth statistics: {e}")
            return {}
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"sess_{secrets.token_urlsafe(32)}"
    
    def _cleanup_session(self, session_id: str, token: str = None):
        """Clean up session and token data"""
        try:
            # Remove session
            session_key = f"{self.session_prefix}{session_id}"
            self.redis.delete(session_key)
            
            # Remove token mapping if provided
            if token:
                token_key = f"{self.token_prefix}{token}"
                self.redis.delete(token_key)
                
        except Exception as e:
            current_app.logger.error(f"Session cleanup error: {e}")


# Global instance
auth_service = None


def init_auth_service(redis_client: Optional[redis.Redis] = None):
    """Initialize the authentication service"""
    global auth_service
    auth_service = AuthService(redis_client)
    return auth_service


def get_auth_service() -> Optional[AuthService]:
    """Get the global authentication service instance"""
    return auth_service