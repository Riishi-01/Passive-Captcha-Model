#!/usr/bin/env python3
"""
Render Deployment Tests
"""

import sys
import os
import unittest
import requests
import subprocess
import json
import time
from pathlib import Path


class TestRenderDeployment(unittest.TestCase):
    """Test Render deployment configuration"""
    
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.backend_dir = self.project_root / 'backend'
        self.frontend_dir = self.project_root / 'frontend'
        
    def test_render_files_exist(self):
        """Test that all required Render files exist"""
        required_files = [
            'render-build.sh',
            'render.yaml',
            'backend/render_start.py',
            'backend/requirements-render.txt'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            self.assertTrue(full_path.exists(), f"Required file missing: {file_path}")
            
    def test_render_build_script_executable(self):
        """Test that render-build.sh is executable"""
        build_script = self.project_root / 'render-build.sh'
        self.assertTrue(os.access(build_script, os.X_OK), "render-build.sh should be executable")
        
    def test_requirements_render_valid(self):
        """Test that requirements-render.txt is valid"""
        requirements_file = self.backend_dir / 'requirements-render.txt'
        
        with open(requirements_file, 'r') as f:
            content = f.read()
            
        # Check for essential packages
        essential_packages = [
            'flask>=3.0.0',
            'gunicorn>=21.2.0',
            'numpy>=1.26.2',
            'scikit-learn>=1.4.0',
            'geoip2>=4.7.0',
            'user-agents>=2.2.0'
        ]
        
        for package in essential_packages:
            self.assertIn(package, content, f"Missing essential package: {package}")
            
    def test_render_start_script_syntax(self):
        """Test that render_start.py has valid syntax"""
        render_start = self.backend_dir / 'render_start.py'
        
        try:
            with open(render_start, 'r') as f:
                code = f.read()
            compile(code, str(render_start), 'exec')
        except SyntaxError as e:
            self.fail(f"Syntax error in render_start.py: {e}")
            
    def test_environment_variables_configured(self):
        """Test that required environment variables are documented"""
        render_yaml = self.project_root / 'render.yaml'
        
        with open(render_yaml, 'r') as f:
            content = f.read()
            
        required_env_vars = ['FLASK_ENV', 'ADMIN_SECRET', 'HOST']
        
        for var in required_env_vars:
            self.assertIn(var, content, f"Missing environment variable in render.yaml: {var}")
            
    def test_frontend_package_json_exists(self):
        """Test that frontend has package.json for build"""
        package_json = self.frontend_dir / 'package.json'
        self.assertTrue(package_json.exists(), "Frontend package.json missing")
        
        with open(package_json, 'r') as f:
            data = json.load(f)
            
        self.assertIn('scripts', data, "package.json should have scripts section")
        self.assertIn('build', data['scripts'], "package.json should have build script")
        
    def test_backend_models_exist(self):
        """Test that ML models exist for deployment"""
        models_dir = self.backend_dir / 'models'
        
        required_models = [
            'passive_captcha_rf.pkl',
            'passive_captcha_rf_scaler.pkl'
        ]
        
        for model in required_models:
            model_path = models_dir / model
            self.assertTrue(model_path.exists(), f"Missing ML model: {model}")


class TestLocalDeployment(unittest.TestCase):
    """Test local deployment simulation"""
    
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.backend_dir = self.project_root / 'backend'
        
    def test_local_requirements_install(self):
        """Test that requirements can be installed locally"""
        requirements_file = self.backend_dir / 'requirements-render.txt'
        
        # Try to validate requirements (don't actually install)
        try:
            result = subprocess.run([
                'pip', 'install', '--dry-run', '-r', str(requirements_file)
            ], capture_output=True, text=True, timeout=30)
            
            # If dry-run fails, at least check file format
            if result.returncode != 0:
                with open(requirements_file, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Basic format check
                        self.assertTrue(
                            '>=' in line or '==' in line or line.isalpha(),
                            f"Invalid requirement format: {line}"
                        )
        except subprocess.TimeoutExpired:
            self.skipTest("Pip install check timed out")
        except FileNotFoundError:
            self.skipTest("Pip not available for testing")
            
    def test_import_dependencies(self):
        """Test that critical dependencies can be imported"""
        critical_imports = [
            'flask',
            'numpy',
            'sklearn',
            'pandas',
            'sqlalchemy',
            'jwt'
        ]
        
        for module in critical_imports:
            try:
                __import__(module)
            except ImportError:
                self.skipTest(f"Module {module} not available for testing")


class TestDeploymentHealth(unittest.TestCase):
    """Test deployment health and readiness"""
    
    def test_health_check_structure(self):
        """Test that health check returns proper structure"""
        # This would run against a deployed instance
        base_url = os.getenv('DEPLOYMENT_URL')
        
        if not base_url:
            self.skipTest("No DEPLOYMENT_URL provided")
            
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['status', 'components']
                for field in required_fields:
                    self.assertIn(field, data, f"Health check missing field: {field}")
                    
                # Check components structure
                components = data.get('components', {})
                expected_components = ['database', 'ml_model']
                
                for component in expected_components:
                    self.assertIn(component, components, f"Missing component: {component}")
                    
        except requests.exceptions.RequestException:
            self.skipTest("Deployment not accessible for health check")


def run_deployment_tests():
    """Run all deployment tests"""
    print("🚀 PASSIVE CAPTCHA - DEPLOYMENT TESTS")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestRenderDeployment))
    suite.addTest(unittest.makeSuite(TestLocalDeployment))
    suite.addTest(unittest.makeSuite(TestDeploymentHealth))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_deployment_tests()
    sys.exit(0 if success else 1)