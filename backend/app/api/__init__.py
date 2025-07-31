"""
API module for Passive CAPTCHA system
Provides verification, health check, and validation endpoints
"""

import time
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.ml import predict_human_probability, extract_features, is_model_loaded, get_model_info
from app.database import log_verification, get_db_session

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@api_bp.route('/verify', methods=['POST', 'OPTIONS'])
@limiter.limit("10 per minute")
def verify_captcha():
    """
    Main verification endpoint - analyzes behavioral data to determine human vs bot
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    start_time = time.time()
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'error': {
                    'code': 'INVALID_CONTENT_TYPE',
                    'message': 'Content-Type must be application/json'
                }
            }), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Extract required fields
        session_id = data.get('sessionId', f'session_{int(time.time())}')
        origin = data.get('origin', request.headers.get('Origin', 'unknown'))
        
        # Extract features from behavioral data
        try:
            features = extract_features(data)
        except Exception as e:
            return jsonify({
                'error': {
                    'code': 'FEATURE_EXTRACTION_ERROR',
                    'message': f'Failed to extract features: {str(e)}'
                }
            }), 400
        
        # Get ML prediction
        try:
            prediction = predict_human_probability(features)
        except Exception as e:
            return jsonify({
                'error': {
                    'code': 'PREDICTION_ERROR', 
                    'message': f'ML model prediction failed: {str(e)}'
                }
            }), 500
        
        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)
        
        # Prepare response
        result = {
            'isHuman': prediction['isHuman'],
            'confidence': prediction['confidence'],
            'sessionId': session_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'responseTime': response_time
        }
        
        # Log verification
        try:
            log_verification(
                session_id=session_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                origin=origin,
                is_human=prediction['isHuman'],
                confidence=prediction['confidence'],
                features=features,
                response_time=response_time
            )
        except Exception as e:
            print(f"Warning: Failed to log verification: {e}")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in verify_captcha: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error occurred'
            }
        }), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint
    """
    try:
        from app.database import get_last_verification_time
        
        # Check model status
        model_loaded = is_model_loaded()
        model_info = get_model_info() if model_loaded else None
        
        # Check database connection
        try:
            session = get_db_session()
            session.execute('SELECT 1')
            session.close()
            db_healthy = True
            last_verification = get_last_verification_time()
        except Exception:
            db_healthy = False
            last_verification = None
        
        # Calculate uptime (simplified)
        uptime = int(time.time())  # Could be enhanced with actual start time
        
        # Overall health status
        overall_status = 'healthy' if (model_loaded and db_healthy) else 'degraded'
        
        health_data = {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': {
                'modelLoaded': model_loaded,
                'dbConnection': db_healthy,
                'api': True  # If we're responding, API is working
            },
            'metrics': {
                'lastVerification': last_verification,
                'uptime': uptime,
                'version': '1.0'
            }
        }
        
        if model_info:
            health_data['model'] = {
                'algorithm': model_info.get('algorithm', 'Random Forest'),
                'version': model_info.get('version', '1.0'),
                'features': model_info.get('features', 11)
            }
        
        status_code = 200 if overall_status == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        print(f"Error in health_check: {e}")
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'HEALTH_CHECK_FAILED',
                'message': 'Health check failed'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@api_bp.route('/validate', methods=['POST'])
@limiter.limit("50 per hour")
def validate_token():
    """
    Server-side token validation endpoint for backend integration
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                'valid': False,
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Token is required'
                }
            }), 400
        
        token = data['token']
        secret = data.get('secret')
        
        # Validate against admin secret (simplified approach)
        expected_secret = current_app.config.get('ADMIN_SECRET')
        
        if secret != expected_secret:
            return jsonify({
                'valid': False,
                'error': {
                    'code': 'INVALID_SECRET',
                    'message': 'Invalid secret key'
                }
            }), 401
        
        # Basic token validation - check format and length
        # In production, you'd verify JWT tokens or check against a database
        if not token or len(token) < 10:
            return jsonify({
                'valid': False,
                'reason': 'Invalid token format'
            }), 200
        
        # Additional basic checks for token validity
        if not token.replace('-', '').replace('_', '').isalnum():
            return jsonify({
                'valid': False,
                'reason': 'Token contains invalid characters'
            }), 200
        
        return jsonify({
            'valid': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        print(f"Error in validate_token: {e}")
        return jsonify({
            'valid': False,
            'error': {
                'code': 'VALIDATION_ERROR', 
                'message': 'Token validation failed'
            }
        }), 500


@api_bp.route('/ml/info', methods=['GET'])
def model_info():
    """
    Get ML model information and status
    """
    try:
        if not is_model_loaded():
            return jsonify({
                'error': {
                    'code': 'MODEL_NOT_LOADED',
                    'message': 'ML model is not loaded'
                }
            }), 503
        
        info = get_model_info()
        
        return jsonify({
            'model': {
                'algorithm': info.get('algorithm', 'Random Forest'),
                'version': info.get('version', '1.0'),
                'features': info.get('features', 11),
                'accuracy': info.get('accuracy', 'N/A'),
                'inference_time': info.get('inference_time', '<100ms')
            },
            'status': 'loaded',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        print(f"Error in model_info: {e}")
        return jsonify({
            'error': {
                'code': 'MODEL_INFO_ERROR',
                'message': 'Failed to retrieve model information'
            }
        }), 500


@api_bp.route('/status', methods=['GET'])
def api_status():
    """
    Simple API status endpoint
    """
    return jsonify({
        'api': 'Passive CAPTCHA',
        'version': '1.0',
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'endpoints': {
            'verify': '/api/verify',
            'health': '/api/health', 
            'validate': '/api/validate',
            'model_info': '/api/ml/info'
        }
    }), 200


# Error handlers
@api_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests. Try again later.',
            'retryAfter': 3600
        }
    }), 429


@api_bp.errorhandler(404)
def not_found_handler(e):
    """Handle not found errors"""
    return jsonify({
        'error': {
            'code': 'ENDPOINT_NOT_FOUND',
            'message': 'The requested endpoint was not found'
        }
    }), 404


@api_bp.errorhandler(405)
def method_not_allowed_handler(e):
    """Handle method not allowed errors"""
    return jsonify({
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'The HTTP method is not allowed for this endpoint'
        }
    }), 405 