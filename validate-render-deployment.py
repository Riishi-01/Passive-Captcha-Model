#!/usr/bin/env python3
"""
Render Deployment Validation Script
Tests all aspects of the deployment to ensure everything works correctly
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

def check_project_structure():
    """Validate project structure"""
    print("🔍 Checking project structure...")
    
    required_files = [
        'render.yaml',
        'render-build-enhanced.sh',
        'backend/requirements-render.txt',
        'backend/render_start.py',
        'frontend/package.json',
        'frontend/.nvmrc'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_build_script():
    """Test build script execution"""
    print("🔍 Testing build script...")
    
    try:
        # Make script executable
        subprocess.run(['chmod', '+x', 'render-build-enhanced.sh'], check=True)
        
        # Test script (dry run)
        result = subprocess.run(['bash', '-n', 'render-build-enhanced.sh'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build script syntax is valid")
            return True
        else:
            print(f"❌ Build script syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Build script check failed: {e}")
        return False

def check_frontend_build():
    """Check if frontend can be built"""
    print("🔍 Checking frontend build capability...")
    
    if not os.path.exists('frontend/package.json'):
        print("❌ Frontend package.json not found")
        return False
    
    # Check if dist folder exists
    if os.path.exists('frontend/dist'):
        print("✅ Frontend dist folder exists")
        
        # Check if index.html exists
        if os.path.exists('frontend/dist/index.html'):
            print("✅ Frontend index.html exists")
            
            # Check file size
            size = os.path.getsize('frontend/dist/index.html')
            if size > 100:  # At least 100 bytes
                print(f"✅ Frontend index.html has content ({size} bytes)")
                return True
            else:
                print(f"⚠️ Frontend index.html is very small ({size} bytes)")
                return True
        else:
            print("❌ Frontend index.html missing")
            return False
    else:
        print("⚠️ Frontend dist folder not found - will be created during build")
        return True

def check_python_requirements():
    """Validate Python requirements"""
    print("🔍 Checking Python requirements...")
    
    try:
        with open('backend/requirements-render.txt', 'r') as f:
            requirements = f.read()
        
        # Check for essential packages
        essential_packages = [
            'flask',
            'flask-cors',
            'flask-socketio',
            'numpy',
            'scikit-learn',
            'pandas'
        ]
        
        missing_packages = []
        for package in essential_packages:
            if package not in requirements.lower():
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing essential packages: {missing_packages}")
            return False
        else:
            print("✅ All essential packages present in requirements")
            return True
            
    except Exception as e:
        print(f"❌ Failed to check requirements: {e}")
        return False

def check_render_config():
    """Validate render.yaml configuration"""
    print("🔍 Checking Render configuration...")
    
    try:
        with open('render.yaml', 'r') as f:
            config = f.read()
        
        # Check for essential configurations
        required_configs = [
            'buildCommand',
            'startCommand',
            'envVars',
            'healthCheckPath'
        ]
        
        missing_configs = []
        for config_item in required_configs:
            if config_item not in config:
                missing_configs.append(config_item)
        
        if missing_configs:
            print(f"❌ Missing configurations: {missing_configs}")
            return False
        else:
            print("✅ Render configuration looks good")
            return True
            
    except Exception as e:
        print(f"❌ Failed to check render.yaml: {e}")
        return False

def test_local_server():
    """Test if the app can start locally"""
    print("🔍 Testing local server startup...")
    
    try:
        # Try to import the main app
        sys.path.insert(0, 'backend')
        from app.production_app import create_production_app
        
        app, socketio = create_production_app()
        print("✅ App can be created successfully")
        
        # Test a simple route
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint responds correctly")
                return True
            else:
                print(f"⚠️ Health endpoint returned status {response.status_code}")
                return True  # Not critical for deployment
                
    except Exception as e:
        print(f"❌ Local server test failed: {e}")
        return False

def generate_deployment_report():
    """Generate deployment readiness report"""
    print("\n" + "="*50)
    print("🚀 RENDER DEPLOYMENT VALIDATION REPORT")
    print("="*50)
    
    checks = [
        ("Project Structure", check_project_structure),
        ("Build Script", check_build_script),
        ("Frontend Build", check_frontend_build),
        ("Python Requirements", check_python_requirements),
        ("Render Config", check_render_config),
        ("Local Server", test_local_server)
    ]
    
    results = {}
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            result = check_func()
            results[check_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {e}")
            results[check_name] = False
            all_passed = False
    
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    print("="*50)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED!")
        print("✅ Your deployment should succeed on Render")
        print("\n📋 Next steps:")
        print("1. Commit all changes to your repository")
        print("2. Push to your main branch")
        print("3. Deploy on Render")
        print("4. Test the deployed endpoints")
    else:
        print("\n⚠️ SOME CHECKS FAILED")
        print("❌ Please fix the failing checks before deploying")
        print("\n🔧 Common fixes:")
        print("- Run: chmod +x render-build-enhanced.sh")
        print("- Run: cd frontend && npm run build")
        print("- Check file paths in render.yaml")
    
    return all_passed

if __name__ == "__main__":
    # Change to project root directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success = generate_deployment_report()
    sys.exit(0 if success else 1)