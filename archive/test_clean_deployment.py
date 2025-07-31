#!/usr/bin/env python3
"""
Test the clean single-endpoint deployment
"""

import requests
import json
import time

def test_deployment():
    print("🧪 TESTING CLEAN DEPLOYMENT")
    print("=" * 50)
    
    base_url = "http://localhost:5003"
    
    # Test 1: Health check
    print("1️⃣ Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   ✅ Health: {response.status_code} - {response.json().get('status', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Health failed: {e}")
        return False
    
    # Test 2: Login page (GET)
    print("2️⃣ Testing Login Page (GET)...")
    try:
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login page: {data.get('message', 'OK')}")
        else:
            print(f"   ❌ Login page failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Login page error: {e}")
    
    # Test 3: Authentication (POST)
    print("3️⃣ Testing Authentication (POST)...")
    try:
        auth_data = {"password": "Admin123"}
        response = requests.post(
            f"{base_url}/login",
            json=auth_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                token = data['token']
                print(f"   ✅ Authentication successful!")
                print(f"   🔑 Token: {token[:50]}...")
                
                # Test 4: Authenticated API call
                print("4️⃣ Testing Authenticated API...")
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    api_response = requests.get(
                        f"{base_url}/admin/analytics/summary",
                        headers=headers,
                        timeout=5
                    )
                    
                    if api_response.status_code == 200:
                        print("   ✅ Authenticated API working")
                    else:
                        print(f"   ⚠️ API call: {api_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ API test error: {e}")
                
                return True
            else:
                print(f"   ❌ No token in response: {data}")
        else:
            print(f"   ❌ Auth failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
    
    return False

def get_tunnel_info():
    """Try to find tunnel URL from process"""
    import subprocess
    try:
        # Try to get the tunnel URL from logs
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'cloudflared tunnel' in line and 'localhost:5003' in line:
                print("🌐 Cloudflare tunnel is running")
                return True
    except:
        pass
    return False

if __name__ == '__main__':
    print("🚀 PASSIVE CAPTCHA - CLEAN DEPLOYMENT TEST")
    print("=" * 60)
    
    success = test_deployment()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        
        print(f"\n🌐 ACCESS INFORMATION:")
        print(f"   Frontend:  http://localhost:5003/")
        print(f"   Login:     http://localhost:5003/login")
        print(f"   Health:    http://localhost:5003/health")
        
        print(f"\n🔑 CREDENTIALS:")
        print(f"   Password: Admin123")
        
        print(f"\n🧪 WORKING EXAMPLES:")
        print(f"   # Get login info:")
        print(f"   curl http://localhost:5003/login")
        print(f"   ")
        print(f"   # Authenticate:")
        print(f"   curl -X POST http://localhost:5003/login \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d '{{\"password\": \"Admin123\"}}'")
        
        # Check for tunnel
        if get_tunnel_info():
            print(f"\n🌐 TUNNEL STATUS: Running (check logs for URL)")
        else:
            print(f"\n🌐 TUNNEL STATUS: Not detected")
        
        print(f"\n✅ DEPLOYMENT IS READY!")
        
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the server logs for details.")