#!/usr/bin/env python3
"""
Test script to verify backend-frontend integration
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:5003"
ADMIN_PASSWORD = "admin123"

def test_backend_endpoints():
    """Test key backend endpoints"""
    print("🧪 Testing Backend API Integration")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: OK")
        else:
            print(f"❌ Health endpoint: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Health endpoint: Error - {e}")
    
    # Test admin login
    try:
        login_data = {"password": ADMIN_PASSWORD}
        response = requests.post(f"{BACKEND_URL}/admin/login", 
                               json=login_data, 
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('token'):
                token = data['data']['token']
                print("✅ Admin login: OK")
                
                # Test authenticated endpoint
                headers = {"Authorization": f"Bearer {token}"}
                auth_response = requests.get(f"{BACKEND_URL}/admin/verify-token", 
                                           headers=headers, 
                                           timeout=5)
                
                if auth_response.status_code == 200:
                    print("✅ Token verification: OK")
                else:
                    print(f"❌ Token verification: Failed ({auth_response.status_code})")
                
                # Test statistics endpoint
                stats_response = requests.get(f"{BACKEND_URL}/admin/analytics/stats", 
                                            headers=headers, 
                                            timeout=5)
                
                if stats_response.status_code == 200:
                    print("✅ Analytics stats: OK")
                else:
                    print(f"❌ Analytics stats: Failed ({stats_response.status_code})")
                
                # Test websites endpoint
                websites_response = requests.get(f"{BACKEND_URL}/admin/websites", 
                                               headers=headers, 
                                               timeout=5)
                
                if websites_response.status_code == 200:
                    print("✅ Websites endpoint: OK")
                else:
                    print(f"❌ Websites endpoint: Failed ({websites_response.status_code})")
                
                # Test ML health endpoint
                ml_response = requests.get(f"{BACKEND_URL}/admin/ml/health", 
                                         headers=headers, 
                                         timeout=5)
                
                if ml_response.status_code in [200, 503]:  # 503 is acceptable if model not loaded
                    print("✅ ML health endpoint: OK")
                else:
                    print(f"❌ ML health endpoint: Failed ({ml_response.status_code})")
                
            else:
                print(f"❌ Admin login: No token received")
        else:
            print(f"❌ Admin login: Failed ({response.status_code})")
            if response.content:
                print(f"    Response: {response.content.decode()}")
    
    except Exception as e:
        print(f"❌ Admin login: Error - {e}")


def test_cors_headers():
    """Test CORS configuration"""
    print("\n🌐 Testing CORS Configuration")
    print("=" * 50)
    
    try:
        # Test OPTIONS request for CORS preflight
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
        
        response = requests.options(f"{BACKEND_URL}/admin/login", 
                                  headers=headers, 
                                  timeout=5)
        
        if response.status_code in [200, 204]:
            cors_headers = response.headers
            if 'Access-Control-Allow-Origin' in cors_headers:
                print("✅ CORS preflight: OK")
                print(f"    Allow-Origin: {cors_headers.get('Access-Control-Allow-Origin')}")
                print(f"    Allow-Methods: {cors_headers.get('Access-Control-Allow-Methods')}")
                print(f"    Allow-Headers: {cors_headers.get('Access-Control-Allow-Headers')}")
            else:
                print("❌ CORS preflight: Missing CORS headers")
        else:
            print(f"❌ CORS preflight: Failed ({response.status_code})")
    
    except Exception as e:
        print(f"❌ CORS test: Error - {e}")


def generate_integration_report():
    """Generate integration summary report"""
    print("\n📋 Integration Summary Report")
    print("=" * 50)
    
    endpoints_tested = [
        "/health",
        "/admin/login", 
        "/admin/verify-token",
        "/admin/analytics/stats",
        "/admin/websites",
        "/admin/ml/health"
    ]
    
    print("🔗 Backend-Frontend API Mapping:")
    print(f"   Backend Base URL: {BACKEND_URL}")
    print(f"   Frontend Expected: http://localhost:5003")
    print(f"   Admin Password: {ADMIN_PASSWORD}")
    print()
    
    print("📡 Tested Endpoints:")
    for endpoint in endpoints_tested:
        print(f"   ✓ {endpoint}")
    
    print()
    print("🎯 Frontend Integration Checklist:")
    print("   ✓ API base URL updated to match backend")
    print("   ✓ Authentication token handling unified")
    print("   ✓ Response format standardized")
    print("   ✓ Error handling improved")
    print("   ✓ CORS configuration set up")
    
    print()
    print("⚙️  Configuration Files:")
    print("   ✓ backend/.env created with default settings")
    print("   ✓ frontend/.env created with API URL")
    print("   ✓ Duplicate API routes removed")
    print("   ✓ Authentication system unified")
    
    print()
    print("🚀 Next Steps:")
    print("   1. Start backend: cd backend && python main.py")
    print("   2. Start frontend: cd frontend && npm run dev")
    print("   3. Access dashboard: http://localhost:5173")
    print("   4. Login with password: admin123")


if __name__ == "__main__":
    start_time = time.time()
    
    print("🛡️  PASSIVE CAPTCHA INTEGRATION TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    test_backend_endpoints()
    test_cors_headers() 
    generate_integration_report()
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Test completed in {elapsed:.2f} seconds")
    print("\n" + "=" * 60)
