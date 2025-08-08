#!/usr/bin/env python3
"""
Unified Authentication Decorators
Consolidates all authentication logic into a single module
"""

from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def require_admin_auth(f):
    """
    Unified admin authentication decorator
    Replaces all scattered @require_auth and @require_admin_auth decorators
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header with Bearer token required'
                }
            }), 401
        
        # Extract token
        token = auth_header.replace('Bearer ', '', 1).strip()
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Token cannot be empty'
                }
            }), 401
        
        # Validate token using unified auth service
        try:
            from app.services.auth_service import unified_auth_service
            
            # Validate JWT token
            user_data = unified_auth_service.validate_jwt_token(token)
            if not user_data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_TOKEN',
                        'message': 'Token validation failed'
                    }
                }), 401
            
            # Check admin role
            if user_data.get('role') != 'admin':
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': 'Admin access required'
                    }
                }), 403
            
            # Add user data to request context
            request.current_user = user_data
            
        except Exception as e:
            logger.error(f"Auth validation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_ERROR',
                    'message': 'Authentication failed'
                }
            }), 401
        
        # Proceed with original function
        return f(*args, **kwargs)
    
    return decorated_function

# Alias for backward compatibility
require_auth = require_admin_auth

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from request context
    """
    return getattr(request, 'current_user', None)

def is_authenticated() -> bool:
    """
    Check if current request is authenticated
    """
    return get_current_user() is not None