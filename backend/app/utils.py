"""
Utility functions for Passive CAPTCHA platform
Shared validation, formatting, and helper functions
"""

import re
import secrets
import string
from datetime import datetime
from typing import Dict, Any, Optional, Union


def validate_email(email: str) -> bool:
    """
    Validate email format using regex pattern
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """
    Validate URL format using regex pattern
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid URL format, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$'
    return re.match(pattern, url) is not None


def sanitize_string(input_str: str, max_length: int = 255) -> str:
    """
    Sanitize string input by trimming and limiting length
    
    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized string
    """
    if not input_str or not isinstance(input_str, str):
        return ""
    
    return input_str.strip()[:max_length]


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token
    
    Args:
        length: Length of token to generate
        
    Returns:
        str: Secure random token
    """
    return secrets.token_urlsafe(length)


def generate_api_key(prefix: str = "pc") -> str:
    """
    Generate API key with prefix
    
    Args:
        prefix: Prefix for the API key
        
    Returns:
        str: API key with format prefix_token
    """
    token = generate_secure_token(32)
    return f"{prefix}_{token}"


def format_timestamp(dt: datetime = None) -> str:
    """
    Format datetime to ISO string with Z suffix
    
    Args:
        dt: Datetime to format, defaults to current UTC time
        
    Returns:
        str: ISO formatted timestamp
    """
    if dt is None:
        dt = datetime.utcnow()
    
    return dt.isoformat() + 'Z'


def safe_get(data: Dict[str, Any], key: str, default: Any = None, 
           expected_type: type = None) -> Any:
    """
    Safely get value from dictionary with type checking
    
    Args:
        data: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        expected_type: Expected type for validation
        
    Returns:
        Any: Retrieved value or default
    """
    if not isinstance(data, dict) or key not in data:
        return default
    
    value = data[key]
    
    if expected_type and not isinstance(value, expected_type):
        return default
    
    return value


def create_error_response(code: str, message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        code: Error code
        message: Error message
        status_code: HTTP status code
        
    Returns:
        Dict: Standardized error response
    """
    return {
        'error': {
            'code': code,
            'message': message,
            'timestamp': format_timestamp()
        }
    }, status_code


def create_success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        data: Response data
        status_code: HTTP status code
        
    Returns:
        Dict: Standardized success response
    """
    response_data = dict(data)
    response_data['success'] = True
    response_data['timestamp'] = format_timestamp()
    
    return response_data, status_code


def validate_rate_limit_params(hours: Union[str, int]) -> int:
    """
    Validate and convert hours parameter for rate limiting
    
    Args:
        hours: Hours parameter to validate
        
    Returns:
        int: Validated hours value
        
    Raises:
        ValueError: If hours is invalid
    """
    try:
        hours_int = int(hours)
        if hours_int < 1 or hours_int > 168:  # Max 1 week
            raise ValueError("Hours must be between 1 and 168")
        return hours_int
    except (ValueError, TypeError):
        raise ValueError("Invalid hours parameter")


def extract_bearer_token(auth_header: str) -> Optional[str]:
    """
    Extract token from Authorization header
    
    Args:
        auth_header: Authorization header value
        
    Returns:
        Optional[str]: Extracted token or None
    """
    if not auth_header or not isinstance(auth_header, str):
        return None
    
    if not auth_header.startswith('Bearer '):
        return None
    
    return auth_header.split(' ')[1] if len(auth_header.split(' ')) > 1 else None


def normalize_origin(origin: str) -> str:
    """
    Normalize origin URL for consistent storage
    
    Args:
        origin: Origin URL to normalize
        
    Returns:
        str: Normalized origin
    """
    if not origin or not isinstance(origin, str):
        return 'unknown'
    
    # Remove trailing slashes and normalize
    return origin.rstrip('/')


def calculate_confidence_score(features: Dict[str, Any]) -> float:
    """
    Calculate basic confidence score from features
    
    Args:
        features: Feature dictionary
        
    Returns:
        float: Confidence score between 0 and 1
    """
    if not features:
        return 0.0
    
    # Basic confidence calculation based on feature completeness
    total_features = 11  # Expected number of features
    available_features = sum(1 for v in features.values() if v is not None)
    
    return min(available_features / total_features, 1.0)


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data showing only first and last characters
    
    Args:
        data: Sensitive data to mask
        visible_chars: Number of characters to show at start/end
        
    Returns:
        str: Masked data
    """
    if not data or len(data) <= visible_chars * 2:
        return '*' * len(data) if data else ''
    
    return data[:visible_chars] + '*' * (len(data) - visible_chars * 2) + data[-visible_chars:]


def get_client_ip(request) -> str:
    """
    Get client IP address from request, handling proxies
    
    Args:
        request: Flask request object
        
    Returns:
        str: Client IP address
    """
    # Check for forwarded headers (for proxies/load balancers)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr or 'unknown'


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Human readable size
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix