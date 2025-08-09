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
    """Admin authentication decorator using centralized AuthService"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header with Bearer token required'
                }
            }), 401

        token = auth_header.replace('Bearer ', '', 1).strip()
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Token cannot be empty'
                }
            }), 401

        try:
            from app.services import get_auth_service
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
                        'message': 'Token validation failed'
                    }
                }), 401

            if getattr(user, 'role', None) and getattr(user.role, 'value', None) != 'admin':
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': 'Admin access required'
                    }
                }), 403

            request.current_user = user.to_dict() if hasattr(user, 'to_dict') else {
                'id': getattr(user, 'id', 'admin'),
                'email': getattr(user, 'email', 'admin@passive-captcha.com'),
                'role': getattr(user.role, 'value', 'admin') if getattr(user, 'role', None) else 'admin'
            }

        except Exception as e:
            logger.error(f"Auth validation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_ERROR',
                    'message': 'Authentication failed'
                }
            }), 401

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