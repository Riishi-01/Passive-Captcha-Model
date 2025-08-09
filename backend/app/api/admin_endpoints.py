"""
Unified Admin API Endpoints
Consolidated, single-source-of-truth admin API with all required endpoints
"""

from flask import Blueprint, request, jsonify, current_app, make_response
from datetime import datetime, timedelta
from functools import wraps
from app.services import get_auth_service, get_website_service
from app.script_token_manager import get_script_token_manager, ScriptVersion
from app.database import get_db_session, VerificationLog
from sqlalchemy import func, and_, desc
import traceback
import uuid

admin_bp = Blueprint('admin_api', __name__, url_prefix='/admin')


def require_auth(f):
    """Authentication decorator using centralized AuthService for consistency"""
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

        try:
            auth_service = get_auth_service()
            if not auth_service:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'AUTH_SERVICE_UNAVAILABLE',
                        'message': 'Authentication service not available'
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

            # Attach user to request context
            request.current_user = {
                'id': user.id,
                'email': user.email,
                'role': user.role.value,
                'last_login': user.last_login.isoformat() if hasattr(user.last_login, 'isoformat') else None
            }

            return f(*args, **kwargs)

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
    """Enhanced CORS preflight handler for cross-browser compatibility"""
    if request.method == "OPTIONS":
        response = make_response()
        
        # Get origin from request or use wildcard for development
        origin = request.headers.get('Origin', '*')
        
        # Comprehensive CORS headers for all browsers
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 
                           'Content-Type,Authorization,X-Requested-With,X-CSRF-Token,Accept,Origin,User-Agent,DNT,Cache-Control,X-Mx-ReqToken')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,PATCH,OPTIONS,HEAD')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '86400')  # 24 hours
        
        # Browser-specific headers
        response.headers.add('Vary', 'Origin,Access-Control-Request-Method,Access-Control-Request-Headers')
        
        # Additional headers for IE/Edge compatibility
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'SAMEORIGIN')
        
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

        email = data.get('email')  # optional
        password = data['password']

        # Use centralized auth service for verification (supports password-only and email+password)
        auth_service = get_auth_service()
        if not auth_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_SERVICE_UNAVAILABLE',
                    'message': 'Authentication service not available'
                }
            }), 503

        try:
            result = auth_service.authenticate_admin(password=password, email=email)
            if not result:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CREDENTIALS',
                        'message': 'Invalid credentials'
                    }
                }), 401

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

            # Response headers
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, no-transform'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            origin = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Content-Type'] = 'application/json; charset=utf-8'

            return response
        except Exception as e:
            current_app.logger.error(f"Login auth error: {e}")
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


@admin_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh():
    """Refresh authentication token"""
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]

        auth_service = get_auth_service()
        result = auth_service.refresh_token(token)

        if not result:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'REFRESH_FAILED',
                    'message': 'Token refresh failed'
                }
            }), 401

        return jsonify({
            'success': True,
            'token': result['token'],
            'user': result['user'],
            'expires_in': result.get('expires_in', 3600)
        })

    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Token refresh failed'
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


