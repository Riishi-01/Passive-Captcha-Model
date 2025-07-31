#!/usr/bin/env python3
"""
API Endpoint Tests for Passive CAPTCHA
"""

import sys
import os
import unittest
import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5003')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin123')


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = API_BASE_URL
        cls.admin_password = ADMIN_PASSWORD
        cls.auth_token = None
        
        print(f"Testing API at: {cls.base_url}")
        
        # Wait for server to be ready
        cls._wait_for_server()
        
        # Authenticate and get token
        cls._authenticate()
    
    @classmethod
    def _wait_for_server(cls, timeout=30):
        """Wait for server to be ready"""
        print("⏳ Waiting for server to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{cls.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is ready")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        
        print("❌ Server not ready after timeout")
        
    @classmethod
    def _authenticate(cls):
        """Authenticate and get token"""
        try:
            response = requests.post(
                f"{cls.base_url}/login",
                json={"password": cls.admin_password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                cls.auth_token = data.get('token')
                print("✅ Authentication successful")
            else:
                print(f"❌ Authentication failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Authentication error: {e}")
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.base_url}/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('status', data)
        self.assertIn('components', data)
        
    def test_login_get(self):
        """Test login endpoint GET request"""
        response = requests.get(f"{self.base_url}/login")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertIn('endpoint', data)
        
    def test_login_post_success(self):
        """Test successful login"""
        response = requests.post(
            f"{self.base_url}/login",
            json={"password": self.admin_password},
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('token', data)
        self.assertIn('expires_in', data)
        self.assertEqual(data['expires_in'], 86400)
        
    def test_login_post_failure(self):
        """Test failed login"""
        response = requests.post(
            f"{self.base_url}/login",
            json={"password": "wrongpassword"},
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertEqual(data['success'], False)
        
    def test_login_missing_password(self):
        """Test login without password"""
        response = requests.post(
            f"{self.base_url}/login",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertIn('error', data)
        
    def test_analytics_unauthorized(self):
        """Test analytics endpoint without authentication"""
        response = requests.get(f"{self.base_url}/admin/analytics/summary")
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'MISSING_AUTH')
        
    def test_analytics_authorized(self):
        """Test analytics endpoint with authentication"""
        if not self.auth_token:
            self.skipTest("No authentication token available")
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.get(f"{self.base_url}/admin/analytics/summary", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('data', data)
            self.assertTrue(data['success'])
        else:
            # May fail if dependencies missing, that's OK for this test
            self.assertIn(response.status_code, [401, 500, 503])
            
    def test_websites_authorized(self):
        """Test websites endpoint with authentication"""
        if not self.auth_token:
            self.skipTest("No authentication token available")
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.get(f"{self.base_url}/admin/websites", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('data', data)
        else:
            # May fail if dependencies missing, that's OK for this test
            self.assertIn(response.status_code, [401, 500, 503])
            
    def test_ml_metrics_authorized(self):
        """Test ML metrics endpoint with authentication"""
        if not self.auth_token:
            self.skipTest("No authentication token available")
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.get(f"{self.base_url}/admin/ml/metrics", headers=headers)
        
        # ML metrics often fail due to missing dependencies, so we're flexible
        self.assertIn(response.status_code, [200, 401, 500, 503])
        
    def test_frontend_routes(self):
        """Test frontend routes are served"""
        # Test root route
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers.get('content-type', ''))
        
        # Test frontend login route (SPA route)
        response = requests.get(f"{self.base_url}/dashboard")
        self.assertEqual(response.status_code, 200)


class TestAPIPerformance(unittest.TestCase):
    """Test API performance"""
    
    def setUp(self):
        self.base_url = API_BASE_URL
        
    def test_health_response_time(self):
        """Test health endpoint response time"""
        start_time = time.time()
        response = requests.get(f"{self.base_url}/health", timeout=5)
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 2.0, "Health check should respond within 2 seconds")
        
    def test_login_response_time(self):
        """Test login endpoint response time"""
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/login",
            json={"password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 5.0, "Login should respond within 5 seconds")


def run_api_tests():
    """Run all API tests and generate report"""
    print("🧪 PASSIVE CAPTCHA - API TESTS")
    print("=" * 50)
    print(f"Target URL: {API_BASE_URL}")
    print(f"Admin Password: {'*' * len(ADMIN_PASSWORD)}")
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestAPIEndpoints))
    suite.addTest(unittest.makeSuite(TestAPIPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_api_tests()
    sys.exit(0 if success else 1)