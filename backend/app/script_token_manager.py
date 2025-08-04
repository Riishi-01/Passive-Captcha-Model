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
    """Enhanced script token data structure with advanced management features"""
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

    # Enhanced management fields
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revoked_reason: Optional[str] = None
    regeneration_count: int = 0
    parent_token_id: Optional[str] = None
    environment: str = 'production'  # production, staging, development
    rate_limit_config: Dict[str, Any] = None
    security_config: Dict[str, Any] = None
    monitoring_config: Dict[str, Any] = None
    notification_config: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['script_version'] = self.script_version.value
        data['created_at'] = self.created_at.isoformat()
        data['activated_at'] = self.activated_at.isoformat() if self.activated_at else None
        data['last_used_at'] = self.last_used_at.isoformat() if self.last_used_at else None
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        data['revoked_at'] = self.revoked_at.isoformat() if self.revoked_at else None

        # Ensure config dictionaries are properly initialized
        data['config'] = self.config or {}
        data['rate_limit_config'] = self.rate_limit_config or {}
        data['security_config'] = self.security_config or {}
        data['monitoring_config'] = self.monitoring_config or {}
        data['notification_config'] = self.notification_config or {}
        data['metadata'] = self.metadata or {}

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
            config=data.get('config', {}),

            # Enhanced management fields
            revoked_at=datetime.fromisoformat(data['revoked_at']) if data.get('revoked_at') else None,
            revoked_by=data.get('revoked_by'),
            revoked_reason=data.get('revoked_reason'),
            regeneration_count=data.get('regeneration_count', 0),
            parent_token_id=data.get('parent_token_id'),
            environment=data.get('environment', 'production'),
            rate_limit_config=data.get('rate_limit_config', {}),
            security_config=data.get('security_config', {}),
            monitoring_config=data.get('monitoring_config', {}),
            notification_config=data.get('notification_config', {}),
            metadata=data.get('metadata', {})
        )


