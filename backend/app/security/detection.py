# -*- coding: utf-8 -*-
"""
Enhanced Bot Detection and Security Module
Centralized security logic for the passive CAPTCHA system
"""

import time
import json
import base64
import logging
from typing import Dict, List, Optional, Tuple, Any
from flask import request, jsonify

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Centralized security configuration with app config integration"""
    
    def __init__(self, app_config=None):
        """Initialize with optional app configuration"""
        from app.config import get_config
        self.config = app_config or get_config()
    
    @property
    def AUTOMATION_THRESHOLD(self):
        return self.config.AUTOMATION_THRESHOLD
    
    @property 
    def ML_CONFIDENCE_THRESHOLD(self):
        return self.config.ML_CONFIDENCE_THRESHOLD
    
    @property
    def MIN_INTERACTION_TIME(self):
        return self.config.MIN_INTERACTION_TIME
    
    # Static thresholds
    HUMAN_SCORE_THRESHOLD = 0.5
    AUTOMATION_HUMAN_COMBINED_THRESHOLD = 0.2
    
    # IP Tracking
    IP_TRACKING_WINDOW = 3600  # 1 hour in seconds
    MAX_SUSPICIOUS_ATTEMPTS = 3
    
    # Bot patterns
    BOT_USER_AGENTS = ['python', 'requests', 'bot', 'curl', 'wget']
    WEBDRIVER_INDICATORS = ['webdriver', 'selenium', 'phantomjs', 'headless']
    
    # Skip paths
    SKIP_PATHS = ['/admin', '/api/', '/health', '/static/', '/assets/', '/favicon.ico', '/robots.txt']


class IPTracker:
    """Progressive IP tracking for enhanced security"""
    
    def __init__(self):
        self.tracking_data = {}
    
    def track_suspicious_activity(self, ip_address: str, event_type: str) -> bool:
        """
        Track suspicious activities per IP for progressive blocking
        Returns True if IP should be blocked
        """
        current_time = time.time()
        
        if ip_address not in self.tracking_data:
            self.tracking_data[ip_address] = {
                'attempts': 0, 
                'first_attempt': current_time, 
                'events': []
            }
        
        # Clean old entries (older than tracking window)
        if current_time - self.tracking_data[ip_address]['first_attempt'] > self.IP_TRACKING_WINDOW:
            self.tracking_data[ip_address] = {
                'attempts': 0, 
                'first_attempt': current_time, 
                'events': []
            }
        
        # Record the event
        self.tracking_data[ip_address]['attempts'] += 1
        self.tracking_data[ip_address]['events'].append({
            'type': event_type, 
            'time': current_time
        })
        
        # Check if IP should be blocked
        return self.tracking_data[ip_address]['attempts'] >= self.MAX_SUSPICIOUS_ATTEMPTS
    
    def get_ip_stats(self, ip_address: str) -> Dict[str, Any]:
        """Get statistics for an IP address"""
        return self.tracking_data.get(ip_address, {
            'attempts': 0,
            'events': []
        })


class BotDetector:
    """Comprehensive bot detection logic"""
    
    def __init__(self, security_config):
        self.config = security_config
    
    def detect_bot_user_agent(self, user_agent: str) -> bool:
        """Check if user agent indicates bot traffic"""
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in self.config.BOT_USER_AGENTS)
    
    def detect_webdriver_properties(self, user_agent: str, token_data: Dict[str, Any]) -> bool:
        """Enhanced WebDriver and automation detection"""
        user_agent_lower = user_agent.lower()
        
        # Check user agent patterns
        user_agent_indicators = any(
            indicator in user_agent_lower 
            for indicator in self.config.WEBDRIVER_INDICATORS
        )
        
        # Check token-based indicators
        token_indicators = any([
            token_data.get('webdriverDetected', False),
            token_data.get('automationFlags', False),
            token_data.get('chromeDriverDetected', False),
            token_data.get('webglRendererAnomaly', False),
            token_data.get('navigatorWebdriver', False)
        ])
        
        return user_agent_indicators or token_indicators
    
    def validate_interaction_time(self, token_data: Dict[str, Any]) -> bool:
        """Validate minimum interaction time"""
        session_duration = token_data.get('sessionDuration', 0)
        return session_duration >= self.config.MIN_INTERACTION_TIME
    
    def evaluate_automation_score(self, token_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Extract and evaluate automation score and indicators"""
        automation_score = token_data.get('automationScore', 0)
        automation_indicators = token_data.get('automationIndicators', [])
        return automation_score, automation_indicators
    
    def evaluate_combined_risk(self, automation_score: float, human_score: float) -> bool:
        """Evaluate combined automation and human scores for risk assessment"""
        return (automation_score > self.config.AUTOMATION_HUMAN_COMBINED_THRESHOLD and 
                human_score < self.config.HUMAN_SCORE_THRESHOLD)


