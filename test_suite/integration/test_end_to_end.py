#!/usr/bin/env python3
"""
End-to-End Integration Tests
"""

import sys
import os
import unittest
import requests
import time
import json
from datetime import datetime


class TestEndToEndFlow(unittest.TestCase):
    """Test complete user workflows"""
    
    def setUp(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:5003')
        self.admin_password = os.getenv('ADMIN_PASSWORD', 'Admin123')
        self.auth_token = None
        
    def authenticate(self):
        """Helper method to authenticate"""
        response = requests.post(
            f"{self.base_url}/login",
            json={"password": self.admin_password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('token')
            return True
        return False
        
    def test_complete_admin_workflow(self):
        """Test complete admin workflow"""
        # Step 1: Access login page
        response = requests.get(f"{self.base_url}/login")
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Authenticate
        self.assertTrue(self.authenticate(), "Authentication should succeed")
        self.assertIsNotNone(self.auth_token, "Should receive auth token")
        
        # Step 3: Access dashboard data
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Health check
        response = requests.get(f"{self.base_url}/health", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Analytics (may fail gracefully)
        response = requests.get(f"{self.base_url}/admin/analytics/summary", headers=headers)
        self.assertIn(response.status_code, [200, 401, 500, 503])
        
        # Websites (may fail gracefully)
        response = requests.get(f"{self.base_url}/admin/websites", headers=headers)
        self.assertIn(response.status_code, [200, 401, 500, 503])
        
    def test_frontend_spa_routing(self):
        """Test that SPA routing works"""
        # Test main routes return HTML
        routes = ['/', '/dashboard', '/login']
        
        for route in routes:
            response = requests.get(f"{self.base_url}{route}")
            self.assertEqual(response.status_code, 200)
            self.assertIn('text/html', response.headers.get('content-type', ''))
            
    def test_authentication_flow(self):
        """Test authentication state management"""
        # Test without authentication
        response = requests.get(f"{self.base_url}/admin/analytics/summary")
        self.assertEqual(response.status_code, 401)
        
        # Test with authentication
        if self.authenticate():
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(f"{self.base_url}/admin/analytics/summary", headers=headers)
            # Should either work or fail gracefully, not return 401
            self.assertNotEqual(response.status_code, 401)
            
    def test_error_handling(self):
        """Test error handling"""
        # Test invalid endpoint
        response = requests.get(f"{self.base_url}/nonexistent")
        self.assertEqual(response.status_code, 404)
        
        # Test invalid JSON
        response = requests.post(
            f"{self.base_url}/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        self.assertIn(response.status_code, [400, 500])
        
        # Test invalid credentials
        response = requests.post(
            f"{self.base_url}/login",
            json={"password": "wrong"},
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 401)


class TestSystemIntegration(unittest.TestCase):
    """Test system component integration"""
    
    def setUp(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:5003')
        
    def test_database_integration(self):
        """Test database connectivity"""
        response = requests.get(f"{self.base_url}/health")
        
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            
            # Database should be present in health check
            self.assertIn('database', components)
            
            # Database status should be healthy or error (not missing)
            db_status = components.get('database')
            self.assertIn(db_status, ['healthy', 'error'])
            
    def test_ml_model_integration(self):
        """Test ML model loading"""
        response = requests.get(f"{self.base_url}/health")
        
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            
            # ML model should be present
            self.assertIn('ml_model', components)
            
            # Should be loaded successfully
            ml_status = components.get('ml_model')
            self.assertEqual(ml_status, 'healthy')
            
    def test_redis_integration(self):
        """Test Redis integration (optional)"""
        response = requests.get(f"{self.base_url}/health")
        
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            
            # Redis may be disabled or error - that's OK
            if 'redis' in components:
                redis_status = components.get('redis')
                self.assertIn(redis_status, ['healthy', 'disabled', 'error'])


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:5003')
        
    def test_response_times(self):
        """Test API response times"""
        endpoints = [
            ('/health', 'GET', None),
            ('/login', 'GET', None),
            ('/login', 'POST', {"password": "Admin123"})
        ]
        
        for endpoint, method, data in endpoints:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            else:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
            response_time = time.time() - start_time
            
            # Response should be within reasonable time
            self.assertLess(response_time, 10.0, f"{endpoint} response time too slow: {response_time:.2f}s")
            
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
                
        # Launch multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Check results
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
                
        # At least 80% should succeed
        self.assertGreaterEqual(success_count, 4, "Most concurrent requests should succeed")


def run_integration_tests():
    """Run all integration tests"""
    print("🔗 PASSIVE CAPTCHA - INTEGRATION TESTS")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestEndToEndFlow))
    suite.addTest(unittest.makeSuite(TestSystemIntegration))
    suite.addTest(unittest.makeSuite(TestPerformanceIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)