"""
Script Token Management Endpoints for Admin Dashboard
Handles script token generation, management, and monitoring
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app.admin import require_admin_auth
from app.script_token_manager import get_script_token_manager, ScriptVersion, TokenStatus
from app.database import get_db_session, Website
from app.logs_pipeline import logs_pipeline, LogLevel
import redis
import json

script_mgmt_bp = Blueprint('script_mgmt', __name__, url_prefix='/admin/scripts')

# Redis client for caching
redis_client = None

def init_script_management(redis_client_instance):
    """Initialize script management endpoints with Redis client"""
    global redis_client
    redis_client = redis_client_instance


@script_mgmt_bp.route('/generate', methods=['POST'])
@require_admin_auth
def generate_script_token():
    """
    Generate a script token for a website (one-time only)
    """
    try:
        data = request.get_json()
        website_id = data.get('website_id')
        script_version = data.get('script_version', 'v2_enhanced')
        
        if not website_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_WEBSITE_ID',
                    'message': 'Website ID is required'
                }
            }), 400
        
        # Validate script version
        try:
            version_enum = ScriptVersion(script_version)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_SCRIPT_VERSION',
                    'message': f'Invalid script version. Valid options: {[v.value for v in ScriptVersion]}'
                }
            }), 400
        
        # Get token manager
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Script token manager not available'
                }
            }), 503
        
        try:
            # Generate script token
            script_token = token_manager.generate_script_token(website_id, version_enum)
            
            # Generate integration instructions
            api_base = current_app.config.get('API_BASE_URL', request.host_url.rstrip('/'))
            script_url = f"{api_base}/api/script/generate?token={script_token.script_token}"
            
            integration_code = f'''
<!-- Passive CAPTCHA Integration -->
<script>
(function() {{
    var script = document.createElement('script');
    script.src = '{script_url}';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
}})();
</script>
<!-- End Passive CAPTCHA -->
'''
            
            return jsonify({
                'success': True,
                'data': {
                    'token': script_token.to_dict(),
                    'integration': {
                        'script_url': script_url,
                        'integration_code': integration_code.strip(),
                        'instructions': [
                            'Copy the integration code below',
                            'Paste it in the <head> section of your website',
                            'The script will automatically start collecting data',
                            'Monitor the dashboard for real-time analytics'
                        ]
                    },
                    'message': 'Script token generated successfully'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TOKEN_GENERATION_FAILED',
                    'message': str(e)
                }
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error generating script token: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to generate script token'
            }
        }), 500


@script_mgmt_bp.route('/tokens', methods=['GET'])
@require_admin_auth
def get_script_tokens():
    """
    Get all script tokens with their status
    """
    try:
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Script token manager not available'
                }
            }), 503
        
        # Get all tokens
        tokens = token_manager.get_all_tokens()
        
        # Get additional stats
        stats = token_manager.get_token_stats()
        
        # Enhance tokens with additional information
        enhanced_tokens = []
        for token in tokens:
            token_dict = token.to_dict()
            
            # Add status information
            token_dict['status_info'] = {
                'is_active': token.status == TokenStatus.ACTIVE,
                'days_since_created': (datetime.utcnow() - token.created_at).days,
                'days_since_last_used': (datetime.utcnow() - token.last_used_at).days if token.last_used_at else None,
                'integration_url': f"{current_app.config.get('API_BASE_URL', request.host_url.rstrip('/'))}/api/script/generate?token={token.script_token}"
            }
            
            enhanced_tokens.append(token_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'tokens': enhanced_tokens,
                'statistics': stats,
                'total_count': len(enhanced_tokens)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting script tokens: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve script tokens'
            }
        }), 500


@script_mgmt_bp.route('/tokens/<website_id>', methods=['GET'])
@require_admin_auth
def get_website_token(website_id):
    """
    Get script token for a specific website
    """
    try:
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Script token manager not available'
                }
            }), 503
        
        token = token_manager.get_website_token(website_id)
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TOKEN_NOT_FOUND',
                    'message': 'No script token found for this website'
                }
            }), 404
        
        # Enhance with additional information
        token_dict = token.to_dict()
        api_base = current_app.config.get('API_BASE_URL', request.host_url.rstrip('/'))
        script_url = f"{api_base}/api/script/generate?token={token.script_token}"
        
        integration_code = f'''
<!-- Passive CAPTCHA Integration -->
<script>
(function() {{
    var script = document.createElement('script');
    script.src = '{script_url}';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
}})();
</script>
<!-- End Passive CAPTCHA -->
'''
        
        token_dict['integration'] = {
            'script_url': script_url,
            'integration_code': integration_code.strip(),
            'status_check_url': f"{api_base}/api/script/health"
        }
        
        return jsonify({
            'success': True,
            'data': {
                'token': token_dict
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting website token: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve website token'
            }
        }), 500


@script_mgmt_bp.route('/tokens/<website_id>/revoke', methods=['POST'])
@require_admin_auth
def revoke_script_token(website_id):
    """
    Revoke a script token for a website
    """
    try:
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Script token manager not available'
                }
            }), 503
        
        # Get token before revoking for logging
        token = token_manager.get_website_token(website_id)
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TOKEN_NOT_FOUND',
                    'message': 'No script token found for this website'
                }
            }), 404
        
        # Revoke token
        success = token_manager.revoke_token(website_id)
        if not success:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'REVOCATION_FAILED',
                    'message': 'Failed to revoke script token'
                }
            }), 400
        
        # Log revocation
        if logs_pipeline:
            logs_pipeline.log_system_event(
                f"Script token revoked for {token.website_name}",
                LogLevel.INFO,
                website_id=website_id,
                metadata={
                    'token_id': token.token_id,
                    'revoked_by': 'admin_dashboard'
                }
            )
        
        return jsonify({
            'success': True,
            'data': {
                'message': f'Script token revoked for {token.website_name}',
                'website_id': website_id,
                'revoked_at': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error revoking script token: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to revoke script token'
            }
        }), 500


@script_mgmt_bp.route('/tokens/<website_id>/regenerate', methods=['POST'])
@require_admin_auth
def regenerate_script_token(website_id):
    """
    Regenerate a script token for a website (revoke old, create new)
    """
    try:
        data = request.get_json()
        script_version = data.get('script_version', 'v2_enhanced')
        
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Script token manager not available'
                }
            }), 503
        
        # Validate script version
        try:
            version_enum = ScriptVersion(script_version)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_SCRIPT_VERSION',
                    'message': f'Invalid script version. Valid options: {[v.value for v in ScriptVersion]}'
                }
            }), 400
        
        # Get existing token for logging
        old_token = token_manager.get_website_token(website_id)
        
        # Revoke existing token if it exists
        if old_token:
            token_manager.revoke_token(website_id)
        
        # Generate new token
        try:
            new_token = token_manager.generate_script_token(website_id, version_enum)
            
            # Generate integration instructions
            api_base = current_app.config.get('API_BASE_URL', request.host_url.rstrip('/'))
            script_url = f"{api_base}/api/script/generate?token={new_token.script_token}"
            
            integration_code = f'''
<!-- Passive CAPTCHA Integration -->
<script>
(function() {{
    var script = document.createElement('script');
    script.src = '{script_url}';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
}})();
</script>
<!-- End Passive CAPTCHA -->
'''
            
            # Log regeneration
            if logs_pipeline:
                logs_pipeline.log_system_event(
                    f"Script token regenerated for {new_token.website_name}",
                    LogLevel.INFO,
                    website_id=website_id,
                    metadata={
                        'old_token_id': old_token.token_id if old_token else None,
                        'new_token_id': new_token.token_id,
                        'regenerated_by': 'admin_dashboard'
                    }
                )
            
            return jsonify({
                'success': True,
                'data': {
                    'token': new_token.to_dict(),
                    'integration': {
                        'script_url': script_url,
                        'integration_code': integration_code.strip(),
                        'instructions': [
                            'Replace the old integration code with the new one below',
                            'Update your website with the new script URL',
                            'The old token has been revoked and will no longer work',
                            'Monitor the dashboard to verify the new integration'
                        ]
                    },
                    'message': 'Script token regenerated successfully'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TOKEN_REGENERATION_FAILED',
                    'message': str(e)
                }
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error regenerating script token: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to regenerate script token'
            }
        }), 500


@script_mgmt_bp.route('/statistics', methods=['GET'])
@require_admin_auth
def get_script_statistics():
    """
    Get comprehensive script integration statistics
    """
    try:
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Script token manager not available'
                }
            }), 503
        
        # Get basic token stats
        stats = token_manager.get_token_stats()
        
        # Get detailed usage information
        all_tokens = token_manager.get_all_tokens()
        active_tokens = [t for t in all_tokens if t.status == TokenStatus.ACTIVE]
        
        # Calculate additional metrics
        total_usage = sum(t.usage_count for t in all_tokens)
        avg_usage = total_usage / len(all_tokens) if all_tokens else 0
        
        # Usage by time periods
        now = datetime.utcnow()
        tokens_last_24h = len([t for t in all_tokens if t.last_used_at and (now - t.last_used_at).total_seconds() < 86400])
        tokens_last_week = len([t for t in all_tokens if t.last_used_at and (now - t.last_used_at).total_seconds() < 604800])
        
        # Enhanced statistics
        enhanced_stats = {
            **stats,
            'usage_metrics': {
                'total_requests': total_usage,
                'average_requests_per_token': round(avg_usage, 2),
                'tokens_used_last_24h': tokens_last_24h,
                'tokens_used_last_week': tokens_last_week,
                'most_active_token': max(all_tokens, key=lambda t: t.usage_count).to_dict() if all_tokens else None
            },
            'integration_health': {
                'healthy_integrations': len([t for t in active_tokens if t.usage_count > 0]),
                'stale_integrations': len([t for t in active_tokens if t.usage_count == 0]),
                'integration_success_rate': round((len(active_tokens) / len(all_tokens) * 100), 2) if all_tokens else 0
            }
        }
        
        return jsonify({
            'success': True,
            'data': enhanced_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting script statistics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve script statistics'
            }
        }), 500


@script_mgmt_bp.route('/cleanup', methods=['POST'])
@require_admin_auth
def cleanup_expired_tokens():
    """
    Clean up expired and stale tokens
    """
    try:
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Script token manager not available'
                }
            }), 503
        
        # Clean up expired tokens
        cleaned_count = token_manager.cleanup_expired_tokens()
        
        # Log cleanup
        if logs_pipeline:
            logs_pipeline.log_system_event(
                f"Script token cleanup completed: {cleaned_count} tokens processed",
                LogLevel.INFO,
                metadata={
                    'cleaned_tokens': cleaned_count,
                    'initiated_by': 'admin_dashboard'
                }
            )
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Token cleanup completed',
                'tokens_processed': cleaned_count,
                'cleanup_time': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error during token cleanup: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to clean up tokens'
            }
        }), 500