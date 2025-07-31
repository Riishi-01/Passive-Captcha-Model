"""
Integration Tests for API Endpoints
Comprehensive testing of all API endpoints with real Flask app
"""

import unittest
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from unittest.mock import Mock, patch, MagicMock
import tempfile
import sqlite3
from datetime import datetime, timedelta
import jwt

# Mock external dependencies
sys.modules['redis'] = Mock()
sys.modules['app.services'] = Mock()
sys.modules['app.script_token_manager'] = Mock()


class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Create temporary database
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        
        # Mock environment variables
        os.environ['DATABASE_URL'] = f'sqlite:///{cls.db_path}'
        os.environ['JWT_SECRET'] = 'test-secret-key'
        os.environ['ADMIN_SECRET'] = 'TestAdmin123'
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        os.close(cls.db_fd)
        os.unlink(cls.db_path)
    
    def setUp(self):
        """Set up test client"""
        # Import and configure Flask app
        with patch('redis.Redis'), \
             patch('app.services.init_auth_service'), \
             patch('app.services.init_website_service'), \
             patch('app.script_token_manager.init_script_token_manager'):
            
            from app.api.admin_endpoints import admin_bp
            from flask import Flask
            
            self.app = Flask(__name__)
            self.app.config['TESTING'] = True
            self.app.config['JWT_SECRET'] = 'test-secret-key'
            self.app.register_blueprint(admin_bp)
            
            self.client = self.app.test_client()
            self.app_context = self.app.app_context()
            self.app_context.push()
        
        # Mock services
        self.mock_auth_service = Mock()
        self.mock_website_service = Mock()
        self.mock_token_manager = Mock()
        
        # Patch service getters
        self.auth_patcher = patch('app.api.admin_endpoints.get_auth_service')
        self.website_patcher = patch('app.api.admin_endpoints.get_website_service')
        self.token_patcher = patch('app.api.admin_endpoints.get_script_token_manager')
        
        self.mock_get_auth = self.auth_patcher.start()
        self.mock_get_website = self.website_patcher.start()
        self.mock_get_token = self.token_patcher.start()
        
        self.mock_get_auth.return_value = self.mock_auth_service
        self.mock_get_website.return_value = self.mock_website_service
        self.mock_get_token.return_value = self.mock_token_manager
        
        # Generate test JWT token
        self.test_token = self._generate_test_token()
    
    def tearDown(self):
        """Clean up after each test"""
        self.auth_patcher.stop()
        self.website_patcher.stop()
        self.token_patcher.stop()
        self.app_context.pop()
    
    def _generate_test_token(self):
        """Generate a valid JWT token for testing"""
        payload = {
            'admin': True,
            'iat': datetime.utcnow().timestamp(),
            'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp()
        }
        return jwt.encode(payload, 'test-secret-key', algorithm='HS256')
    
    def _get_auth_headers(self):
        """Get authorization headers for requests"""
        return {'Authorization': f'Bearer {self.test_token}'}
    
    def test_login_endpoint_success(self):
        """Test successful login"""
        # Mock successful authentication
        self.mock_auth_service.authenticate_admin.return_value = {
            'token': self.test_token,
            'user': {
                'id': 'admin',
                'email': 'admin@test.com',
                'name': 'Administrator',
                'role': 'admin',
                'last_login': datetime.utcnow().isoformat()
            },
            'expires_in': 3600,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Make request
        response = self.client.post('/admin/login', 
                                  json={'password': 'TestAdmin123'},
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['role'], 'admin')
    
    def test_login_endpoint_failure(self):
        """Test failed login"""
        # Mock failed authentication
        self.mock_auth_service.authenticate_admin.return_value = None
        
        # Make request
        response = self.client.post('/admin/login',
                                  json={'password': 'WrongPassword'},
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_CREDENTIALS')
    
    def test_login_missing_password(self):
        """Test login without password"""
        response = self.client.post('/admin/login',
                                  json={},
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'MISSING_PASSWORD')
    
    def test_logout_endpoint(self):
        """Test logout endpoint"""
        # Mock successful logout
        self.mock_auth_service.logout.return_value = True
        
        # Make request
        response = self.client.post('/admin/logout',
                                  headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_verify_token_endpoint(self):
        """Test token verification endpoint"""
        # Mock user object
        mock_user = Mock()
        mock_user.to_dict.return_value = {
            'id': 'admin',
            'email': 'admin@test.com',
            'role': 'admin'
        }
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.get('/admin/verify-token',
                                 headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('user', data['data'])
    
    def test_unauthorized_access(self):
        """Test access without authorization"""
        response = self.client.get('/admin/verify-token')
        
        # Assertions
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'MISSING_AUTH')
    
    def test_invalid_token_access(self):
        """Test access with invalid token"""
        # Mock invalid token validation
        self.mock_auth_service.validate_token.return_value = None
        
        response = self.client.get('/admin/verify-token',
                                 headers={'Authorization': 'Bearer invalid-token'})
        
        # Assertions
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'INVALID_TOKEN')
    
    def test_get_websites_endpoint(self):
        """Test get websites endpoint"""
        # Mock website data
        mock_website = Mock()
        mock_website.to_dict.return_value = {
            'id': 'test-id',
            'name': 'Test Website',
            'url': 'https://test.com',
            'status': 'active',
            'total_verifications': 100
        }
        self.mock_website_service.get_all_websites.return_value = [mock_website]
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.get('/admin/websites',
                                 headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['websites']), 1)
        self.assertEqual(data['data']['websites'][0]['name'], 'Test Website')
    
    def test_create_website_endpoint(self):
        """Test create website endpoint"""
        # Mock website creation
        mock_website = Mock()
        mock_website.to_dict.return_value = {
            'id': 'new-id',
            'name': 'New Website',
            'url': 'https://new.com',
            'status': 'pending_integration'
        }
        self.mock_website_service.create_website.return_value = mock_website
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.post('/admin/websites',
                                  json={
                                      'name': 'New Website',
                                      'url': 'https://new.com',
                                      'description': 'Test description'
                                  },
                                  headers=self._get_auth_headers(),
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['website']['name'], 'New Website')
    
    def test_create_website_missing_data(self):
        """Test create website with missing data"""
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request without required fields
        response = self.client.post('/admin/websites',
                                  json={'name': 'Test'},  # Missing URL
                                  headers=self._get_auth_headers(),
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'MISSING_FIELDS')
    
    def test_update_website_endpoint(self):
        """Test update website endpoint"""
        # Mock website update
        self.mock_website_service.update_website.return_value = True
        
        # Mock updated website
        mock_website = Mock()
        mock_website.to_dict.return_value = {
            'id': 'test-id',
            'name': 'Updated Website',
            'url': 'https://updated.com'
        }
        self.mock_website_service.get_website.return_value = mock_website
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.put('/admin/websites/test-id',
                                 json={'name': 'Updated Website'},
                                 headers=self._get_auth_headers(),
                                 content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_delete_website_endpoint(self):
        """Test delete website endpoint"""
        # Mock website deletion
        self.mock_website_service.delete_website.return_value = True
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.delete('/admin/websites/test-id',
                                    headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_delete_nonexistent_website(self):
        """Test deleting non-existent website"""
        # Mock website not found
        self.mock_website_service.delete_website.return_value = False
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.delete('/admin/websites/nonexistent',
                                    headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'WEBSITE_NOT_FOUND')
    
    def test_toggle_website_status(self):
        """Test toggle website status endpoint"""
        # Mock status toggle
        from app.services.website_service import WebsiteStatus
        self.mock_website_service.toggle_website_status.return_value = WebsiteStatus.INACTIVE
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.patch('/admin/websites/test-id/toggle-status',
                                   headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['new_status'], 'inactive')
    
    def test_generate_script_token_endpoint(self):
        """Test script token generation endpoint"""
        # Mock token generation
        mock_token = Mock()
        mock_token.to_dict.return_value = {
            'script_token': 'test-token-123',
            'website_id': 'test-id',
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        self.mock_token_manager.generate_script_token.return_value = mock_token
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.post('/admin/scripts/generate',
                                  json={
                                      'website_id': 'test-id',
                                      'script_version': 'v2_enhanced'
                                  },
                                  headers=self._get_auth_headers(),
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data['data'])
        self.assertIn('integration', data['data'])
    
    def test_get_script_token_endpoint(self):
        """Test get script token endpoint"""
        # Mock token retrieval
        mock_token = Mock()
        mock_token.to_dict.return_value = {
            'script_token': 'test-token-123',
            'website_id': 'test-id',
            'status': 'active'
        }
        self.mock_token_manager.get_website_token.return_value = mock_token
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.get('/admin/scripts/tokens/test-id',
                                 headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data['data'])
    
    def test_get_script_token_not_found(self):
        """Test get script token when not found"""
        # Mock token not found
        self.mock_token_manager.get_website_token.return_value = None
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.get('/admin/scripts/tokens/nonexistent',
                                 headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'TOKEN_NOT_FOUND')
    
    def test_revoke_script_token_endpoint(self):
        """Test script token revocation endpoint"""
        # Mock token revocation
        self.mock_token_manager.revoke_token.return_value = True
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.post('/admin/scripts/tokens/test-id/revoke',
                                  headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('revoked_at', data['data'])
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        # Make request (no auth required for health check)
        response = self.client.get('/admin/health')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('services', data)
    
    def test_get_statistics_endpoint(self):
        """Test get statistics endpoint"""
        # Mock statistics
        self.mock_auth_service.get_auth_statistics.return_value = {
            'active_sessions': 2,
            'total_tokens': 5
        }
        self.mock_website_service.get_website_statistics.return_value = {
            'total_websites': 3,
            'active_websites': 2
        }
        self.mock_token_manager.get_token_stats.return_value = {
            'total_tokens': 4,
            'active_tokens': 3
        }
        
        # Mock user validation
        mock_user = Mock()
        self.mock_auth_service.validate_token.return_value = mock_user
        
        # Make request
        response = self.client.get('/admin/statistics',
                                 headers=self._get_auth_headers())
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('auth', data['data'])
        self.assertIn('websites', data['data'])
        self.assertIn('script_tokens', data['data'])
    
    def test_service_unavailable_scenarios(self):
        """Test scenarios when services are unavailable"""
        # Mock service unavailable
        self.mock_get_auth.return_value = None
        
        # Make request
        response = self.client.post('/admin/login',
                                  json={'password': 'TestAdmin123'},
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'SERVICE_UNAVAILABLE')
    
    def test_error_handling_in_endpoints(self):
        """Test error handling in API endpoints"""
        # Mock service raising exception
        self.mock_auth_service.authenticate_admin.side_effect = Exception("Database error")
        
        # Make request
        response = self.client.post('/admin/login',
                                  json={'password': 'TestAdmin123'},
                                  content_type='application/json')
        
        # Assertions
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'INTERNAL_ERROR')


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)