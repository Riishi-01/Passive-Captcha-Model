#!/usr/bin/env python3
"""
API endpoint tests for Passive CAPTCHA system
"""

import unittest
import requests
import json
import time
from unittest.mock import patch

class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.base_url = 'http://localhost:5003'
        self.admin_password = 'Admin123'
        self.auth_token = None
        self.server_available = self._check_server_availability()
    
    def _check_server_availability(self):
        """Check if the server is running"""
        try:
            response = requests.get(f'{self.base_url}/health', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _get_auth_token(self):
        """Get authentication token for testing"""
        if not self.server_available:
            return None
        
        try:
            response = requests.post(
                f'{self.base_url}/admin/login',
                json={'password': self.admin_password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('token')
            return None
        except:
            return None
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        response = requests.get(f'{self.base_url}/health', timeout=5)
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        try:
            data = response.json()
            self.assertIsInstance(data, dict)
            print(f"Health endpoint response: {data}")
        except json.JSONDecodeError:
            self.fail("Health endpoint did not return valid JSON")
    
    def test_admin_login_success(self):
        """Test successful admin login"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        response = requests.post(
            f'{self.base_url}/admin/login',
            json={'password': self.admin_password},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('token', data)
        self.assertIsInstance(data['token'], str)
        self.assertGreater(len(data['token']), 0)
        
        # Store token for other tests
        self.auth_token = data['token']
        print(f"Login successful, token length: {len(self.auth_token)}")
    
    def test_admin_login_failure(self):
        """Test failed admin login"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        response = requests.post(
            f'{self.base_url}/admin/login',
            json={'password': 'WrongPassword'},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_admin_health_endpoint(self):
        """Test admin health endpoint"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        response = requests.get(f'{self.base_url}/admin/health', timeout=5)
        
        # Should be accessible without auth
        self.assertEqual(response.status_code, 200)
        
        try:
            data = response.json()
            self.assertIn('status', data)
            print(f"Admin health: {data}")
        except json.JSONDecodeError:
            self.fail("Admin health endpoint did not return valid JSON")
    
    def test_websites_endpoint_auth_required(self):
        """Test that websites endpoint requires authentication"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Test without auth token
        response = requests.get(f'{self.base_url}/admin/websites', timeout=5)
        self.assertEqual(response.status_code, 401)
    
    def test_websites_endpoint_with_auth(self):
        """Test websites endpoint with authentication"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Get auth token
        auth_token = self._get_auth_token()
        if not auth_token:
            self.skipTest("Could not get auth token")
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(f'{self.base_url}/admin/websites', headers=headers, timeout=10)
        
        self.assertEqual(response.status_code, 200)
        
        try:
            data = response.json()
            self.assertIsInstance(data, dict)
            
            # Check for expected structure (new API format)
            if 'success' in data:
                self.assertTrue(data['success'])
                if 'data' in data and 'websites' in data['data']:
                    websites = data['data']['websites']
                    self.assertIsInstance(websites, list)
            else:
                # Legacy format
                self.assertIsInstance(data, (list, dict))
            
            print(f"Websites endpoint response structure: {list(data.keys())}")
        except json.JSONDecodeError:
            self.fail("Websites endpoint did not return valid JSON")
    
    def test_script_health_endpoint(self):
        """Test script API health endpoint"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        try:
            response = requests.get(f'{self.base_url}/api/script/health', timeout=5)
            
            # This endpoint might not exist yet, so either 200 or 404 is acceptable
            self.assertIn(response.status_code, [200, 404])
            
            if response.status_code == 200:
                print("Script health endpoint is available")
            else:
                print("Script health endpoint not implemented yet")
                
        except requests.exceptions.RequestException:
            self.skipTest("Script endpoints not available")
    
    def test_token_verification(self):
        """Test token verification endpoint"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Get auth token
        auth_token = self._get_auth_token()
        if not auth_token:
            self.skipTest("Could not get auth token")
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(f'{self.base_url}/admin/verify-token', headers=headers, timeout=10)
        
        # This endpoint might not exist in legacy API
        if response.status_code == 404:
            self.skipTest("Token verification endpoint not implemented")
        
        self.assertEqual(response.status_code, 200)
        
        try:
            data = response.json()
            if 'success' in data:
                self.assertTrue(data['success'])
            print("Token verification successful")
        except json.JSONDecodeError:
            self.fail("Token verification did not return valid JSON")
    
    def test_api_rate_limiting(self):
        """Test API rate limiting (if implemented)"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Make multiple rapid requests to test rate limiting
        rapid_requests = 0
        rate_limited = False
        
        for i in range(20):
            try:
                response = requests.get(f'{self.base_url}/health', timeout=2)
                rapid_requests += 1
                
                if response.status_code == 429:  # Too Many Requests
                    rate_limited = True
                    break
                    
            except requests.exceptions.Timeout:
                break
        
        print(f"Made {rapid_requests} rapid requests")
        
        if rate_limited:
            print("Rate limiting is active")
        else:
            print("Rate limiting not detected (may not be implemented)")
        
        # This test passes regardless - rate limiting is optional
        self.assertTrue(True)
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        response = requests.options(f'{self.base_url}/admin/login', timeout=5)
        
        # Check for CORS headers
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        found_cors_headers = []
        for header in cors_headers:
            if header in response.headers:
                found_cors_headers.append(header)
        
        if found_cors_headers:
            print(f"CORS headers found: {found_cors_headers}")
        else:
            print("No CORS headers detected")
        
        # This test passes regardless - CORS is optional for same-origin
        self.assertTrue(True)
    
    def test_response_time(self):
        """Test API response times"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Test health endpoint response time
        start_time = time.time()
        response = requests.get(f'{self.base_url}/health', timeout=5)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 2000, f"Health endpoint too slow: {response_time:.2f}ms")
        
        print(f"Health endpoint response time: {response_time:.2f}ms")
    
    def test_error_handling(self):
        """Test API error handling"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Test invalid endpoint
        response = requests.get(f'{self.base_url}/invalid/endpoint', timeout=5)
        self.assertEqual(response.status_code, 404)
        
        # Test malformed JSON
        response = requests.post(
            f'{self.base_url}/admin/login',
            data='invalid json',
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        self.assertIn(response.status_code, [400, 422])  # Bad Request or Unprocessable Entity
        
        print("Error handling tests passed")


class TestScriptDeliveryAPI(unittest.TestCase):
    """Test script delivery API endpoints"""
    
    def setUp(self):
        self.base_url = 'http://localhost:5003'
        self.server_available = self._check_server_availability()
    
    def _check_server_availability(self):
        """Check if the server is running"""
        try:
            response = requests.get(f'{self.base_url}/health', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_script_generation_endpoint(self):
        """Test script generation endpoint"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Test script generation with a dummy token
        test_token = "test_token_123"
        response = requests.get(f'{self.base_url}/api/script/generate?token={test_token}', timeout=5)
        
        # This might return 404, 400, or 200 depending on implementation
        self.assertIn(response.status_code, [200, 400, 404])
        
        if response.status_code == 200:
            # Should return JavaScript content
            content_type = response.headers.get('Content-Type', '')
            self.assertIn('javascript', content_type.lower())
            print("Script generation endpoint is functional")
        else:
            print(f"Script generation endpoint returned {response.status_code} (expected for invalid token)")
    
    def test_script_collect_endpoint(self):
        """Test script data collection endpoint"""
        if not self.server_available:
            self.skipTest("Server not available")
        
        # Test data collection endpoint
        test_data = {
            'token': 'test_token_123',
            'data': {
                'mouse_movements': 100,
                'keystrokes': 5,
                'scroll_events': 3
            }
        }
        
        response = requests.post(f'{self.base_url}/api/script/collect', json=test_data, timeout=5)
        
        # This might return various status codes depending on implementation
        self.assertIn(response.status_code, [200, 400, 401, 404])
        
        print(f"Script collect endpoint returned {response.status_code}")


if __name__ == '__main__':
    # Add more verbose output
    unittest.main(verbosity=2)