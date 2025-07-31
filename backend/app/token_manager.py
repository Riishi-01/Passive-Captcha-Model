"""
Multi-Tenant Token Management System for Passive CAPTCHA Platform
Handles website registration, token generation, and access control
"""

import os
import uuid
import secrets
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import current_app
import redis
import json

@dataclass
class WebsiteToken:
    """Data class for website token information"""
    website_id: str
    website_name: str
    website_url: str
    admin_email: str
    api_key: str
    secret_key: str
    created_at: datetime
    permissions: List[str]
    rate_limits: Dict[str, int]
    status: str = 'active'

class TokenManager:
    """
    Manages multi-tenant tokens for website isolation
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or self._get_redis_client()
        self.jwt_secret = current_app.config.get('JWT_SECRET_KEY', 'fallback-secret')
        self.token_expiry = 86400 * 30  # 30 days
        
    def _get_redis_client(self):
        """Initialize Redis client for token storage"""
        try:
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379')
            return redis.from_url(redis_url)
        except Exception:
            # Fallback to in-memory storage for development
            return None
    
    def generate_website_token(self, website_name: str, website_url: str, admin_email: str) -> WebsiteToken:
        """
        Generate unique tokens for each website integration
        """
        website_id = str(uuid.uuid4())
        api_key = self._generate_secure_api_key()
        secret_key = self._generate_secret_key()
        
        website_token = WebsiteToken(
            website_id=website_id,
            website_name=website_name,
            website_url=website_url,
            admin_email=admin_email,
            api_key=api_key,
            secret_key=secret_key,
            created_at=datetime.utcnow(),
            permissions=['read', 'write', 'analytics', 'dashboard'],
            rate_limits={
                'verify_requests_per_hour': 10000,
                'analytics_requests_per_hour': 1000,
                'dashboard_requests_per_hour': 500
            }
        )
        
        # Store in database/cache
        self._store_website_token(website_token)
        
        return website_token
    
    def _generate_secure_api_key(self) -> str:
        """Generate cryptographically secure API key"""
        return f"pc_{secrets.token_urlsafe(32)}"
    
    def _generate_secret_key(self) -> str:
        """Generate secret key for JWT signing"""
        return secrets.token_urlsafe(64)
    
    def _store_website_token(self, token: WebsiteToken):
        """Store website token in persistent storage"""
        token_data = {
            'website_id': token.website_id,
            'website_name': token.website_name,
            'website_url': token.website_url,
            'admin_email': token.admin_email,
            'api_key': token.api_key,
            'secret_key': token.secret_key,
            'created_at': token.created_at.isoformat(),
            'permissions': token.permissions,
            'rate_limits': token.rate_limits,
            'status': token.status
        }
        
        if self.redis_client:
            # Store in Redis
            self.redis_client.hset(
                f"website_tokens:{token.website_id}",
                mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                        for k, v in token_data.items()}
            )
            # Index by API key for quick lookup
            self.redis_client.set(f"api_key_lookup:{token.api_key}", token.website_id)
        
        # Also store in database for persistence
        from app.database import store_website_registration
        store_website_registration(token_data)
    
    def get_website_by_api_key(self, api_key: str) -> Optional[WebsiteToken]:
        """Retrieve website information by API key"""
        try:
            if self.redis_client:
                website_id = self.redis_client.get(f"api_key_lookup:{api_key}")
                if website_id:
                    return self._get_website_by_id(website_id.decode())
            
            # Fallback to database lookup
            from app.database import get_website_by_api_key
            website_data = get_website_by_api_key(api_key)
            
            if website_data:
                return self._dict_to_website_token(website_data)
            
            return None
            
        except Exception as e:
            print(f"Error retrieving website by API key: {e}")
            return None
    
    def _get_website_by_id(self, website_id: str) -> Optional[WebsiteToken]:
        """Get website token by ID"""
        try:
            if self.redis_client:
                token_data = self.redis_client.hgetall(f"website_tokens:{website_id}")
                if token_data:
                    # Convert byte strings to proper types
                    parsed_data = {}
                    for k, v in token_data.items():
                        key = k.decode() if isinstance(k, bytes) else k
                        value = v.decode() if isinstance(v, bytes) else v
                        
                        if key in ['permissions', 'rate_limits']:
                            parsed_data[key] = json.loads(value)
                        else:
                            parsed_data[key] = value
                    
                    return self._dict_to_website_token(parsed_data)
            
            return None
            
        except Exception as e:
            print(f"Error retrieving website by ID: {e}")
            return None
    
    def _dict_to_website_token(self, data: Dict[str, Any]) -> WebsiteToken:
        """Convert dictionary to WebsiteToken object"""
        return WebsiteToken(
            website_id=data['website_id'],
            website_name=data['website_name'],
            website_url=data['website_url'],
            admin_email=data['admin_email'],
            api_key=data['api_key'],
            secret_key=data['secret_key'],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            permissions=data.get('permissions', []),
            rate_limits=data.get('rate_limits', {}),
            status=data.get('status', 'active')
        )
    
    def generate_dashboard_token(self, website_id: str, admin_email: str) -> str:
        """Generate JWT token for dashboard access"""
        payload = {
            'website_id': website_id,
            'admin_email': admin_email,
            'scope': ['dashboard', 'analytics', 'logs'],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiry)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_dashboard_token(self, token: str, website_id: str) -> bool:
        """Validate dashboard access token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload.get('website_id') == website_id
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
    
    def validate_api_request(self, api_key: str, website_id: str = None) -> Optional[WebsiteToken]:
        """Validate API request and return website token if valid"""
        website_token = self.get_website_by_api_key(api_key)
        
        if not website_token:
            return None
        
        if website_token.status != 'active':
            return None
        
        if website_id and website_token.website_id != website_id:
            return None
        
        return website_token
    
    def get_all_websites_for_admin(self, admin_email: str) -> List[WebsiteToken]:
        """Get all websites registered by an admin"""
        # This would typically query the database
        from app.database import get_websites_by_admin
        websites_data = get_websites_by_admin(admin_email)
        
        return [self._dict_to_website_token(data) for data in websites_data]
    
    def revoke_website_access(self, website_id: str) -> bool:
        """Revoke access for a website (soft delete)"""
        try:
            if self.redis_client:
                # Update status in Redis
                self.redis_client.hset(f"website_tokens:{website_id}", 'status', 'revoked')
            
            # Update in database
            from app.database import update_website_status
            update_website_status(website_id, 'revoked')
            
            return True
            
        except Exception as e:
            print(f"Error revoking website access: {e}")
            return False

