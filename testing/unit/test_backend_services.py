#!/usr/bin/env python3
"""
Unit tests for backend services
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

class TestAuthService(unittest.TestCase):
    """Test authentication service"""
    
    def setUp(self):
        self.mock_redis = Mock()
        self.mock_redis.setex = Mock()
        self.mock_redis.get = Mock()
        self.mock_redis.delete = Mock()
        self.mock_redis.scan_iter = Mock(return_value=[])
        
        # Create Flask app context for testing
        try:
            from app import create_app
            self.app = create_app()
            self.app_context = self.app.app_context()
            self.app_context.push()
        except:
            # If create_app doesn't exist, create minimal Flask app
            from flask import Flask
            self.app = Flask(__name__)
            self.app_context = self.app.app_context()
            self.app_context.push()
    
    def tearDown(self):
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def test_auth_service_import(self):
        """Test that auth service can be imported"""
        try:
            from app.services.auth_service import AuthService
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Could not import AuthService: {e}")
    
    def test_auth_service_initialization(self):
        """Test auth service initialization"""
        try:
            from app.services.auth_service import AuthService
            auth_service = AuthService(self.mock_redis)
            self.assertIsNotNone(auth_service)
            self.assertEqual(auth_service.redis, self.mock_redis)
        except Exception as e:
            self.fail(f"Auth service initialization failed: {e}")
    
    @patch.dict(os.environ, {'ADMIN_SECRET': 'TestPassword123'})
    def test_admin_authentication_success(self):
        """Test successful admin authentication"""
        try:
            from app.services.auth_service import AuthService
            auth_service = AuthService(self.mock_redis)
            
            result = auth_service.authenticate_admin('TestPassword123')
            self.assertIsNotNone(result)
            self.assertIn('token', result)
            self.assertIn('user', result)
        except Exception as e:
            self.fail(f"Admin authentication test failed: {e}")
    
    @patch.dict(os.environ, {'ADMIN_SECRET': 'TestPassword123'})
    def test_admin_authentication_failure(self):
        """Test failed admin authentication"""
        try:
            from app.services.auth_service import AuthService
            auth_service = AuthService(self.mock_redis)
            
            result = auth_service.authenticate_admin('WrongPassword')
            self.assertIsNone(result)
        except Exception as e:
            self.fail(f"Admin authentication failure test failed: {e}")


class TestWebsiteService(unittest.TestCase):
    """Test website service"""
    
    def setUp(self):
        self.mock_redis = Mock()
        self.mock_redis.setex = Mock()
        self.mock_redis.get = Mock()
        self.mock_redis.scan_iter = Mock(return_value=[])
        self.mock_redis.delete = Mock()
    
    def test_website_service_import(self):
        """Test that website service can be imported"""
        try:
            from app.services.website_service import WebsiteService
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Could not import WebsiteService: {e}")
    
    def test_website_service_initialization(self):
        """Test website service initialization"""
        try:
            from app.services.website_service import WebsiteService
            website_service = WebsiteService(self.mock_redis)
            self.assertIsNotNone(website_service)
            self.assertEqual(website_service.redis, self.mock_redis)
        except Exception as e:
            self.fail(f"Website service initialization failed: {e}")


class TestScriptTokenManager(unittest.TestCase):
    """Test script token manager"""
    
    def setUp(self):
        self.mock_redis = Mock()
        self.mock_redis.setex = Mock()
        self.mock_redis.get = Mock()
        self.mock_redis.exists = Mock(return_value=False)
        self.mock_redis.scan_iter = Mock(return_value=[])
        self.mock_redis.delete = Mock()
        
        # Create Flask app context for testing
        try:
            from app import create_app
            self.app = create_app()
            self.app_context = self.app.app_context()
            self.app_context.push()
        except:
            # If create_app doesn't exist, create minimal Flask app
            from flask import Flask
            self.app = Flask(__name__)
            self.app_context = self.app.app_context()
            self.app_context.push()
    
    def tearDown(self):
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def test_script_token_manager_import(self):
        """Test that script token manager can be imported"""
        try:
            from app.script_token_manager import ScriptTokenManager, ScriptVersion
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Could not import ScriptTokenManager: {e}")
    
    def test_token_generation(self):
        """Test script token generation"""
        try:
            from app.script_token_manager import ScriptTokenManager, ScriptVersion
            
            token_manager = ScriptTokenManager(self.mock_redis)
            token = token_manager.generate_script_token("test-website", ScriptVersion.V2_ENHANCED)
            
            self.assertIsNotNone(token)
            self.assertTrue(hasattr(token, 'script_token'))
            self.assertTrue(hasattr(token, 'website_id'))
            self.assertEqual(token.website_id, "test-website")
            
        except Exception as e:
            self.fail(f"Token generation test failed: {e}")


if __name__ == '__main__':
    unittest.main()