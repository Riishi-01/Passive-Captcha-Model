#!/usr/bin/env python3
"""
Simple HTTP Requests Bot
Pure HTTP requests without browser interaction - should be easily detected
"""

import sys
import os
import time
import json
import requests
from datetime import datetime
from urllib.parse import urljoin

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_URL, UIDAI_URL, ADMIN_URL, USER_AGENTS, RESULTS_DIR

class SimpleRequestsBot:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            'bot_type': 'http_requests',
            'start_time': datetime.now().isoformat(),
            'requests': [],
            'detections': [],
            'errors': []
        }
        
        # Use obvious bot user agent
        self.session.headers.update({
            'User-Agent': USER_AGENTS['bot_obvious'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def log_request(self, method, url, status_code, response_time, details=None):
        """Log HTTP request with details"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'url': url,
            'status_code': status_code,
            'response_time_ms': round(response_time * 1000, 2),
            'details': details or {}
        }
        self.results['requests'].append(log_entry)
        print(f"[HTTP BOT] {method} {url} -> {status_code} ({log_entry['response_time_ms']}ms)")
        
    def test_uidai_portal(self):
        """Test UIDAI portal with pure HTTP requests"""
        print(f"\n=== Testing UIDAI Portal: {UIDAI_URL} ===")
        
        try:
            # Main page request
            start_time = time.time()
            response = self.session.get(UIDAI_URL, timeout=10)
            response_time = time.time() - start_time
            
            self.log_request('GET', UIDAI_URL, response.status_code, response_time, {
                'content_length': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'has_captcha_script': 'passive-captcha' in response.text.lower()
            })
            
            # Try to extract any forms or interesting endpoints
            if response.status_code == 200:
                content = response.text.lower()
                
                # Look for common endpoints
                endpoints_to_test = [
                    '/health',
                    '/api/health',
                    '/robots.txt',
                    '/favicon.ico',
                    '/sitemap.xml'
                ]
                
                # Test additional endpoints rapidly (bot-like behavior)
                for endpoint in endpoints_to_test:
                    try:
                        url = urljoin(BASE_URL, endpoint)
                        start_time = time.time()
                        resp = self.session.get(url, timeout=5)
                        response_time = time.time() - start_time
                        
                        self.log_request('GET', url, resp.status_code, response_time)
                        time.sleep(0.05)  # Very short delay - bot-like
                        
                    except Exception as e:
                        self.log_request('GET', url, 0, 0, {'error': str(e)})
                        
        except Exception as e:
            self.results['errors'].append(f"UIDAI portal test failed: {str(e)}")
            print(f"Error testing UIDAI portal: {e}")
            
    def test_admin_panel(self):
        """Test admin panel access"""
        print(f"\n=== Testing Admin Panel: {ADMIN_URL} ===")
        
        try:
            # Try to access admin panel
            start_time = time.time()
            response = self.session.get(ADMIN_URL, timeout=10)
            response_time = time.time() - start_time
            
            self.log_request('GET', ADMIN_URL, response.status_code, response_time, {
                'content_length': len(response.content),
                'has_login_form': 'login' in response.text.lower() or 'password' in response.text.lower()
            })
            
            # Try common admin endpoints (bot-like enumeration)
            admin_endpoints = [
                '/admin/login',
                '/admin/dashboard',
                '/admin/api',
                '/admin/users',
                '/admin/settings',
                '/login',
                '/dashboard'
            ]
            
            for endpoint in admin_endpoints:
                try:
                    url = urljoin(BASE_URL, endpoint)
                    start_time = time.time()
                    resp = self.session.get(url, timeout=5)
                    response_time = time.time() - start_time
                    
                    self.log_request('GET', url, resp.status_code, response_time)
                    time.sleep(0.02)  # Extremely fast enumeration
                    
                except Exception as e:
                    self.log_request('GET', url, 0, 0, {'error': str(e)})
            
            # Attempt login with common credentials (if login form found)
            if response.status_code == 200 and 'login' in response.text.lower():
                self.attempt_login()
                
        except Exception as e:
            self.results['errors'].append(f"Admin panel test failed: {str(e)}")
            print(f"Error testing admin panel: {e}")
            
    def attempt_login(self):
        """Attempt login with common credentials"""
        print("Attempting automated login...")
        
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # Try different login endpoints
        login_endpoints = [
            '/admin/login',
            '/login',
            '/admin'
        ]
        
        for endpoint in login_endpoints:
            try:
                url = urljoin(BASE_URL, endpoint)
                start_time = time.time()
                resp = self.session.post(url, data=login_data, timeout=10)
                response_time = time.time() - start_time
                
                self.log_request('POST', url, resp.status_code, response_time, {
                    'login_attempt': True,
                    'credentials': 'admin/admin123',
                    'response_length': len(resp.content)
                })
                
                # Check for successful login indicators
                if resp.status_code in [200, 302] and ('dashboard' in resp.text.lower() or resp.status_code == 302):
                    print("Possible successful login detected!")
                    
            except Exception as e:
                self.log_request('POST', url, 0, 0, {'error': str(e), 'login_attempt': True})
                
    def test_api_endpoints(self):
        """Test common API endpoints"""
        print("\n=== Testing API Endpoints ===")
        
        api_endpoints = [
            '/api/health',
            '/api/captcha/verify',
            '/api/admin/stats',
            '/api/websites',
            '/health'
        ]
        
        for endpoint in api_endpoints:
            try:
                url = urljoin(BASE_URL, endpoint)
                start_time = time.time()
                resp = self.session.get(url, timeout=5)
                response_time = time.time() - start_time
                
                self.log_request('GET', url, resp.status_code, response_time, {
                    'is_api': True,
                    'response_length': len(resp.content)
                })
                
                time.sleep(0.01)  # Rapid API testing
                
            except Exception as e:
                self.log_request('GET', url, 0, 0, {'error': str(e), 'is_api': True})
                
    def run_test(self):
        """Run complete HTTP bot test"""
        print("🌐 Starting Simple HTTP Requests Bot Test")
        print("This bot makes pure HTTP requests without browser simulation")
        
        try:
            # Test main components
            self.test_uidai_portal()
            time.sleep(0.5)  # Short break
            
            self.test_admin_panel()
            time.sleep(0.5)  # Short break
            
            self.test_api_endpoints()
            
        except Exception as e:
            print(f"Test failed: {e}")
            self.results['errors'].append(str(e))
            
        self.results['end_time'] = datetime.now().isoformat()
        return self.results
        
    def save_results(self):
        """Save test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{RESULTS_DIR}/http_requests_{timestamp}.json"
        
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to: {filename}")

def main():
    bot = SimpleRequestsBot()
    results = bot.run_test()
    bot.save_results()
    
    print(f"\n=== Test Summary ===")
    print(f"HTTP requests made: {len(results['requests'])}")
    print(f"Errors encountered: {len(results['errors'])}")
    print(f"Test duration: {results['end_time']} - {results['start_time']}")
    
    # Analyze response codes
    status_codes = {}
    for req in results['requests']:
        code = req['status_code']
        status_codes[code] = status_codes.get(code, 0) + 1
    
    print(f"Response codes: {status_codes}")
    
    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")

if __name__ == "__main__":
    main()