class SecurityManager:
    """
    Enhanced security management for API tokens and requests
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or self._get_redis_client()
        self.rate_limits = {
            'verify': 10000,  # per hour
            'analytics': 1000,  # per hour
            'dashboard': 500   # per hour
        }
    
    def _get_redis_client(self):
        """Initialize Redis client"""
        try:
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379')
            return redis.from_url(redis_url)
        except Exception:
            return None
    
    def apply_rate_limit(self, website_id: str, request_type: str = 'verify') -> bool:
        """Apply per-website rate limiting"""
        if not self.redis_client:
            return True  # Skip rate limiting if Redis unavailable
        
        key = f"rate_limit:{website_id}:{request_type}"
        current_count = self.redis_client.get(key) or 0
        limit = self.rate_limits.get(request_type, 1000)
        
        if int(current_count) >= limit:
            return False
        
        # Increment counter with expiry
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 3600)  # 1 hour window
        pipe.execute()
        
        return True
    
    def get_rate_limit_info(self, website_id: str, request_type: str = 'verify') -> Dict[str, int]:
        """Get current rate limit information"""
        if not self.redis_client:
            return {'used': 0, 'limit': self.rate_limits.get(request_type, 1000), 'remaining': 1000}
        
        key = f"rate_limit:{website_id}:{request_type}"
        used = int(self.redis_client.get(key) or 0)
        limit = self.rate_limits.get(request_type, 1000)
        
        return {
            'used': used,
            'limit': limit,
            'remaining': max(0, limit - used)
        }
    
    def log_security_event(self, website_id: str, event_type: str, details: Dict[str, Any]):
        """Log security events for monitoring"""
        if self.redis_client:
            event = {
                'website_id': website_id,
                'event_type': event_type,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store in security log
            self.redis_client.lpush(
                f"security_log:{website_id}",
                json.dumps(event)
            )
            
            # Keep only last 1000 events
            self.redis_client.ltrim(f"security_log:{website_id}", 0, 999)

# Global instances
token_manager = None
security_manager = None

def init_token_management(app):
    """Initialize token management with Flask app"""
    global token_manager, security_manager
    
    with app.app_context():
        token_manager = TokenManager()
        security_manager = SecurityManager()