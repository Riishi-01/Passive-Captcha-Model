"""
Website Registration and Management API
Handles multi-tenant website registration, script generation, and dashboard access
"""

from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import re

from app.token_manager import token_manager, security_manager
from app.script_generator import script_generator
from app.database import get_website_by_id, get_websites_by_admin, get_analytics_data_for_website
from app.utils import (
    validate_email, validate_url, sanitize_string, create_error_response, 
    create_success_response, extract_bearer_token, safe_get, format_timestamp
)

# Create website API blueprint
website_bp = Blueprint('website', __name__)

@website_bp.route('/register', methods=['POST'])
def register_website():
    """
    Register new website and generate tokens
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(create_error_response('MISSING_DATA', 'Request body is required'))
        
        # Validate required fields
        required_fields = ['name', 'url', 'admin_email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Field "{field}" is required'
                    }
                }), 400
        
        # Extract and sanitize required fields
        website_name = sanitize_string(data['name'], 100)
        website_url = sanitize_string(data['url'], 500)
        admin_email = sanitize_string(data['admin_email'].lower(), 255)
        
        # Validate inputs
        if len(website_name) < 2 or len(website_name) > 100:
            return jsonify({
                'error': {
                    'code': 'INVALID_NAME',
                    'message': 'Website name must be between 2 and 100 characters'
                }
            }), 400
        
        if not validate_url(website_url):
            return jsonify({
                'error': {
                    'code': 'INVALID_URL',
                    'message': 'Invalid website URL format'
                }
            }), 400
        
        if not validate_email(admin_email):
            return jsonify({
                'error': {
                    'code': 'INVALID_EMAIL',
                    'message': 'Invalid admin email format'
                }
            }), 400
        
        # Generate unique tokens
        website_registration = token_manager.generate_website_token(
            website_name, website_url, admin_email
        )
        
        # Generate script tag
        script_tag = script_generator.generate_html_script_tag(
            website_registration.website_id,
            website_registration.api_key,
            website_name
        )
        
        # Generate integration example
        integration_example = script_generator.generate_integration_example(
            website_registration.website_id,
            website_registration.api_key,
            website_name
        )
        
        # Create dashboard URL
        dashboard_url = f"{current_app.config.get('DASHBOARD_BASE_URL', 'https://dashboard.passive-captcha.com')}/{website_registration.website_id}"
        
        # Generate dashboard access token
        dashboard_token = token_manager.generate_dashboard_token(
            website_registration.website_id,
            admin_email
        )
        
        return jsonify({
            'success': True,
            'website_id': website_registration.website_id,
            'website_name': website_name,
            'api_key': website_registration.api_key,
            'secret_key': website_registration.secret_key,
            'dashboard_url': dashboard_url,
            'dashboard_token': dashboard_token,
            'script_tag': script_tag,
            'integration_example_url': f"/api/v1/websites/{website_registration.website_id}/integration-example",
            'created_at': website_registration.created_at.isoformat() + 'Z',
            'rate_limits': website_registration.rate_limits,
            'instructions': {
                'step_1': 'Copy the script tag and paste it before the closing </body> tag of your website',
                'step_2': 'Initialize PassiveCaptcha with your desired options',
                'step_3': 'Access your dashboard using the provided URL and token',
                'step_4': 'Monitor verification attempts and analytics in real-time'
            }
        }), 201
        
    except Exception as e:
        print(f"Error in register_website: {e}")
        return jsonify({
            'error': {
                'code': 'REGISTRATION_FAILED',
                'message': 'Website registration failed. Please try again.'
            }
        }), 500


@website_bp.route('/<website_id>/script', methods=['GET'])
def get_website_script(website_id):
    """
    Get the JavaScript script for a specific website
    """
    try:
        # Get website information
        website_data = get_website_by_id(website_id)
        
        if not website_data:
            return jsonify({
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404
        
        if website_data['status'] != 'active':
            return jsonify({
                'error': {
                    'code': 'WEBSITE_INACTIVE',
                    'message': 'Website is not active'
                }
            }), 403
        
        # Generate script
        script_content = script_generator.generate_embedded_script(
            website_id,
            website_data['api_key'],
            website_data['website_name']
        )
        
        # Return as JavaScript content type
        return script_content, 200, {'Content-Type': 'application/javascript'}
        
    except Exception as e:
        print(f"Error in get_website_script: {e}")
        return jsonify({
            'error': {
                'code': 'SCRIPT_GENERATION_FAILED',
                'message': 'Failed to generate script'
            }
        }), 500


@website_bp.route('/<website_id>/integration-example', methods=['GET'])
def get_integration_example(website_id):
    """
    Get complete integration example HTML
    """
    try:
        # Get website information
        website_data = get_website_by_id(website_id)
        
        if not website_data:
            return jsonify({
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404
        
        # Generate integration example
        integration_html = script_generator.generate_integration_example(
            website_id,
            website_data['api_key'],
            website_data['website_name']
        )
        
        # Return as HTML
        return integration_html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        print(f"Error in get_integration_example: {e}")
        return jsonify({
            'error': {
                'code': 'EXAMPLE_GENERATION_FAILED',
                'message': 'Failed to generate integration example'
            }
        }), 500


@website_bp.route('/<website_id>/dashboard', methods=['GET'])
def get_website_dashboard(website_id):
    """
    Access website-specific dashboard
    """
    try:
        # Check authorization
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header required'
                }
            }), 401
        
        token = auth_header.split(' ')[1]
        
        if not token_manager.validate_dashboard_token(token, website_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired dashboard token'
                }
            }), 401
        
        # Get website information
        website_data = get_website_by_id(website_id)
        
        if not website_data:
            return jsonify({
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404
        
        # Generate dashboard HTML (will be implemented in dashboard module)
        from app.dashboard_manager import dashboard_manager
        dashboard_html = dashboard_manager.create_website_dashboard(
            website_id, 
            website_data['website_name']
        )
        
        return dashboard_html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        print(f"Error in get_website_dashboard: {e}")
        return jsonify({
            'error': {
                'code': 'DASHBOARD_ACCESS_FAILED',
                'message': 'Failed to access dashboard'
            }
        }), 500


@website_bp.route('/<website_id>/analytics', methods=['GET'])
def get_website_analytics(website_id):
    """
    Get website-specific analytics and logs
    """
    try:
        # Validate website API token
        api_key = request.headers.get('X-Website-Token')
        
        if not api_key:
            return jsonify({
                'error': {
                    'code': 'MISSING_API_KEY',
                    'message': 'Website API key required'
                }
            }), 401
        
        website_token = token_manager.validate_api_request(api_key, website_id)
        
        if not website_token:
            return jsonify({
                'error': {
                    'code': 'INVALID_API_KEY',
                    'message': 'Invalid API key or website ID'
                }
            }), 401
        
        # Apply rate limiting
        if not security_manager.apply_rate_limit(website_id, 'analytics'):
            return jsonify({
                'error': {
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'Analytics rate limit exceeded'
                }
            }), 429
        
        # Get query parameters
        hours = int(request.args.get('hours', 24))
        
        # Validate hours parameter
        if hours < 1 or hours > 168:  # Max 1 week
            return jsonify({
                'error': {
                    'code': 'INVALID_PARAMETER',
                    'message': 'Hours must be between 1 and 168'
                }
            }), 400
        
        # Get analytics data
        analytics_data = get_analytics_data_for_website(website_id, hours)
        
        # Get rate limit info
        rate_limit_info = security_manager.get_rate_limit_info(website_id, 'analytics')
        
        # Add rate limit headers
        response_data = {
            'analytics': analytics_data,
            'rate_limit': rate_limit_info,
            'website_id': website_id,
            'website_name': website_token.website_name
        }
        
        return jsonify(response_data), 200
        
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_PARAMETER',
                'message': 'Invalid hours parameter'
            }
        }), 400
        
    except Exception as e:
        print(f"Error in get_website_analytics: {e}")
        return jsonify({
            'error': {
                'code': 'ANALYTICS_FAILED',
                'message': 'Failed to retrieve analytics data'
            }
        }), 500


@website_bp.route('/admin/<admin_email>/websites', methods=['GET'])
def get_admin_websites(admin_email):
    """
    Get all websites registered by an admin
    """
    try:
        # Basic auth check (in production, use proper admin authentication)
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header required'
                }
            }), 401
        
        # Validate email format
        if not validate_email(admin_email):
            return jsonify({
                'error': {
                    'code': 'INVALID_EMAIL',
                    'message': 'Invalid admin email format'
                }
            }), 400
        
        # Get websites
        websites = get_websites_by_admin(admin_email.lower())
        
        # Remove sensitive information
        safe_websites = []
        for website in websites:
            safe_website = {
                'website_id': website['website_id'],
                'website_name': website['website_name'],
                'website_url': website['website_url'],
                'status': website['status'],
                'created_at': website['created_at'],
                'dashboard_url': f"{current_app.config.get('DASHBOARD_BASE_URL', 'https://dashboard.passive-captcha.com')}/{website['website_id']}",
                'rate_limits': website.get('rate_limits', {})
            }
            safe_websites.append(safe_website)
        
        return jsonify({
            'admin_email': admin_email,
            'websites': safe_websites,
            'total_websites': len(safe_websites),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        print(f"Error in get_admin_websites: {e}")
        return jsonify({
            'error': {
                'code': 'ADMIN_LOOKUP_FAILED',
                'message': 'Failed to retrieve admin websites'
            }
        }), 500


@website_bp.route('/<website_id>/status', methods=['GET'])
def get_website_status(website_id):
    """
    Get website status and basic information
    """
    try:
        # Get website information
        website_data = get_website_by_id(website_id)
        
        if not website_data:
            return jsonify({
                'error': {
                    'code': 'WEBSITE_NOT_FOUND',
                    'message': 'Website not found'
                }
            }), 404
        
        # Return basic status information
        return jsonify({
            'website_id': website_id,
            'website_name': website_data['website_name'],
            'website_url': website_data['website_url'],
            'status': website_data['status'],
            'created_at': website_data['created_at'],
            'script_url': f"/api/v1/websites/{website_id}/script",
            'dashboard_url': f"{current_app.config.get('DASHBOARD_BASE_URL', 'https://dashboard.passive-captcha.com')}/{website_id}",
            'rate_limits': website_data.get('rate_limits', {}),
            'permissions': website_data.get('permissions', [])
        }), 200
        
    except Exception as e:
        print(f"Error in get_website_status: {e}")
        return jsonify({
            'error': {
                'code': 'STATUS_LOOKUP_FAILED',
                'message': 'Failed to retrieve website status'
            }
        }), 500


# Enhanced verify endpoint with website isolation
@website_bp.route('/<website_id>/verify', methods=['POST', 'OPTIONS'])
def verify_with_website(website_id):
    """
    Enhanced verification endpoint with website isolation
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Validate website API token
        api_key = request.headers.get('X-Website-Token')
        
        if not api_key:
            return jsonify({
                'error': {
                    'code': 'MISSING_API_KEY',
                    'message': 'Website API key required'
                }
            }), 401
        
        website_token = token_manager.validate_api_request(api_key, website_id)
        
        if not website_token:
            return jsonify({
                'error': {
                    'code': 'INVALID_API_KEY',
                    'message': 'Invalid API key or website ID'
                }
            }), 401
        
        # Apply rate limiting
        if not security_manager.apply_rate_limit(website_id, 'verify'):
            rate_limit_info = security_manager.get_rate_limit_info(website_id, 'verify')
            return jsonify({
                'error': {
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'Verification rate limit exceeded',
                    'rate_limit': rate_limit_info
                }
            }), 429
        
        # Process verification request (use existing ML logic)
        from app.api import verify_captcha
        
        # Temporarily set website_id in request context for logging
        request.website_id = website_id
        
        # Call existing verification logic
        return verify_captcha()
        
    except Exception as e:
        print(f"Error in verify_with_website: {e}")
        return jsonify({
            'error': {
                'code': 'VERIFICATION_FAILED',
                'message': 'Verification request failed'
            }
        }), 500


# Error handlers for website blueprint


@website_bp.errorhandler(404)
def website_not_found_handler(e):
    """Handle not found errors for website endpoints"""
    return jsonify({
        'error': {
            'code': 'ENDPOINT_NOT_FOUND',
            'message': 'The requested website endpoint was not found'
        }
    }), 404