class SecurityValidator:
    """Main security validation orchestrator"""
    
    def __init__(self, app_config=None):
        self.security_config = SecurityConfig(app_config)
        self.ip_tracker = IPTracker()
        self.bot_detector = BotDetector(self.security_config)
    
    def should_skip_validation(self, request_path: str, method: str) -> bool:
        """Check if request should skip validation"""
        if method == 'OPTIONS':
            return True
        return any(request_path.startswith(path) for path in self.security_config.SKIP_PATHS)
    
    def validate_request(self, user_agent: str, ip_address: str, behavioral_token: Optional[str]) -> Optional[Tuple[Dict[str, Any], int]]:
        """
        Main request validation logic
        Returns (error_response, status_code) if request should be blocked, None if allowed
        """
        try:
            from app.ml import log_detection_event
        except ImportError:
            logger.warning("ML module not available for logging")
            log_detection_event = lambda *args, **kwargs: None
        
        # Check progressive IP blocking
        if self.ip_tracker.track_suspicious_activity(ip_address, 'access_attempt'):
            log_detection_event('ip_blocked_progressive', {
                'user_agent': user_agent,
                'ip_address': ip_address,
                'result': 'progressive_ip_blocking',
                'confidence': 0.95
            })
            logger.warning(f"Progressive IP block: {ip_address}")
            return jsonify({'error': 'Access denied - repeated suspicious activity'}), 403
        
        # Check for obvious bot patterns
        if not behavioral_token and self.bot_detector.detect_bot_user_agent(user_agent):
            self.ip_tracker.track_suspicious_activity(ip_address, 'bot_user_agent')
            log_detection_event('bot_blocked', {
                'user_agent': user_agent,
                'ip_address': ip_address,
                'result': 'blocked_user_agent',
                'confidence': 1.0
            })
            logger.warning(f"Blocked bot request: {user_agent}")
            return jsonify({'error': 'Access denied - automated traffic detected'}), 403
        
        # Validate behavioral token if present
        if behavioral_token:
            return self._validate_behavioral_token(behavioral_token, user_agent, ip_address, log_detection_event)
        else:
            # Block browsers without tokens (strict enforcement)
            if any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari']):
                log_detection_event('browser_blocked_no_token', {
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'result': 'browser_missing_required_token',
                    'confidence': 0.85
                })
                logger.warning(f"Blocked browser without behavioral token: {user_agent}")
                return jsonify({'error': 'Access denied - behavioral validation required'}), 403
        
        return None
    
    def _validate_behavioral_token(self, behavioral_token: str, user_agent: str, ip_address: str, log_detection_event) -> Optional[Tuple[Dict[str, Any], int]]:
        """Validate behavioral token with comprehensive ML and security checks"""
        try:
            from app.ml import validate_behavioral_token, extract_features, predict_human_probability
            
            # Validate token structure
            validation = validate_behavioral_token(behavioral_token)
            if not validation['valid']:
                log_detection_event('token_invalid', {
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'result': validation['reason'],
                    'confidence': 0.8
                })
                logger.warning(f"Invalid behavioral token: {validation['reason']}")
                return jsonify({'error': 'Invalid behavioral validation'}), 403
            
            # Parse token data
            token_data = json.loads(base64.b64decode(behavioral_token).decode())
            
            # WebDriver detection
            if self.bot_detector.detect_webdriver_properties(user_agent, token_data):
                self.ip_tracker.track_suspicious_activity(ip_address, 'webdriver_detected')
                log_detection_event('webdriver_blocked', {
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'result': 'webdriver_properties_detected',
                    'confidence': 0.95
                })
                logger.warning(f"WebDriver blocked: {user_agent}")
                return jsonify({'error': 'Access denied - automation tools detected'}), 403
            
            # Interaction time validation
            if not self.bot_detector.validate_interaction_time(token_data):
                session_duration = token_data.get('sessionDuration', 0)
                log_detection_event('insufficient_interaction', {
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'result': f'session_too_short_{session_duration}ms',
                    'confidence': 0.9
                })
                logger.warning(f"Blocked insufficient interaction: {session_duration}ms")
                return jsonify({'error': 'Access denied - insufficient interaction time'}), 403
            
            # Automation score evaluation
            automation_score, automation_indicators = self.bot_detector.evaluate_automation_score(token_data)
            if automation_score > self.security_config.AUTOMATION_THRESHOLD:
                self.ip_tracker.track_suspicious_activity(ip_address, 'automation_detected')
                log_detection_event('automation_blocked', {
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'result': f'automation_detected_{"|".join(automation_indicators)}',
                    'confidence': automation_score
                })
                logger.warning(f"Automation blocked: {automation_indicators}, score {automation_score}")
                return jsonify({'error': 'Access denied - browser automation detected'}), 403
            
            # ML prediction
            request_data = self._build_ml_request_data(token_data, user_agent)
            features = extract_features(request_data)
            ml_prediction = predict_human_probability(features)
            
            if not ml_prediction['isHuman'] or ml_prediction['confidence'] < self.security_config.ML_CONFIDENCE_THRESHOLD:
                log_detection_event('ml_blocked', {
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'result': 'ml_prediction_bot',
                    'confidence': ml_prediction['confidence']
                })
                logger.warning(f"ML blocked request: confidence {ml_prediction['confidence']}")
                return jsonify({'error': 'Access denied - automated behavior detected'}), 403
            
            # Combined risk assessment
            human_score = token_data.get('humanScore', 0)
            if self.bot_detector.evaluate_combined_risk(automation_score, human_score):
                log_detection_event('combined_blocked', {
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'result': f'automation_{automation_score}_human_{human_score}',
                    'confidence': 0.8
                })
                logger.warning(f"Combined detection blocked: automation {automation_score}, human {human_score}")
                return jsonify({'error': 'Access denied - suspicious behavioral patterns'}), 403
            
            # Log successful validation
            log_detection_event('human_verified', {
                'user_agent': user_agent,
                'ip_address': ip_address,
                'result': 'ml_prediction_human',
                'confidence': ml_prediction['confidence']
            })
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            # Fail securely - block on validation errors
            return jsonify({'error': 'Validation error - access denied'}), 403
        
        return None
    
    def _build_ml_request_data(self, token_data: Dict[str, Any], user_agent: str) -> Dict[str, Any]:
        """Build request data structure for ML analysis"""
        return {
            'mouseMovements': [
                {'x': i*10, 'y': i*5, 'timestamp': i*100} 
                for i in range(token_data.get('mouseEvents', 0))
            ],
            'keystrokes': [
                {'timestamp': i*200} 
                for i in range(token_data.get('keyEvents', 0))
            ],
            'scrollEvents': [
                {'y': i*50} 
                for i in range(token_data.get('scrollEvents', 0))
            ],
            'sessionDuration': token_data.get('sessionDuration', 0),
            'fingerprint': {
                'userAgent': user_agent,
                'hardwareConcurrency': 4,
                'screenWidth': 1920,
                'screenHeight': 1080
            }
        }


# Global security validator instance
security_validator = SecurityValidator()


def get_security_validator() -> SecurityValidator:
    """Get the global security validator instance"""
    return security_validator