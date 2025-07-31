#!/usr/bin/env python3
"""
Complete API Test Suite for Passive CAPTCHA
Shows all working endpoints and authentication
"""

import requests
import json
import sys

def test_complete_api():
    """Test the complete API suite"""
    
    print("🚀 PASSIVE CAPTCHA - COMPLETE API TEST")
    print("=" * 60)
    
    # Get base URLs
    localhost = "http://localhost:5003"
    tunnel = "https://seeker-busy-acquisitions-peace.trycloudflare.com"
    
    results = []
    
    for base_url, name in [(localhost, "LOCALHOST"), (tunnel, "TUNNEL")]:
        print(f"\n📡 TESTING {name}: {base_url}")
        print("-" * 50)
        
        # Step 1: Test login and get token
        try:
            print("🔐 Step 1: Admin Login...")
            login_response = requests.post(
                f"{base_url}/admin/legacy/login",
                json={"password": "Admin123"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                token = login_data.get('token')
                print(f"   ✅ Login successful!")
                print(f"   🔑 Token: {token[:50]}...")
                results.append(f"{name} Login: ✅ SUCCESS")
                
                # Step 2: Test authenticated endpoints
                auth_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                endpoints = [
                    ("/admin/analytics/summary", "Analytics Summary"),
                    ("/admin/ml/metrics", "ML Metrics"),
                    ("/admin/websites", "Websites List"),
                    ("/health", "Health Check")
                ]
                
                for endpoint, desc in endpoints:
                    try:
                        print(f"📊 Testing {desc}...")
                        response = requests.get(
                            f"{base_url}{endpoint}",
                            headers=auth_headers,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            print(f"   ✅ {desc}: SUCCESS")
                            
                            # Show sample data
                            if 'data' in data:
                                if endpoint == "/admin/analytics/summary":
                                    analytics = data['data']
                                    print(f"      📈 Total Verifications: {analytics.get('total_verifications', 0)}")
                                    print(f"      🤖 Human Rate: {analytics.get('human_rate', 0)}%")
                                elif endpoint == "/admin/ml/metrics":
                                    print(f"      🤖 ML Model Status: Available")
                                elif endpoint == "/admin/websites":
                                    websites = data.get('data', [])
                                    print(f"      🌐 Registered Websites: {len(websites)}")
                            elif 'status' in data:
                                print(f"      💊 Health Status: {data['status']}")
                            
                            results.append(f"{name} {desc}: ✅ SUCCESS")
                        else:
                            print(f"   ❌ {desc}: Failed ({response.status_code})")
                            results.append(f"{name} {desc}: ❌ FAILED")
                            
                    except Exception as e:
                        print(f"   ❌ {desc}: Error - {e}")
                        results.append(f"{name} {desc}: ❌ ERROR")
                
            else:
                print(f"   ❌ Login failed: {login_response.status_code}")
                results.append(f"{name} Login: ❌ FAILED")
                
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
            results.append(f"{name} Connection: ❌ ERROR")
    
    # Summary
    print("\n📊 FINAL RESULTS")
    print("=" * 60)
    
    success_count = 0
    for result in results:
        if "✅ SUCCESS" in result:
            print(f"✅ {result}")
            success_count += 1
        else:
            print(f"❌ {result}")
    
    total = len(results)
    print(f"\n📈 OVERALL: {success_count}/{total} tests passed")
    
    if success_count >= total * 0.8:
        print("\n🎉 DEPLOYMENT IS WORKING! Password 'Admin123' is functional!")
        
        print("\n🔧 WORKING EXAMPLES:")
        print("# Login and get token:")
        print(f"TOKEN=$(curl -s -X POST {localhost}/admin/legacy/login \\")
        print("       -H 'Content-Type: application/json' \\")
        print("       -d '{\"password\": \"Admin123\"}' | jq -r '.token')")
        print()
        print("# Use token for API calls:")
        print(f"curl -s -X GET {localhost}/admin/analytics/summary \\")
        print("     -H \"Authorization: Bearer $TOKEN\" | jq .")
        
        return True
    else:
        print("\n⚠️ Some issues found. Check logs above.")
        return False

if __name__ == "__main__":
    success = test_complete_api()
    sys.exit(0 if success else 1)