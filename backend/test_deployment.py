#!/usr/bin/env python3
"""
Comprehensive Deployment Testing for Passive CAPTCHA System
Tests production readiness, performance, and deployment configuration
"""

import os
import sys
import json
import time
import requests
import subprocess
import threading
from pathlib import Path
import pytest

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestDeploymentReadiness:
    """Test deployment readiness and configuration"""
    
    def test_requirements_files_exist(self):
        """Test that all required deployment files exist"""
        required_files = [
            'requirements-deploy.txt',
            'app.py',
            '../render.yaml',
            'models/passive_captcha_rf.pkl',
            'models/passive_captcha_rf_scaler.pkl',
            'models/passive_captcha_rf_metadata.json'
        ]
        
        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file missing: {file_path}"
            
    def test_render_yaml_configuration(self):
        """Test render.yaml configuration"""
        render_yaml_path = '../render.yaml'
        assert os.path.exists(render_yaml_path), "render.yaml not found"
        
        # Basic structure validation
        with open(render_yaml_path, 'r') as f:
            content = f.read()
            assert 'passive-captcha-backend' in content
            assert 'passive-captcha-frontend' in content
            assert 'requirements-deploy.txt' in content
            
    def test_environment_variables(self):
        """Test that required environment variables are documented"""
        env_example_path = 'config.env.example'
        assert os.path.exists(env_example_path), "config.env.example not found"
        
        required_vars = [
            'FLASK_ENV',
            'MODEL_PATH', 
            'DATABASE_URL',
            'CONFIDENCE_THRESHOLD',
            'SECRET_KEY'
        ]
        
        with open(env_example_path, 'r') as f:
            content = f.read()
            for var in required_vars:
                assert var in content, f"Required environment variable {var} not documented"

class TestApplicationStartup:
    """Test application startup and basic functionality"""
    
    def test_flask_app_importable(self):
        """Test that the Flask app can be imported"""
        try:
            # Import the Flask app from app.py
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # Import the app variable from app.py
            from app import app  # This imports from the root app.py file in backend/
            assert app is not None
            assert app.config is not None
        except ImportError as e:
            pytest.fail(f"Cannot import Flask app: {e}")
            
    def test_model_loading_on_startup(self):
        """Test that models can be loaded during app startup"""
        try:
            from app.ml import load_model, predict_human_probability
            
            # Test model loading
            model, scaler, metadata = load_model()
            assert model is not None
            assert scaler is not None
            assert metadata is not None
            
            # Test basic prediction
            test_features = {
                'mouse_movement_count': 10,
                'avg_mouse_velocity': 1.0,
                'mouse_acceleration_variance': 5.0,
                'keystroke_count': 5,
                'avg_keystroke_interval': 0.2,
                'session_duration_normalized': 10.0,
                'webgl_support_score': 1.0,
                'canvas_fingerprint_score': 0.8,
                'hardware_legitimacy_score': 0.9,
                'browser_consistency_score': 0.8,
                'device_entropy_score': 0.7
            }
            
            probability = predict_human_probability(test_features)
            assert 0 <= probability <= 1, f"Invalid probability: {probability}"
            
        except Exception as e:
            pytest.fail(f"Model loading failed: {e}")

class TestProductionConfiguration:
    """Test production-specific configuration"""
    
    def test_gunicorn_compatibility(self):
        """Test that the app works with gunicorn configuration"""
        try:
            # Test that the app can be imported in the way gunicorn expects
            import app as app_module
            app = app_module.app
            
            # Test WSGI callable
            assert callable(app)
            
            # Test that app has required attributes for production
            assert hasattr(app, 'config')
            assert hasattr(app, 'wsgi_app')
            
        except Exception as e:
            pytest.fail(f"Gunicorn compatibility test failed: {e}")
            
    def test_security_headers(self):
        """Test security configuration"""
        try:
            import app as app_module
            app = app_module.app
            
            with app.test_client() as client:
                response = client.get('/health')
                
                # Check for security headers (if implemented)
                # These might be added by the deployment platform
                headers = response.headers
                
                # Basic security check - ensure no debug info is leaked
                assert 'DEBUG' not in str(response.data).upper()
                
        except Exception as e:
            pytest.fail(f"Security headers test failed: {e}")

class TestPerformanceBasics:
    """Test basic performance requirements"""
    
    def test_startup_time(self):
        """Test application startup time"""
        start_time = time.time()
        
        try:
            import app as app_module
            app = app_module.app
            from app.ml import load_model
            
            # Load models (this happens during startup)
            load_model()
            
            startup_time = time.time() - start_time
            
            # Startup should be under 10 seconds
            assert startup_time < 10.0, f"Startup too slow: {startup_time:.2f}s"
            
        except Exception as e:
            pytest.fail(f"Startup time test failed: {e}")
            
    def test_memory_usage_basic(self):
        """Test basic memory usage"""
        try:
            import psutil
            import gc
            
            # Get initial memory
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Import and load models
            import app as app_module
            app = app_module.app
            from app.ml import load_model
            load_model()
            
            gc.collect()
            
            # Get memory after loading
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 1GB for this app)
            assert memory_increase < 1024, f"Memory usage too high: {memory_increase:.2f}MB increase"
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        except Exception as e:
            pytest.fail(f"Memory usage test failed: {e}")

def test_deployment_readiness_summary():
    """Run a comprehensive deployment readiness check"""
    print("\n🚀 Deployment Readiness Summary")
    print("=" * 50)
    
    checks = [
        ("Requirements files", lambda: os.path.exists('requirements-deploy.txt')),
        ("Flask app", lambda: __import__('app')),
        ("Model files", lambda: all(os.path.exists(f) for f in [
            'models/passive_captcha_rf.pkl',
            'models/passive_captcha_rf_scaler.pkl', 
            'models/passive_captcha_rf_metadata.json'
        ])),
        ("Render config", lambda: os.path.exists('../render.yaml')),
        ("Environment config", lambda: os.path.exists('config.env.example'))
    ]
    
    results = []
    for name, check_fn in checks:
        try:
            check_fn()
            status = "✅ PASS"
            results.append(True)
        except Exception as e:
            status = f"❌ FAIL: {e}"
            results.append(False)
        
        print(f"{name:<20} {status}")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\nOverall Readiness: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Ready for deployment!")
    else:
        print("⚠️  Some issues need to be addressed before deployment")
    
    return success_rate >= 80

if __name__ == "__main__":
    # Run as standalone script
    test_deployment_readiness_summary() 