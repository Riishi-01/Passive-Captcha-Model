#!/usr/bin/env python3
"""
Database Connectivity and CRUD Testing
Tests database operations, multi-tenancy, and data integrity
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_database_connectivity():
    """Test database connection and basic operations"""
    print("🗄️  Testing Database Connectivity...")
    
    try:
        from app import create_app
        from app.database import (
            init_db, get_db_session, store_website_registration,
            get_website_by_id, get_website_by_api_key, log_verification_with_website,
            get_analytics_data_for_website
        )
        
        # Create test app with temporary database
        app = create_app('testing')
        app.config['DATABASE_URL'] = 'sqlite:///test_captcha.db'
        
        with app.app_context():
            # Test 1: Database initialization
            print("   🔄 Testing database initialization...")
            init_db()
            print("   ✅ Database initialized successfully")
            
            # Test 2: Session creation
            print("   🔄 Testing session creation...")
            from sqlalchemy import text
            session = get_db_session()
            session.execute(text('SELECT 1'))
            session.close()
            print("   ✅ Database session created successfully")
            
            # Test 3: Website registration
            print("   🔄 Testing website registration...")
            test_website_data = {
                'website_id': 'test-website-123',
                'website_name': 'Test Website',
                'website_url': 'https://test.example.com',
                'admin_email': 'test@example.com',
                'api_key': 'pc_test_api_key_123',
                'secret_key': 'test_secret_key_456',
                'created_at': '2024-01-01T00:00:00',
                'status': 'active',
                'permissions': ['read', 'write'],
                'rate_limits': {'verify': 1000}
            }
            
            result = store_website_registration(test_website_data)
            assert result, "Website registration failed"
            print("   ✅ Website registration successful")
            
            # Test 4: Website retrieval by ID
            print("   🔄 Testing website retrieval by ID...")
            website = get_website_by_id('test-website-123')
            assert website is not None, "Website not found by ID"
            assert website['website_name'] == 'Test Website', "Website data mismatch"
            print("   ✅ Website retrieval by ID successful")
            
            # Test 5: Website retrieval by API key
            print("   🔄 Testing website retrieval by API key...")
            website = get_website_by_api_key('pc_test_api_key_123')
            assert website is not None, "Website not found by API key"
            assert website['website_id'] == 'test-website-123', "Website ID mismatch"
            print("   ✅ Website retrieval by API key successful")
            
            # Test 6: Verification logging
            print("   🔄 Testing verification logging...")
            test_features = [0.5, 0.8, 0.2, 0.7, 0.9, 0.6, 0.3, 0.8, 0.7, 0.9, 0.6]
            result = log_verification_with_website(
                website_id='test-website-123',
                session_id='test-session-456',
                ip_address='192.168.1.1',
                user_agent='Test User Agent',
                origin='https://test.example.com',
                is_human=True,
                confidence=0.85,
                features=test_features,
                response_time=45.5
            )
            assert result, "Verification logging failed"
            print("   ✅ Verification logging successful")
            
            # Test 7: Analytics retrieval
            print("   🔄 Testing analytics retrieval...")
            analytics = get_analytics_data_for_website('test-website-123', 24)
            assert analytics is not None, "Analytics retrieval failed"
            assert analytics['website_id'] == 'test-website-123', "Analytics website ID mismatch"
            assert analytics['total_verifications'] == 1, "Verification count mismatch"
            print("   ✅ Analytics retrieval successful")
            
        # Cleanup
        test_db_path = Path('test_captcha.db')
        if test_db_path.exists():
            test_db_path.unlink()
        
        print("   🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_tenant_isolation():
    """Test multi-tenant isolation in database"""
    print("🏢 Testing Multi-Tenant Isolation...")
    
    try:
        from app import create_app
        from app.database import (
            store_website_registration, get_analytics_data_for_website,
            log_verification_with_website
        )
        
        app = create_app('testing')
        app.config['DATABASE_URL'] = 'sqlite:///test_isolation.db'
        
        with app.app_context():
            # Create two test websites
            website1_data = {
                'website_id': 'website-1',
                'website_name': 'Website One',
                'website_url': 'https://one.example.com',
                'admin_email': 'admin1@example.com',
                'api_key': 'pc_key_1',
                'secret_key': 'secret_1',
                'created_at': '2024-01-01T00:00:00',
                'status': 'active',
                'permissions': ['read', 'write'],
                'rate_limits': {'verify': 1000}
            }
            
            website2_data = {
                'website_id': 'website-2',
                'website_name': 'Website Two',
                'website_url': 'https://two.example.com',
                'admin_email': 'admin2@example.com',
                'api_key': 'pc_key_2',
                'secret_key': 'secret_2',
                'created_at': '2024-01-01T00:00:00',
                'status': 'active',
                'permissions': ['read', 'write'],
                'rate_limits': {'verify': 1000}
            }
            
            # Store both websites
            store_website_registration(website1_data)
            store_website_registration(website2_data)
            
            # Log verifications for website 1
            test_features = [0.5, 0.8, 0.2, 0.7, 0.9, 0.6, 0.3, 0.8, 0.7, 0.9, 0.6]
            for i in range(3):
                log_verification_with_website(
                    website_id='website-1',
                    session_id=f'session-1-{i}',
                    ip_address='192.168.1.1',
                    user_agent='Test Agent',
                    origin='https://one.example.com',
                    is_human=True,
                    confidence=0.8,
                    features=test_features,
                    response_time=50
                )
            
            # Log verifications for website 2  
            for i in range(5):
                log_verification_with_website(
                    website_id='website-2',
                    session_id=f'session-2-{i}',
                    ip_address='192.168.1.2',
                    user_agent='Test Agent',
                    origin='https://two.example.com',
                    is_human=False,
                    confidence=0.3,
                    features=test_features,
                    response_time=30
                )
            
            # Test isolation - website 1 should only see its data
            analytics1 = get_analytics_data_for_website('website-1', 24)
            assert analytics1['total_verifications'] == 3, f"Website 1 isolation failed: {analytics1['total_verifications']}"
            assert analytics1['human_detections'] == 3, "Website 1 human count mismatch"
            
            # Test isolation - website 2 should only see its data
            analytics2 = get_analytics_data_for_website('website-2', 24)
            assert analytics2['total_verifications'] == 5, f"Website 2 isolation failed: {analytics2['total_verifications']}"
            assert analytics2['bot_detections'] == 5, "Website 2 bot count mismatch"
            
        # Cleanup
        test_db_path = Path('test_isolation.db')
        if test_db_path.exists():
            test_db_path.unlink()
            
        print("   🎉 Multi-tenant isolation tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Multi-tenant test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all database tests"""
    print("🧪 Database Testing Suite")
    print("=" * 50)
    
    tests = [
        test_database_connectivity,
        test_multi_tenant_isolation
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
    
    if failed == 0:
        print("🎉 All database tests passed!")
        return True
    else:
        print("❌ Some database tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)