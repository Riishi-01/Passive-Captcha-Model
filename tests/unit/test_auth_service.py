"""
Unit Tests for Authentication Service
Comprehensive testing of authentication and session management
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from datetime import datetime, timedelta
import json
import jwt
import redis

# Mock dependencies before importing
sys.modules['flask'] = Mock()

from app.services.auth_service import AuthService, AuthenticatedUser, UserRole


class TestAuthService(unittest.TestCase):
    """Test cases for AuthService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_redis = Mock(spec=redis.Redis)
        self.service = AuthService(self.mock_redis)
        
        # Override config for testing
        self.service.jwt_secret = 'test-secret'
        self.service.admin_secret = 'TestPassword123'
        self.service.session_ttl = 3600  # 1 hour
        
        # Mock current_app
        self.mock_app_patcher = patch('app.services.auth_service.current_app')
        self.mock_app = self.mock_app_patcher.start()
        self.mock_app.logger = Mock()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.mock_app_patcher.stop()
    
    def test_authenticated_user_creation(self):
        """Test AuthenticatedUser object creation and serialization"""
        now = datetime.utcnow()
        user = AuthenticatedUser(
            id="admin",
            email="admin@test.com",
            name="Administrator",
            role=UserRole.ADMIN,
            last_login=now
        )
        
        # Test object creation
        self.assertEqual(user.id, "admin")
        self.assertEqual(user.role, UserRole.ADMIN)
        
        # Test serialization
        user_dict = user.to_dict()
        self.assertEqual(user_dict['id'], "admin")
        self.assertEqual(user_dict['role'], "admin")
        self.assertEqual(user_dict['email'], "admin@test.com")
    
    def test_authenticate_admin_success(self):
        """Test successful admin authentication"""
        # Mock datetime for consistent token generation
        with patch('app.services.auth_service.datetime') as mock_datetime:
            now = datetime(2025, 1, 30, 12, 0, 0)
            mock_datetime.utcnow.return_value = now
            
            # Execute test
            result = self.service.authenticate_admin('TestPassword123')
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertIn('token', result)
            self.assertIn('user', result)
            self.assertEqual(result['user']['role'], 'admin')
            
            # Verify Redis operations
            self.mock_redis.setex.assert_called()
            
            # Verify JWT token
            token = result['token']
            decoded = jwt.decode(token, 'test-secret', algorithms=['HS256'])
            self.assertTrue(decoded['admin'])
    
    def test_authenticate_admin_failure(self):
        """Test failed admin authentication"""
        result = self.service.authenticate_admin('WrongPassword')
        
        # Assertions
        self.assertIsNone(result)
        self.mock_redis.setex.assert_not_called()
    
    def test_validate_token_success(self):
        """Test successful token validation"""
        # Create a valid token
        now = datetime.utcnow()
        exp_time = now + timedelta(seconds=3600)
        payload = {
            'admin': True,
            'iat': int(now.timestamp()),
            'exp': int(exp_time.timestamp())
        }
        token = jwt.encode(payload, 'test-secret', algorithm='HS256')
        
        # Mock Redis responses
        session_id = 'test-session-id'
        session_data = {
            'user': {
                'id': 'admin',
                'email': 'admin@test.com',
                'name': 'Administrator',
                'role': 'admin',
                'last_login': now.isoformat()
            },
            'token': token,
            'created_at': now.isoformat(),
            'expires_at': exp_time.isoformat()
        }
        
        self.mock_redis.get.side_effect = [
            session_id.encode(),  # Token lookup
            json.dumps(session_data).encode()  # Session data
        ]
        
        # Execute test
        user = self.service.validate_token(token)
        
        # Assertions
        self.assertIsNotNone(user)
        self.assertEqual(user.id, 'admin')
        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertEqual(user.email, 'admin@test.com')
    
    def test_validate_token_expired(self):
        """Test validation of expired token"""
        # Create an expired token
        now = datetime.utcnow()
        exp_time = now - timedelta(seconds=3600)  # Expired 1 hour ago
        payload = {
            'admin': True,
            'iat': int((now - timedelta(seconds=7200)).timestamp()),
            'exp': int(exp_time.timestamp())
        }
        token = jwt.encode(payload, 'test-secret', algorithm='HS256')
        
        # Mock Redis responses
        session_id = 'test-session-id'
        self.mock_redis.get.side_effect = [
            session_id.encode(),  # Token lookup
            json.dumps({'user': {}}).encode()  # Session data
        ]
        
        # Execute test
        user = self.service.validate_token(token)
        
        # Assertions
        self.assertIsNone(user)
    
    def test_validate_token_invalid(self):
        """Test validation of invalid token"""
        # Use invalid token
        invalid_token = 'invalid.token.here'
        
        # Execute test
        user = self.service.validate_token(invalid_token)
        
        # Assertions
        self.assertIsNone(user)
    
    def test_validate_token_not_in_redis(self):
        """Test validation when token not found in Redis"""
        # Create a valid token
        now = datetime.utcnow()
        exp_time = now + timedelta(seconds=3600)
        payload = {
            'admin': True,
            'iat': int(now.timestamp()),
            'exp': int(exp_time.timestamp())
        }
        token = jwt.encode(payload, 'test-secret', algorithm='HS256')
        
        # Mock Redis returning None (token not found)
        self.mock_redis.get.return_value = None
        
        # Execute test
        user = self.service.validate_token(token)
        
        # Assertions
        self.assertIsNone(user)
    
    def test_logout_success(self):
        """Test successful logout"""
        token = 'test-token'
        session_id = 'test-session-id'
        
        # Mock Redis responses
        self.mock_redis.get.return_value = session_id.encode()
        
        # Execute test
        result = self.service.logout(token)
        
        # Assertions
        self.assertTrue(result)
        
        # Verify Redis operations
        token_key = f"token:{token}"
        session_key = f"session:{session_id}"
        
        calls = self.mock_redis.delete.call_args_list
        self.assertTrue(any(session_key in str(call) for call in calls))
    
    def test_logout_token_not_found(self):
        """Test logout when token not found"""
        token = 'non-existent-token'
        
        # Mock Redis returning None
        self.mock_redis.get.return_value = None
        
        # Execute test
        result = self.service.logout(token)
        
        # Assertions
        self.assertFalse(result)
    
    def test_refresh_session_success(self):
        """Test successful session refresh"""
        # Create a valid token and user
        now = datetime.utcnow()
        exp_time = now + timedelta(seconds=3600)
        payload = {
            'admin': True,
            'iat': int(now.timestamp()),
            'exp': int(exp_time.timestamp())
        }
        token = jwt.encode(payload, 'test-secret', algorithm='HS256')
        
        session_id = 'test-session-id'
        session_data = {
            'user': {
                'id': 'admin',
                'email': 'admin@test.com',
                'name': 'Administrator',
                'role': 'admin',
                'last_login': now.isoformat()
            },
            'token': token,
            'created_at': now.isoformat(),
            'expires_at': exp_time.isoformat()
        }
        
        # Mock Redis responses for validation
        self.mock_redis.get.side_effect = [
            session_id.encode(),  # Token lookup for validation
            json.dumps(session_data).encode(),  # Session data for validation
            session_id.encode(),  # Token lookup for refresh
            json.dumps(session_data).encode()  # Session data for refresh
        ]
        
        # Execute test
        with patch('app.services.auth_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = now
            result = self.service.refresh_session(token)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['token'], token)
        self.assertIn('user', result)
        self.assertIn('expires_in', result)
    
    def test_get_active_sessions(self):
        """Test retrieval of active sessions"""
        # Mock Redis scan results
        session_keys = [b'session:sess1', b'session:sess2']
        session_data = {
            'user': {'id': 'admin', 'name': 'Admin'},
            'created_at': '2025-01-30T12:00:00',
            'expires_at': '2025-01-30T13:00:00'
        }
        
        self.mock_redis.scan_iter.return_value = session_keys
        self.mock_redis.get.return_value = json.dumps(session_data).encode()
        
        # Execute test
        sessions = self.service.get_active_sessions()
        
        # Assertions
        self.assertEqual(len(sessions), 2)
        self.assertEqual(sessions[0]['user']['id'], 'admin')
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions"""
        # Mock expired session
        now = datetime.utcnow()
        expired_time = now - timedelta(hours=1)
        
        session_data = {
            'token': 'expired-token',
            'expires_at': expired_time.isoformat()
        }
        
        session_keys = [b'session:expired-sess']
        self.mock_redis.scan_iter.return_value = session_keys
        self.mock_redis.get.return_value = json.dumps(session_data).encode()
        
        # Execute test
        cleaned_count = self.service.cleanup_expired_sessions()
        
        # Assertions
        self.assertEqual(cleaned_count, 1)
        self.mock_redis.delete.assert_called()
    
    def test_get_auth_statistics(self):
        """Test authentication statistics"""
        # Mock active sessions
        with patch.object(self.service, 'get_active_sessions') as mock_sessions:
            mock_sessions.return_value = [{'session': 'data'}]
            
            # Mock token scan
            self.mock_redis.scan_iter.return_value = [b'token:1', b'token:2', b'token:3']
            
            # Execute test
            stats = self.service.get_auth_statistics()
            
            # Assertions
            self.assertEqual(stats['active_sessions'], 1)
            self.assertEqual(stats['total_tokens'], 3)
            self.assertEqual(stats['session_ttl'], 3600)
    
    def test_session_id_generation(self):
        """Test session ID generation"""
        session_id = self.service._generate_session_id()
        
        # Assertions
        self.assertTrue(session_id.startswith('sess_'))
        self.assertGreater(len(session_id), 10)
    
    def test_session_cleanup_with_malformed_data(self):
        """Test session cleanup with malformed JSON data"""
        # Mock malformed session data
        session_keys = [b'session:malformed']
        self.mock_redis.scan_iter.return_value = session_keys
        self.mock_redis.get.return_value = b'invalid-json'
        
        # Execute test
        cleaned_count = self.service.cleanup_expired_sessions()
        
        # Assertions
        self.assertEqual(cleaned_count, 1)  # Should clean up malformed data
        self.mock_redis.delete.assert_called()
    
    def test_error_handling_in_validation(self):
        """Test error handling during token validation"""
        # Mock Redis raising an exception
        self.mock_redis.get.side_effect = Exception("Redis connection error")
        
        # Execute test
        user = self.service.validate_token('any-token')
        
        # Assertions
        self.assertIsNone(user)  # Should gracefully handle errors
    
    def test_multiple_role_support(self):
        """Test support for multiple user roles"""
        # Test different user roles
        roles = [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER]
        
        for role in roles:
            user = AuthenticatedUser(
                id=f"user-{role.value}",
                email=f"{role.value}@test.com",
                name=f"{role.value.title()} User",
                role=role,
                last_login=datetime.utcnow()
            )
            
            user_dict = user.to_dict()
            self.assertEqual(user_dict['role'], role.value)


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)