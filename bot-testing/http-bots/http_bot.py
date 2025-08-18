#!/usr/bin/env python3
"""
HTTP Bot - Demo Version
Pure HTTP requests targeting endpoints that get blocked - perfect for demonstrations
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
from config import BASE_URL, USER_AGENTS, RESULTS_DIR

class HTTPBot:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            'bot_type': 'http_bot_demo',
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
        
        # Color code the status for demo
        if status_code == 403:
            status_display = f"🚫 {status_code} BLOCKED"
        elif status_code == 404:
            status_display = f"❌ {status_code} BLOCKED" 
        else:
            status_display = str(status_code)
            
        print(f"[HTTP BOT] {method} {url} -> {status_display} ({log_entry['response_time_ms']}ms)")
        
    def test_blocked_endpoints(self):
        """Test only endpoints that get blocked - perfect for demo"""
        print(f"\n🎯 Testing Blocked Endpoints (Demo Mode)")
        print(f"Target: {BASE_URL}")
        print(f"User-Agent: {USER_AGENTS['bot_obvious']}")
        print("=" * 60)
        
        # Only test endpoints that get blocked (based on previous results)
        blocked_endpoints = [
            {
                'url': '/',
                'description': 'Main UIDAI Portal',
                'expected': '403 Forbidden'
            },
            {
                'url': '/api/health',
                'description': 'API Health Check',
                'expected': '404 Not Found'
            },
            {
                'url': '/api/captcha/verify',
                'description': 'CAPTCHA API Endpoint',
                'expected': '404 Not Found'
            },
            {
                'url': '/api/admin/stats',
                'description': 'Admin Statistics API',
                'expected': '404 Not Found'
            }
        ]
        
        for endpoint in blocked_endpoints:
            try:
                url = urljoin(BASE_URL, endpoint['url'])
                print(f"\n📍 Testing: {endpoint['description']}")
                print(f"   Expected: {endpoint['expected']}")
                
                start_time = time.time()
                response = self.session.get(url, timeout=10)
                response_time = time.time() - start_time
                
                # Log with additional context
                details = {
                    'description': endpoint['description'],
                    'expected': endpoint['expected'],
                    'content_length': len(response.content)
                }
                
                # Add response content for error messages
                if response.status_code in [403, 404]:
                    try:
                        error_content = response.json()
                        details['error_message'] = error_content.get('error', 'Access denied')
                    except:
                        details['error_message'] = 'Blocked by security system'
                
                self.log_request('GET', url, response.status_code, response_time, details)
                
                # Short delay between requests (bot-like behavior)
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error testing {endpoint['url']}: {str(e)}")
                self.results['errors'].append(f"Error testing {endpoint['url']}: {str(e)}")
                
    def run_test(self):
        """Run focused bot test for demo"""
        print("🤖 Starting HTTP Bot Test (Demo Version)")
        print("This bot targets endpoints that demonstrate bot detection")
        print("")
        
        try:
            self.test_blocked_endpoints()
            
        except Exception as e:
            print(f"Test failed: {e}")
            self.results['errors'].append(str(e))
            
        self.results['end_time'] = datetime.now().isoformat()
        return self.results
        
    def save_results(self):
        """Save test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{RESULTS_DIR}/http_bot_demo_{timestamp}.json"
        
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")

def main():
    bot = HTTPBot()
    results = bot.run_test()
    bot.save_results()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 DEMO SUMMARY")
    print(f"=" * 60)
    print(f"📊 HTTP requests made: {len(results['requests'])}")
    print(f"⚠️  Errors encountered: {len(results['errors'])}")
    
    # Analyze response codes
    blocked_count = 0
    status_codes = {}
    for req in results['requests']:
        code = req['status_code']
        status_codes[code] = status_codes.get(code, 0) + 1
        if code in [403, 404]:
            blocked_count += 1
    
    print(f"🚫 Blocked requests: {blocked_count}/{len(results['requests'])}")
    print(f"📈 Response codes: {status_codes}")
    
    if blocked_count == len(results['requests']):
        print(f"✅ PERFECT DEMO: All requests blocked!")
    else:
        print(f"⚠️  Some requests not blocked")
    
    if results['errors']:
        print(f"\n❌ Errors:")
        for error in results['errors']:
            print(f"   - {error}")
    
    print(f"\n🎉 Bot detection demonstration complete!")

if __name__ == "__main__":
    main()