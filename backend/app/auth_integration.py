#!/usr/bin/env python3
"""
Authentication System Integration
Integrates robust authentication service with existing Flask app
"""

import os
import redis
from flask import Flask, request, jsonify, current_app
from functools import wraps
from typing import Optional, Dict, Any
import logging

# Import the robust auth service
from app.services.robust_auth_service import (
    RobustAuthService, 
    init_robust_auth_service, 
    get_robust_auth_service,
    UserRole,
    AuthenticationError,
    RateLimitError
)

logger = logging.getLogger(__name__)

def init_authentication(app: Flask, redis_client: redis.Redis = None):
    """Initialize authentication system with Flask app"""
    try:
        # Initialize the robust auth service
        auth_service = init_robust_auth_service(redis_client)
        
        # Store in app context
        app.auth_service = auth_service
        
        logger.info("✅ Robust authentication system initialized")
        return auth_service
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize authentication: {e}")
        raise

def require_admin_auth(f):
    """Enhanced admin authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get auth service
            auth_service = get_robust_auth_service()
            if not auth_service:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'AUTH_SERVICE_UNAVAILABLE',
                        'message': 'Authentication service not available'
                    }
                }), 503
            
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_TOKEN',
                        'message': 'Authorization token required'
                    }
                }), 401
            
            token = auth_header.split(' ')[1]
            
            # Validate JWT token
            payload = auth_service.validate_jwt_token(token)
            if not payload:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_TOKEN',
                        'message': 'Invalid or expired token'
                    }
                }), 401
            
            # Get session
            session = auth_service.validate_session(payload['session_id'])
            if not session:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'SESSION_EXPIRED',
                        'message': 'Session expired or invalid'
                    }
                }), 401
            
            # Check if user has admin role
            if not auth_service.require_role(UserRole.ADMIN, session):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': 'Admin access required'
                    }
                }), 403
            
            # Add session to request context
            request.current_session = session
            request.current_user = {
                'user_id': session.user_id,
                'email': session.email,
                'role': session.role.value
            }
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTHENTICATION_ERROR',
                    'message': 'Authentication failed'
                }
            }), 500
    
    return decorated_function

def create_enhanced_auth_endpoints(app: Flask):
    """Create enhanced authentication endpoints"""
    
    @app.route('/api/admin/login', methods=['POST'])
    def enhanced_login():
        """Enhanced login endpoint with robust authentication"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': 'JSON data required'
                    }
                }), 400
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            if not email or not password:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_CREDENTIALS',
                        'message': 'Email and password required'
                    }
                }), 400
            
            # Get auth service
            auth_service = get_robust_auth_service()
            if not auth_service:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'AUTH_SERVICE_UNAVAILABLE',
                        'message': 'Authentication service not available'
                    }
                }), 503
            
            # Try backward compatible admin authentication first
            if password == auth_service.admin_secret:
                # Create a session for admin_secret authentication
                from app.services.robust_auth_service import AuthSession, UserRole
                from datetime import datetime
                import secrets
                
                session = AuthSession(
                    session_id=f"sess_{secrets.token_urlsafe(32)}",
                    user_id="admin_user",
                    email=email if email else "admin@passivecaptcha.com",
                    role=UserRole.SUPER_ADMIN,
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    ip_address=request.remote_addr or "127.0.0.1",
                    user_agent=request.headers.get('User-Agent', 'unknown'),
                    security_flags={
                        'login_method': 'admin_secret',
                        'ip_address': request.remote_addr or "127.0.0.1"
                    }
                )
                auth_service._store_session(session)
                success = True
                error_message = None
            else:
                # Authenticate user normally
                success, session, error_message = auth_service.authenticate_user(
                    email=email,
                    password=password,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'AUTHENTICATION_FAILED',
                        'message': error_message or 'Authentication failed'
                    }
                }), 401
            
            # Generate JWT token
            jwt_token = auth_service.generate_jwt_token(session)
            
            return jsonify({
                'success': True,
                'data': {
                    'token': jwt_token,
                    'user': {
                        'email': session.email,
                        'role': session.role.value,
                        'session_id': session.session_id
                    },
                    'expires_in': int(auth_service.session_timeout.total_seconds())
                },
                'message': 'Login successful'
            })
            
        except RateLimitError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'RATE_LIMITED',
                    'message': str(e)
                }
            }), 429
            
        except AuthenticationError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTHENTICATION_ERROR',
                    'message': str(e)
                }
            }), 400
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Login failed'
                }
            }), 500
    
    @app.route('/api/admin/logout', methods=['POST'])
    @require_admin_auth
    def enhanced_logout():
        """Enhanced logout endpoint"""
        try:
            auth_service = get_robust_auth_service()
            session = getattr(request, 'current_session', None)
            
            if auth_service and session:
                auth_service.logout_user(session.session_id)
            
            return jsonify({
                'success': True,
                'message': 'Logout successful'
            })
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'LOGOUT_ERROR',
                    'message': 'Logout failed'
                }
            }), 500
    
    @app.route('/api/admin/verify-token', methods=['GET'])
    @require_admin_auth
    def verify_token():
        """Token verification endpoint"""
        try:
            session = getattr(request, 'current_session', None)
            
            return jsonify({
                'success': True,
                'data': {
                    'valid': True,
                    'user': {
                        'email': session.email,
                        'role': session.role.value,
                        'session_id': session.session_id
                    },
                    'last_activity': session.last_activity.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VERIFICATION_ERROR',
                    'message': 'Token verification failed'
                }
            }), 500
    
    @app.route('/api/admin/change-password', methods=['POST'])
    @require_admin_auth
    def change_password():
        """Change password endpoint"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': 'JSON data required'
                    }
                }), 400
            
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            
            if not old_password or not new_password:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_PASSWORDS',
                        'message': 'Old and new passwords required'
                    }
                }), 400
            
            auth_service = get_robust_auth_service()
            session = getattr(request, 'current_session', None)
            
            if not auth_service or not session:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'AUTH_SERVICE_ERROR',
                        'message': 'Authentication service error'
                    }
                }), 500
            
            # Change password
            success = auth_service.change_password(
                email=session.email,
                old_password=old_password,
                new_password=new_password
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Password changed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'PASSWORD_CHANGE_FAILED',
                        'message': 'Failed to change password'
                    }
                }), 400
                
        except AuthenticationError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTHENTICATION_ERROR',
                    'message': str(e)
                }
            }), 400
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Password change failed'
                }
            }), 500
    
    @app.route('/api/admin/sessions', methods=['GET'])
    @require_admin_auth
    def get_user_sessions():
        """Get user sessions endpoint"""
        try:
            auth_service = get_robust_auth_service()
            session = getattr(request, 'current_session', None)
            
            if not auth_service or not session:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'AUTH_SERVICE_ERROR',
                        'message': 'Authentication service error'
                    }
                }), 500
            
            # Get user sessions
            sessions = auth_service.get_user_sessions(session.email)
            
            return jsonify({
                'success': True,
                'data': {
                    'sessions': [s.to_dict() for s in sessions],
                    'total': len(sessions)
                }
            })
            
        except Exception as e:
            logger.error(f"Get sessions error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get sessions'
                }
            }), 500

def create_auth_status_endpoint(app: Flask):
    """Create authentication status endpoint for health checks"""
    
    @app.route('/api/auth/status', methods=['GET'])
    def auth_status():
        """Authentication system status"""
        try:
            auth_service = get_robust_auth_service()
            
            status = {
                'auth_service_available': auth_service is not None,
                'redis_available': False,
                'default_admin_exists': False
            }
            
            if auth_service:
                # Check Redis connectivity
                try:
                    if auth_service.redis:
                        auth_service.redis.ping()
                        status['redis_available'] = True
                except:
                    pass
                
                # Check if default admin exists
                try:
                    admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@passivecaptcha.com')
                    admin_user = auth_service.get_user_by_email(admin_email)
                    status['default_admin_exists'] = admin_user is not None
                except:
                    pass
            
            return jsonify({
                'success': True,
                'data': status,
                'message': 'Authentication status retrieved'
            })
            
        except Exception as e:
            logger.error(f"Auth status error: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'STATUS_ERROR',
                    'message': 'Failed to get auth status'
                }
            }), 500

def integrate_with_existing_app(app: Flask) -> bool:
    """Integrate robust authentication with existing Flask app"""
    try:
        # Initialize Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        try:
            redis_client = redis.from_url(redis_url)
            redis_client.ping()  # Test connection
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.info(f"💾 Redis not available, using in-memory auth (development mode): {type(e).__name__}")
            redis_client = None
        
        # Initialize authentication
        auth_service = init_authentication(app, redis_client)
        
        # Create enhanced endpoints
        create_enhanced_auth_endpoints(app)
        create_auth_status_endpoint(app)
        
        logger.info("✅ Enhanced authentication system integrated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to integrate authentication: {e}")
        return False

# Export the decorator for use in other modules
__all__ = ['require_admin_auth', 'integrate_with_existing_app', 'init_authentication']