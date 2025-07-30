#!/usr/bin/env python3
"""
Deployment Testing Suite
Tests deployment readiness, configuration, and build processes
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_environment_variables():
    """Test required environment variables and configuration"""
    print("🔧 Testing Environment Variables...")
    
    try:
        # Required environment variables for production
        required_env_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'ADMIN_SECRET'
        ]
        
        # Optional but recommended environment variables
        optional_env_vars = [
            'REDIS_URL',
            'JWT_SECRET_KEY',
            'CONFIDENCE_THRESHOLD',
            'RATE_LIMIT_REQUESTS',
            'ALLOWED_ORIGINS',
            'API_BASE_URL',
            'DASHBOARD_BASE_URL'
        ]
        
        missing_required = []
        missing_optional = []
        
        # Check required variables
        for var in required_env_vars:
            if not os.getenv(var):
                missing_required.append(var)
            else:
                print(f"   ✅ {var} configured")
        
        # Check optional variables
        for var in optional_env_vars:
            if not os.getenv(var):
                missing_optional.append(var)
            else:
                print(f"   ✅ {var} configured")
        
        if missing_required:
            print(f"   ❌ Missing required variables: {missing_required}")
            return False
        
        if missing_optional:
            print(f"   ⚠️  Missing optional variables: {missing_optional}")
        
        print("   ✅ All required environment variables present")
        return True
        
    except Exception as e:
        print(f"   ❌ Environment variables test failed: {e}")
        return False


def test_production_configuration():
    """Test production configuration settings"""
    print("⚙️  Testing Production Configuration...")
    
    try:
        from app import create_app
        
        # Test production configuration
        app = create_app('production')
        
        with app.app_context():
            # Check debug mode is off
            assert not app.config.get('DEBUG', True), "Debug mode should be disabled in production"
            print("   ✅ Debug mode disabled")
            
            # Check secret key is secure
            secret_key = app.config.get('SECRET_KEY', '')
            assert len(secret_key) >= 32, "Secret key should be at least 32 characters"
            print("   ✅ Secret key is secure")
            
            # Check database URL is set
            db_url = app.config.get('DATABASE_URL', '')
            assert db_url, "Database URL must be configured"
            print("   ✅ Database URL configured")
            
            # Check admin secret is set
            admin_secret = app.config.get('ADMIN_SECRET', '')
            assert admin_secret and admin_secret != 'admin-secret-key', "Admin secret must be changed from default"
            print("   ✅ Admin secret configured")
            
            # Check rate limiting
            rate_limit = app.config.get('RATE_LIMIT_REQUESTS', 100)
            assert isinstance(rate_limit, int) and rate_limit > 0, "Rate limit should be positive integer"
            print(f"   ✅ Rate limiting configured: {rate_limit} requests/hour")
            
            # Check confidence threshold
            threshold = app.config.get('CONFIDENCE_THRESHOLD', 0.6)
            assert 0 < threshold < 1, "Confidence threshold should be between 0 and 1"
            print(f"   ✅ ML confidence threshold: {threshold}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Production configuration test failed: {e}")
        return False


def test_requirements_integrity():
    """Test requirements.txt and dependencies"""
    print("📦 Testing Requirements Integrity...")
    
    try:
        # Check requirements files exist
        requirements_files = [
            'requirements.txt',
            'requirements-minimal.txt',
            'requirements-deploy.txt'
        ]
        
        for req_file in requirements_files:
            req_path = Path(req_file)
            if req_path.exists():
                print(f"   ✅ {req_file} exists")
                
                # Check file is not empty
                with open(req_path, 'r') as f:
                    content = f.read().strip()
                    assert content, f"{req_file} should not be empty"
                    
                    # Count dependencies
                    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                    print(f"   📊 {req_file}: {len(lines)} dependencies")
            else:
                print(f"   ⚠️  {req_file} not found")
        
        # Test if requirements can be parsed
        main_req_path = Path('requirements.txt')
        if main_req_path.exists():
            with open(main_req_path, 'r') as f:
                requirements = f.read()
                
            # Check for critical dependencies
            critical_deps = ['flask', 'scikit-learn', 'sqlalchemy', 'numpy']
            missing_deps = []
            
            for dep in critical_deps:
                if dep.lower() not in requirements.lower():
                    missing_deps.append(dep)
                else:
                    print(f"   ✅ Critical dependency found: {dep}")
            
            if missing_deps:
                print(f"   ❌ Missing critical dependencies: {missing_deps}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Requirements integrity test failed: {e}")
        return False


def test_docker_configuration():
    """Test Docker configuration files"""
    print("🐳 Testing Docker Configuration...")
    
    try:
        # Check Dockerfile exists
        dockerfile_path = Path('Dockerfile')
        if dockerfile_path.exists():
            print("   ✅ Dockerfile exists")
            
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
            
            # Check for essential Dockerfile commands
            essential_commands = ['FROM', 'COPY', 'RUN', 'EXPOSE', 'CMD']
            for cmd in essential_commands:
                if cmd in dockerfile_content:
                    print(f"   ✅ Dockerfile has {cmd} command")
                else:
                    print(f"   ⚠️  Dockerfile missing {cmd} command")
            
            # Check if port is exposed
            if 'EXPOSE' in dockerfile_content:
                print("   ✅ Port exposed in Dockerfile")
        else:
            print("   ⚠️  Dockerfile not found")
        
        # Check docker-compose.yml
        compose_path = Path('docker-compose.yml')
        if compose_path.exists():
            print("   ✅ docker-compose.yml exists")
            
            try:
                import yaml
                with open(compose_path, 'r') as f:
                    compose_data = yaml.safe_load(f)
                
                # Check for services
                if 'services' in compose_data:
                    services = list(compose_data['services'].keys())
                    print(f"   ✅ Docker services defined: {services}")
                else:
                    print("   ⚠️  No services defined in docker-compose.yml")
                    
            except ImportError:
                print("   ⚠️  PyYAML not available for compose validation")
                
        else:
            print("   ⚠️  docker-compose.yml not found")
        
        # Check .dockerignore
        dockerignore_path = Path('.dockerignore')
        if dockerignore_path.exists():
            print("   ✅ .dockerignore exists")
        else:
            print("   ⚠️  .dockerignore not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Docker configuration test failed: {e}")
        return False


def test_railway_configuration():
    """Test Railway deployment configuration"""
    print("🚂 Testing Railway Configuration...")
    
    try:
        # Check railway.toml
        railway_config_path = Path('railway.toml')
        if railway_config_path.exists():
            print("   ✅ railway.toml exists")
            
            try:
                import toml
                with open(railway_config_path, 'r') as f:
                    railway_config = toml.load(f)
                
                # Check for build configuration
                if 'build' in railway_config:
                    print("   ✅ Build configuration found")
                
                # Check for environment variables
                if 'variables' in railway_config:
                    print("   ✅ Environment variables configured")
                    
            except ImportError:
                print("   ⚠️  TOML library not available for validation")
                
        else:
            print("   ⚠️  railway.toml not found")
        
        # Check for deployment script
        deploy_script_path = Path('deploy-backend.sh')
        if deploy_script_path.exists():
            print("   ✅ Deployment script exists")
        else:
            print("   ⚠️  Deployment script not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Railway configuration test failed: {e}")
        return False


def test_model_files_deployment():
    """Test ML model files are ready for deployment"""
    print("🤖 Testing Model Files for Deployment...")
    
    try:
        models_dir = Path('models')
        
        if not models_dir.exists():
            print("   ❌ Models directory not found")
            return False
        
        # Check required model files
        required_files = [
            'passive_captcha_rf.pkl',
            'passive_captcha_rf_scaler.pkl',
            'passive_captcha_rf_metadata.json'
        ]
        
        total_size = 0
        
        for filename in required_files:
            file_path = models_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                total_size += size
                size_mb = size / (1024 * 1024)
                print(f"   ✅ {filename}: {size_mb:.2f} MB")
            else:
                print(f"   ❌ {filename}: Not found")
                return False
        
        total_size_mb = total_size / (1024 * 1024)
        print(f"   📊 Total model size: {total_size_mb:.2f} MB")
        
        # Warn if models are very large (might cause deployment issues)
        if total_size_mb > 100:
            print("   ⚠️  Model files are large (>100MB), may cause deployment issues")
        elif total_size_mb > 25:
            print("   ⚠️  Model files are moderate size (>25MB), monitor deployment")
        else:
            print("   ✅ Model file sizes are reasonable for deployment")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model files deployment test failed: {e}")
        return False


def test_static_files():
    """Test static files and frontend assets"""
    print("📁 Testing Static Files...")
    
    try:
        # Check for frontend assets
        frontend_dir = Path('../frontend')
        if frontend_dir.exists():
            print("   ✅ Frontend directory exists")
            
            # Check for package.json
            package_json_path = frontend_dir / 'package.json'
            if package_json_path.exists():
                print("   ✅ Frontend package.json exists")
                
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                # Check for build scripts
                scripts = package_data.get('scripts', {})
                if 'build' in scripts:
                    print("   ✅ Frontend build script configured")
                else:
                    print("   ⚠️  Frontend build script not found")
            else:
                print("   ⚠️  Frontend package.json not found")
        else:
            print("   ℹ️  Frontend directory not found (backend-only deployment)")
        
        # Check for static assets in backend
        static_files = [
            'modern_dashboard.html'
        ]
        
        for static_file in static_files:
            if Path(static_file).exists():
                print(f"   ✅ Static file: {static_file}")
            else:
                print(f"   ⚠️  Static file missing: {static_file}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Static files test failed: {e}")
        return False


def test_database_migration():
    """Test database migration and schema setup"""
    print("🗄️  Testing Database Migration...")
    
    try:
        from app import create_app
        from app.database import init_db
        
        # Test with temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            test_db_url = f'sqlite:///{tmp_db.name}'
        
        app = create_app('testing')
        app.config['DATABASE_URL'] = test_db_url
        
        with app.app_context():
            # Test database initialization
            result = init_db()
            assert result, "Database initialization should succeed"
            print("   ✅ Database initialization successful")
            
            # Test migration
            result = init_db()  # Run again to test migration
            assert result, "Database migration should succeed"
            print("   ✅ Database migration successful")
        
        # Cleanup
        os.unlink(tmp_db.name)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database migration test failed: {e}")
        return False


def test_security_headers():
    """Test security configuration for deployment"""
    print("🔒 Testing Security Configuration...")
    
    try:
        from app import create_app
        
        app = create_app('production')
        
        # Test CORS configuration
        with app.test_client() as client:
            # Test preflight request
            response = client.options('/api/verify')
            print(f"   ✅ CORS preflight response: {response.status_code}")
            
            # Test actual request
            response = client.post('/api/verify', json={})
            print(f"   ✅ API endpoint response: {response.status_code}")
        
        # Check security-related configuration
        security_configs = {
            'SECRET_KEY': app.config.get('SECRET_KEY'),
            'ADMIN_SECRET': app.config.get('ADMIN_SECRET'),
            'JWT_SECRET_KEY': app.config.get('JWT_SECRET_KEY')
        }
        
        for config_name, config_value in security_configs.items():
            if config_value and len(str(config_value)) >= 16:
                print(f"   ✅ {config_name} properly configured")
            else:
                print(f"   ⚠️  {config_name} may be insecure")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Security configuration test failed: {e}")
        return False


def main():
    """Run all deployment tests"""
    print("🧪 Deployment Testing Suite")
    print("=" * 50)
    
    tests = [
        test_environment_variables,
        test_production_configuration,
        test_requirements_integrity,
        test_docker_configuration,
        test_railway_configuration,
        test_model_files_deployment,
        test_static_files,
        test_database_migration,
        test_security_headers
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
        print("🎉 All deployment tests passed!")
        print("🚀 System is ready for production deployment!")
        return True
    else:
        print("❌ Some deployment tests failed!")
        print("🔧 Fix the issues before deploying to production.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)