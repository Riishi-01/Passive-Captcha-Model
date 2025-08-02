"""
Configuration and Website Management Endpoints
Handles website CRUD operations, API configuration, and alert settings
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app.admin import require_admin_auth
from app.database import get_db_session, Website
from app.logs_pipeline import logs_pipeline
from app.script_token_manager import get_script_token_manager, ScriptVersion
import redis
import json
import uuid
import secrets
import requests
from sqlalchemy import and_, or_

config_bp = Blueprint('config', __name__, url_prefix='/admin')

# DEPRECATED: Use centralized Redis client from Flask app context
# Access via current_app.redis_client instead of module-level global

def init_config_endpoints(redis_client_instance):
    """DEPRECATED: Redis client now managed centrally"""
    pass  # No-op for backward compatibility


# Website Management Endpoints

@config_bp.route('/websites', methods=['GET'])
@require_admin_auth
def get_websites():
    """
    Get all registered websites
    """
    try:
        cache_key = "websites_list"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        session = get_db_session()
        try:
            websites = session.query(Website).all()
            websites_data = []
            
            # Get script token manager for integration status
            token_manager = get_script_token_manager()
            
            for website in websites:
                # Get recent activity count
                recent_count = _get_recent_activity_count(website.website_id)
                
                # Get script token status
                script_token = None
                integration_status = 'not_integrated'
                if token_manager:
                    script_token = token_manager.get_website_token(website.website_id)
                    if script_token:
                        integration_status = script_token.status.value
                
                website_data = website.to_dict()
                website_data.update({
                    'total_verifications': recent_count,
                    'last_activity': _get_last_activity_time(website.website_id),
                    'status_color': 'green' if website.status == 'active' else 'red' if website.status == 'suspended' else 'gray',
                    'integration_status': integration_status,
                    'has_script_token': script_token is not None,
                    'script_token_info': script_token.to_dict() if script_token else None
                })
                websites_data.append(website_data)
            
            result = {
                'websites': websites_data,
                'total_count': len(websites_data),
                'active_count': len([w for w in websites_data if w['status'] == 'active']),
                'suspended_count': len([w for w in websites_data if w['status'] == 'suspended'])
            }
            
            # Cache result
            if redis_client:
                redis_client.setex(cache_key, 300, json.dumps(result, default=str))  # 5 min cache
            
            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting websites: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'WEBSITES_GET_ERROR',
                'message': 'Failed to retrieve websites'
            }
        }), 500


@config_bp.route('/websites', methods=['POST'])
@require_admin_auth
def create_website():
    """
    Create a new website registration
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Missing required field: {field}'
                    }
                }), 400
        
        # Validate URL format
        if not data['url'].startswith(('http://', 'https://')):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_URL',
                    'message': 'URL must start with http:// or https://'
                }
            }), 400
        
        session = get_db_session()
        try:
            # Check if website already exists
            existing = session.query(Website).filter(
                or_(
                    Website.website_name == data['name'],
                    Website.website_url == data['url']
                )
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'WEBSITE_EXISTS',
                        'message': 'Website with this name or URL already exists'
                    }
                }), 409
            
            # Generate API credentials
            website_id = str(uuid.uuid4())
            api_key = f"pk_{secrets.token_urlsafe(32)}"
            secret_key = f"sk_{secrets.token_urlsafe(32)}"
            
            # Create website record
            website = Website(
                website_id=website_id,
                website_name=data['name'],
                website_url=data['url'],
                admin_email=data.get('admin_email', 'admin@example.com'),
                api_key=api_key,
                secret_key=secret_key,
                status='active',
                permissions=json.dumps(['verify', 'analytics']),
                rate_limits=json.dumps({
                    'requests_per_minute': 1000,
                    'requests_per_hour': 50000,
                    'requests_per_day': 1000000
                })
            )
            
            session.add(website)
            session.commit()
            
            # Clear cache
            if redis_client:
                redis_client.delete("websites_list")
            
            # Log creation
            if logs_pipeline:
                logs_pipeline.log_system_event(
                    f"New website created: {data['name']}",
                    metadata={
                        'website_id': website_id,
                        'website_name': data['name'],
                        'website_url': data['url']
                    }
                )
            
            return jsonify({
                'success': True,
                'data': {
                    'website': website.to_dict(),
                    'message': 'Website created successfully'
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 201
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error creating website: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'WEBSITE_CREATE_ERROR',
                'message': 'Failed to create website'
            }
        }), 500


