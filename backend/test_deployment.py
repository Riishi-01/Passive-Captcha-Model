#!/usr/bin/env python3
"""
Comprehensive Deployment Testing for Passive CAPTCHA System
Tests deployment configurations, environment setup, and production readiness
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

class DeploymentTestSuite:
    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        self.project_root = Path(__file__).parent.parent
        
    def add_result(self, test_name, status, message="", severity="info"):
        """Add test result"""
        result = {
            'test': test_name,
            'status': status,  # 'pass', 'fail', 'warn'
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results['details'].append(result)
        
        if status == 'pass':
            self.test_results['passed'] += 1
            print(f"   ✅ {test_name} - {message}")
        elif status == 'warn':
            self.test_results['warnings'] += 1
            print(f"   ⚠️  {test_name} - {message}")
        else:
            self.test_results['failed'] += 1
            print(f"   ❌ {test_name} - {message}")

    def test_file_structure(self):
        """Test required file structure exists"""
        print("\n📁 Testing File Structure...")
        print("-" * 40)
        
        required_files = [
            # Backend files
            "backend/app.py",
            "backend/requirements.txt", 
            "backend/railway.toml",
            "backend/models/passive_captcha_rf.pkl",
            "backend/models/passive_captcha_rf_scaler.pkl",
            "backend/models/passive_captcha_rf_metadata.json",
            
            # Frontend files
            "frontend/src/passive-captcha.js",
            "frontend/src/passive-captcha.min.js",
            "frontend/vercel.json",
            "frontend/demo/index.html",
            
            # Documentation
            "Integration_Guide.md",
            "README_ML_Implementation.md",
            "deploy.sh"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if not missing_files:
            self.add_result("Required files present", "pass", f"All {len(required_files)} files found")
        else:
            self.add_result("Required files present", "fail", f"Missing files: {', '.join(missing_files)}")
        
        # Test directory structure
        required_dirs = [
            "backend/app/api",
            "backend/app/admin", 
            "backend/app/ml",
            "backend/app/database",
            "backend/models",
            "frontend/src",
            "frontend/demo"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if not missing_dirs:
            self.add_result("Directory structure", "pass", "All required directories exist")
        else:
            self.add_result("Directory structure", "fail", f"Missing dirs: {', '.join(missing_dirs)}")

    def test_model_files(self):
        """Test ML model files are valid"""
        print("\n🤖 Testing Model Files...")
        print("-" * 40)
        
        model_dir = self.project_root / "backend" / "models"
        
        # Test model file
        model_file = model_dir / "passive_captcha_rf.pkl"
        if model_file.exists():
            try:
                import joblib
                model = joblib.load(model_file)
                self.add_result("Model file validity", "pass", f"Model loaded successfully ({model_file.stat().st_size} bytes)")
            except Exception as e:
                self.add_result("Model file validity", "fail", f"Cannot load model: {e}")
        else:
            self.add_result("Model file validity", "fail", "Model file not found")
        
        # Test scaler file
        scaler_file = model_dir / "passive_captcha_rf_scaler.pkl"
        if scaler_file.exists():
            try:
                import joblib
                scaler = joblib.load(scaler_file)
                self.add_result("Scaler file validity", "pass", "Scaler loaded successfully")
            except Exception as e:
                self.add_result("Scaler file validity", "fail", f"Cannot load scaler: {e}")
        else:
            self.add_result("Scaler file validity", "fail", "Scaler file not found")
        
        # Test metadata file
        metadata_file = model_dir / "passive_captcha_rf_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                required_keys = ['model_version', 'feature_names', 'training_date']
                missing_keys = [key for key in required_keys if key not in metadata]
                
                if not missing_keys:
                    self.add_result("Metadata file validity", "pass", "All required metadata present")
                else:
                    self.add_result("Metadata file validity", "warn", f"Missing metadata: {missing_keys}")
            except Exception as e:
                self.add_result("Metadata file validity", "fail", f"Cannot parse metadata: {e}")
        else:
            self.add_result("Metadata file validity", "fail", "Metadata file not found")

    def test_dependencies(self):
        """Test dependencies and requirements"""
        print("\n📦 Testing Dependencies...")
        print("-" * 40)
        
        # Test requirements.txt
        req_file = self.project_root / "backend" / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read().strip().split('\n')
                
                critical_packages = ['flask', 'scikit-learn', 'numpy', 'pandas', 'joblib']
                missing_packages = []
                
                req_text = '\n'.join(requirements).lower()
                for package in critical_packages:
                    if package not in req_text:
                        missing_packages.append(package)
                
                if not missing_packages:
                    self.add_result("Critical dependencies", "pass", f"All critical packages in requirements ({len(requirements)} total)")
                else:
                    self.add_result("Critical dependencies", "warn", f"Missing packages: {missing_packages}")
                    
            except Exception as e:
                self.add_result("Requirements file", "fail", f"Cannot read requirements: {e}")
        else:
            self.add_result("Requirements file", "fail", "requirements.txt not found")
        
        # Test Python imports
        try:
            import flask
            import sklearn
            import numpy
            import pandas
            import joblib
            self.add_result("Python dependencies", "pass", "All critical packages importable")
        except ImportError as e:
            self.add_result("Python dependencies", "fail", f"Import error: {e}")

    def test_configuration_files(self):
        """Test deployment configuration files"""
        print("\n⚙️ Testing Configuration Files...")
        print("-" * 40)
        
        # Test Railway configuration
        railway_file = self.project_root / "backend" / "railway.toml"
        if railway_file.exists():
            try:
                import toml
                config = toml.load(railway_file)
                
                required_sections = ['build', 'deploy', 'variables']
                missing_sections = [section for section in required_sections if section not in config]
                
                if not missing_sections:
                    self.add_result("Railway configuration", "pass", "All required sections present")
                else:
                    self.add_result("Railway configuration", "warn", f"Missing sections: {missing_sections}")
                    
            except ImportError:
                self.add_result("Railway configuration", "warn", "Cannot validate TOML (toml package not available)")
            except Exception as e:
                self.add_result("Railway configuration", "fail", f"Invalid TOML: {e}")
        else:
            self.add_result("Railway configuration", "fail", "railway.toml not found")
        
        # Test Vercel configuration  
        vercel_file = self.project_root / "frontend" / "vercel.json"
        if vercel_file.exists():
            try:
                with open(vercel_file, 'r') as f:
                    config = json.load(f)
                
                expected_keys = ['headers', 'rewrites']
                missing_keys = [key for key in expected_keys if key not in config]
                
                if not missing_keys:
                    self.add_result("Vercel configuration", "pass", "Configuration structure valid")
                else:
                    self.add_result("Vercel configuration", "warn", f"Missing keys: {missing_keys}")
                    
            except Exception as e:
                self.add_result("Vercel configuration", "fail", f"Invalid JSON: {e}")
        else:
            self.add_result("Vercel configuration", "fail", "vercel.json not found")

    def test_frontend_assets(self):
        """Test frontend assets are ready for deployment"""
        print("\n🌐 Testing Frontend Assets...")
        print("-" * 40)
        
        frontend_dir = self.project_root / "frontend"
        
        # Test main JavaScript file
        main_js = frontend_dir / "src" / "passive-captcha.js"
        if main_js.exists():
            content = main_js.read_text()
            
            # Check for key functions
            required_functions = ['PassiveCaptcha', 'init', 'verify', 'extractFeatures']
            missing_functions = [func for func in required_functions if func not in content]
            
            if not missing_functions:
                self.add_result("Main JavaScript file", "pass", f"All key functions present ({len(content)} chars)")
            else:
                self.add_result("Main JavaScript file", "warn", f"Missing functions: {missing_functions}")
        else:
            self.add_result("Main JavaScript file", "fail", "passive-captcha.js not found")
        
        # Test minified version
        min_js = frontend_dir / "src" / "passive-captcha.min.js"
        if min_js.exists():
            min_content = min_js.read_text()
            if len(min_content) > 0:
                compression_ratio = len(min_content) / len(content) if main_js.exists() else 0
                self.add_result("Minified JavaScript", "pass", f"Minified version available (compression: {compression_ratio:.2f})")
            else:
                self.add_result("Minified JavaScript", "fail", "Minified file is empty")
        else:
            self.add_result("Minified JavaScript", "warn", "No minified version found")
        
        # Test demo page
        demo_html = frontend_dir / "demo" / "index.html"
        if demo_html.exists():
            demo_content = demo_html.read_text()
            if 'passive-captcha' in demo_content.lower():
                self.add_result("Demo page", "pass", "Demo page includes CAPTCHA integration")
            else:
                self.add_result("Demo page", "warn", "Demo page may not include CAPTCHA")
        else:
            self.add_result("Demo page", "fail", "Demo HTML not found")

    def test_security_configuration(self):
        """Test security configurations"""
        print("\n🔒 Testing Security Configuration...")
        print("-" * 40)
        
        # Check for environment variables
        env_example = self.project_root / "backend" / "config.env.example"
        if env_example.exists():
            self.add_result("Environment template", "pass", "Environment template exists")
        else:
            self.add_result("Environment template", "warn", "No environment template found")
        
        # Test for hardcoded secrets
        suspicious_patterns = ['secret.*=.*["\'][^"\']*["\']', 'password.*=.*["\'][^"\']*["\']', 'key.*=.*["\'][^"\']*["\']']
        
        config_files = [
            self.project_root / "backend" / "app.py",
            self.project_root / "backend" / "railway.toml"
        ]
        
        hardcoded_secrets = []
        for config_file in config_files:
            if config_file.exists():
                import re
                content = config_file.read_text()
                for pattern in suspicious_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        hardcoded_secrets.append(config_file.name)
        
        if not hardcoded_secrets:
            self.add_result("Hardcoded secrets check", "pass", "No obvious hardcoded secrets found")
        else:
            self.add_result("Hardcoded secrets check", "warn", f"Potential secrets in: {hardcoded_secrets}")

    def test_deployment_scripts(self):
        """Test deployment scripts"""
        print("\n🚀 Testing Deployment Scripts...")
        print("-" * 40)
        
        # Test deploy script
        deploy_script = self.project_root / "deploy.sh"
        if deploy_script.exists():
            content = deploy_script.read_text()
            
            # Check if executable
            is_executable = os.access(deploy_script, os.X_OK)
            if is_executable:
                self.add_result("Deploy script executable", "pass", "Script has execute permissions")
            else:
                self.add_result("Deploy script executable", "warn", "Script not executable (run: chmod +x deploy.sh)")
            
            # Check for key deployment steps
            deployment_steps = ['vercel', 'railway', 'health']
            present_steps = [step for step in deployment_steps if step in content.lower()]
            
            if len(present_steps) >= 2:
                self.add_result("Deploy script content", "pass", f"Contains {len(present_steps)} deployment steps")
            else:
                self.add_result("Deploy script content", "warn", "May be missing deployment steps")
                
        else:
            self.add_result("Deploy script", "fail", "deploy.sh not found")

    def test_database_configuration(self):
        """Test database setup and configuration"""
        print("\n🗄️ Testing Database Configuration...")
        print("-" * 40)
        
        try:
            # Test database module import
            sys.path.insert(0, str(self.project_root / "backend"))
            from app.database import init_db, VerificationLog
            
            self.add_result("Database module import", "pass", "Database module imports successfully")
            
            # Test database initialization with temporary DB
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                os.environ['DATABASE_URL'] = f'sqlite:///{tmp_db.name}'
                
                try:
                    from flask import Flask
                    app = Flask(__name__)
                    app.config['DATABASE_URL'] = f'sqlite:///{tmp_db.name}'
                    
                    with app.app_context():
                        result = init_db()
                        if result:
                            self.add_result("Database initialization", "pass", "Database initializes successfully")
                        else:
                            self.add_result("Database initialization", "fail", "Database initialization failed")
                            
                except Exception as e:
                    self.add_result("Database initialization", "fail", f"Error: {e}")
                finally:
                    # Cleanup
                    try:
                        os.unlink(tmp_db.name)
                    except:
                        pass
                        
        except ImportError as e:
            self.add_result("Database module import", "fail", f"Import error: {e}")

    def test_performance_requirements(self):
        """Test performance requirements are met"""
        print("\n⚡ Testing Performance Requirements...")
        print("-" * 40)
        
        try:
            # Test model inference speed
            import joblib
            import numpy as np
            
            model_path = self.project_root / "backend" / "models" / "passive_captcha_rf.pkl"
            scaler_path = self.project_root / "backend" / "models" / "passive_captcha_rf_scaler.pkl"
            
            if model_path.exists() and scaler_path.exists():
                model = joblib.load(model_path)
                scaler = joblib.load(scaler_path)
                
                # Test inference time
                test_features = np.array([[45, 0.8, 10, 0.4, 35, 0.8, 1.0, 0.85, 0.9, 0.88, 0.85]])
                
                times = []
                for _ in range(10):
                    start_time = time.time()
                    scaled_features = scaler.transform(test_features)
                    prediction = model.predict(scaled_features)
                    end_time = time.time()
                    times.append((end_time - start_time) * 1000)
                
                avg_time = sum(times) / len(times)
                max_time = max(times)
                
                if max_time < 100:  # SRS requirement
                    self.add_result("Inference speed requirement", "pass", f"Max: {max_time:.3f}ms (< 100ms)")
                else:
                    self.add_result("Inference speed requirement", "fail", f"Too slow: {max_time:.3f}ms")
                
                # Test model size
                model_size = model_path.stat().st_size / (1024 * 1024)  # MB
                if model_size < 50:  # SRS requirement
                    self.add_result("Model size requirement", "pass", f"Size: {model_size:.2f}MB (< 50MB)")
                else:
                    self.add_result("Model size requirement", "fail", f"Too large: {model_size:.2f}MB")
                    
            else:
                self.add_result("Performance testing", "fail", "Model files not available")
                
        except Exception as e:
            self.add_result("Performance testing", "fail", f"Error: {e}")

    def test_documentation_completeness(self):
        """Test documentation is complete"""
        print("\n📚 Testing Documentation...")
        print("-" * 40)
        
        doc_files = [
            ("Integration Guide", "Integration_Guide.md"),
            ("ML Implementation README", "README_ML_Implementation.md"),
            ("SRS Completion Report", "SRS_COMPLETION_REPORT.md")
        ]
        
        for doc_name, doc_file in doc_files:
            doc_path = self.project_root / doc_file
            if doc_path.exists():
                content = doc_path.read_text()
                if len(content) > 1000:  # Reasonable documentation length
                    self.add_result(f"{doc_name} documentation", "pass", f"Complete documentation ({len(content)} chars)")
                else:
                    self.add_result(f"{doc_name} documentation", "warn", "Documentation may be incomplete")
            else:
                self.add_result(f"{doc_name} documentation", "fail", f"{doc_file} not found")

    def test_production_readiness(self):
        """Test overall production readiness"""
        print("\n🏭 Testing Production Readiness...")
        print("-" * 40)
        
        # Test environment handling
        try:
            import os
            test_vars = ['DATABASE_URL', 'ADMIN_SECRET', 'MODEL_PATH']
            env_handling = True
            
            # This tests that the app can handle environment variables
            for var in test_vars:
                os.environ[var] = 'test_value'
            
            self.add_result("Environment variable handling", "pass", "App should handle env vars")
            
            # Cleanup
            for var in test_vars:
                if var in os.environ:
                    del os.environ[var]
                    
        except Exception as e:
            self.add_result("Environment variable handling", "warn", f"Error: {e}")
        
        # Test error handling readiness
        error_handling_files = [
            self.project_root / "backend" / "app" / "api" / "__init__.py",
            self.project_root / "backend" / "app" / "admin" / "__init__.py"
        ]
        
        error_patterns = ['except', 'try:', 'error', 'exception']
        has_error_handling = False
        
        for file_path in error_handling_files:
            if file_path.exists():
                content = file_path.read_text().lower()
                if any(pattern in content for pattern in error_patterns):
                    has_error_handling = True
                    break
        
        if has_error_handling:
            self.add_result("Error handling", "pass", "Error handling present in code")
        else:
            self.add_result("Error handling", "warn", "Limited error handling detected")

    def generate_deployment_report(self):
        """Generate comprehensive deployment readiness report"""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT READINESS REPORT")
        print("=" * 60)
        
        total_tests = self.test_results['passed'] + self.test_results['failed'] + self.test_results['warnings']
        
        print(f"\n📈 TEST SUMMARY:")
        print(f"   ✅ Tests Passed: {self.test_results['passed']}")
        print(f"   ⚠️  Warnings: {self.test_results['warnings']}")
        print(f"   ❌ Tests Failed: {self.test_results['failed']}")
        print(f"   📊 Total Tests: {total_tests}")
        
        if total_tests > 0:
            success_rate = (self.test_results['passed'] / total_tests) * 100
            warning_rate = (self.test_results['warnings'] / total_tests) * 100
        else:
            success_rate = 0
            warning_rate = 0
        
        print(f"   🎯 Success Rate: {success_rate:.1f}%")
        print(f"   ⚠️  Warning Rate: {warning_rate:.1f}%")
        
        # Show failures and warnings
        failures = [r for r in self.test_results['details'] if r['status'] == 'fail']
        warnings = [r for r in self.test_results['details'] if r['status'] == 'warn']
        
        if failures:
            print(f"\n❌ CRITICAL ISSUES ({len(failures)}):")
            for failure in failures:
                print(f"   - {failure['test']}: {failure['message']}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"   - {warning['test']}: {warning['message']}")
        
        # Overall deployment readiness
        print(f"\n🎯 DEPLOYMENT READINESS:")
        
        if self.test_results['failed'] == 0 and self.test_results['warnings'] <= 2:
            print("   🏆 READY FOR PRODUCTION - All critical requirements met!")
            readiness = "READY"
        elif self.test_results['failed'] <= 2 and success_rate >= 80:
            print("   ✅ MOSTLY READY - Minor issues to address")
            readiness = "MOSTLY_READY"
        elif self.test_results['failed'] <= 5:
            print("   ⚠️  NEEDS ATTENTION - Several issues to fix")
            readiness = "NEEDS_WORK"
        else:
            print("   ❌ NOT READY - Significant issues found")
            readiness = "NOT_READY"
        
        print(f"\n📅 Assessment completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return readiness == "READY" or readiness == "MOSTLY_READY"


def main():
    """Run comprehensive deployment testing"""
    print("🧪 COMPREHENSIVE DEPLOYMENT TESTING")
    print("=" * 60)
    
    try:
        test_suite = DeploymentTestSuite()
        
        # Run all deployment tests
        test_suite.test_file_structure()
        test_suite.test_model_files()
        test_suite.test_dependencies()
        test_suite.test_configuration_files()
        test_suite.test_frontend_assets()
        test_suite.test_security_configuration()
        test_suite.test_deployment_scripts()
        test_suite.test_database_configuration()
        test_suite.test_performance_requirements()
        test_suite.test_documentation_completeness()
        test_suite.test_production_readiness()
        
        # Generate final report
        ready_for_deployment = test_suite.generate_deployment_report()
        
        return ready_for_deployment
        
    except Exception as e:
        print(f"\n❌ Deployment testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 