#!/usr/bin/env python3
"""
API Routing Validator - Comprehensive API Route Testing and Validation
Ensures routing accuracy, consistency, and proper endpoint behavior
"""

import os
import sys
import json
import requests
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"

class AuthType(Enum):
    NONE = "none"
    JWT = "jwt"
    API_KEY = "api_key"
    SCRIPT_TOKEN = "script_token"

@dataclass
class APIEndpoint:
    """API endpoint definition"""
    path: str
    method: HTTPMethod
    auth_type: AuthType
    expected_status_codes: List[int]
    description: str
    required_params: List[str] = None
    optional_params: List[str] = None
    request_schema: Dict = None
    response_schema: Dict = None

@dataclass
class TestResult:
    """Test result for API endpoint"""
    endpoint: APIEndpoint
    status: str  # PASS, FAIL, SKIP
    actual_status_code: int
    response_time_ms: float
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None

class APIRoutingValidator:
    """Comprehensive API routing validator"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
        self.api_key = None
        self.script_token = None
        
        # Define all API endpoints
        self.endpoints = self._define_api_endpoints()
    
    def _define_api_endpoints(self) -> List[APIEndpoint]:
        """Define comprehensive list of API endpoints"""
        return [
            # Public API Endpoints
            APIEndpoint(
                path="/api/status",
                method=HTTPMethod.GET,
                auth_type=AuthType.NONE,
                expected_status_codes=[200],
                description="System status endpoint"
            ),
            APIEndpoint(
                path="/api/ml/info",
                method=HTTPMethod.GET,
                auth_type=AuthType.NONE,
                expected_status_codes=[200],
                description="ML model information"
            ),
            
            # Authentication Endpoints
            APIEndpoint(
                path="/api/admin/login",
                method=HTTPMethod.POST,
                auth_type=AuthType.NONE,
                expected_status_codes=[200, 400, 401],
                description="Admin login",
                required_params=["email", "password"]
            ),
            APIEndpoint(
                path="/api/admin/logout",
                method=HTTPMethod.POST,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Admin logout"
            ),
            APIEndpoint(
                path="/api/admin/verify-token",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200, 401],
                description="Token verification"
            ),
            
            # Website Management Endpoints
            APIEndpoint(
                path="/api/admin/websites",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="List websites"
            ),
            APIEndpoint(
                path="/api/admin/websites",
                method=HTTPMethod.POST,
                auth_type=AuthType.JWT,
                expected_status_codes=[200, 201, 400],
                description="Create website",
                required_params=["website_name", "website_url", "admin_email"]
            ),
            
            # Script Management Endpoints
            APIEndpoint(
                path="/admin/scripts/generate",
                method=HTTPMethod.POST,
                auth_type=AuthType.JWT,
                expected_status_codes=[200, 400],
                description="Generate script token",
                required_params=["website_id"]
            ),
            APIEndpoint(
                path="/admin/scripts/tokens",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="List script tokens"
            ),
            APIEndpoint(
                path="/admin/scripts/statistics",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Script statistics"
            ),
            
            # Script API Endpoints
            APIEndpoint(
                path="/api/script/generate",
                method=HTTPMethod.GET,
                auth_type=AuthType.SCRIPT_TOKEN,
                expected_status_codes=[200, 400, 401, 404],
                description="Generate script content",
                required_params=["token"]
            ),
            APIEndpoint(
                path="/api/script/activate",
                method=HTTPMethod.POST,
                auth_type=AuthType.SCRIPT_TOKEN,
                expected_status_codes=[200, 400, 401],
                description="Activate script token",
                required_params=["token", "website_id"]
            ),
            APIEndpoint(
                path="/api/script/collect",
                method=HTTPMethod.POST,
                auth_type=AuthType.SCRIPT_TOKEN,
                expected_status_codes=[200, 400, 401],
                description="Collect behavioral data",
                required_params=["token", "website_id", "behavioral_data"]
            ),
            
            # Analytics Endpoints
            APIEndpoint(
                path="/admin/analytics/stats",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Analytics statistics"
            ),
            APIEndpoint(
                path="/admin/analytics/charts",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Analytics charts data"
            ),
            
            # ML Endpoints
            APIEndpoint(
                path="/admin/ml/metrics",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="ML model metrics"
            ),
            APIEndpoint(
                path="/admin/ml/performance",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="ML model performance"
            ),
            
            # Alert Endpoints
            APIEndpoint(
                path="/admin/alerts/recent",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Recent alerts"
            ),
            APIEndpoint(
                path="/admin/alerts/summary",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Alert summary"
            ),
            
            # Configuration Endpoints
            APIEndpoint(
                path="/admin/config/websites",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Website configuration"
            ),
            APIEndpoint(
                path="/admin/config/api",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="API configuration"
            ),
            
            # Log Endpoints
            APIEndpoint(
                path="/admin/logs/timeline",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Log timeline"
            ),
            APIEndpoint(
                path="/admin/logs/activity",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Activity logs"
            ),
            
            # Dashboard Endpoints
            APIEndpoint(
                path="/admin/dashboard/analytics/summary",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="Dashboard analytics summary"
            ),
            APIEndpoint(
                path="/admin/dashboard/system/health",
                method=HTTPMethod.GET,
                auth_type=AuthType.JWT,
                expected_status_codes=[200],
                description="System health"
            ),
        ]
    
    def authenticate(self, email: str = "admin@passivecaptcha.com", password: str = "SecurePassword123!") -> bool:
        """Authenticate and get JWT token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/admin/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'token' in data.get('data', {}):
                    self.auth_token = data['data']['token']
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    logger.info("Authentication successful")
                    return True
            
            logger.error(f"Authentication failed: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def test_endpoint(self, endpoint: APIEndpoint, custom_params: Dict = None) -> TestResult:
        """Test a single API endpoint"""
        url = urljoin(self.base_url, endpoint.path)
        headers = {"Content-Type": "application/json"}
        
        # Setup authentication
        if endpoint.auth_type == AuthType.JWT and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif endpoint.auth_type == AuthType.API_KEY and self.api_key:
            headers["X-API-Key"] = self.api_key
        elif endpoint.auth_type == AuthType.SCRIPT_TOKEN and self.script_token:
            # Script tokens are usually passed as query params or in body
            pass
        
        # Prepare request data
        request_data = custom_params or {}
        if endpoint.required_params:
            for param in endpoint.required_params:
                if param not in request_data:
                    # Add dummy data for testing
                    request_data[param] = self._get_dummy_value(param)
        
        try:
            start_time = time.time()
            
            if endpoint.method == HTTPMethod.GET:
                response = self.session.get(url, headers=headers, params=request_data)
            elif endpoint.method == HTTPMethod.POST:
                response = self.session.post(url, headers=headers, json=request_data)
            elif endpoint.method == HTTPMethod.PUT:
                response = self.session.put(url, headers=headers, json=request_data)
            elif endpoint.method == HTTPMethod.PATCH:
                response = self.session.patch(url, headers=headers, json=request_data)
            elif endpoint.method == HTTPMethod.DELETE:
                response = self.session.delete(url, headers=headers)
            elif endpoint.method == HTTPMethod.OPTIONS:
                response = self.session.options(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {endpoint.method}")
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Parse response
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_content": response.text[:200]}
            
            # Determine test status
            status = "PASS" if response.status_code in endpoint.expected_status_codes else "FAIL"
            error_message = None if status == "PASS" else f"Expected {endpoint.expected_status_codes}, got {response.status_code}"
            
            return TestResult(
                endpoint=endpoint,
                status=status,
                actual_status_code=response.status_code,
                response_time_ms=response_time_ms,
                error_message=error_message,
                response_data=response_data
            )
            
        except Exception as e:
            return TestResult(
                endpoint=endpoint,
                status="FAIL",
                actual_status_code=0,
                response_time_ms=0,
                error_message=str(e)
            )
    
    def _get_dummy_value(self, param_name: str) -> Any:
        """Get dummy value for parameter"""
        dummy_values = {
            "email": "test@example.com",
            "password": "testpassword123",
            "website_id": "test_website_id",
            "website_name": "Test Website",
            "website_url": "https://test.example.com",
            "admin_email": "admin@test.com",
            "token": "test_token_123",
            "session_id": "test_session_123",
            "behavioral_data": {
                "mouseMovements": [],
                "keystrokes": [],
                "scrollEvents": []
            }
        }
        return dummy_values.get(param_name, f"test_{param_name}")
    
    def test_cors_configuration(self) -> List[TestResult]:
        """Test CORS configuration"""
        results = []
        
        cors_test_endpoints = [
            "/api/verify",
            "/api/script/collect",
            "/api/status"
        ]
        
        for path in cors_test_endpoints:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.options(
                    url,
                    headers={
                        "Origin": "https://example.com",
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "Content-Type"
                    }
                )
                
                cors_headers = {
                    "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                    "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                    "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
                }
                
                status = "PASS" if any(cors_headers.values()) else "FAIL"
                
                results.append(TestResult(
                    endpoint=APIEndpoint(
                        path=path,
                        method=HTTPMethod.OPTIONS,
                        auth_type=AuthType.NONE,
                        expected_status_codes=[200, 204],
                        description=f"CORS test for {path}"
                    ),
                    status=status,
                    actual_status_code=response.status_code,
                    response_time_ms=0,
                    response_data={"cors_headers": cors_headers}
                ))
                
            except Exception as e:
                results.append(TestResult(
                    endpoint=APIEndpoint(
                        path=path,
                        method=HTTPMethod.OPTIONS,
                        auth_type=AuthType.NONE,
                        expected_status_codes=[200, 204],
                        description=f"CORS test for {path}"
                    ),
                    status="FAIL",
                    actual_status_code=0,
                    response_time_ms=0,
                    error_message=str(e)
                ))
        
        return results
    
    def validate_all_routes(self) -> Dict[str, Any]:
        """Validate all defined routes"""
        logger.info("Starting comprehensive API route validation...")
        
        # Authenticate first
        auth_success = self.authenticate()
        
        results = []
        
        # Test all endpoints
        for endpoint in self.endpoints:
            if endpoint.auth_type in [AuthType.JWT] and not auth_success:
                results.append(TestResult(
                    endpoint=endpoint,
                    status="SKIP",
                    actual_status_code=0,
                    response_time_ms=0,
                    error_message="Authentication required but failed"
                ))
                continue
            
            result = self.test_endpoint(endpoint)
            results.append(result)
            
            # Small delay between requests
            time.sleep(0.1)
        
        # Test CORS configuration
        cors_results = self.test_cors_configuration()
        results.extend(cors_results)
        
        # Compile summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == "PASS")
        failed_tests = sum(1 for r in results if r.status == "FAIL")
        skipped_tests = sum(1 for r in results if r.status == "SKIP")
        
        avg_response_time = sum(r.response_time_ms for r in results if r.response_time_ms > 0) / max(1, len([r for r in results if r.response_time_ms > 0]))
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "success_rate": passed_tests / (total_tests - skipped_tests) if (total_tests - skipped_tests) > 0 else 0,
            "average_response_time_ms": avg_response_time,
            "authentication_successful": auth_success,
            "detailed_results": [
                {
                    "endpoint": f"{r.endpoint.method.value} {r.endpoint.path}",
                    "description": r.endpoint.description,
                    "status": r.status,
                    "actual_status_code": r.actual_status_code,
                    "expected_status_codes": r.endpoint.expected_status_codes,
                    "response_time_ms": r.response_time_ms,
                    "error_message": r.error_message,
                    "auth_type": r.endpoint.auth_type.value
                }
                for r in results
            ]
        }
        
        return summary
    
    def generate_route_documentation(self) -> str:
        """Generate comprehensive route documentation"""
        doc = """
# Passive CAPTCHA API Route Documentation

## Authentication Types
- **NONE**: No authentication required
- **JWT**: Requires Bearer token authentication
- **API_KEY**: Requires API key in headers
- **SCRIPT_TOKEN**: Requires script token parameter

## Endpoints

"""
        
        # Group endpoints by category
        categories = {}
        for endpoint in self.endpoints:
            category = endpoint.path.split('/')[1] if endpoint.path.startswith('/') else 'root'
            if category not in categories:
                categories[category] = []
            categories[category].append(endpoint)
        
        for category, endpoints in sorted(categories.items()):
            doc += f"### {category.upper()} Endpoints\n\n"
            
            for endpoint in sorted(endpoints, key=lambda x: x.path):
                doc += f"**{endpoint.method.value} {endpoint.path}**\n"
                doc += f"- Description: {endpoint.description}\n"
                doc += f"- Authentication: {endpoint.auth_type.value}\n"
                doc += f"- Expected Status Codes: {endpoint.expected_status_codes}\n"
                
                if endpoint.required_params:
                    doc += f"- Required Parameters: {', '.join(endpoint.required_params)}\n"
                
                if endpoint.optional_params:
                    doc += f"- Optional Parameters: {', '.join(endpoint.optional_params)}\n"
                
                doc += "\n"
            
            doc += "\n"
        
        return doc

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Routing Validator")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for testing")
    parser.add_argument("--output", default="api_validation_report.json", help="Output file for validation report")
    parser.add_argument("--docs", help="Generate route documentation to specified file")
    args = parser.parse_args()
    
    # Create validator
    validator = APIRoutingValidator(base_url=args.url)
    
    # Run validation
    summary = validator.validate_all_routes()
    
    # Save detailed report
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Generate documentation if requested
    if args.docs:
        documentation = validator.generate_route_documentation()
        with open(args.docs, 'w') as f:
            f.write(documentation)
        print(f"Route documentation saved to: {args.docs}")
    
    # Print summary
    print(f"\nAPI Route Validation Summary:")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Success Rate: {summary['success_rate']:.2%}")
    print(f"Average Response Time: {summary['average_response_time_ms']:.2f}ms")
    print(f"Authentication: {'✓' if summary['authentication_successful'] else '✗'}")
    
    # Show failed tests
    failed_tests = [r for r in summary['detailed_results'] if r['status'] == 'FAIL']
    if failed_tests:
        print(f"\nFailed Tests ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"  - {test['endpoint']}: {test['error_message']}")
    
    print(f"\nDetailed report saved to: {args.output}")
    
    # Exit with error code if tests failed
    exit_code = 0 if summary['failed'] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()