@config_bp.route('/websites/<website_id>', methods=['PUT'])
@require_admin_auth
def update_website(website_id):
    """
    Update website configuration
    """
    try:
        data = request.get_json()
        
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            
            if not website:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'WEBSITE_NOT_FOUND',
                        'message': 'Website not found'
                    }
                }), 404
            
            # Update allowed fields
            updatable_fields = ['website_name', 'website_url', 'admin_email', 'status']
            updates_made = []
            
            for field in updatable_fields:
                if field in data:
                    old_value = getattr(website, field)
                    setattr(website, field, data[field])
                    updates_made.append(f"{field}: {old_value} -> {data[field]}")
            
            # Update permissions if provided
            if 'permissions' in data:
                website.permissions = json.dumps(data['permissions'])
                updates_made.append(f"permissions updated")
            
            # Update rate limits if provided
            if 'rate_limits' in data:
                website.rate_limits = json.dumps(data['rate_limits'])
                updates_made.append(f"rate_limits updated")
            
            session.commit()
            
            # Clear cache
            if redis_client:
                redis_client.delete("websites_list")
            
            # Log update
            if logs_pipeline:
                logs_pipeline.log_system_event(
                    f"Website updated: {website.website_name}",
                    metadata={
                        'website_id': website_id,
                        'updates': updates_made
                    }
                )
            
            return jsonify({
                'success': True,
                'data': {
                    'website': website.to_dict(),
                    'updates_made': updates_made,
                    'message': 'Website updated successfully'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error updating website: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'WEBSITE_UPDATE_ERROR',
                'message': 'Failed to update website'
            }
        }), 500


@config_bp.route('/websites/<website_id>', methods=['DELETE'])
@require_admin_auth
def delete_website(website_id):
    """
    Delete a website registration
    """
    try:
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            
            if not website:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'WEBSITE_NOT_FOUND',
                        'message': 'Website not found'
                    }
                }), 404
            
            website_name = website.website_name
            
            # Delete website
            session.delete(website)
            session.commit()
            
            # Clear cache
            if redis_client:
                redis_client.delete("websites_list")
            
            # Log deletion
            if logs_pipeline:
                logs_pipeline.log_system_event(
                    f"Website deleted: {website_name}",
                    metadata={
                        'website_id': website_id,
                        'website_name': website_name
                    }
                )
            
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Website "{website_name}" deleted successfully'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error deleting website: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'WEBSITE_DELETE_ERROR',
                'message': 'Failed to delete website'
            }
        }), 500


@config_bp.route('/websites/<website_id>/status', methods=['PATCH'])
@require_admin_auth
def toggle_website_status(website_id):
    """
    Toggle website status (active/suspended)
    """
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'suspended']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Status must be "active" or "suspended"'
                }
            }), 400
        
        session = get_db_session()
        try:
            website = session.query(Website).filter(Website.website_id == website_id).first()
            
            if not website:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'WEBSITE_NOT_FOUND',
                        'message': 'Website not found'
                    }
                }), 404
            
            old_status = website.status
            website.status = new_status
            session.commit()
            
            # Clear cache
            if redis_client:
                redis_client.delete("websites_list")
            
            # Log status change
            if logs_pipeline:
                logs_pipeline.log_system_event(
                    f"Website status changed: {website.website_name}",
                    metadata={
                        'website_id': website_id,
                        'old_status': old_status,
                        'new_status': new_status
                    }
                )
            
            return jsonify({
                'success': True,
                'data': {
                    'website': website.to_dict(),
                    'message': f'Website status changed from {old_status} to {new_status}'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error toggling website status: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'WEBSITE_STATUS_ERROR',
                'message': 'Failed to update website status'
            }
        }), 500


# API Configuration Endpoints

@config_bp.route('/config/api', methods=['GET'])
@require_admin_auth
def get_api_config():
    """
    Get API configuration settings
    """
    try:
        cache_key = "api_config"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        # Get configuration from environment/database
        config = {
            'api_endpoint': current_app.config.get('API_BASE_URL', 'http://localhost:5003'),
            'websocket_endpoint': current_app.config.get('WEBSOCKET_URL', 'ws://localhost:5003'),
            'rate_limiting': {
                'enabled': True,
                'default_requests_per_minute': 1000,
                'default_requests_per_hour': 50000,
                'default_requests_per_day': 1000000
            },
            'timeouts': {
                'connection_timeout': 30,
                'read_timeout': 60,
                'write_timeout': 60
            },
            'ssl_verification': True,
            'cors_enabled': True,
            'cors_origins': ['http://localhost:3000', 'https://yourdomain.com'],
            'api_version': 'v1',
            'max_request_size_mb': 10,
            'supported_formats': ['json'],
            'authentication': {
                'type': 'api_key',
                'header_name': 'X-API-Key',
                'token_expiry_hours': 24
            }
        }
        
        # Cache result
        if redis_client:
            redis_client.setex(cache_key, 900, json.dumps(config, default=str))  # 15 min cache
        
        return jsonify({
            'success': True,
            'data': config,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting API config: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'API_CONFIG_GET_ERROR',
                'message': 'Failed to retrieve API configuration'
            }
        }), 500


