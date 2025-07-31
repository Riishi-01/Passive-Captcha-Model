#!/usr/bin/env python3
"""
Test script for Passive CAPTCHA Production Deployment
Tests both localhost and Cloudflare tunnel
"""

import requests
import json
import time
import sys

def test_endpoint(url, description, method='GET', data=None, headers=None):
    """Test an endpoint and return results"""
    try:
        print(f"🔄 Testing {description}...")
        print(f"   URL: {url}")
        
        if method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ SUCCESS: {description}")
                if 'token' in result:
                    print(f"   🔑 Token: {result['token'][:50]}...")
                return True, result
            except:
                print(f"   ✅ SUCCESS: {description} (HTML response)")
                return True, response.text[:100]
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text[:100]}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, None

def main():
    print("🚀 Passive CAPTCHA Production Deployment Test")
    print("=" * 60)
    
    # Test configurations
    localhost_base = "http://localhost:5003"
    tunnel_base = "https://kiss-creek-finite-blend.trycloudflare.com"
    
    admin_credentials = {"password": "Admin123"}
    headers = {"Content-Type": "application/json"}
    
    tests = [
        # Localhost tests
        (f"{localhost_base}/", "Localhost Frontend", "GET"),
        (f"{localhost_base}/health", "Localhost Health Check", "GET"),
        (f"{localhost_base}/admin/legacy/login", "Localhost Admin Login", "POST", admin_credentials, headers),
        
        # Tunnel tests
        (f"{tunnel_base}/", "Tunnel Frontend", "GET"),
        (f"{tunnel_base}/health", "Tunnel Health Check", "GET"),
        (f"{tunnel_base}/admin/legacy/login", "Tunnel Admin Login", "POST", admin_credentials, headers),
    ]
    
    results = []
    
    for test_args in tests:
        success, data = test_endpoint(*test_args)
        results.append((test_args[1], success))
        print()
        time.sleep(1)
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
        if success:
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📈 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your deployment is working perfectly!")
        print("\n🌐 ACCESS YOUR APP:")
        print(f"   Local:  {localhost_base}/")
        print(f"   Public: {tunnel_base}/")
        print(f"\n🔑 LOGIN CREDENTIALS:")
        print(f"   Password: Admin123")
        print(f"   Endpoint: /admin/legacy/login")
    else:
        print("⚠️ Some tests failed. Check the logs above.")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)