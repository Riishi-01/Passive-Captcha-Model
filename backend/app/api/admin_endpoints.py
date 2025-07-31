"""
Refactored Admin Endpoints
Modern, service-based admin API endpoints using centralized services
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from functools import wraps
from app.services import get_auth_service, get_website_service
from app.script_token_manager import get_script_token_manager, ScriptVersion
import traceback

admin_bp = Blueprint('admin_api', __name__, url_prefix='/admin')


def require_auth(f):
    """Decorator to require authentication for admin endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header required'
                }
            }), 401
        
        token = auth_header.split(' ')[1]
        auth_service = get_auth_service()
        
        if not auth_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Authentication service unavailable'
                }
            }), 503
        
        user = auth_service.validate_token(token)
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired token'
                }
            }), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


# Authentication Endpoints

@admin_bp.route('/login', methods=['POST'])
def login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_PASSWORD',
                    'message': 'Password is required'
                }
            }), 400
        
        auth_service = get_auth_service()
        if not auth_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Authentication service unavailable'
                }
            }), 503
        
        result = auth_service.authenticate_admin(data['password'])
        if not result:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid password'
                }
            }), 401
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Login failed'
            }
        }), 500


@admin_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Admin logout endpoint"""
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        
        auth_service = get_auth_service()
        success = auth_service.logout(token)
        
        return jsonify({
            'success': success,
            'message': 'Logged out successfully' if success else 'Logout failed'
        })
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Logout failed'
            }
        }), 500


@admin_bp.route('/verify-token', methods=['GET'])
@require_auth
def verify_token():
    """Verify token validity"""
    try:
        user = request.current_user
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'valid': True
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Token verification error: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Token verification failed'
            }
        }), 500


# Website Management Endpoints

@admin_bp.route('/websites', methods=['GET'])
@require_auth
def get_websites():
    """Get all websites with analytics and integration status"""
    try:
        website_service = get_website_service()
        if not website_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Website service unavailable'
                }
            }), 503
        
        include_analytics = request.args.get('include_analytics', 'true').lower() == 'true'
        websites = website_service.get_all_websites(include_analytics=include_analytics)
        
        return jsonify({
            'success': True,
            'data': {
                'websites': [website.to_dict() for website in websites],
                'total_count': len(websites),
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting websites: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve websites'
            }
        }), 500


@admin_bp.route('/websites', methods=['POST'])
@require_auth
def create_website():
    """Create a new website"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request data is required'
                }
            }), 400
        
        name = data.get('name')
        url = data.get('url')
        description = data.get('description', '')
        
        if not name or not url:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Name and URL are required'
                }
            }), 400
        
        website_service = get_website_service()
        if not website_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Website service unavailable'
                }
            }), 503
        
        website = website_service.create_website(name, url, description)
        
        return jsonify({
            'success': True,
            'data': {
                'website': website.to_dict(),
                'message': 'Website created successfully'
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating website: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to create website'
            }
        }), 500


@admin_bp.route('/websites/<website_id>', methods=['PUT'])
@require_auth
def update_website(website_id):
    """Update a website"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request data is required'
                }
            }), 400
        
        website_service = get_website_service()
        if not website_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Website service unavailable'
                }
            }), 503
        
        success = website_service.update_website(
            website_id,
            name=data.get('name'),
            url=data.get('url'),
            description=data.get('description')
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404
        
        # Get updated website
        website = website_service.get_website(website_id)
        
        return jsonify({
            'success': True,
            'data': {
                'website': website.to_dict() if website else None,
                'message': 'Website updated successfully'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating website: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to update website'
            }
        }), 500


@admin_bp.route('/websites/<website_id>', methods=['DELETE'])
@require_auth
def delete_website(website_id):
    """Delete a website"""
    try:
        website_service = get_website_service()
        if not website_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Website service unavailable'
                }
            }), 503
        
        success = website_service.delete_website(website_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Website deleted successfully'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting website: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to delete website'
            }
        }), 500


@admin_bp.route('/websites/<website_id>/toggle-status', methods=['PATCH'])
@require_auth
def toggle_website_status(website_id):
    """Toggle website status"""
    try:
        website_service = get_website_service()
        if not website_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Website service unavailable'
                }
            }), 503
        
        new_status = website_service.toggle_website_status(website_id)
        
        if not new_status:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'new_status': new_status.value,
                'message': f'Website status changed to {new_status.value}'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error toggling website status: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to toggle website status'
            }
        }), 500


# Script Token Management Endpoints

@admin_bp.route('/scripts/generate', methods=['POST'])
@require_auth
def generate_script_token():
    """Generate script token for a website"""
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


@admin_bp.route('/scripts/tokens/<website_id>', methods=['GET'])
@require_auth
def get_script_token(website_id):
    """Get script token for a website"""
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
        
        # Generate integration information
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
        
        token_dict = token.to_dict()
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
        current_app.logger.error(f"Error getting script token: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve script token'
            }
        }), 500


@admin_bp.route('/scripts/tokens/<website_id>/revoke', methods=['POST'])
@require_auth
def revoke_script_token(website_id):
    """Revoke script token for a website"""
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
        
        success = token_manager.revoke_token(website_id)
        if not success:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'REVOCATION_FAILED',
                    'message': 'Failed to revoke script token'
                }
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Script token revoked successfully',
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


# Health and Statistics Endpoints

@admin_bp.route('/health', methods=['GET'])
def health_check():
    """Admin API health check"""
    try:
        auth_service = get_auth_service()
        website_service = get_website_service()
        token_manager = get_script_token_manager()
        
        services_status = {
            'auth_service': 'healthy' if auth_service else 'unavailable',
            'website_service': 'healthy' if website_service else 'unavailable',
            'script_token_manager': 'healthy' if token_manager else 'unavailable'
        }
        
        overall_status = 'healthy' if all(
            status == 'healthy' for status in services_status.values()
        ) else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@admin_bp.route('/statistics', methods=['GET'])
@require_auth
def get_admin_statistics():
    """Get comprehensive admin statistics"""
    try:
        stats = {}
        
        # Auth statistics
        auth_service = get_auth_service()
        if auth_service:
            stats['auth'] = auth_service.get_auth_statistics()
        
        # Website statistics
        website_service = get_website_service()
        if website_service:
            stats['websites'] = website_service.get_website_statistics()
        
        # Script token statistics
        token_manager = get_script_token_manager()
        if token_manager:
            stats['script_tokens'] = token_manager.get_token_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve statistics'
            }
        }), 500


# Legacy Compatibility Endpoints

@admin_bp.route('/admin/health', methods=['GET'])
def legacy_admin_health():
    """Legacy admin health endpoint for backward compatibility"""
    try:
        auth_service = get_auth_service()
        website_service = get_website_service()
        
        return jsonify({
            'status': 'healthy' if auth_service and website_service else 'degraded',
            'service': 'admin_legacy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'services': {
                'auth': 'up' if auth_service else 'down',
                'websites': 'up' if website_service else 'down'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Legacy health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500