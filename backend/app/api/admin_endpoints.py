"""
Refactored Admin Endpoints
Modern, service-based admin API endpoints using centralized services
"""

from flask import Blueprint, request, jsonify, current_app, make_response
from datetime import datetime, timedelta
from functools import wraps
from app.services import get_auth_service, get_website_service
from app.script_token_manager import get_script_token_manager, ScriptVersion
import traceback

admin_bp = Blueprint('admin_api', __name__, url_prefix='/admin')


def require_auth(f):
    """Simplified authentication decorator for admin endpoints"""
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
        
        # Direct JWT validation using the configured secret
        import jwt
        import os
        
        try:
            jwt_secret = os.getenv('JWT_SECRET', current_app.config.get('JWT_SECRET'))
            if not jwt_secret:
                jwt_secret = 'jwt-secret-key-for-passive-captcha-production-environment'
            
            # Decode and validate JWT token with browser-compatible options
            payload = jwt.decode(
                token, 
                jwt_secret, 
                algorithms=['HS256'],
                options={
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_signature': True,
                    'require_exp': True,
                    'require_iat': True
                }
            )
            
            # Extract user information from JWT payload
            request.current_user = {
                'user_id': payload.get('user_id', 'admin_user'),
                'email': payload.get('email', 'admin@passivecaptcha.com'),
                'role': payload.get('role', 'super_admin'),
                'session_id': payload.get('session_id')
            }
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TOKEN_EXPIRED',
                    'message': 'Token has expired'
                }
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid token'
                }
            }), 401
        except Exception as e:
            current_app.logger.error(f"Authentication error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_ERROR',
                    'message': 'Authentication failed'
                }
            }), 401

    return decorated_function


# Preflight handler for better browser compatibility
@admin_bp.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,PATCH,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', "true")
        return response


# Authentication Endpoints

@admin_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Unified admin login endpoint"""
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

        email = data.get('email', 'admin@passivecaptcha.com')
        password = data['password']
        
        # Check against ADMIN_SECRET from config first (backward compatibility)
        admin_secret = current_app.config.get('ADMIN_SECRET', 'Admin123')
        if password == admin_secret:
            # Use basic auth service for admin secret authentication
            auth_service = get_auth_service()
            if auth_service:
                try:
                    result = auth_service.authenticate_admin(email, password, remember_me=False)
                    response = jsonify({
                        'success': True,
                        'data': {
                            'token': result['token'],
                            'user': result['user'],
                            'expires_in': result.get('expires_in', 3600),
                            'token_type': 'Bearer'
                        },
                        'message': 'Login successful'
                    })
                    
                    # Add browser-compatible headers
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    
                    return response
                except Exception as e:
                    current_app.logger.error(f"Basic auth failed: {e}")

        # Try robust authentication service as fallback
        try:
            from app.services.robust_auth_service import get_robust_auth_service
            auth_service = get_robust_auth_service()
            
            if auth_service:
                # Try robust authentication with browser-neutral parameters
                safe_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', '127.0.0.1')
                if ',' in safe_ip:
                    safe_ip = safe_ip.split(',')[0].strip()
                
                success, session, error_message = auth_service.authenticate_user(
                    email=email,
                    password=password,
                    ip_address=safe_ip,
                    user_agent='browser-client'  # Use consistent user agent
                )
                
                # Fallback to admin_secret check
                if not success and hasattr(auth_service, 'admin_secret') and password == auth_service.admin_secret:
                    from app.services.robust_auth_service import AuthSession, UserRole
                    from datetime import datetime
                    import secrets
                    
                    session = AuthSession(
                        session_id=f"sess_{secrets.token_urlsafe(32)}",
                        user_id="admin_user",
                        email=email,
                        role=UserRole.SUPER_ADMIN,
                        created_at=datetime.utcnow(),
                        last_activity=datetime.utcnow(),
                        ip_address=safe_ip,
                        user_agent='browser-client',
                        security_flags={'login_method': 'admin_secret', 'browser_compatible': True}
                    )
                    auth_service._store_session(session)
                    success = True
                    error_message = None
                
                if success:
                    # Generate JWT token for successful authentication
                    jwt_token = auth_service.generate_jwt_token(session)
                    
                    response = jsonify({
                        'success': True,
                        'data': {
                            'token': jwt_token,
                            'user': {
                                'email': session.email,
                                'role': session.role.value,
                                'session_id': session.session_id
                            },
                            'expires_in': 86400,  # 24 hours
                            'token_type': 'Bearer'
                        },
                        'message': 'Login successful'
                    })
                    
                    # Add browser-compatible headers
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    
                    return response
        except Exception as e:
            current_app.logger.warning(f"Robust auth not available: {e}")
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid credentials'
            }
        }), 401

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


@admin_bp.route('/verify-token', methods=['GET', 'OPTIONS'])
@require_auth
def verify_token():
    """Verify token validity"""
    try:
        user = request.current_user
        return jsonify({
            'success': True,
            'data': {
                'user': user,
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

@admin_bp.route('/websites', methods=['GET', 'OPTIONS'])
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

# REMOVED: Duplicate health endpoint - consolidated to main app level at /health


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

# REMOVED: Duplicate legacy health endpoint - consolidated to main app level at /health
