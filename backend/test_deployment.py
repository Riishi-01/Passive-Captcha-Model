#!/usr/bin/env python3
"""
Deployment Test Script
Test critical endpoints to verify deployment is working
"""

import requests
import json
import time
import sys
from typing import Dict, Any


def test_endpoint(url: str, method: str = 'GET', data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    try:
        print(f"Testing {method} {url}...")
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return {'status': 'error', 'message': f'Unsupported method: {method}'}
        
        return {
            'status': 'success',
            'status_code': response.status_code,
            'response_size': len(response.content),
            'content_type': response.headers.get('content-type', 'unknown'),
            'response_time': response.elapsed.total_seconds(),
            'data': response.json() if 'application/json' in response.headers.get('content-type', '') else response.text[:200]
        }
        
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': str(e)}
    except json.JSONDecodeError as e:
        return {'status': 'error', 'message': f'JSON decode error: {e}'}
    except Exception as e:
        return {'status': 'error', 'message': f'Unexpected error: {e}'}


def main():
    """Run deployment tests"""
    
    # Configuration
    BASE_URL = 'http://localhost:5003'
    
    # Test endpoints
    endpoints = [
        # Basic health checks
        {'url': f'{BASE_URL}/health', 'name': 'Main Health Check'},
        {'url': f'{BASE_URL}/admin/health', 'name': 'Admin Health Check'},
        
        # Analytics endpoints (without auth)
        {'url': f'{BASE_URL}/admin/analytics/detection?timeRange=24h', 'name': 'Detection Analytics'},
        {'url': f'{BASE_URL}/admin/analytics/charts?timeRange=24h', 'name': 'Charts Data'},
        {'url': f'{BASE_URL}/admin/analytics/stats?timeRange=24h', 'name': 'Stats (requires auth)'},
        
        # Alerts endpoints
        {'url': f'{BASE_URL}/admin/alerts/recent', 'name': 'Recent Alerts'},
        
        # Admin endpoints
        {'url': f'{BASE_URL}/admin/websites?include_analytics=true', 'name': 'Websites List'},
        
        # API endpoints
        {'url': f'{BASE_URL}/api/health', 'name': 'API Health (if exists)'},
    ]
    
    print("🧪 Deployment Test Suite")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing {len(endpoints)} endpoints...")
    print()
    
    results = []
    passed = 0
    failed = 0
    
    for endpoint in endpoints:
        result = test_endpoint(endpoint['url'])
        result['name'] = endpoint['name']
        result['url'] = endpoint['url']
        results.append(result)
        
        # Determine if test passed
        if result['status'] == 'success' and result['status_code'] < 500:
            status_emoji = "✅"
            passed += 1
        else:
            status_emoji = "❌"
            failed += 1
        
        # Print result
        if result['status'] == 'success':
            print(f"{status_emoji} {endpoint['name']}: {result['status_code']} ({result['response_time']:.3f}s)")
            if result['status_code'] >= 400:
                if isinstance(result['data'], dict) and 'error' in result['data']:
                    print(f"   Error: {result['data']['error']}")
        else:
            print(f"{status_emoji} {endpoint['name']}: {result['message']}")
        
        time.sleep(0.1)  # Brief pause between requests
    
    print()
    print("📊 Test Summary")
    print("=" * 30)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    # Detailed results for debugging
    if failed > 0:
        print()
        print("🔍 Failed Endpoints Details:")
        print("-" * 40)
        for result in results:
            if result['status'] != 'success' or result['status_code'] >= 500:
                print(f"❌ {result['name']} ({result['url']})")
                if result['status'] == 'success':
                    print(f"   Status: {result['status_code']}")
                    if isinstance(result['data'], dict):
                        print(f"   Response: {json.dumps(result['data'], indent=2)}")
                else:
                    print(f"   Error: {result['message']}")
                print()
    
    # Exit with appropriate code
    if failed == 0:
        print("🎉 All tests passed! Deployment looks good.")
        sys.exit(0)
    else:
        print(f"⚠️  {failed} test(s) failed. Check the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()