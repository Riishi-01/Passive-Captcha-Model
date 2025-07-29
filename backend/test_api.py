#!/usr/bin/env python3
"""
Comprehensive API Testing for Passive CAPTCHA System
Tests all endpoints, error handling, performance, and security
"""

import os
import sys
import time
import json
import requests
import threading
import subprocess
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import tempfile

# Test configuration
API_BASE_URL = "http://localhost:5000"
ADMIN_SECRET = "test-secret-key"
MAX_RETRIES = 3
TIMEOUT = 10

class APITestSuite:
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.admin_token = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'details': []
        }
        
    def add_result(self, test_name, passed, message="", response_time=None):
        """Add test result"""
        result = {
            'test': test_name,
            'passed': passed,
            'message': message,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results['details'].append(result)
        
        if passed:
            self.test_results['passed'] += 1
            print(f"   ✅ {test_name} - {message}")
        else:
            self.test_results['failed'] += 1
            print(f"   ❌ {test_name} - {message}")
            
        if response_time:
            print(f"      ⏱️  Response time: {response_time:.3f}ms")
    
    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            return response, response_time
            
        except requests.exceptions.RequestException as e:
            return None, None

    def test_health_endpoint(self):
        """Test health check endpoint"""
        print("\n🏥 Testing Health Endpoint...")
        print("-" * 40)
        
        response, response_time = self.make_request('GET', '/api/health')
        
        if response is None:
            self.add_result("Health endpoint connectivity", False, "Connection failed")
            return
        
        # Test basic connectivity
        if response.status_code in [200, 503]:
            self.add_result("Health endpoint connectivity", True, f"Status: {response.status_code}", response_time)
        else:
            self.add_result("Health endpoint connectivity", False, f"Unexpected status: {response.status_code}", response_time)
            return
        
        # Test response format
        try:
            data = response.json()
            
            required_fields = ['status', 'timestamp', 'checks']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.add_result("Health response format", True, "All required fields present")
            else:
                self.add_result("Health response format", False, f"Missing fields: {missing_fields}")
                
            # Test checks structure
            if 'checks' in data and isinstance(data['checks'], dict):
                expected_checks = ['modelLoaded', 'dbConnection', 'api']
                present_checks = [check for check in expected_checks if check in data['checks']]
                
                if len(present_checks) >= 2:
                    self.add_result("Health checks structure", True, f"Found {len(present_checks)} health checks")
                else:
                    self.add_result("Health checks structure", False, f"Only {len(present_checks)} health checks found")
            
        except json.JSONDecodeError:
            self.add_result("Health response format", False, "Invalid JSON response")

    def test_status_endpoint(self):
        """Test status endpoint"""
        print("\n📊 Testing Status Endpoint...")
        print("-" * 40)
        
        response, response_time = self.make_request('GET', '/api/status')
        
        if response is None:
            self.add_result("Status endpoint connectivity", False, "Connection failed")
            return
        
        if response.status_code == 200:
            self.add_result("Status endpoint", True, "Operational", response_time)
        else:
            self.add_result("Status endpoint", False, f"Status: {response.status_code}", response_time)
            return
        
        # Test response format
        try:
            data = response.json()
            
            required_fields = ['api', 'version', 'status']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.add_result("Status response format", True, "All required fields present")
                
                if data.get('status') == 'operational':
                    self.add_result("API operational status", True, "API reports operational")
                else:
                    self.add_result("API operational status", False, f"Status: {data.get('status')}")
            else:
                self.add_result("Status response format", False, f"Missing fields: {missing_fields}")
                
        except json.JSONDecodeError:
            self.add_result("Status response format", False, "Invalid JSON response")

    def test_verify_endpoint(self):
        """Test verification endpoint with various inputs"""
        print("\n🔍 Testing Verification Endpoint...")
        print("-" * 40)
        
        # Test valid human-like request
        human_payload = {
            "sessionId": "test_human_123",
            "mouseMovements": [
                {"x": 100, "y": 200, "timestamp": 1627234567890},
                {"x": 150, "y": 250, "timestamp": 1627234567950},
                {"x": 200, "y": 300, "timestamp": 1627234568000}
            ],
            "keystrokes": [
                {"key": "h", "timestamp": 1627234567900},
                {"key": "e", "timestamp": 1627234568000},
                {"key": "l", "timestamp": 1627234568100}
            ],
            "sessionDuration": 15000,
            "fingerprint": {
                "userAgent": "Mozilla/5.0 (test)",
                "screenWidth": 1920,
                "screenHeight": 1080,
                "webglVendor": "NVIDIA Corporation",
                "canvasFingerprint": "test_canvas_hash"
            },
            "origin": "test.com"
        }
        
        headers = {'Content-Type': 'application/json'}
        response, response_time = self.make_request('POST', '/api/verify', 
                                                   json=human_payload, headers=headers)
        
        if response is None:
            self.add_result("Verify endpoint connectivity", False, "Connection failed")
            return
        
        if response.status_code == 200:
            self.add_result("Verify endpoint - valid request", True, "Success", response_time)
            
            # Test response format
            try:
                data = response.json()
                required_fields = ['isHuman', 'confidence', 'sessionId', 'timestamp']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.add_result("Verify response format", True, "All required fields present")
                    
                    # Validate data types
                    if isinstance(data.get('isHuman'), bool):
                        self.add_result("isHuman field type", True, f"Value: {data['isHuman']}")
                    else:
                        self.add_result("isHuman field type", False, f"Not boolean: {type(data.get('isHuman'))}")
                    
                    confidence = data.get('confidence')
                    if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                        self.add_result("Confidence range", True, f"Value: {confidence:.3f}")
                    else:
                        self.add_result("Confidence range", False, f"Invalid confidence: {confidence}")
                        
                else:
                    self.add_result("Verify response format", False, f"Missing fields: {missing_fields}")
                    
            except json.JSONDecodeError:
                self.add_result("Verify response format", False, "Invalid JSON response")
        else:
            self.add_result("Verify endpoint - valid request", False, f"Status: {response.status_code}", response_time)
        
        # Test empty request
        response, response_time = self.make_request('POST', '/api/verify', 
                                                   json={}, headers=headers)
        
        if response and response.status_code in [200, 400]:
            self.add_result("Verify endpoint - empty request", True, f"Handled gracefully (status: {response.status_code})", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("Verify endpoint - empty request", False, f"Status: {status}", response_time)
        
        # Test invalid content type
        response, response_time = self.make_request('POST', '/api/verify', data='invalid')
        
        if response and response.status_code == 400:
            self.add_result("Verify endpoint - invalid content type", True, "Rejected invalid content type", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("Verify endpoint - invalid content type", False, f"Unexpected status: {status}", response_time)

    def test_admin_authentication(self):
        """Test admin authentication"""
        print("\n🔐 Testing Admin Authentication...")
        print("-" * 40)
        
        # Test login with correct password
        login_payload = {"password": ADMIN_SECRET}
        headers = {'Content-Type': 'application/json'}
        
        response, response_time = self.make_request('POST', '/admin/login', 
                                                   json=login_payload, headers=headers)
        
        if response is None:
            self.add_result("Admin login connectivity", False, "Connection failed")
            return
        
        if response.status_code == 200:
            self.add_result("Admin login - valid credentials", True, "Login successful", response_time)
            
            try:
                data = response.json()
                if 'token' in data:
                    self.admin_token = data['token']
                    self.add_result("Admin token generation", True, "Token received")
                else:
                    self.add_result("Admin token generation", False, "No token in response")
            except json.JSONDecodeError:
                self.add_result("Admin login response format", False, "Invalid JSON response")
        else:
            self.add_result("Admin login - valid credentials", False, f"Status: {response.status_code}", response_time)
        
        # Test login with wrong password
        wrong_payload = {"password": "wrong-password"}
        response, response_time = self.make_request('POST', '/admin/login', 
                                                   json=wrong_payload, headers=headers)
        
        if response and response.status_code == 401:
            self.add_result("Admin login - invalid credentials", True, "Correctly rejected", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("Admin login - invalid credentials", False, f"Unexpected status: {status}", response_time)

    def test_admin_endpoints(self):
        """Test admin-protected endpoints"""
        print("\n👑 Testing Admin-Protected Endpoints...")
        print("-" * 40)
        
        if not self.admin_token:
            self.add_result("Admin endpoints", False, "No admin token available")
            return
        
        auth_headers = {
            'Authorization': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Test analytics endpoint
        response, response_time = self.make_request('GET', '/admin/analytics?hours=24', 
                                                   headers=auth_headers)
        
        if response and response.status_code == 200:
            self.add_result("Admin analytics endpoint", True, "Accessible with token", response_time)
            
            try:
                data = response.json()
                expected_fields = ['stats', 'trends', 'topOrigins']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    self.add_result("Analytics response format", True, "All expected fields present")
                else:
                    self.add_result("Analytics response format", False, f"Missing fields: {missing_fields}")
            except json.JSONDecodeError:
                self.add_result("Analytics response format", False, "Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            self.add_result("Admin analytics endpoint", False, f"Status: {status}", response_time)
        
        # Test stats endpoint
        response, response_time = self.make_request('GET', '/admin/stats', headers=auth_headers)
        
        if response and response.status_code == 200:
            self.add_result("Admin stats endpoint", True, "Accessible", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("Admin stats endpoint", False, f"Status: {status}", response_time)
        
        # Test without token
        response, response_time = self.make_request('GET', '/admin/analytics')
        
        if response and response.status_code == 401:
            self.add_result("Admin endpoint security", True, "Correctly requires authentication", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("Admin endpoint security", False, f"Unexpected status: {status}", response_time)

    def test_performance_benchmarks(self):
        """Test API performance under load"""
        print("\n⚡ Testing Performance Benchmarks...")
        print("-" * 40)
        
        # Test single request performance
        test_payload = {
            "sessionId": "perf_test",
            "mouseMovements": [{"x": 100, "y": 200, "timestamp": 1627234567890}],
            "keystrokes": [{"key": "a", "timestamp": 1627234567900}],
            "sessionDuration": 1000,
            "fingerprint": {"userAgent": "test"},
            "origin": "test.com"
        }
        
        headers = {'Content-Type': 'application/json'}
        
        # Single request performance
        response, response_time = self.make_request('POST', '/api/verify', 
                                                   json=test_payload, headers=headers)
        
        if response and response.status_code == 200:
            if response_time < 100:
                self.add_result("Single request performance", True, f"Fast response: {response_time:.3f}ms", response_time)
            elif response_time < 500:
                self.add_result("Single request performance", True, f"Acceptable response: {response_time:.3f}ms", response_time)
            else:
                self.add_result("Single request performance", False, f"Slow response: {response_time:.3f}ms", response_time)
        
        # Rapid sequential requests
        print("   🔥 Testing rapid sequential requests...")
        times = []
        success_count = 0
        
        for i in range(10):
            response, response_time = self.make_request('POST', '/api/verify', 
                                                       json=test_payload, headers=headers)
            if response and response.status_code == 200:
                times.append(response_time)
                success_count += 1
        
        if success_count >= 8:
            avg_time = sum(times) / len(times) if times else 0
            self.add_result("Rapid sequential requests", True, f"Success rate: {success_count}/10, Avg: {avg_time:.3f}ms")
        else:
            self.add_result("Rapid sequential requests", False, f"Low success rate: {success_count}/10")

    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        print("\n🚀 Testing Concurrent Requests...")
        print("-" * 40)
        
        test_payload = {
            "sessionId": "concurrent_test",
            "mouseMovements": [{"x": 100, "y": 200, "timestamp": 1627234567890}],
            "keystrokes": [{"key": "a", "timestamp": 1627234567900}],
            "sessionDuration": 1000,
            "fingerprint": {"userAgent": "test"},
            "origin": "test.com"
        }
        
        def make_concurrent_request():
            headers = {'Content-Type': 'application/json'}
            response, response_time = self.make_request('POST', '/api/verify', 
                                                       json=test_payload, headers=headers)
            return response is not None and response.status_code == 200, response_time
        
        # Test with 5 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            futures = [executor.submit(make_concurrent_request) for _ in range(5)]
            results = [future.result() for future in futures]
            end_time = time.time()
        
        successful_requests = sum(1 for success, _ in results if success)
        total_time = (end_time - start_time) * 1000
        
        if successful_requests >= 4:
            self.add_result("Concurrent request handling", True, 
                          f"Success rate: {successful_requests}/5 in {total_time:.3f}ms")
        else:
            self.add_result("Concurrent request handling", False, 
                          f"Low success rate: {successful_requests}/5")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n🚫 Testing Error Handling...")
        print("-" * 40)
        
        # Test non-existent endpoint
        response, response_time = self.make_request('GET', '/api/nonexistent')
        
        if response and response.status_code == 404:
            self.add_result("404 error handling", True, "Correctly returns 404", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("404 error handling", False, f"Unexpected status: {status}", response_time)
        
        # Test method not allowed
        response, response_time = self.make_request('DELETE', '/api/verify')
        
        if response and response.status_code == 405:
            self.add_result("405 method not allowed", True, "Correctly rejects invalid method", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("405 method not allowed", False, f"Unexpected status: {status}", response_time)
        
        # Test malformed JSON
        headers = {'Content-Type': 'application/json'}
        response, response_time = self.make_request('POST', '/api/verify', 
                                                   data='{"invalid": json}', headers=headers)
        
        if response and response.status_code == 400:
            self.add_result("Malformed JSON handling", True, "Correctly rejects malformed JSON", response_time)
        else:
            status = response.status_code if response else "No response"
            self.add_result("Malformed JSON handling", False, f"Unexpected status: {status}", response_time)

    def test_cors_headers(self):
        """Test CORS headers"""
        print("\n🌐 Testing CORS Headers...")
        print("-" * 40)
        
        # Test OPTIONS request
        headers = {
            'Origin': 'https://example.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response, response_time = self.make_request('OPTIONS', '/api/verify', headers=headers)
        
        if response:
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if any(cors_headers.values()):
                self.add_result("CORS headers present", True, "CORS headers found", response_time)
            else:
                self.add_result("CORS headers present", False, "No CORS headers found", response_time)
        else:
            self.add_result("CORS preflight", False, "OPTIONS request failed")

    def test_rate_limiting(self):
        """Test rate limiting (if implemented)"""
        print("\n🛡️  Testing Rate Limiting...")
        print("-" * 40)
        
        # Make rapid requests to test rate limiting
        test_payload = {"sessionId": "rate_test", "origin": "test.com"}
        headers = {'Content-Type': 'application/json'}
        
        responses = []
        for i in range(15):  # Try 15 requests rapidly
            response, response_time = self.make_request('POST', '/api/verify', 
                                                       json=test_payload, headers=headers)
            if response:
                responses.append(response.status_code)
            time.sleep(0.1)  # Small delay
        
        # Check if any requests were rate limited (429 status)
        rate_limited = sum(1 for status in responses if status == 429)
        successful = sum(1 for status in responses if status == 200)
        
        if rate_limited > 0:
            self.add_result("Rate limiting active", True, f"Rate limited {rate_limited}/15 requests")
        else:
            self.add_result("Rate limiting", True, f"No rate limiting detected (or threshold not reached)")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE API TEST REPORT")
        print("=" * 60)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 SUMMARY:")
        print(f"   ✅ Tests Passed: {self.test_results['passed']}")
        print(f"   ❌ Tests Failed: {self.test_results['failed']}")
        print(f"   📊 Total Tests: {total_tests}")
        print(f"   🎯 Success Rate: {success_rate:.1f}%")
        
        # Response time analysis
        response_times = [r['response_time'] for r in self.test_results['details'] if r.get('response_time')]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            min_response = min(response_times)
            
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Average response time: {avg_response:.3f}ms")
            print(f"   Fastest response: {min_response:.3f}ms")
            print(f"   Slowest response: {max_response:.3f}ms")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results['details'] if not r['passed']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['message']}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 95:
            print("   🏆 EXCELLENT - API is production ready!")
        elif success_rate >= 85:
            print("   ✅ GOOD - API is mostly functional")
        elif success_rate >= 70:
            print("   ⚠️  FAIR - Some issues need attention")
        else:
            print("   ❌ POOR - Significant problems found")
        
        print(f"\n📅 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 85


def start_test_server():
    """Start the Flask server for testing"""
    print("🚀 Starting test server...")
    
    try:
        # Start Flask server in background
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Test if server is responding
        try:
            response = requests.get(f"{API_BASE_URL}/api/status", timeout=5)
            if response.status_code == 200:
                print("✅ Test server started successfully")
                return process
            else:
                print(f"⚠️  Server started but returned status: {response.status_code}")
                return process
        except requests.exceptions.RequestException:
            print("⚠️  Server may be starting up... proceeding with tests")
            return process
            
    except Exception as e:
        print(f"❌ Failed to start test server: {e}")
        return None


def main():
    """Run comprehensive API testing"""
    print("🧪 COMPREHENSIVE API TESTING SUITE")
    print("=" * 60)
    
    # Check if server is already running
    try:
        response = requests.get(f"{API_BASE_URL}/api/status", timeout=5)
        print("✅ API server is already running")
        server_process = None
    except requests.exceptions.RequestException:
        print("🚀 Starting API server for testing...")
        server_process = start_test_server()
        if not server_process:
            print("❌ Cannot start server. Please start manually with: python app.py")
            return
    
    try:
        # Initialize test suite
        test_suite = APITestSuite()
        
        # Run all test suites
        test_suite.test_health_endpoint()
        test_suite.test_status_endpoint()
        test_suite.test_verify_endpoint()
        test_suite.test_admin_authentication()
        test_suite.test_admin_endpoints()
        test_suite.test_performance_benchmarks()
        test_suite.test_concurrent_requests()
        test_suite.test_error_handling()
        test_suite.test_cors_headers()
        test_suite.test_rate_limiting()
        
        # Generate final report
        success = test_suite.generate_report()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up server process
        if server_process:
            print("\n🛑 Stopping test server...")
            server_process.terminate()
            server_process.wait()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 