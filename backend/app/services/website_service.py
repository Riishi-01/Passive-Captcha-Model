"""
Website Management Service
Centralized service for website CRUD operations and integration status management
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from flask import current_app
from app.database import get_db_session, Website, VerificationLog
from app.script_token_manager import get_script_token_manager, TokenStatus
from sqlalchemy import and_, or_, func, desc
import redis


class WebsiteStatus(Enum):
    """Website status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_INTEGRATION = "pending_integration"


class IntegrationStatus(Enum):
    """Script integration status enumeration"""
    NOT_INTEGRATED = "not_integrated"
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class WebsiteData:
    """Website data structure"""
    id: str
    name: str
    url: str
    status: WebsiteStatus
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    
    # Analytics data
    total_verifications: int = 0
    human_rate: float = 0.0
    avg_confidence: float = 0.0
    last_activity: Optional[datetime] = None
    
    # Integration data
    integration_status: IntegrationStatus = IntegrationStatus.NOT_INTEGRATED
    has_script_token: bool = False
    script_token_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['integration_status'] = self.integration_status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat() if self.last_activity else None
        return data


class WebsiteService:
    """Centralized website management service"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_prefix = "website:"
        self.cache_ttl = 300  # 5 minutes
        
    def get_all_websites(self, include_analytics: bool = True) -> List[WebsiteData]:
        """
        Get all websites with optional analytics data and integration status
        """
        session = get_db_session()
        try:
            websites = session.query(Website).order_by(Website.created_at.desc()).all()
            website_data = []
            
            # Get script token manager for integration status
            token_manager = get_script_token_manager()
            
            for website in websites:
                # Get analytics data if requested
                analytics = {}
                if include_analytics:
                    analytics = self._get_website_analytics(website.website_id, session)
                
                # Get integration status
                integration_data = self._get_integration_status(website.website_id, token_manager)
                
                website_data.append(WebsiteData(
                    id=website.website_id,
                    name=website.website_name,
                    url=website.website_url,
                    status=WebsiteStatus(website.status or 'active'),
                    created_at=website.created_at,
                    updated_at=website.updated_at or website.created_at,
                    description=getattr(website, 'description', None),
                    
                    # Analytics
                    total_verifications=analytics.get('total_verifications', 0),
                    human_rate=analytics.get('human_rate', 0.0),
                    avg_confidence=analytics.get('avg_confidence', 0.0),
                    last_activity=analytics.get('last_activity'),
                    
                    # Integration
                    integration_status=integration_data['status'],
                    has_script_token=integration_data['has_token'],
                    script_token_info=integration_data['token_info']
                ))
            
            return website_data
            
        finally:
            session.close()
    
    def get_website(self, website_id: str, include_analytics: bool = True) -> Optional[WebsiteData]:
        """
        Get a specific website by ID
        """
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                return None
            
            # Get analytics data if requested
            analytics = {}
            if include_analytics:
                analytics = self._get_website_analytics(website_id, session)
            
            # Get integration status
            token_manager = get_script_token_manager()
            integration_data = self._get_integration_status(website_id, token_manager)
            
            return WebsiteData(
                id=website.website_id,
                name=website.website_name,
                url=website.website_url,
                status=WebsiteStatus(website.status or 'active'),
                created_at=website.created_at,
                updated_at=website.updated_at or website.created_at,
                description=getattr(website, 'description', None),
                
                # Analytics
                total_verifications=analytics.get('total_verifications', 0),
                human_rate=analytics.get('human_rate', 0.0),
                avg_confidence=analytics.get('avg_confidence', 0.0),
                last_activity=analytics.get('last_activity'),
                
                # Integration
                integration_status=integration_data['status'],
                has_script_token=integration_data['has_token'],
                script_token_info=integration_data['token_info']
            )
            
        finally:
            session.close()
    
    def create_website(self, name: str, url: str, description: str = None) -> WebsiteData:
        """
        Create a new website
        """
        session = get_db_session()
        try:
            website_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            new_website = Website(
                website_id=website_id,
                website_name=name,
                website_url=url,
                status=WebsiteStatus.PENDING_INTEGRATION.value,
                created_at=now,
                updated_at=now
            )
            
            # Add description if provided (assuming the model supports it)
            if hasattr(new_website, 'description'):
                new_website.description = description
            
            session.add(new_website)
            session.commit()
            
            # Clear cache
            self._clear_website_cache()
            
            current_app.logger.info(f"Created new website: {name} ({url})")
            
            return WebsiteData(
                id=website_id,
                name=name,
                url=url,
                status=WebsiteStatus.PENDING_INTEGRATION,
                created_at=now,
                updated_at=now,
                description=description,
                
                # New website has no analytics or integration yet
                total_verifications=0,
                human_rate=0.0,
                avg_confidence=0.0,
                last_activity=None,
                integration_status=IntegrationStatus.NOT_INTEGRATED,
                has_script_token=False,
                script_token_info=None
            )
            
        finally:
            session.close()
    
    def update_website(self, website_id: str, name: str = None, url: str = None, 
                      description: str = None, status: WebsiteStatus = None) -> bool:
        """
        Update an existing website
        """
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                return False
            
            # Update fields if provided
            if name is not None:
                website.website_name = name
            if url is not None:
                website.website_url = url
            if status is not None:
                website.status = status.value
            if description is not None and hasattr(website, 'description'):
                website.description = description
            
            website.updated_at = datetime.utcnow()
            session.commit()
            
            # Clear cache
            self._clear_website_cache()
            
            current_app.logger.info(f"Updated website {website_id}: {name or website.website_name}")
            return True
            
        finally:
            session.close()
    
    def delete_website(self, website_id: str) -> bool:
        """
        Delete a website and its associated script token
        """
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                return False
            
            website_name = website.website_name
            
            # Revoke script token if exists
            token_manager = get_script_token_manager()
            if token_manager:
                token_manager.revoke_token(website_id)
            
            # Delete website
            session.delete(website)
            session.commit()
            
            # Clear cache
            self._clear_website_cache()
            
            current_app.logger.info(f"Deleted website {website_id}: {website_name}")
            return True
            
        finally:
            session.close()
    
    def toggle_website_status(self, website_id: str) -> Optional[WebsiteStatus]:
        """
        Toggle website status between active and inactive
        """
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                return None
            
            current_status = WebsiteStatus(website.status or 'active')
            new_status = WebsiteStatus.ACTIVE if current_status == WebsiteStatus.INACTIVE else WebsiteStatus.INACTIVE
            
            website.status = new_status.value
            website.updated_at = datetime.utcnow()
            session.commit()
            
            # Clear cache
            self._clear_website_cache()
            
            current_app.logger.info(f"Toggled website {website_id} status: {current_status.value} → {new_status.value}")
            return new_status
            
        finally:
            session.close()
    
    def update_integration_status(self, website_id: str, status: IntegrationStatus) -> bool:
        """
        Update website integration status based on script token state
        """
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                return False
            
            # Map integration status to website status
            if status == IntegrationStatus.ACTIVE:
                website.status = WebsiteStatus.ACTIVE.value
            elif status == IntegrationStatus.PENDING:
                website.status = WebsiteStatus.PENDING_INTEGRATION.value
            elif status in [IntegrationStatus.NOT_INTEGRATED, IntegrationStatus.REVOKED]:
                website.status = WebsiteStatus.INACTIVE.value
            
            website.updated_at = datetime.utcnow()
            session.commit()
            
            # Clear cache
            self._clear_website_cache()
            
            return True
            
        finally:
            session.close()
    
    def get_website_statistics(self) -> Dict[str, Any]:
        """
        Get overall website statistics
        """
        session = get_db_session()
        try:
            total_websites = session.query(Website).count()
            active_websites = session.query(Website).filter(Website.status == WebsiteStatus.ACTIVE.value).count()
            
            # Get total verifications across all websites
            total_verifications = session.query(func.count(VerificationLog.id)).scalar() or 0
            
            # Get websites with script tokens
            token_manager = get_script_token_manager()
            tokens_stats = token_manager.get_token_stats() if token_manager else {}
            
            return {
                'total_websites': total_websites,
                'active_websites': active_websites,
                'inactive_websites': total_websites - active_websites,
                'total_verifications': total_verifications,
                'integration_stats': {
                    'total_tokens': tokens_stats.get('total_tokens', 0),
                    'active_tokens': tokens_stats.get('active_tokens', 0),
                    'pending_tokens': tokens_stats.get('pending_tokens', 0)
                }
            }
            
        finally:
            session.close()
    
    def _get_website_analytics(self, website_id: str, session) -> Dict[str, Any]:
        """
        Get analytics data for a specific website
        """
        # Cache key for analytics
        cache_key = f"{self.cache_prefix}analytics:{website_id}"
        cached_data = self.redis.get(cache_key)
        
        if cached_data:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                pass
        
        # Calculate analytics from verification logs
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get verification counts and stats
        verifications = session.query(VerificationLog).filter(
            and_(
                VerificationLog.origin.contains(website_id) if hasattr(VerificationLog, 'origin') else True,
                VerificationLog.timestamp >= thirty_days_ago
            )
        ).all()
        
        total_verifications = len(verifications)
        human_count = sum(1 for v in verifications if getattr(v, 'is_human', False))
        human_rate = (human_count / total_verifications * 100) if total_verifications > 0 else 0.0
        
        avg_confidence = (
            sum(getattr(v, 'confidence', 0) for v in verifications) / total_verifications
        ) if total_verifications > 0 else 0.0
        
        last_activity = max(
            (getattr(v, 'timestamp', None) for v in verifications if getattr(v, 'timestamp', None)),
            default=None
        )
        
        analytics = {
            'total_verifications': total_verifications,
            'human_rate': round(human_rate, 2),
            'avg_confidence': round(avg_confidence, 4),
            'last_activity': last_activity
        }
        
        # Cache for 5 minutes
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(analytics, default=str))
        
        return analytics
    
    def _get_integration_status(self, website_id: str, token_manager) -> Dict[str, Any]:
        """
        Get script integration status for a website
        """
        if not token_manager:
            return {
                'status': IntegrationStatus.NOT_INTEGRATED,
                'has_token': False,
                'token_info': None
            }
        
        script_token = token_manager.get_website_token(website_id)
        
        if not script_token:
            return {
                'status': IntegrationStatus.NOT_INTEGRATED,
                'has_token': False,
                'token_info': None
            }
        
        # Map token status to integration status
        status_mapping = {
            TokenStatus.PENDING: IntegrationStatus.PENDING,
            TokenStatus.ACTIVE: IntegrationStatus.ACTIVE,
            TokenStatus.INACTIVE: IntegrationStatus.INACTIVE,
            TokenStatus.REVOKED: IntegrationStatus.REVOKED,
            TokenStatus.EXPIRED: IntegrationStatus.EXPIRED
        }
        
        integration_status = status_mapping.get(script_token.status, IntegrationStatus.NOT_INTEGRATED)
        
        return {
            'status': integration_status,
            'has_token': True,
            'token_info': script_token.to_dict()
        }
    
    def _clear_website_cache(self):
        """
        Clear website-related cache entries
        """
        try:
            # Clear all website cache entries
            pattern = f"{self.cache_prefix}*"
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
        except Exception as e:
            current_app.logger.warning(f"Failed to clear website cache: {e}")


# Global instance
website_service = None


def init_website_service(redis_client: redis.Redis):
    """Initialize the website service"""
    global website_service
    website_service = WebsiteService(redis_client)
    return website_service


def get_website_service() -> Optional[WebsiteService]:
    """Get the global website service instance"""
    return website_service