#!/usr/bin/env python3
"""
Deployment Test Script for Render.com
Validates that all components are working correctly
"""

import os
import sys
import subprocess
from pathlib import Path

def test_backend_dependencies():
    """Test if backend dependencies are installed"""
    print("🧪 Testing Backend Dependencies...")
    try:
        import flask
        import flask_cors
        import flask_socketio
        import numpy
        import sklearn
        import sqlalchemy
        print("✅ Backend dependencies OK")
        return True
    except ImportError as e:
        print(f"❌ Backend dependency missing: {e}")
        return False

def test_frontend_build():
    """Test if frontend build exists"""
    print("🧪 Testing Frontend Build...")
    
    frontend_dist = Path(__file__).parent / 'frontend' / 'dist'
    
    if not frontend_dist.exists():
        print(f"❌ Frontend dist folder not found: {frontend_dist}")
        return False
        
    index_file = frontend_dist / 'index.html'
    if not index_file.exists():
        print(f"❌ Frontend index.html not found: {index_file}")
        return False
    
    assets_dir = frontend_dist / 'assets'
    if not assets_dir.exists():
        print(f"❌ Frontend assets folder not found: {assets_dir}")
        return False
        
    asset_files = list(assets_dir.glob('*.js')) + list(assets_dir.glob('*.css'))
    if len(asset_files) < 5:
        print(f"⚠️ Very few asset files found ({len(asset_files)}), build might be incomplete")
        
    print(f"✅ Frontend build OK - {len(asset_files)} asset files found")
    return True

def test_environment():
    """Test environment configuration"""
    print("🧪 Testing Environment...")
    
    required_vars = ['FLASK_ENV', 'PORT']
    optional_vars = ['ADMIN_SECRET', 'VITE_API_URL', 'RENDER_EXTERNAL_URL']
    
    for var in required_vars:
        if not os.environ.get(var):
            print(f"⚠️ Required environment variable missing: {var}")
        else:
            print(f"✅ {var} = {os.environ.get(var)}")
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var} = {value}")
        else:
            print(f"ℹ️ Optional variable not set: {var}")
    
    return True

def test_app_startup():
    """Test if the app can start"""
    print("🧪 Testing App Startup...")
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent / 'backend'))
        
        from app.production_app import create_production_app
        app, socketio = create_production_app()
        
        print("✅ App creation successful")
        
        # Test if key routes are registered
        with app.app_context():
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            
            expected_routes = ['/health', '/admin/login', '/', '/admin/analytics']
            for route in expected_routes:
                if route in rules:
                    print(f"✅ Route registered: {route}")
                else:
                    print(f"⚠️ Route missing: {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("🚀 Render.com Deployment Test")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_backend_dependencies,
        test_frontend_build,
        test_app_startup
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
            print()
    
    print("📊 Test Summary")
    print("=" * 30)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    if passed == total:
        print("🎉 All tests passed! Deployment should work.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        
    # Additional deployment tips
    print("\n💡 Deployment Tips:")
    print("1. Ensure Node.js is available during Render build")
    print("2. Check that 'npm run build' runs successfully")
    print("3. Verify all environment variables are set in Render dashboard")
    print("4. Check Render build logs for any errors")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)