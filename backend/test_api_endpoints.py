#!/usr/bin/env python3
"""
API Endpoint Testing Suite
Tests all API endpoints for correct input/output and functionality
"""

import os
import sys
import json
import time
import threading
import requests
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def start_test_server():
    """Start Flask test server in background"""
    from app import create_app
    
    app = create_app('testing')
    app.config.update({
        'DATABASE_URL': 'sqlite:///test_api.db',
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'ADMIN_SECRET': 'test-admin-secret'
    })
    
    # Run server in thread
    def run_server():
        app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    return app


def test_health_endpoint():
    """Test health check endpoint"""
    print("🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get('http://127.0.0.1:5001/health', timeout=5)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'status' in data, "Health response missing 'status'"
        assert data['status'] == 'healthy', f"Expected healthy status, got {data['status']}"
        
        print(f"   ✅ Health check: {data['status']}")
        print(f"   📊 Model loaded: {data.get('model_loaded', 'unknown')}")
        return True
        
    except Exception as e:
        print(f"   ❌ Health endpoint test failed: {e}")
        return False


def test_website_registration():
    """Test website registration endpoint"""
    print("🌐 Testing Website Registration...")
    
    try:
        # Test valid registration
        registration_data = {
            'name': 'Test E-commerce Site',
            'url': 'https://test-shop.example.com',
            'admin_email': 'admin@test-shop.example.com'
        }
        
        response = requests.post(
            'http://127.0.0.1:5001/api/v1/websites/register',
            json=registration_data,
            timeout=10
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        
        data = response.json()
        assert data['success'] is True, "Registration should be successful"
        assert 'website_id' in data, "Response missing website_id"
        assert 'api_key' in data, "Response missing api_key"
        assert 'script_tag' in data, "Response missing script_tag"
        assert 'dashboard_url' in data, "Response missing dashboard_url"
        
        # Validate script tag contains website ID
        assert data['website_id'] in data['script_tag'], "Script tag missing website ID"
        
        print(f"   ✅ Website registered: {data['website_id']}")
        print(f"   🔑 API key generated: {data['api_key'][:20]}...")
        print(f"   📋 Script tag: {len(data['script_tag'])} characters")
        
        # Store for later tests
        global test_website_id, test_api_key
        test_website_id = data['website_id']
        test_api_key = data['api_key']
        
        return True
        
    except Exception as e:
        print(f"   ❌ Website registration test failed: {e}")
        return False


def test_website_registration_validation():
    """Test website registration input validation"""
    print("🔍 Testing Registration Validation...")
    
    try:
        # Test missing fields
        invalid_data = {'name': 'Test Site'}  # Missing url and admin_email
        
        response = requests.post(
            'http://127.0.0.1:5001/api/v1/websites/register',
            json=invalid_data,
            timeout=5
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid data, got {response.status_code}"
        
        data = response.json()
        assert 'error' in data, "Error response should contain 'error'"
        
        print("   ✅ Input validation working correctly")
        
        # Test invalid email
        invalid_email_data = {
            'name': 'Test Site',
            'url': 'https://test.example.com',
            'admin_email': 'invalid-email'
        }
        
        response = requests.post(
            'http://127.0.0.1:5001/api/v1/websites/register',
            json=invalid_email_data,
            timeout=5
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid email, got {response.status_code}"
        
        print("   ✅ Email validation working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Registration validation test failed: {e}")
        return False


def test_verification_endpoint():
    """Test verification endpoint"""
    print("🛡️  Testing Verification Endpoint...")
    
    try:
        # Test basic verification (legacy mode)
        verification_data = {
            'sessionId': 'test-session-123',
            'origin': 'https://test.example.com',
            'features': {
                'mouse_movement_count': 45,
                'avg_mouse_velocity': 0.8,
                'keystroke_count': 12,
                'session_duration': 25000,
                'webgl_support_score': 1.0,
                'canvas_fingerprint_score': 0.85,
                'hardware_legitimacy': 0.9,
                'browser_consistency': 0.88
            }
        }
        
        response = requests.post(
            'http://127.0.0.1:5001/api/verify',
            json=verification_data,
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'isHuman' in data, "Response missing 'isHuman'"
        assert 'confidence' in data, "Response missing 'confidence'"
        assert isinstance(data['confidence'], (int, float)), "Confidence should be numeric"
        assert 0 <= data['confidence'] <= 1, "Confidence should be between 0 and 1"
        
        print(f"   ✅ Verification result: {'Human' if data['isHuman'] else 'Bot'}")
        print(f"   📊 Confidence: {data['confidence']:.3f}")
        print(f"   ⏱️  Response time: {data.get('responseTime', 'N/A')}ms")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Verification endpoint test failed: {e}")
        return False


def test_verification_with_website_token():
    """Test verification with website token (multi-tenant mode)"""
    print("🏢 Testing Multi-Tenant Verification...")
    
    try:
        if 'test_api_key' not in globals():
            print("   ⚠️  Skipping - no test API key available")
            return True
        
        verification_data = {
            'sessionId': 'test-session-456',
            'origin': 'https://test-shop.example.com',
            'features': {
                'mouse_movement_count': 35,
                'avg_mouse_velocity': 0.7,
                'keystroke_count': 8,
                'session_duration': 15000,
                'webgl_support_score': 1.0,
                'canvas_fingerprint_score': 0.9,
                'hardware_legitimacy': 0.95,
                'browser_consistency': 0.85
            }
        }
        
        headers = {
            'X-Website-Token': test_api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'http://127.0.0.1:5001/api/verify',
            json=verification_data,
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'isHuman' in data, "Response missing 'isHuman'"
        assert 'confidence' in data, "Response missing 'confidence'"
        
        print(f"   ✅ Multi-tenant verification: {'Human' if data['isHuman'] else 'Bot'}")
        print(f"   📊 Confidence: {data['confidence']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Multi-tenant verification test failed: {e}")
        return False


def test_website_analytics():
    """Test website analytics endpoint"""
    print("📈 Testing Website Analytics...")
    
    try:
        if 'test_api_key' not in globals() or 'test_website_id' not in globals():
            print("   ⚠️  Skipping - no test website available")
            return True
        
        headers = {
            'X-Website-Token': test_api_key
        }
        
        response = requests.get(
            f'http://127.0.0.1:5001/api/v1/websites/{test_website_id}/analytics?hours=24',
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'analytics' in data, "Response missing 'analytics'"
        
        analytics = data['analytics']
        assert 'total_verifications' in analytics, "Analytics missing 'total_verifications'"
        assert 'website_id' in analytics, "Analytics missing 'website_id'"
        assert analytics['website_id'] == test_website_id, "Website ID mismatch"
        
        print(f"   ✅ Analytics retrieved for website: {test_website_id}")
        print(f"   📊 Total verifications: {analytics['total_verifications']}")
        print(f"   🎯 Human percentage: {analytics.get('human_percentage', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Website analytics test failed: {e}")
        return False


def test_script_generation():
    """Test script generation endpoint"""
    print("📜 Testing Script Generation...")
    
    try:
        if 'test_website_id' not in globals():
            print("   ⚠️  Skipping - no test website available")
            return True
        
        response = requests.get(
            f'http://127.0.0.1:5001/api/v1/websites/{test_website_id}/script',
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get('Content-Type') == 'application/javascript', "Wrong content type"
        
        script_content = response.text
        assert test_website_id in script_content, "Script missing website ID"
        assert 'PassiveCaptchaClient' in script_content, "Script missing client class"
        assert 'WEBSITE_CONFIG' in script_content, "Script missing config"
        
        print(f"   ✅ Script generated: {len(script_content)} characters")
        print(f"   🔧 Contains website ID: {test_website_id in script_content}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Script generation test failed: {e}")
        return False


def test_admin_endpoints():
    """Test admin endpoints"""
    print("👑 Testing Admin Endpoints...")
    
    try:
        # Test admin login
        login_data = {'password': 'test-admin-secret'}
        
        response = requests.post(
            'http://127.0.0.1:5001/admin/login',
            json=login_data,
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'token' in data, "Login response missing token"
        
        admin_token = data['token']
        print("   ✅ Admin login successful")
        
        # Test admin dashboard access
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        response = requests.get(
            'http://127.0.0.1:5001/admin/dashboard',
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'text/html' in response.headers.get('Content-Type', ''), "Dashboard should return HTML"
        
        print("   ✅ Admin dashboard accessible")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Admin endpoints test failed: {e}")
        return False


def test_error_handling():
    """Test error handling and edge cases"""
    print("🚨 Testing Error Handling...")
    
    try:
        # Test invalid endpoint
        response = requests.get('http://127.0.0.1:5001/api/invalid-endpoint', timeout=5)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        # Test malformed JSON
        response = requests.post(
            'http://127.0.0.1:5001/api/verify',
            data='invalid json',
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        assert response.status_code == 400, f"Expected 400 for malformed JSON, got {response.status_code}"
        
        # Test unauthorized access to protected endpoint
        response = requests.get(
            'http://127.0.0.1:5001/admin/analytics',
            timeout=5
        )
        assert response.status_code == 401, f"Expected 401 for unauthorized, got {response.status_code}"
        
        print("   ✅ Error handling working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False


def main():
    """Run all API tests"""
    print("🧪 API Endpoint Testing Suite")
    print("=" * 50)
    
    # Start test server
    print("🚀 Starting test server...")
    try:
        start_test_server()
        print("✅ Test server started on port 5001")
    except Exception as e:
        print(f"❌ Failed to start test server: {e}")
        return False
    
    # Wait for server to be ready
    for i in range(10):
        try:
            requests.get('http://127.0.0.1:5001/health', timeout=1)
            break
        except:
            time.sleep(1)
    else:
        print("❌ Test server not responding")
        return False
    
    # Run tests
    tests = [
        test_health_endpoint,
        test_website_registration,
        test_website_registration_validation,
        test_verification_endpoint,
        test_verification_with_website_token,
        test_website_analytics,
        test_script_generation,
        test_admin_endpoints,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    # Cleanup
    import os
    try:
        os.remove('test_api.db')
    except:
        pass
    
    if failed == 0:
        print("🎉 All API tests passed!")
        return True
    else:
        print("❌ Some API tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)