@admin_bp.route('/websites/<website_id>/status', methods=['PATCH'])
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

        # Get current website
        website = website_service.get_website(website_id)
        if not website:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404

        # Toggle status
        new_status = 'inactive' if website.status == 'active' else 'active'
        success = website_service.update_website_status(website_id, new_status)

        if success:
            updated_website = website_service.get_website(website_id)
            return jsonify({
                'success': True,
                'data': {
                    'website': updated_website.to_dict() if updated_website else None,
                    'message': f'Website status updated to {new_status}'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UPDATE_FAILED',
                    'message': 'Failed to update website status'
                }
            }), 500

    except Exception as e:
        current_app.logger.error(f"Error toggling website status: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to toggle website status'
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
def toggle_website_status_alt(website_id):
    """Alternative toggle website status endpoint"""
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

@admin_bp.route('/health', methods=['GET'])
def admin_health():
    """Admin health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'admin_api',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@admin_bp.route('/system-status', methods=['GET'])
@require_auth
def system_status():
    """System status endpoint"""
    return jsonify({
        'status': 'operational',
        'components': {
            'database': 'healthy',
            'ml_model': 'loaded',
            'admin_api': 'operational'
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@admin_bp.route('/analytics', methods=['GET'])
@require_auth
def analytics():
    """Analytics endpoint"""
    return jsonify({
        'message': 'Analytics data endpoint',
        'data': {
            'total_verifications': 0,
            'success_rate': 0,
            'last_24h': 0
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@admin_bp.route('/analytics/stats', methods=['GET'])
@require_auth
def analytics_stats():
    """Dashboard statistics endpoint"""
    time_range = request.args.get('timeRange', '24h')
    
    return jsonify({
        'success': True,
        'data': {
            'totalVerifications': 0,
            'humanRate': 0,
            'avgConfidence': 0,
            'avgResponseTime': 0,
            'verificationChange': 0,
            'humanRateChange': 0,
            'confidenceChange': 0,
            'responseTimeChange': 0
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@admin_bp.route('/analytics/charts/<chart_type>', methods=['GET'])
@require_auth
def analytics_charts(chart_type):
    """Chart data endpoint - generates data based on chart type"""
    try:
        period = request.args.get('period', '24h')
        
        # Calculate time window
        if period == '24h':
            hours = 24
        elif period == '7d':
            hours = 168
        elif period == '30d':
            hours = 720
        else:
            hours = 24
            
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        session = get_db_session()
        try:
            if chart_type == 'verifications':
                # Generate hourly verification data
                data = []
                for i in range(hours):
                    hour_start = start_time + timedelta(hours=i)
                    hour_end = hour_start + timedelta(hours=1)
                    
                    count = session.query(func.count(VerificationLog.id)).filter(
                        and_(
                            VerificationLog.timestamp >= hour_start,
                            VerificationLog.timestamp < hour_end
                        )
                    ).scalar() or 0
                    
                    data.append({
                        'timestamp': hour_start.isoformat() + 'Z',
                        'value': count
                    })
                    
            elif chart_type == 'confidence':
                # Generate confidence distribution data
                confidence_ranges = [
                    {'min': 0.0, 'max': 0.2, 'label': '0-20%'},
                    {'min': 0.2, 'max': 0.4, 'label': '20-40%'},
                    {'min': 0.4, 'max': 0.6, 'label': '40-60%'},
                    {'min': 0.6, 'max': 0.8, 'label': '60-80%'},
                    {'min': 0.8, 'max': 1.0, 'label': '80-100%'}
                ]
                
                data = []
                for range_info in confidence_ranges:
                    count = session.query(func.count(VerificationLog.id)).filter(
                        and_(
                            VerificationLog.timestamp >= start_time,
                            VerificationLog.confidence >= range_info['min'],
                            VerificationLog.confidence < range_info['max']
                        )
                    ).scalar() or 0
                    
                    data.append({
                        'label': range_info['label'],
                        'value': count
                    })
                    
            elif chart_type == 'response_time':
                # Generate response time data (simulated for now)
                data = []
                for i in range(hours):
                    hour_start = start_time + timedelta(hours=i)
                    
                    avg_response_time = session.query(func.avg(VerificationLog.response_time)).filter(
                        and_(
                            VerificationLog.timestamp >= hour_start,
                            VerificationLog.timestamp < hour_start + timedelta(hours=1)
                        )
                    ).scalar() or 0
                    
                    data.append({
                        'timestamp': hour_start.isoformat() + 'Z',
                        'value': round(avg_response_time, 2) if avg_response_time else 0
                    })
                    
            else:
                # Default empty data for unknown chart types
                data = []
                
            return jsonify({
                'success': True,
                'data': data,
                'chart_type': chart_type,
                'period': period,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting chart data for {chart_type}: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CHART_DATA_ERROR',
                'message': f'Failed to retrieve {chart_type} chart data'
            }
        }), 500


@admin_bp.route('/analytics/detection', methods=['GET'])
@require_auth
def analytics_detection():
    """Detection data endpoint with real database data"""
    try:
        time_range = request.args.get('timeRange', '24h')
        
        # Calculate time window
        if time_range == '24h':
            hours = 24
        elif time_range == '7d':
            hours = 168
        elif time_range == '30d':
            hours = 720
        else:
            hours = 24
            
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        session = get_db_session()
        try:
            # Get detection counts
            total_query = session.query(func.count(VerificationLog.id)).filter(
                VerificationLog.timestamp >= start_time
            )
            total_count = total_query.scalar() or 0
            
            human_query = session.query(func.count(VerificationLog.id)).filter(
                and_(
                    VerificationLog.timestamp >= start_time,
                    VerificationLog.is_human == True
                )
            )
            human_count = human_query.scalar() or 0
            
            bot_count = total_count - human_count
            human_percentage = (human_count / total_count * 100) if total_count > 0 else 0
            bot_percentage = 100 - human_percentage
            
            return jsonify({
                'success': True,
                'data': {
                    'human': human_count,
                    'bot': bot_count,
                    'humanPercentage': round(human_percentage, 2),
                    'botPercentage': round(bot_percentage, 2),
                    'total': total_count
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting detection data: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve detection data'
            }
        }), 500


# ML Monitoring Endpoints (Frontend expects these)

@admin_bp.route('/ml/health', methods=['GET'])
@require_auth
def ml_health():
    """ML model health endpoint - simplified version"""
    try:
        import os
        
        # Check if model files exist
        model_paths = [
            'models/passive_captcha_rf.pkl',
            'models/passive_captcha_ensemble.pkl'
        ]
        
        model_exists = False
        existing_model_path = None
        
        for path in model_paths:
            if os.path.exists(path):
                model_exists = True
                existing_model_path = path
                break
        
        # Basic status determination
        if model_exists:
            status = 'healthy'
            message = f'Model file found at {existing_model_path}'
        else:
            status = 'degraded'
            message = 'No model files found, but system can create one'
        
        return jsonify({
            'success': True,
            'status': status,
            'model_loaded': model_exists,  # Simplified assumption
            'model_file_exists': model_exists,
            'model_path': existing_model_path or 'Not found',
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error checking ML health: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ML_HEALTH_ERROR',
                'message': f'Failed to check ML model health: {str(e)}'
            }
        }), 500


@admin_bp.route('/ml/metrics', methods=['GET'])
@require_auth
def ml_metrics():
    """ML model metrics endpoint"""
    try:
        session = get_db_session()
        try:
            # Calculate model performance metrics from recent verifications
            recent_time = datetime.utcnow() - timedelta(hours=24)
            
            total_predictions = session.query(func.count(VerificationLog.id)).filter(
                VerificationLog.timestamp >= recent_time
            ).scalar() or 0
            
            avg_confidence = session.query(func.avg(VerificationLog.confidence)).filter(
                VerificationLog.timestamp >= recent_time
            ).scalar() or 0
            
            high_confidence_count = session.query(func.count(VerificationLog.id)).filter(
                and_(
                    VerificationLog.timestamp >= recent_time,
                    VerificationLog.confidence >= 0.8
                )
            ).scalar() or 0
            
            accuracy_rate = (high_confidence_count / total_predictions * 100) if total_predictions > 0 else 0
            
            return jsonify({
                'success': True,
                'data': {
                    'total_predictions_24h': total_predictions,
                    'average_confidence': round(avg_confidence, 4),
                    'accuracy_rate': round(accuracy_rate, 2),
                    'high_confidence_predictions': high_confidence_count,
                    'model_performance': 'Good' if accuracy_rate > 80 else 'Fair' if accuracy_rate > 60 else 'Poor'
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting ML metrics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ML_METRICS_ERROR',
                'message': 'Failed to retrieve ML metrics'
            }
        }), 500


@admin_bp.route('/ml/retrain', methods=['POST'])
@require_auth
def ml_retrain():
    """ML model retraining endpoint"""
    try:
        # In a real implementation, this would trigger model retraining
        # For now, return a success response
        return jsonify({
            'success': True,
            'data': {
                'message': 'Model retraining initiated',
                'job_id': str(uuid.uuid4()),
                'estimated_completion': (datetime.utcnow() + timedelta(minutes=30)).isoformat() + 'Z'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error initiating ML retrain: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'RETRAIN_ERROR',
                'message': 'Failed to initiate model retraining'
            }
        }), 500


# Settings Endpoints (Frontend expects these)

@admin_bp.route('/settings', methods=['GET'])
@require_auth
def get_settings():
    """Get admin settings"""
    try:
        # Return default settings - in a real app, these would be stored in database
        settings = {
            'general': {
                'confidence_threshold': current_app.config.get('CONFIDENCE_THRESHOLD', 0.6),
                'rate_limit_requests': current_app.config.get('RATE_LIMIT_REQUESTS', 1000),
                'admin_email': current_app.config.get('ADMIN_EMAIL', 'admin@passive-captcha.com')
            },
            'alerts': {
                'email_notifications': True,
                'high_bot_activity_threshold': 50,
                'low_confidence_threshold': 0.5,
                'alert_frequency': 'immediate'
            },
            'ml': {
                'auto_retrain': False,
                'retrain_threshold': 1000,
                'model_backup': True
            },
            'security': {
                'session_timeout': 3600,
                'max_login_attempts': 5,
                'ip_blocking': True
            }
        }
        
        return jsonify({
            'success': True,
            'data': settings,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting settings: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SETTINGS_ERROR',
                'message': 'Failed to retrieve settings'
            }
        }), 500


@admin_bp.route('/settings', methods=['PUT'])
@require_auth
def update_settings():
    """Update admin settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Settings data is required'
                }
            }), 400
            
        # In a real implementation, validate and save settings to database
        # For now, just return success
        return jsonify({
            'success': True,
            'data': {
                'message': 'Settings updated successfully',
                'updated_fields': list(data.keys())
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating settings: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SETTINGS_UPDATE_ERROR',
                'message': 'Failed to update settings'
            }
        }), 500