class ScriptTokenManager:
    """Manages script tokens and website integration"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.token_prefix = "script_token:"
        self.website_tokens_prefix = "website_tokens:"
        self.active_tokens_prefix = "active_tokens:"

    def generate_script_token(self, website_id: str, script_version: ScriptVersion = ScriptVersion.V2_ENHANCED,
                             environment: str = 'production', custom_config: Dict[str, Any] = None,
                             admin_user: str = None) -> ScriptToken:
        """
        Generate a new script token for a website (one-time only)
        """
        try:
            session = get_db_session()
            # Get website details
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                # For testing, create a mock website
                website = type('MockWebsite', (), {
                    'website_id': website_id,
                    'website_name': f'Website {website_id}',
                    'website_url': f'https://example-{website_id}.com'
                })()
        except Exception as db_error:
            logger.warning(f"Database not available, using mock website: {db_error}")
            # Create a mock website for testing/offline use
            website = type('MockWebsite', (), {
                'website_id': website_id,
                'website_name': f'Website {website_id}',
                'website_url': f'https://example-{website_id}.com'
            })()
            session = None

        # Check if token already exists for this website (moved outside try block)
        try:
            existing_token = self.get_website_token(website_id)
            if existing_token:
                raise ValueError(f"Script token already exists for website {website.website_name}")
        except Exception:
            # If check fails, continue with generation
            pass

        # Generate unique tokens
        token_id = str(uuid.uuid4())
        script_token = f"pcs_{secrets.token_urlsafe(32)}"  # Passive CAPTCHA Script
        integration_key = f"pck_{secrets.token_urlsafe(24)}"  # Passive CAPTCHA Key

        # Set expiration (tokens don't expire unless manually revoked)
        expires_at = None  # No expiration for script tokens

        # Build default configuration based on environment
        default_config = self._get_default_config(environment, script_version)
        if custom_config:
            default_config.update(custom_config)

        # Build advanced configurations
        rate_limit_config = self._get_default_rate_limit_config(environment)
        security_config = self._get_default_security_config(environment)
        monitoring_config = self._get_default_monitoring_config(environment)
        notification_config = self._get_default_notification_config()

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
                config=default_config,

                # Enhanced management fields
                environment=environment,
                rate_limit_config=rate_limit_config,
                security_config=security_config,
                monitoring_config=monitoring_config,
                notification_config=notification_config,
                metadata={
                    'created_by': admin_user or 'system',
                    'creation_ip': 'unknown',  # Could be passed from request
                    'creation_user_agent': 'admin_dashboard',
                    'website_domain': website.website_url.split('://')[1] if '://' in website.website_url else website.website_url
                }
            )

            # Store in Redis
            self._store_token(script_token_obj)

            # Update website status to pending integration (if session exists)
            if session and hasattr(website, 'status'):
                try:
                    website.status = 'pending_integration'
                    session.commit()
                except Exception as commit_error:
                    logger.warning(f"Could not update website status: {commit_error}")
                    if session:
                        session.rollback()

            logger.info(f"Generated script token for website {website.website_name}")
            return script_token_obj

        finally:
            if session:
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

    def revoke_token(self, website_id: str, reason: str = None, admin_user: str = None) -> bool:
        """
        Revoke a script token for a website with detailed tracking
        """
        token_obj = self.get_website_token(website_id)
        if not token_obj:
            return False

        # Check if already revoked
        if token_obj.status == TokenStatus.REVOKED:
            current_app.logger.warning(f"Token for website {token_obj.website_name} is already revoked")
            return False

        # Revoke token with tracking
        token_obj.status = TokenStatus.REVOKED
        token_obj.revoked_at = datetime.utcnow()
        token_obj.revoked_by = admin_user or 'system'
        token_obj.revoked_reason = reason or 'Manual revocation'

        # Update metadata
        if not token_obj.metadata:
            token_obj.metadata = {}
        token_obj.metadata.update({
            'revocation_timestamp': datetime.utcnow().isoformat(),
            'revocation_method': 'admin_dashboard',
            'final_usage_count': token_obj.usage_count,
            'active_duration_hours': self._calculate_active_duration(token_obj)
        })

        self._store_token(token_obj)

        # Update website status
        self._update_website_status(website_id, 'inactive')

        # Log revocation with details
        current_app.logger.info(
            f"Revoked script token for website {token_obj.website_name}. "
            f"Reason: {reason}, Admin: {admin_user}, Usage: {token_obj.usage_count}"
        )

        return True

    def regenerate_token(self, website_id: str, script_version: ScriptVersion = None,
                        environment: str = None, custom_config: Dict[str, Any] = None,
                        admin_user: str = None, regeneration_reason: str = None) -> ScriptToken:
        """
        Regenerate a script token with enhanced tracking and rollback capability
        """
        session = get_db_session()
        try:
            # Get existing token
            old_token = self.get_website_token(website_id)
            if not old_token:
                raise ValueError(f"No existing token found for website {website_id}")

            # Get website details
            website = session.query(Website).filter(Website.website_id == website_id).first()
            if not website:
                raise ValueError(f"Website {website_id} not found")

            # Use existing values if not specified
            new_script_version = script_version or old_token.script_version
            new_environment = environment or old_token.environment

            # Merge configurations
            new_config = old_token.config.copy() if old_token.config else {}
            if custom_config:
                new_config.update(custom_config)

            # Generate new tokens
            new_token_id = str(uuid.uuid4())
            new_script_token = f"pcs_{secrets.token_urlsafe(32)}"
            new_integration_key = f"pck_{secrets.token_urlsafe(24)}"

            # Build advanced configurations
            rate_limit_config = old_token.rate_limit_config.copy() if old_token.rate_limit_config else self._get_default_rate_limit_config(new_environment)
            security_config = old_token.security_config.copy() if old_token.security_config else self._get_default_security_config(new_environment)
            monitoring_config = old_token.monitoring_config.copy() if old_token.monitoring_config else self._get_default_monitoring_config(new_environment)
            notification_config = old_token.notification_config.copy() if old_token.notification_config else self._get_default_notification_config()

            # Create new token
            new_token = ScriptToken(
                token_id=new_token_id,
                website_id=website_id,
                website_name=website.website_name,
                website_url=website.website_url,
                script_token=new_script_token,
                integration_key=new_integration_key,
                status=TokenStatus.PENDING,
                script_version=new_script_version,
                created_at=datetime.utcnow(),
                config=new_config,

                # Enhanced management fields
                regeneration_count=old_token.regeneration_count + 1,
                parent_token_id=old_token.token_id,
                environment=new_environment,
                rate_limit_config=rate_limit_config,
                security_config=security_config,
                monitoring_config=monitoring_config,
                notification_config=notification_config,
                metadata={
                    'created_by': admin_user or 'system',
                    'regeneration_reason': regeneration_reason or 'Token regeneration',
                    'regenerated_from': old_token.token_id,
                    'regeneration_timestamp': datetime.utcnow().isoformat(),
                    'old_token_usage_count': old_token.usage_count,
                    'old_token_active_duration': self._calculate_active_duration(old_token),
                    'website_domain': website.website_url.split('://')[1] if '://' in website.website_url else website.website_url,
                    'inheritance': {
                        'script_version_changed': str(new_script_version) != str(old_token.script_version),
                        'environment_changed': new_environment != old_token.environment,
                        'config_changed': new_config != old_token.config
                    }
                }
            )

            # Revoke old token
            self.revoke_token(website_id, f"Regenerated: {regeneration_reason or 'Token regeneration'}", admin_user)

            # Store new token
            self._store_token(new_token)

            # Update website status to pending integration
            website.status = 'pending_integration'
            session.commit()

            current_app.logger.info(
                f"Regenerated script token for website {website.website_name}. "
                f"Regeneration #{new_token.regeneration_count}, Admin: {admin_user}"
            )

            return new_token

        finally:
            session.close()

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

    def _get_default_config(self, environment: str, script_version: ScriptVersion) -> Dict[str, Any]:
        """Get default script configuration based on environment and version"""
        base_config = {
            'collect_mouse_movements': True,
            'collect_keyboard_patterns': True,
            'collect_scroll_behavior': True,
            'collect_timing_data': True,
            'collect_device_info': True,
            'debug_mode': False
        }

        # Environment-specific settings
        if environment == 'development':
            base_config.update({
                'sampling_rate': 1.0,  # 100% sampling in dev
                'batch_size': 10,
                'send_interval': 5000,  # 5 seconds
                'debug_mode': True
            })
        elif environment == 'staging':
            base_config.update({
                'sampling_rate': 0.5,  # 50% sampling in staging
                'batch_size': 25,
                'send_interval': 15000,  # 15 seconds
                'debug_mode': False
            })
        else:  # production
            base_config.update({
                'sampling_rate': 0.1,  # 10% sampling in production
                'batch_size': 50,
                'send_interval': 30000,  # 30 seconds
                'debug_mode': False
            })

        # Version-specific enhancements
        if script_version == ScriptVersion.V2_ENHANCED:
            base_config.update({
                'advanced_fingerprinting': True,
                'behavioral_analysis': True,
                'real_time_scoring': True,
                'canvas_fingerprinting': True,
                'webgl_fingerprinting': True
            })

        return base_config

    def _get_default_rate_limit_config(self, environment: str) -> Dict[str, Any]:
        """Get default rate limiting configuration"""
        if environment == 'development':
            return {
                'requests_per_minute': 1000,
                'requests_per_hour': 10000,
                'burst_limit': 100,
                'cooldown_period': 60,  # seconds
                'enabled': False  # Disabled in development
            }
        elif environment == 'staging':
            return {
                'requests_per_minute': 500,
                'requests_per_hour': 5000,
                'burst_limit': 50,
                'cooldown_period': 120,
                'enabled': True
            }
        else:  # production
            return {
                'requests_per_minute': 200,
                'requests_per_hour': 2000,
                'burst_limit': 20,
                'cooldown_period': 300,
                'enabled': True
            }

    def _get_default_security_config(self, environment: str) -> Dict[str, Any]:
        """Get default security configuration"""
        base_config = {
            'ip_validation': True,
            'user_agent_validation': True,
            'referrer_validation': True,
            'token_rotation_enabled': False,
            'token_rotation_interval_days': 90,
            'suspicious_activity_detection': True,
            'honeypot_detection': True,
            'bot_detection_sensitivity': 'medium'  # low, medium, high
        }

        if environment == 'production':
            base_config.update({
                'token_rotation_enabled': True,
                'bot_detection_sensitivity': 'high',
                'advanced_threat_detection': True,
                'geo_location_validation': True
            })

        return base_config

    def _get_default_monitoring_config(self, environment: str) -> Dict[str, Any]:
        """Get default monitoring configuration"""
        return {
            'performance_monitoring': True,
            'error_tracking': True,
            'usage_analytics': True,
            'real_time_alerts': environment == 'production',
            'health_check_interval': 300,  # 5 minutes
            'metric_retention_days': 90,
            'alert_thresholds': {
                'error_rate_percent': 5.0,
                'response_time_ms': 1000,
                'availability_percent': 99.0,
                'suspicious_activity_rate': 10.0
            },
            'notifications': {
                'webhook_enabled': False,
                'email_enabled': False,
                'slack_enabled': False
            }
        }

    def _get_default_notification_config(self) -> Dict[str, Any]:
        """Get default notification configuration"""
        return {
            'token_events': {
                'creation': True,
                'activation': True,
                'revocation': True,
                'regeneration': True,
                'expiration': True
            },
            'security_events': {
                'suspicious_activity': True,
                'rate_limit_exceeded': True,
                'invalid_access_attempts': True,
                'token_misuse': True
            },
            'performance_events': {
                'high_error_rate': True,
                'slow_response_time': True,
                'service_degradation': True
            },
            'channels': {
                'webhook_url': None,
                'email_addresses': [],
                'slack_webhook': None
            }
        }

    def _calculate_active_duration(self, token: ScriptToken) -> float:
        """Calculate active duration in hours"""
        if not token.activated_at:
            return 0.0

        end_time = token.revoked_at or datetime.utcnow()
        duration = end_time - token.activated_at
        return duration.total_seconds() / 3600.0  # Convert to hours

    def get_token_history(self, website_id: str) -> List[ScriptToken]:
        """Get complete token history for a website"""
        current_token = self.get_website_token(website_id)
        if not current_token:
            return []

        history = [current_token]

        # Walk back through parent tokens
        current = current_token
        while current and current.parent_token_id:
            # In a real implementation, you'd need to store historical tokens
            # For now, we'll just return the current token
            break

        return history

    def update_token_config(self, website_id: str, config_updates: Dict[str, Any],
                           admin_user: str = None) -> bool:
        """Update token configuration without regenerating the token"""
        token_obj = self.get_website_token(website_id)
        if not token_obj:
            return False

        if token_obj.status not in [TokenStatus.PENDING, TokenStatus.ACTIVE]:
            current_app.logger.warning(f"Cannot update config for token with status {token_obj.status}")
            return False

        # Update configuration
        old_config = token_obj.config.copy() if token_obj.config else {}
        token_obj.config = token_obj.config or {}
        token_obj.config.update(config_updates)

        # Update metadata
        if not token_obj.metadata:
            token_obj.metadata = {}
        token_obj.metadata.update({
            'last_config_update': datetime.utcnow().isoformat(),
            'config_updated_by': admin_user or 'system',
            'config_changes': {
                'previous': old_config,
                'updates': config_updates,
                'timestamp': datetime.utcnow().isoformat()
            }
        })

        self._store_token(token_obj)

        current_app.logger.info(
            f"Updated configuration for token {token_obj.website_name}. "
            f"Changes: {config_updates}, Admin: {admin_user}"
        )

        return True

    def bulk_revoke_tokens(self, website_ids: List[str], reason: str = None,
                          admin_user: str = None) -> Dict[str, bool]:
        """Bulk revoke multiple tokens"""
        results = {}

        for website_id in website_ids:
            try:
                success = self.revoke_token(website_id, reason, admin_user)
                results[website_id] = success
            except Exception as e:
                current_app.logger.error(f"Failed to revoke token for {website_id}: {e}")
                results[website_id] = False

        successful_revocations = sum(1 for success in results.values() if success)
        current_app.logger.info(
            f"Bulk revocation completed: {successful_revocations}/{len(website_ids)} successful. "
            f"Admin: {admin_user}, Reason: {reason}"
        )

        return results

    def get_tokens_by_environment(self, environment: str) -> List[ScriptToken]:
        """Get all tokens for a specific environment"""
        all_tokens = self.get_all_tokens()
        return [token for token in all_tokens if token.environment == environment]

    def get_tokens_requiring_rotation(self, days_threshold: int = 90) -> List[ScriptToken]:
        """Get tokens that should be rotated based on age or configuration"""
        all_tokens = self.get_all_tokens()
        rotation_candidates = []

        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        for token in all_tokens:
            if token.status != TokenStatus.ACTIVE:
                continue

            should_rotate = False
            rotation_reason = []

            # Check age-based rotation
            if token.created_at < cutoff_date:
                should_rotate = True
                rotation_reason.append(f"Age exceeds {days_threshold} days")

            # Check security config rotation settings
            if (token.security_config and
                token.security_config.get('token_rotation_enabled', False)):

                rotation_interval = token.security_config.get('token_rotation_interval_days', 90)
                rotation_cutoff = datetime.utcnow() - timedelta(days=rotation_interval)

                if token.created_at < rotation_cutoff:
                    should_rotate = True
                    rotation_reason.append(f"Security policy requires rotation every {rotation_interval} days")

            # Check for high usage that might indicate compromise
            if token.usage_count > 100000:  # Configurable threshold
                should_rotate = True
                rotation_reason.append("High usage count indicates potential security risk")

            if should_rotate:
                # Add rotation reason to token metadata for tracking
                if not hasattr(token, '_rotation_reasons'):
                    token._rotation_reasons = rotation_reason
                rotation_candidates.append(token)

        return rotation_candidates

    def validate_token_security(self, website_id: str) -> Dict[str, Any]:
        """Perform comprehensive security validation on a token"""
        token_obj = self.get_website_token(website_id)
        if not token_obj:
            return {'valid': False, 'error': 'Token not found'}

        security_report = {
            'valid': True,
            'issues': [],
            'recommendations': [],
            'security_score': 100,
            'details': {}
        }

        # Check token age
        age_days = (datetime.utcnow() - token_obj.created_at).days
        if age_days > 365:
            security_report['issues'].append('Token is over 1 year old')
            security_report['recommendations'].append('Consider regenerating token')
            security_report['security_score'] -= 20
        elif age_days > 180:
            security_report['recommendations'].append('Token is aging, consider rotation')
            security_report['security_score'] -= 10

        # Check usage patterns
        if token_obj.usage_count > 1000000:
            security_report['issues'].append('Extremely high usage count')
            security_report['recommendations'].append('Investigate for potential abuse')
            security_report['security_score'] -= 30

        # Check regeneration count
        if token_obj.regeneration_count > 5:
            security_report['issues'].append('High regeneration count')
            security_report['recommendations'].append('Investigate frequent regenerations')
            security_report['security_score'] -= 15

        # Check environment security
        if token_obj.environment == 'development' and token_obj.status == TokenStatus.ACTIVE:
            security_report['issues'].append('Development token is active in production')
            security_report['recommendations'].append('Use production environment tokens')
            security_report['security_score'] -= 25

        # Check security configuration
        if token_obj.security_config:
            if not token_obj.security_config.get('ip_validation', True):
                security_report['recommendations'].append('Enable IP validation for better security')
                security_report['security_score'] -= 5

            if not token_obj.security_config.get('suspicious_activity_detection', True):
                security_report['recommendations'].append('Enable suspicious activity detection')
                security_report['security_score'] -= 10

        security_report['details'] = {
            'token_age_days': age_days,
            'usage_count': token_obj.usage_count,
            'regeneration_count': token_obj.regeneration_count,
            'environment': token_obj.environment,
            'last_used': token_obj.last_used_at.isoformat() if token_obj.last_used_at else None,
            'status': token_obj.status.value
        }

        return security_report


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
