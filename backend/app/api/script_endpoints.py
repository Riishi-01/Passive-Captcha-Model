"""
Script Integration API Endpoints
Handles script delivery, token activation, and passive data collection
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, Response, current_app, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.script_token_manager import get_script_token_manager
from app.logs_pipeline import logs_pipeline, LogType, LogLevel
from app.database import log_verification
from app.ml import predict_human_probability
import geoip2.database
import geoip2.errors
from user_agents import parse

script_bp = Blueprint('script', __name__, url_prefix='/api/script')

# Rate limiting for script endpoints
limiter = Limiter(key_func=get_remote_address)


@script_bp.route('/generate', methods=['GET'])
def generate_script():
    """
    Generate and deliver the passive CAPTCHA script for a website
    URL: /api/script/generate?token=<script_token>
    """
    try:
        script_token = request.args.get('token')
        if not script_token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Script token is required'
                }
            }), 400
        
        # Validate token
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Token manager not available'
                }
            }), 503
        
        # Get website URL from referrer or parameter
        website_url = request.headers.get('Referer') or request.args.get('url', '')
        if not website_url:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_URL',
                    'message': 'Website URL is required'
                }
            }), 400
        
        # Validate token
        is_valid, token_obj = token_manager.validate_token(script_token, website_url)
        if not is_valid or not token_obj:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired script token'
                }
            }), 401
        
        # Read the script template
        script_path = os.path.join(current_app.root_path, 'static', 'passive-captcha-script.js')
        try:
            with open(script_path, 'r') as f:
                script_content = f.read()
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SCRIPT_NOT_FOUND',
                    'message': 'Script file not found'
                }
            }), 404
        
        # Replace placeholders with actual values
        api_endpoint = current_app.config.get('API_BASE_URL', request.host_url.rstrip('/'))
        script_content = script_content.replace('{API_ENDPOINT}', api_endpoint)
        script_content = script_content.replace('{SCRIPT_TOKEN}', script_token)
        
        # Add configuration based on token settings
        config_js = f"""
window.PASSIVE_CAPTCHA_CONFIG = {{
    apiEndpoint: '{api_endpoint}',
    scriptToken: '{script_token}',
    websiteUrl: '{website_url}',
    collectMouseMovements: {str(token_obj.config.get('collect_mouse_movements', True)).lower()},
    collectKeyboardPatterns: {str(token_obj.config.get('collect_keyboard_patterns', True)).lower()},
    collectScrollBehavior: {str(token_obj.config.get('collect_scroll_behavior', True)).lower()},
    collectTimingData: {str(token_obj.config.get('collect_timing_data', True)).lower()},
    collectDeviceInfo: {str(token_obj.config.get('collect_device_info', True)).lower()},
    samplingRate: {token_obj.config.get('sampling_rate', 0.1)},
    batchSize: {token_obj.config.get('batch_size', 50)},
    sendInterval: {token_obj.config.get('send_interval', 30000)},
    debugMode: {str(token_obj.config.get('debug_mode', False)).lower()}
}};