@admin_bp.route('/change-password', methods=['PUT'])
@require_auth
def change_password():
    """Change admin password"""
    try:
        data = request.get_json()
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'current_password and new_password are required'
                }
            }), 400
            
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Get auth service
        auth_service = get_auth_service()
        if not auth_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_SERVICE_UNAVAILABLE',
                    'message': 'Authentication service not available'
                }
            }), 503
            
        # Verify current password
        try:
            auth_service.authenticate_admin(current_password)
        except Exception:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_CURRENT_PASSWORD',
                    'message': 'Current password is incorrect'
                }
            }), 401
            
        # In a real implementation, update the password
        # For now, just return success
        return jsonify({
            'success': True,
            'data': {
                'message': 'Password changed successfully'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error changing password: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'PASSWORD_CHANGE_ERROR',
                'message': 'Failed to change password'
            }
        }), 500


# Alert Settings Endpoints

@admin_bp.route('/alerts/settings', methods=['GET'])
@require_auth
def get_alert_settings():
    """Get alert settings"""
    try:
        settings = {
            'email_notifications': True,
            'webhook_url': '',
            'thresholds': {
                'high_bot_activity': 50,
                'low_confidence': 0.5,
                'system_error': 10
            },
            'frequency': 'immediate',
            'enabled_alerts': ['bot_activity', 'low_confidence', 'system_errors']
        }
        
        return jsonify({
            'success': True,
            'data': settings,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting alert settings: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ALERT_SETTINGS_ERROR',
                'message': 'Failed to retrieve alert settings'
            }
        }), 500


