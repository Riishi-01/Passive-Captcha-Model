"""
Script Token Management System for Passive CAPTCHA
Handles script generation, token lifecycle, and website integration
"""

import os
import uuid
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from flask import current_app
from app.database import get_db_session, Website
from sqlalchemy import and_, or_
import jwt


class TokenStatus(Enum):
    """Token status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ScriptVersion(Enum):
    """Script version enumeration"""
    V1_BASIC = "v1_basic"
    V1_ADVANCED = "v1_advanced"
    V2_ENHANCED = "v2_enhanced"


@dataclass
class ScriptToken:
    """Script token data structure"""
    token_id: str
    website_id: str
    website_name: str
    website_url: str
    script_token: str
    integration_key: str
    status: TokenStatus
    script_version: ScriptVersion
    created_at: datetime
    activated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    usage_count: int = 0
    config: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['script_version'] = self.script_version.value
        data['created_at'] = self.created_at.isoformat()
        data['activated_at'] = self.activated_at.isoformat() if self.activated_at else None
        data['last_used_at'] = self.last_used_at.isoformat() if self.last_used_at else None
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptToken':
        """Create instance from dictionary"""
        return cls(
            token_id=data['token_id'],
            website_id=data['website_id'],
            website_name=data['website_name'],
            website_url=data['website_url'],
            script_token=data['script_token'],
            integration_key=data['integration_key'],
            status=TokenStatus(data['status']),
            script_version=ScriptVersion(data['script_version']),
            created_at=datetime.fromisoformat(data['created_at']),
            activated_at=datetime.fromisoformat(data['activated_at']) if data['activated_at'] else None,
            last_used_at=datetime.fromisoformat(data['last_used_at']) if data['last_used_at'] else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            usage_count=data.get('usage_count', 0),
            config=data.get('config', {})
        )


class ScriptTokenManager:
    """Manages script tokens and website integration"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.token_prefix = "script_token:"
        self.website_tokens_prefix = "website_tokens:"
        self.active_tokens_prefix = "active_tokens:"
        
    def generate_script_token(self, website_id: str, script_version: ScriptVersion = ScriptVersion.V2_ENHANCED) -> ScriptToken:
        """
        Generate a new script token for a website (one-time only)
        """
        session = get_db_session()
        try:
            # Get website details
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                raise ValueError(f"Website {website_id} not found")
            
            # Check if token already exists for this website
            existing_token = self.get_website_token(website_id)
            if existing_token:
                raise ValueError(f"Script token already exists for website {website.website_name}")
            
            # Generate unique tokens
            token_id = str(uuid.uuid4())
            script_token = f"pcs_{secrets.token_urlsafe(32)}"  # Passive CAPTCHA Script
            integration_key = f"pck_{secrets.token_urlsafe(24)}"  # Passive CAPTCHA Key
            
            # Set expiration (tokens don't expire unless manually revoked)
            expires_at = None  # No expiration for script tokens
            
            # Create script token
            script_token_obj = ScriptToken(
                token_id=token_id,
                website_id=website_id,
                website_name=website.website_name,
                website_url=website.website_url,
                script_token=script_token,
                integration_key=integration_key,
                status=TokenStatus.PENDING,
                script_version=script_version,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                config={
                    'collect_mouse_movements': True,
                    'collect_keyboard_patterns': True,
                    'collect_scroll_behavior': True,
                    'collect_timing_data': True,
                    'collect_device_info': True,
                    'sampling_rate': 0.1,  # 10% of interactions
                    'batch_size': 50,
                    'send_interval': 30000,  # 30 seconds
                    'debug_mode': False
                }
            )
            
            # Store in Redis
            self._store_token(script_token_obj)
            
            # Update website status to pending integration
            website.status = 'pending_integration'
            session.commit()
            
            current_app.logger.info(f"Generated script token for website {website.website_name}")
            return script_token_obj
            
        finally:
            session.close()
    
    def activate_token(self, script_token: str, website_url: str) -> bool:
        """
        Activate a token when the script is first loaded on the website
        """
        token_obj = self.get_token_by_script_token(script_token)
        if not token_obj:
            return False
        
        # Verify website URL matches
        if not self._verify_website_url(token_obj.website_url, website_url):
            current_app.logger.warning(f"Website URL mismatch for token {script_token}")
            return False
        
        # Activate the token
        token_obj.status = TokenStatus.ACTIVE
        token_obj.activated_at = datetime.utcnow()
        token_obj.last_used_at = datetime.utcnow()
        
        # Update website status
        self._update_website_status(token_obj.website_id, 'active')
        
        # Store updated token
        self._store_token(token_obj)
        
        current_app.logger.info(f"Activated script token for website {token_obj.website_name}")
        return True
    
    def validate_token(self, script_token: str, website_url: str) -> Tuple[bool, Optional[ScriptToken]]:
        """
        Validate a script token for data collection
        """
        token_obj = self.get_token_by_script_token(script_token)
        if not token_obj:
            return False, None
        
        # Check token status
        if token_obj.status not in [TokenStatus.PENDING, TokenStatus.ACTIVE]:
            return False, None
        
        # Check expiration
        if token_obj.expires_at and token_obj.expires_at < datetime.utcnow():
            token_obj.status = TokenStatus.EXPIRED
            self._store_token(token_obj)
            return False, None
        
        # Verify website URL
        if not self._verify_website_url(token_obj.website_url, website_url):
            return False, None
        
        # Auto-activate if pending and first request
        if token_obj.status == TokenStatus.PENDING:
            self.activate_token(script_token, website_url)
            token_obj = self.get_token_by_script_token(script_token)  # Refresh
        
        # Update usage
        token_obj.usage_count += 1
        token_obj.last_used_at = datetime.utcnow()
        self._store_token(token_obj)
        
        return True, token_obj
    
    def revoke_token(self, website_id: str) -> bool:
        """
        Revoke a script token for a website
        """
        token_obj = self.get_website_token(website_id)
        if not token_obj:
            return False
        
        # Revoke token
        token_obj.status = TokenStatus.REVOKED
        self._store_token(token_obj)
        
        # Update website status
        self._update_website_status(website_id, 'inactive')
        
        current_app.logger.info(f"Revoked script token for website {token_obj.website_name}")
        return True
    
    def get_website_token(self, website_id: str) -> Optional[ScriptToken]:
        """
        Get script token for a specific website
        """
        key = f"{self.website_tokens_prefix}{website_id}"
        token_data = self.redis.get(key)
        if token_data:
            return ScriptToken.from_dict(json.loads(token_data))
        return None
    
    def get_token_by_script_token(self, script_token: str) -> Optional[ScriptToken]:
        """
        Get token object by script token string
        """
        # Hash the script token for lookup
        token_hash = hashlib.sha256(script_token.encode()).hexdigest()
        key = f"{self.token_prefix}{token_hash}"
        token_data = self.redis.get(key)
        if token_data:
            return ScriptToken.from_dict(json.loads(token_data))
        return None
    
    def get_all_tokens(self) -> List[ScriptToken]:
        """
        Get all script tokens
        """
        tokens = []
        pattern = f"{self.website_tokens_prefix}*"
        for key in self.redis.scan_iter(match=pattern):
            token_data = self.redis.get(key)
            if token_data:
                tokens.append(ScriptToken.from_dict(json.loads(token_data)))
        return tokens
    
    def get_active_tokens(self) -> List[ScriptToken]:
        """
        Get all active script tokens
        """
        tokens = self.get_all_tokens()
        return [token for token in tokens if token.status == TokenStatus.ACTIVE]
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens
        """
        tokens = self.get_all_tokens()
        cleaned = 0
        
        for token in tokens:
            if token.expires_at and token.expires_at < datetime.utcnow():
                token.status = TokenStatus.EXPIRED
                self._store_token(token)
                self._update_website_status(token.website_id, 'inactive')
                cleaned += 1
        
        return cleaned
    
    def get_token_stats(self) -> Dict[str, Any]:
        """
        Get token statistics
        """
        tokens = self.get_all_tokens()
        
        stats = {
            'total_tokens': len(tokens),
            'active_tokens': len([t for t in tokens if t.status == TokenStatus.ACTIVE]),
            'pending_tokens': len([t for t in tokens if t.status == TokenStatus.PENDING]),
            'inactive_tokens': len([t for t in tokens if t.status == TokenStatus.INACTIVE]),
            'expired_tokens': len([t for t in tokens if t.status == TokenStatus.EXPIRED]),
            'revoked_tokens': len([t for t in tokens if t.status == TokenStatus.REVOKED]),
            'total_usage': sum(t.usage_count for t in tokens),
            'tokens_by_version': {}
        }
        
        # Group by script version
        for token in tokens:
            version = token.script_version.value
            if version not in stats['tokens_by_version']:
                stats['tokens_by_version'][version] = 0
            stats['tokens_by_version'][version] += 1
        
        return stats
    
    def _store_token(self, token_obj: ScriptToken):
        """
        Store token in Redis with multiple access patterns
        """
        token_data = json.dumps(token_obj.to_dict(), default=str)
        
        # Store by website ID
        website_key = f"{self.website_tokens_prefix}{token_obj.website_id}"
        self.redis.set(website_key, token_data)
        
        # Store by script token hash for quick lookup
        token_hash = hashlib.sha256(token_obj.script_token.encode()).hexdigest()
        token_key = f"{self.token_prefix}{token_hash}"
        self.redis.set(token_key, token_data)
        
        # Store in active tokens set if active
        active_key = f"{self.active_tokens_prefix}set"
        if token_obj.status == TokenStatus.ACTIVE:
            self.redis.sadd(active_key, token_obj.website_id)
        else:
            self.redis.srem(active_key, token_obj.website_id)
    
    def _verify_website_url(self, registered_url: str, request_url: str) -> bool:
        """
        Verify that the request URL matches the registered website URL
        """
        # Simple domain matching (can be enhanced for subdomains, protocols, etc.)
        from urllib.parse import urlparse
        
        registered_domain = urlparse(registered_url).netloc.lower()
        request_domain = urlparse(request_url).netloc.lower()
        
        # Allow exact match or subdomain match
        return (
            registered_domain == request_domain or
            request_domain.endswith(f".{registered_domain}") or
            registered_domain.endswith(f".{request_domain}")
        )
    
    def _update_website_status(self, website_id: str, status: str):
        """
        Update website status in database
        """
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if website:
                website.status = status
                session.commit()
                current_app.logger.info(f"Updated website {website_id} status to {status}")
        finally:
            session.close()


# Global instance
script_token_manager = None


def init_script_token_manager(redis_client: redis.Redis):
    """Initialize the script token manager"""
    global script_token_manager
    script_token_manager = ScriptTokenManager(redis_client)
    return script_token_manager


def get_script_token_manager() -> Optional[ScriptTokenManager]:
    """Get the global script token manager instance"""
    return script_token_manager