{script_content}
"""
        
        # Log script delivery
        if logs_pipeline:
            logs_pipeline.log_system_event(
                f"Script delivered to {token_obj.website_name}",
                LogLevel.INFO,
                website_id=token_obj.website_id,
                metadata={
                    'script_token': script_token[:10] + '...',  # Partial token for security
                    'website_url': website_url,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'ip_address': request.remote_addr
                }
            )
        
        # Return script with proper headers
        response = Response(
            config_js,
            mimetype='application/javascript',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Access-Control-Allow-Origin': website_url,
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error generating script: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to generate script'
            }
        }), 500


@script_bp.route('/activate', methods=['POST'])
@limiter.limit("10 per minute")
def activate_token():
    """
    Activate a script token when the script is first loaded
    """
    try:
        # Validate request
        script_token = request.headers.get('X-Script-Token')
        if not script_token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Script token header is required'
                }
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request data is required'
                }
            }), 400
        
        website_url = data.get('website_url')
        session_id = data.get('session_id')
        user_agent = data.get('user_agent')
        
        if not all([website_url, session_id]):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'website_url and session_id are required'
                }
            }), 400
        
        # Get token manager
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Token manager not available'
                }
            }), 503
        
        # Activate token
        success = token_manager.activate_token(script_token, website_url)
        if not success:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ACTIVATION_FAILED',
                    'message': 'Failed to activate token'
                }
            }), 400
        
        # Get token details for logging
        token_obj = token_manager.get_token_by_script_token(script_token)
        
        # Log activation
        if logs_pipeline:
            logs_pipeline.log_system_event(
                f"Script activated for {token_obj.website_name}",
                LogLevel.INFO,
                website_id=token_obj.website_id,
                metadata={
                    'session_id': session_id,
                    'website_url': website_url,
                    'user_agent': user_agent,
                    'ip_address': request.remote_addr
                }
            )
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Token activated successfully',
                'session_id': session_id,
                'website_id': token_obj.website_id,
                'config': token_obj.config
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error activating token: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to activate token'
            }
        }), 500


@script_bp.route('/collect', methods=['POST'])
@limiter.limit("100 per minute")
def collect_data():
    """
    Collect passive behavioral data from websites
    """
    try:
        # Validate request
        script_token = request.headers.get('X-Script-Token')
        if not script_token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Script token header is required'
                }
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request data is required'
                }
            }), 400
        
        website_url = data.get('website_url')
        session_id = data.get('session_id')
        behavioral_data = data.get('data', {})
        
        if not all([website_url, session_id, behavioral_data]):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'website_url, session_id, and data are required'
                }
            }), 400
        
        # Get token manager and validate token
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Token manager not available'
                }
            }), 503
        
        is_valid, token_obj = token_manager.validate_token(script_token, website_url)
        if not is_valid or not token_obj:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired script token'
                }
            }), 401
        
        # Extract features for ML prediction
        features = extract_ml_features(behavioral_data)
        
        # Get ML prediction
        try:
            confidence = predict_human_probability(features)
            is_human = confidence > current_app.config.get('CONFIDENCE_THRESHOLD', 0.6)
        except Exception as e:
            current_app.logger.warning(f"ML prediction failed: {e}")
            confidence = 0.5  # Default neutral confidence
            is_human = True   # Default to human when ML fails
        
        # Get additional request information
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        country_code = get_country_from_ip(ip_address)
        
        # Calculate response time (time since page load)
        response_time = behavioral_data.get('timing', {}).get('sessionDuration', 0)
        
        # Log verification to database
        try:
            log_verification(
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                origin=website_url,
                is_human=is_human,
                confidence=confidence,
                features=features,
                response_time=response_time
            )
        except Exception as e:
            current_app.logger.error(f"Failed to log verification: {e}")
        
        # Log to pipeline for real-time updates
        if logs_pipeline:
            logs_pipeline.log_verification(
                website_id=token_obj.website_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                country=country_code,
                confidence=confidence,
                response_time=response_time,
                is_human=is_human,
                metadata={
                    'website_name': token_obj.website_name,
                    'website_url': website_url,
                    'behavioral_data': behavioral_data,
                    'extracted_features': features
                }
            )
        
        # Respond with verification result
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'verification_result': {
                    'is_human': is_human,
                    'confidence': round(confidence, 4),
                    'risk_score': round(1 - confidence, 4),
                    'classification': 'human' if is_human else 'bot'
                },
                'metadata': {
                    'country': country_code,
                    'response_time_ms': response_time,
                    'features_analyzed': len(features),
                    'timestamp': datetime.utcnow().isoformat()
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error collecting data: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to process data'
            }
        }), 500


@script_bp.route('/health', methods=['GET'])
def script_health():
    """
    Health check for script services
    """
    try:
        token_manager = get_script_token_manager()
        if not token_manager:
            return jsonify({
                'status': 'unhealthy',
                'error': 'Token manager not available'
            }), 503
        
        # Get token statistics
        stats = token_manager.get_token_stats()
        
        return jsonify({
            'status': 'healthy',
            'service': 'script_integration',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Script health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


def extract_ml_features(behavioral_data):
    """
    Extract features from behavioral data for ML prediction
    """
    features = {}
    
    # Mouse features
    mouse_data = behavioral_data.get('mouse', {})
    features.update({
        'mouse_movement_count': mouse_data.get('movementCount', 0),
        'mouse_click_count': mouse_data.get('clickCount', 0),
        'mouse_avg_velocity': mouse_data.get('avgVelocity', 0),
        'mouse_avg_acceleration': mouse_data.get('avgAcceleration', 0),
        'mouse_entropy': mouse_data.get('entropy', 0)
    })
    
    # Keyboard features
    keyboard_data = behavioral_data.get('keyboard', {})
    features.update({
        'keyboard_keystroke_count': keyboard_data.get('keystrokeCount', 0),
        'keyboard_avg_typing_speed': keyboard_data.get('avgTypingSpeed', 0),
        'keyboard_rhythm': keyboard_data.get('rhythm', 0)
    })
    
    # Scroll features
    scroll_data = behavioral_data.get('scroll', {})
    features.update({
        'scroll_event_count': scroll_data.get('scrollEventCount', 0),
        'scroll_avg_velocity': scroll_data.get('avgVelocity', 0),
        'scroll_consistency': scroll_data.get('consistency', 0)
    })
    
    # Timing features
    timing_data = behavioral_data.get('timing', {})
    features.update({
        'page_load_time': timing_data.get('pageLoadTime', 0),
        'dom_ready_time': timing_data.get('domReadyTime', 0),
        'first_interaction_time': timing_data.get('firstInteractionTime', 0),
        'session_duration': timing_data.get('sessionDuration', 0)
    })
    
    # Device features
    device_data = behavioral_data.get('device', {})
    if device_data:
        screen_res = device_data.get('screenResolution', {})
        viewport = device_data.get('viewport', {})
        
        features.update({
            'screen_width': screen_res.get('width', 0),
            'screen_height': screen_res.get('height', 0),
            'viewport_width': viewport.get('width', 0),
            'viewport_height': viewport.get('height', 0),
            'color_depth': screen_res.get('colorDepth', 0),
            'timezone_offset': device_data.get('timezoneOffset', 0),
            'touch_support': 1 if device_data.get('touchSupport') else 0,
            'device_memory': device_data.get('deviceMemory', 0),
            'hardware_concurrency': device_data.get('hardwareConcurrency', 0),
            'font_count': len(device_data.get('fonts', [])),
            'plugin_count': len(device_data.get('plugins', []))
        })
    
    # Behavioral metrics
    behavioral_metrics = behavioral_data.get('behavioral_metrics', {})
    features.update({
        'human_likelihood': behavioral_metrics.get('humanLikelihood', 0.5),
        'mouse_entropy_score': behavioral_metrics.get('mouseEntropy', 0),
        'keyboard_rhythm_score': behavioral_metrics.get('keyboardRhythm', 0),
        'scroll_consistency_score': behavioral_metrics.get('scrollConsistency', 0)
    })
    
    return features


def get_country_from_ip(ip_address):
    """
    Get country code from IP address using GeoIP
    """
    try:
        # Try to use GeoIP database if available
        geoip_path = current_app.config.get('GEOIP_DATABASE_PATH')
        if geoip_path and os.path.exists(geoip_path):
            with geoip2.database.Reader(geoip_path) as reader:
                response = reader.country(ip_address)
                return response.country.iso_code
    except Exception:
        pass
    
    # Fallback to simple IP-based country detection (for demo)
    if ip_address.startswith('127.') or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return 'LOCAL'
    elif ip_address.startswith('203.'):
        return 'AU'
    elif ip_address.startswith('172.'):
        return 'CA'
    else:
        return 'US'  # Default fallback


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract browser and OS information
    """
    try:
        user_agent = parse(user_agent_string)
        return {
            'browser': user_agent.browser.family,
            'browser_version': user_agent.browser.version_string,
            'os': user_agent.os.family,
            'os_version': user_agent.os.version_string,
            'device': user_agent.device.family,
            'is_mobile': user_agent.is_mobile,
            'is_tablet': user_agent.is_tablet,
            'is_pc': user_agent.is_pc,
            'is_bot': user_agent.is_bot
        }
    except Exception:
        return {
            'browser': 'Unknown',
            'browser_version': 'Unknown',
            'os': 'Unknown',
            'os_version': 'Unknown',
            'device': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'is_pc': True,
            'is_bot': False
        }