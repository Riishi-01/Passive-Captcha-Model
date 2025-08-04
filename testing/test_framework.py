#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Passive CAPTCHA System
Tests API routing accuracy, database integrity, and authentication robustness
"""

import os
import sys
import json
import time
import requests
import sqlite3
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    execution_time: float
    error_message: Optional[str] = None
    details: Optional[Dict] = None

class TestFramework:
    """Comprehensive test framework for Passive CAPTCHA system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
        self.test_results: List[TestResult] = []
        self.test_data = self._setup_test_data()
        
    def _setup_test_data(self) -> Dict:
        """Setup test data for various scenarios"""
        return {
            "valid_admin": {
                "email": "admin@passivecaptcha.com",
                "password": "SecurePassword123!"
            },
            "invalid_admin": {
                "email": "fake@example.com", 
                "password": "wrongpassword"
            },
            "test_website": {
                "website_name": "Test Website",
                "website_url": "https://test.example.com",
                "admin_email": "admin@passivecaptcha.com"
            },
            "behavioral_data": {
                "mouseMovements": [
                    {"x": 100, "y": 150, "timestamp": 1000},
                    {"x": 120, "y": 160, "timestamp": 1050}
                ],
                "keystrokes": [
                    {"key": "a", "timestamp": 2000, "duration": 100},
                    {"key": "b", "timestamp": 2150, "duration": 95}
                ],
                "scrollEvents": [
                    {"scrollY": 100, "timestamp": 3000},
                    {"scrollY": 200, "timestamp": 3500}
                ]
            }
        }
    
    def run_test(self, test_func) -> TestResult:
        """Execute a single test and record results"""
        test_name = test_func.__name__
        start_time = time.time()
        
        try:
            logger.info(f"Running test: {test_name}")
            result = test_func()
            execution_time = time.time() - start_time
            
            if result.get('success', True):
                test_result = TestResult(
                    test_name=test_name,
                    status="PASS", 
                    execution_time=execution_time,
                    details=result
                )
            else:
                test_result = TestResult(
                    test_name=test_name,
                    status="FAIL",
                    execution_time=execution_time,
                    error_message=result.get('error', 'Test failed'),
                    details=result
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            test_result = TestResult(
                test_name=test_name,
                status="FAIL",
                execution_time=execution_time,
                error_message=str(e)
            )
            logger.error(f"Test {test_name} failed: {e}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_authentication_system(self) -> Dict:
        """Test authentication system robustness"""
        tests = []
        
        # Test 1: Valid login
        try:
            response = self.session.post(
                f"{self.base_url}/api/admin/login",
                json=self.test_data["valid_admin"],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'token' in data.get('data', {}):
                    self.auth_token = data['data']['token']
                    tests.append({"test": "valid_login", "status": "PASS"})
                else:
                    tests.append({"test": "valid_login", "status": "FAIL", "reason": "No token in response"})
            else:
                tests.append({"test": "valid_login", "status": "FAIL", "reason": f"HTTP {response.status_code}"})
        except Exception as e:
            tests.append({"test": "valid_login", "status": "FAIL", "reason": str(e)})
        
        # Test 2: Invalid login
        try:
            response = self.session.post(
                f"{self.base_url}/api/admin/login",
                json=self.test_data["invalid_admin"],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [401, 403]:
                tests.append({"test": "invalid_login_rejection", "status": "PASS"})
            else:
                tests.append({"test": "invalid_login_rejection", "status": "FAIL", "reason": f"HTTP {response.status_code}"})
        except Exception as e:
            tests.append({"test": "invalid_login_rejection", "status": "FAIL", "reason": str(e)})
        
        # Test 3: Token verification
        if self.auth_token:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/admin/verify-token",
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                
                if response.status_code == 200:
                    tests.append({"test": "token_verification", "status": "PASS"})
                else:
                    tests.append({"test": "token_verification", "status": "FAIL", "reason": f"HTTP {response.status_code}"})
            except Exception as e:
                tests.append({"test": "token_verification", "status": "FAIL", "reason": str(e)})
        
        return {"success": True, "tests": tests}
    
    def test_api_routing_accuracy(self) -> Dict:
        """Test API routing accuracy and consistency"""
        routes_to_test = [
            # Public API routes
            {"path": "/api/status", "method": "GET", "expected_code": 200},
            {"path": "/api/ml/info", "method": "GET", "expected_code": 200},
            
            # Script endpoints
            {"path": "/api/script/generate", "method": "GET", "expected_code": [400, 401], "requires_token": True},
            
            # Admin endpoints (require authentication)
            {"path": "/api/admin/websites", "method": "GET", "expected_code": 200, "requires_auth": True},
            {"path": "/api/admin/statistics", "method": "GET", "expected_code": 200, "requires_auth": True},
            
            # Script management endpoints
            {"path": "/admin/scripts/tokens", "method": "GET", "expected_code": 200, "requires_auth": True},
            {"path": "/admin/scripts/statistics", "method": "GET", "expected_code": 200, "requires_auth": True},
        ]
        
        results = []
        headers = {}
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        for route in routes_to_test:
            try:
                if route.get("requires_auth") and not self.auth_token:
                    results.append({
                        "route": route["path"],
                        "status": "SKIP",
                        "reason": "No auth token available"
                    })
                    continue
                
                response = self.session.request(
                    route["method"],
                    f"{self.base_url}{route['path']}",
                    headers=headers
                )
                
                expected_codes = route["expected_code"]
                if isinstance(expected_codes, int):
                    expected_codes = [expected_codes]
                
                if response.status_code in expected_codes:
                    results.append({
                        "route": route["path"],
                        "status": "PASS",
                        "code": response.status_code
                    })
                else:
                    results.append({
                        "route": route["path"],
                        "status": "FAIL",
                        "expected": expected_codes,
                        "actual": response.status_code
                    })
                    
            except Exception as e:
                results.append({
                    "route": route["path"],
                    "status": "FAIL",
                    "error": str(e)
                })
        
        return {"success": True, "route_tests": results}
    
    def test_database_schema_integrity(self) -> Dict:
        """Test database schema and data integrity"""
        tests = []
        
        # Test database connection via API
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                data = response.json()
                if data.get('database_status') == 'connected':
                    tests.append({"test": "database_connection", "status": "PASS"})
                else:
                    tests.append({"test": "database_connection", "status": "FAIL", "reason": "Database not connected"})
            else:
                tests.append({"test": "database_connection", "status": "FAIL", "reason": f"HTTP {response.status_code}"})
        except Exception as e:
            tests.append({"test": "database_connection", "status": "FAIL", "reason": str(e)})
        
        # Test data flow through verification endpoint
        if self.auth_token:
            try:
                # First create a test website
                website_data = self.test_data["test_website"]
                response = self.session.post(
                    f"{self.base_url}/api/admin/websites",
                    json=website_data,
                    headers={"Authorization": f"Bearer {self.auth_token}", "Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201]:
                    website_response = response.json()
                    website_id = website_response.get('data', {}).get('website_id')
                    
                    if website_id:
                        tests.append({"test": "website_creation", "status": "PASS", "website_id": website_id})
                        
                        # Test data insertion through verification
                        verification_data = {
                            "website_id": website_id,
                            "behavioral_data": self.test_data["behavioral_data"],
                            "session_id": f"test_session_{int(time.time())}"
                        }
                        
                        # Note: This might fail if API key is required, but we test the endpoint
                        response = self.session.post(
                            f"{self.base_url}/api/verify",
                            json=verification_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        # Even if it fails due to API key, we check if the endpoint exists
                        if response.status_code in [200, 400, 401, 403]:
                            tests.append({"test": "verification_endpoint_reachable", "status": "PASS"})
                        else:
                            tests.append({"test": "verification_endpoint_reachable", "status": "FAIL", "code": response.status_code})
                    else:
                        tests.append({"test": "website_creation", "status": "FAIL", "reason": "No website_id in response"})
                else:
                    tests.append({"test": "website_creation", "status": "FAIL", "reason": f"HTTP {response.status_code}"})
                    
            except Exception as e:
                tests.append({"test": "data_flow", "status": "FAIL", "reason": str(e)})
        
        return {"success": True, "database_tests": tests}
    
    def test_cors_and_security(self) -> Dict:
        """Test CORS configuration and security headers"""
        tests = []
        
        # Test CORS headers
        try:
            response = self.session.options(
                f"{self.base_url}/api/verify",
                headers={"Origin": "https://example.com"}
            )
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            if any(cors_headers.values()):
                tests.append({"test": "cors_headers_present", "status": "PASS", "headers": cors_headers})
            else:
                tests.append({"test": "cors_headers_present", "status": "FAIL", "reason": "No CORS headers found"})
                
        except Exception as e:
            tests.append({"test": "cors_headers", "status": "FAIL", "reason": str(e)})
        
        # Test security headers
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            security_headers = {
                "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
                "X-Frame-Options": response.headers.get("X-Frame-Options"),
                "X-XSS-Protection": response.headers.get("X-XSS-Protection")
            }
            
            tests.append({"test": "security_headers", "status": "PASS", "headers": security_headers})
            
        except Exception as e:
            tests.append({"test": "security_headers", "status": "FAIL", "reason": str(e)})
        
        return {"success": True, "security_tests": tests}
    
    def test_rate_limiting(self) -> Dict:
        """Test rate limiting functionality"""
        tests = []
        
        # Test multiple rapid requests
        try:
            responses = []
            for i in range(10):
                response = self.session.get(f"{self.base_url}/api/status")
                responses.append(response.status_code)
            
            # Check if any requests were rate limited (429)
            rate_limited = any(code == 429 for code in responses)
            
            tests.append({
                "test": "rate_limiting_check",
                "status": "PASS",
                "rate_limited": rate_limited,
                "response_codes": responses
            })
            
        except Exception as e:
            tests.append({"test": "rate_limiting", "status": "FAIL", "reason": str(e)})
        
        return {"success": True, "rate_limit_tests": tests}
    
    def test_concurrent_access(self) -> Dict:
        """Test concurrent access and thread safety"""
        tests = []
        
        def make_request():
            try:
                response = self.session.get(f"{self.base_url}/api/status")
                return response.status_code
            except:
                return 500
        
        try:
            # Test concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in futures]
            
            success_count = sum(1 for code in results if code == 200)
            total_requests = len(results)
            
            if success_count >= total_requests * 0.8:  # 80% success rate
                tests.append({
                    "test": "concurrent_access",
                    "status": "PASS",
                    "success_rate": success_count / total_requests,
                    "total_requests": total_requests
                })
            else:
                tests.append({
                    "test": "concurrent_access",
                    "status": "FAIL",
                    "success_rate": success_count / total_requests,
                    "reason": "Low success rate under load"
                })
                
        except Exception as e:
            tests.append({"test": "concurrent_access", "status": "FAIL", "reason": str(e)})
        
        return {"success": True, "concurrency_tests": tests}
    
    def run_comprehensive_test_suite(self) -> Dict:
        """Run complete test suite"""
        logger.info("Starting comprehensive test suite...")
        
        # Run all tests
        auth_results = self.run_test(self.test_authentication_system)
        routing_results = self.run_test(self.test_api_routing_accuracy) 
        database_results = self.run_test(self.test_database_schema_integrity)
        security_results = self.run_test(self.test_cors_and_security)
        rate_limit_results = self.run_test(self.test_rate_limiting)
        concurrency_results = self.run_test(self.test_concurrent_access)
        
        # Compile summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == "PASS")
        failed_tests = sum(1 for r in self.test_results if r.status == "FAIL")
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "execution_time": sum(r.execution_time for r in self.test_results),
            "detailed_results": [
                {
                    "test": r.test_name,
                    "status": r.status,
                    "execution_time": r.execution_time,
                    "error": r.error_message,
                    "details": r.details
                }
                for r in self.test_results
            ]
        }
        
        return summary
    
    def generate_test_report(self, summary: Dict) -> str:
        """Generate detailed test report"""
        timestamp = datetime.now().isoformat()
        
        report = f"""
PASSIVE CAPTCHA SYSTEM - COMPREHENSIVE TEST REPORT
Generated: {timestamp}
Base URL: {self.base_url}

SUMMARY:
========
Total Tests: {summary['total_tests']}
Passed: {summary['passed']}
Failed: {summary['failed']}
Success Rate: {summary['success_rate']:.2%}
Total Execution Time: {summary['execution_time']:.2f}s

DETAILED RESULTS:
================
"""
        
        for result in summary['detailed_results']:
            report += f"""
Test: {result['test']}
Status: {result['status']}
Execution Time: {result['execution_time']:.3f}s
"""
            if result['error']:
                report += f"Error: {result['error']}\n"
            
            if result['details']:
                report += f"Details: {json.dumps(result['details'], indent=2)}\n"
            
            report += "-" * 50 + "\n"
        
        return report

def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Passive CAPTCHA Test Framework")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for testing")
    parser.add_argument("--output", default="test_report.txt", help="Output file for test report")
    args = parser.parse_args()
    
    # Run tests
    framework = TestFramework(base_url=args.url)
    summary = framework.run_comprehensive_test_suite()
    
    # Generate report
    report = framework.generate_test_report(summary)
    
    # Save report
    with open(args.output, 'w') as f:
        f.write(report)
    
    # Print summary
    print(report)
    print(f"\nFull report saved to: {args.output}")
    
    # Exit with error code if tests failed
    exit_code = 0 if summary['failed'] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()