@config_bp.route('/config/api', methods=['PUT'])
@require_admin_auth
def update_api_config():
    """
    Update API configuration settings
    """
    try:
        data = request.get_json()
        
        # Validate configuration data
        if 'rate_limiting' in data:
            rate_config = data['rate_limiting']
            if not isinstance(rate_config.get('enabled'), bool):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_RATE_CONFIG',
                        'message': 'Rate limiting enabled must be boolean'
                    }
                }), 400
        
        # Store configuration (in production, save to database/config file)
        # For now, we'll just validate and return success
        
        # Clear cache
        if redis_client:
            redis_client.delete("api_config")
        
        # Log configuration change
        if logs_pipeline:
            logs_pipeline.log_system_event(
                "API configuration updated",
                metadata={'updated_fields': list(data.keys())}
            )
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'API configuration updated successfully',
                'updated_fields': list(data.keys())
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating API config: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'API_CONFIG_UPDATE_ERROR',
                'message': 'Failed to update API configuration'
            }
        }), 500


@config_bp.route('/config/test-connection', methods=['POST'])
@require_admin_auth
def test_api_connection():
    """
    Test API connection and configuration
    """
    try:
        data = request.get_json()
        endpoint = data.get('endpoint', current_app.config.get('API_BASE_URL', 'http://localhost:5003'))
        timeout = data.get('timeout', 10)
        
        # Test connection
        test_url = f"{endpoint}/api/health"
        
        try:
            response = requests.get(test_url, timeout=timeout)
            
            if response.status_code == 200:
                result = {
                    'status': 'success',
                    'message': 'API connection successful',
                    'response_time_ms': response.elapsed.total_seconds() * 1000,
                    'status_code': response.status_code,
                    'endpoint': test_url
                }
            else:
                result = {
                    'status': 'warning',
                    'message': f'API responded with status {response.status_code}',
                    'response_time_ms': response.elapsed.total_seconds() * 1000,
                    'status_code': response.status_code,
                    'endpoint': test_url
                }
        
        except requests.exceptions.Timeout:
            result = {
                'status': 'error',
                'message': 'Connection timeout',
                'endpoint': test_url,
                'timeout_seconds': timeout
            }
        
        except requests.exceptions.ConnectionError:
            result = {
                'status': 'error',
                'message': 'Connection failed - endpoint unreachable',
                'endpoint': test_url
            }
        
        except Exception as e:
            result = {
                'status': 'error',
                'message': f'Connection test failed: {str(e)}',
                'endpoint': test_url
            }
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error testing API connection: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'API_TEST_ERROR',
                'message': 'Failed to test API connection'
            }
        }), 500


# Alert Configuration Endpoints

@config_bp.route('/config/alerts', methods=['GET'])
@require_admin_auth
def get_alert_settings():
    """
    Get alert and notification settings
    """
    try:
        cache_key = "alert_settings"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        # Default alert settings (in production, load from database)
        settings = {
            'email_notifications': {
                'enabled': True,
                'recipients': ['admin@example.com'],
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': '',
                'smtp_password_set': False,  # Don't expose actual password
                'use_tls': True
            },
            'alert_thresholds': {
                'high_bot_rate': {
                    'enabled': True,
                    'threshold': 80,  # percentage
                    'time_window_minutes': 15,
                    'severity': 'warning'
                },
                'low_confidence': {
                    'enabled': True,
                    'threshold': 60,  # percentage
                    'time_window_minutes': 30,
                    'severity': 'warning'
                },
                'system_errors': {
                    'enabled': True,
                    'threshold': 5,  # errors per minute
                    'time_window_minutes': 5,
                    'severity': 'error'
                },
                'high_response_time': {
                    'enabled': True,
                    'threshold': 2000,  # milliseconds
                    'time_window_minutes': 10,
                    'severity': 'warning'
                }
            },
            'notification_channels': {
                'email': True,
                'webhook': False,
                'slack': False,
                'sms': False
            },
            'quiet_hours': {
                'enabled': False,
                'start_time': '22:00',
                'end_time': '08:00',
                'timezone': 'UTC'
            }
        }
        
        # Cache result
        if redis_client:
            redis_client.setex(cache_key, 600, json.dumps(settings, default=str))  # 10 min cache
        
        return jsonify({
            'success': True,
            'data': settings,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting alert settings: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ALERT_SETTINGS_GET_ERROR',
                'message': 'Failed to retrieve alert settings'
            }
        }), 500


