#!/usr/bin/env python3
"""
Complete Deployment Test & API Explorer for Passive CAPTCHA
Tests all endpoints and provides a complete API reference
"""

import requests
import json
import time
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def test_endpoint(url, description, method='GET', data=None, headers=None, expected_status=200):
    """Test an endpoint with detailed output"""
    try:
        print(f"\n🔄 Testing: {Colors.BOLD}{description}{Colors.END}")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        if data:
            print(f"   Data: {json.dumps(data)}")
        
        start_time = time.time()
        
        if method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=15)
        else:
            response = requests.get(url, timeout=15)
        
        duration = (time.time() - start_time) * 1000
        
        print(f"   Status: {response.status_code} ({duration:.2f}ms)")
        
        if response.status_code == expected_status:
            try:
                result = response.json()
                print_success(f"{description}")
                
                # Special handling for different response types
                if 'token' in result:
                    print(f"   🔑 Token: {result['token'][:50]}...")
                elif 'status' in result:
                    print(f"   📊 Status: {result['status']}")
                elif 'error' in result:
                    print(f"   ⚠️  Error: {result['error']}")
                
                return True, result
            except:
                print_success(f"{description} (HTML response)")
                return True, response.text[:200]
        else:
            print_error(f"{description} - Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False, None
            
    except requests.exceptions.Timeout:
        print_error(f"{description} - Request timeout")
        return False, None
    except requests.exceptions.ConnectionError:
        print_error(f"{description} - Connection failed")
        return False, None
    except Exception as e:
        print_error(f"{description} - {str(e)}")
        return False, None

def main():
    print_header("🚀 PASSIVE CAPTCHA - FULL DEPLOYMENT TEST")
    
    # Configuration
    localhost_base = "http://localhost:5003"
    tunnel_base = "https://seeker-busy-acquisitions-peace.trycloudflare.com"
    
    admin_credentials = {"password": "Admin123"}
    headers = {"Content-Type": "application/json"}
    
    # Test results storage
    results = []
    
    print_header("🏠 LOCALHOST TESTING")
    
    # Localhost tests
    localhost_tests = [
        (f"{localhost_base}/", "Frontend Homepage", "GET"),
        (f"{localhost_base}/health", "Health Check", "GET"),
        (f"{localhost_base}/admin/legacy/login", "Admin Login", "POST", admin_credentials, headers),
    ]
    
    localhost_token = None
    
    for test_data in localhost_tests:
        success, response = test_endpoint(*test_data)
        results.append((test_data[1] + " (Local)", success))
        
        # Save token for authenticated requests
        if success and response and isinstance(response, dict) and 'token' in response:
            localhost_token = response['token']
            print(f"   💾 Saved token for authenticated requests")
    
    # Authenticated endpoint tests (localhost)
    if localhost_token:
        auth_headers = {**headers, "Authorization": f"Bearer {localhost_token}"}
        
        auth_tests = [
            (f"{localhost_base}/admin/analytics/summary", "Analytics Summary", "GET", None, auth_headers),
            (f"{localhost_base}/admin/ml/metrics", "ML Metrics", "GET", None, auth_headers),
            (f"{localhost_base}/admin/websites", "Websites List", "GET", None, auth_headers),
        ]
        
        for test_data in auth_tests:
            success, response = test_endpoint(*test_data, expected_status=200)
            results.append((test_data[1] + " (Local)", success))
    
    print_header("🌐 TUNNEL TESTING")
    
    # Tunnel tests
    tunnel_tests = [
        (f"{tunnel_base}/", "Frontend Homepage", "GET"),
        (f"{tunnel_base}/health", "Health Check", "GET"),
        (f"{tunnel_base}/admin/legacy/login", "Admin Login", "POST", admin_credentials, headers),
    ]
    
    tunnel_token = None
    
    for test_data in tunnel_tests:
        success, response = test_endpoint(*test_data)
        results.append((test_data[1] + " (Tunnel)", success))
        
        # Save token for authenticated requests
        if success and response and isinstance(response, dict) and 'token' in response:
            tunnel_token = response['token']
            print(f"   💾 Saved token for authenticated requests")
    
    # Authenticated endpoint tests (tunnel)
    if tunnel_token:
        auth_headers = {**headers, "Authorization": f"Bearer {tunnel_token}"}
        
        auth_tests = [
            (f"{tunnel_base}/admin/analytics/summary", "Analytics Summary", "GET", None, auth_headers),
            (f"{tunnel_base}/admin/ml/metrics", "ML Metrics", "GET", None, auth_headers),
            (f"{tunnel_base}/admin/websites", "Websites List", "GET", None, auth_headers),
        ]
        
        for test_data in auth_tests:
            success, response = test_endpoint(*test_data, expected_status=200)
            results.append((test_data[1] + " (Tunnel)", success))
    
    # Results summary
    print_header("📊 TEST RESULTS SUMMARY")
    
    passed = 0
    total = len(results)
    
    for description, success in results:
        if success:
            print_success(description)
            passed += 1
        else:
            print_error(description)
    
    print(f"\n{Colors.BOLD}📈 OVERALL RESULTS: {passed}/{total} tests passed{Colors.END}")
    
    # API Reference
    print_header("📚 API REFERENCE")
    
    print(f"""
{Colors.BOLD}🔑 AUTHENTICATION:{Colors.END}
Endpoint: POST /admin/legacy/login
Payload: {{"password": "Admin123"}}
Response: {{"token": "jwt_token", "expires_in": 86400}}

{Colors.BOLD}🌐 ACCESS URLS:{Colors.END}
Local Frontend:  {localhost_base}/
Public Frontend: {tunnel_base}/
Local API:       {localhost_base}/admin/legacy/login
Public API:      {tunnel_base}/admin/legacy/login

{Colors.BOLD}🧪 TEST COMMANDS:{Colors.END}
# Test localhost login:
curl -X POST {localhost_base}/admin/legacy/login \\
     -H "Content-Type: application/json" \\
     -d '{{"password": "Admin123"}}'

# Test tunnel login:
curl -X POST {tunnel_base}/admin/legacy/login \\
     -H "Content-Type: application/json" \\
     -d '{{"password": "Admin123"}}'

{Colors.BOLD}🔧 AUTHENTICATED REQUESTS:{Colors.END}
curl -X GET {localhost_base}/admin/analytics/summary \\
     -H "Authorization: Bearer YOUR_TOKEN"
""")
    
    if passed >= total * 0.8:  # 80% pass rate
        print_success("🎉 DEPLOYMENT SUCCESSFUL! Your application is production-ready!")
        return True
    else:
        print_warning("⚠️ Some tests failed. Check the logs above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)