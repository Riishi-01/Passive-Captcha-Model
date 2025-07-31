#!/usr/bin/env python3
"""
Unit Tests for Authentication Service
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import jwt
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

try:
    from app.services.auth_service import AuthService, init_auth_service, get_auth_service
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure backend dependencies are installed")
    sys.exit(1)


class TestAuthService(unittest.TestCase):
    """Test cases for AuthService"""
    
    def setUp(self):
        """Set up test environment"""
        self.redis_mock = Mock()
        self.auth_service = AuthService(self.redis_mock)
    
    def test_init_with_redis(self):
        """Test initialization with Redis"""
        service = AuthService(self.redis_mock)
        self.assertEqual(service.redis, self.redis_mock)
        self.assertEqual(service.admin_secret, 'Admin123')  # Default from env
        
    def test_init_without_redis(self):
        """Test initialization without Redis"""
        service = AuthService(None)
        self.assertIsNone(service.redis)
        
    def test_authenticate_admin_success(self):
        """Test successful admin authentication"""
        with patch.dict(os.environ, {'ADMIN_SECRET': 'testpass'}):
            service = AuthService(None)
            result = service.authenticate_admin('testpass')
            
            self.assertIsNotNone(result)
            self.assertIn('token', result)
            self.assertIn('expires_in', result)
            self.assertEqual(result['expires_in'], 86400)
            
    def test_authenticate_admin_failure(self):
        """Test failed admin authentication"""
        with patch.dict(os.environ, {'ADMIN_SECRET': 'testpass'}):
            service = AuthService(None)
            result = service.authenticate_admin('wrongpass')
            
            self.assertIsNone(result)
            
    def test_validate_token_success(self):
        """Test successful token validation"""
        with patch.dict(os.environ, {'ADMIN_SECRET': 'testpass', 'JWT_SECRET': 'testsecret'}):
            service = AuthService(None)
            
            # First authenticate to get a token
            auth_result = service.authenticate_admin('testpass')
            token = auth_result['token']
            
            # Then validate the token
            user = service.validate_token(token)
            
            self.assertIsNotNone(user)
            self.assertEqual(user.id, 'admin')
            self.assertEqual(user.email, 'admin@passivecaptcha.com')
            
    def test_validate_expired_token(self):
        """Test validation of expired token"""
        with patch.dict(os.environ, {'JWT_SECRET': 'testsecret'}):
            service = AuthService(None)
            
            # Create an expired token
            expired_payload = {
                'admin': True,
                'iat': int((datetime.utcnow() - timedelta(days=2)).timestamp()),
                'exp': int((datetime.utcnow() - timedelta(days=1)).timestamp())
            }
            expired_token = jwt.encode(expired_payload, 'testsecret', algorithm='HS256')
            
            user = service.validate_token(expired_token)
            self.assertIsNone(user)
            
    def test_validate_invalid_token(self):
        """Test validation of invalid token"""
        service = AuthService(None)
        user = service.validate_token('invalid.token.here')
        self.assertIsNone(user)
        
    def test_global_service_initialization(self):
        """Test global service initialization"""
        service = init_auth_service(self.redis_mock)
        self.assertIsInstance(service, AuthService)
        
        retrieved_service = get_auth_service()
        self.assertEqual(service, retrieved_service)


class TestAuthServiceIntegration(unittest.TestCase):
    """Integration tests for AuthService"""
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow"""
        with patch.dict(os.environ, {'ADMIN_SECRET': 'testpass123', 'JWT_SECRET': 'testsecret456'}):
            # Initialize service
            service = init_auth_service(None)
            
            # Authenticate
            auth_result = service.authenticate_admin('testpass123')
            self.assertIsNotNone(auth_result)
            
            token = auth_result['token']
            
            # Validate token
            user = service.validate_token(token)
            self.assertIsNotNone(user)
            self.assertEqual(user.id, 'admin')
            
            # Test wrong password
            failed_auth = service.authenticate_admin('wrongpass')
            self.assertIsNone(failed_auth)


if __name__ == '__main__':
    print("🧪 Running Authentication Service Unit Tests")
    print("=" * 50)
    
    # Set test environment
    os.environ['ADMIN_SECRET'] = 'Admin123'
    os.environ['JWT_SECRET'] = 'test-jwt-secret-key'
    
    unittest.main(verbosity=2)