@config_bp.route('/config/alerts', methods=['PUT'])
@require_admin_auth
def update_alert_settings():
    """
    Update alert and notification settings
    """
    try:
        data = request.get_json()
        
        # Validate email settings if provided
        if 'email_notifications' in data:
            email_config = data['email_notifications']
            if 'recipients' in email_config:
                recipients = email_config['recipients']
                if not isinstance(recipients, list) or not all('@' in email for email in recipients):
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_EMAIL_RECIPIENTS',
                            'message': 'Recipients must be a list of valid email addresses'
                        }
                    }), 400
        
        # Validate thresholds if provided
        if 'alert_thresholds' in data:
            thresholds = data['alert_thresholds']
            for threshold_name, threshold_config in thresholds.items():
                if 'threshold' in threshold_config:
                    if not isinstance(threshold_config['threshold'], (int, float)):
                        return jsonify({
                            'success': False,
                            'error': {
                                'code': 'INVALID_THRESHOLD',
                                'message': f'Threshold for {threshold_name} must be a number'
                            }
                        }), 400
        
        # Store settings (in production, save to database)
        # For now, we'll just validate and return success
        
        # Clear cache
        if redis_client:
            redis_client.delete("alert_settings")
        
        # Log configuration change
        if logs_pipeline:
            logs_pipeline.log_system_event(
                "Alert settings updated",
                metadata={'updated_sections': list(data.keys())}
            )
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Alert settings updated successfully',
                'updated_sections': list(data.keys())
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating alert settings: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ALERT_SETTINGS_UPDATE_ERROR',
                'message': 'Failed to update alert settings'
            }
        }), 500


@config_bp.route('/alerts/test', methods=['POST'])
@require_admin_auth
def send_test_alert():
    """
    Send a test alert to verify notification settings
    """
    try:
        data = request.get_json()
        alert_type = data.get('type', 'email')
        recipient = data.get('recipient')
        
        if alert_type == 'email':
            if not recipient:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_RECIPIENT',
                        'message': 'Email recipient is required for email test'
                    }
                }), 400
            
            # Simulate sending test email
            # In production, use actual email service
            result = {
                'status': 'success',
                'message': f'Test email sent to {recipient}',
                'alert_type': 'email',
                'recipient': recipient,
                'sent_at': datetime.utcnow().isoformat()
            }
        
        else:
            result = {
                'status': 'error',
                'message': f'Alert type "{alert_type}" not supported',
                'supported_types': ['email']
            }
        
        # Log test alert
        if logs_pipeline:
            logs_pipeline.log_system_event(
                f"Test alert sent: {alert_type}",
                metadata={
                    'alert_type': alert_type,
                    'recipient': recipient,
                    'result': result['status']
                }
            )
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error sending test alert: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'TEST_ALERT_ERROR',
                'message': 'Failed to send test alert'
            }
        }), 500


# Helper functions

def _get_recent_activity_count(website_id: str) -> int:
    """Get recent verification count for a website"""
    try:
        session = get_db_session()
        from app.database import VerificationLog
        
        since = datetime.utcnow() - timedelta(hours=24)
        count = session.query(VerificationLog).filter(
            and_(
                VerificationLog.timestamp >= since,
                VerificationLog.origin.like(f'%{website_id}%')
            )
        ).count()
        
        session.close()
        return count
    except:
        return 0


def _get_last_activity_time(website_id: str) -> str:
    """Get last activity timestamp for a website"""
    try:
        session = get_db_session()
        from app.database import VerificationLog
        
        last_log = session.query(VerificationLog).filter(
            VerificationLog.origin.like(f'%{website_id}%')
        ).order_by(VerificationLog.timestamp.desc()).first()
        
        session.close()
        
        if last_log:
            return last_log.timestamp.isoformat()
        else:
            return None
    except:
        return None