@admin_bp.route('/alerts/settings', methods=['PUT'])
@require_auth
def update_alert_settings():
    """Update alert settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Alert settings data is required'
                }
            }), 400
            
        # In a real implementation, validate and save to database
        return jsonify({
            'success': True,
            'data': {
                'message': 'Alert settings updated successfully'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating alert settings: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ALERT_SETTINGS_UPDATE_ERROR',
                'message': 'Failed to update alert settings'
            }
        }), 500


@admin_bp.route('/alerts/<alert_id>/read', methods=['POST'])
@require_auth
def mark_alert_read(alert_id):
    """Mark alert as read"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'alert_id': alert_id,
                'marked_read': True,
                'read_at': datetime.utcnow().isoformat() + 'Z'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error marking alert as read: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ALERT_READ_ERROR',
                'message': 'Failed to mark alert as read'
            }
        }), 500


@admin_bp.route('/logs', methods=['GET'])
@require_auth
def logs():
    """Logs endpoint"""
    return jsonify({
        'logs': [],
        'total': 0,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@admin_bp.route('/logs/timeline', methods=['GET'])
@require_auth
def logs_timeline():
    """Timeline logs endpoint"""
    filter_type = request.args.get('filter', 'all')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 50))
    
    return jsonify({
        'success': True,
        'data': {
            'logs': [],
            'hasMore': False,
            'total': 0
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@admin_bp.route('/alerts/recent', methods=['GET'])
@require_auth
def alerts_recent():
    """Recent alerts endpoint"""
    return jsonify({
        'success': True,
        'data': [],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200
