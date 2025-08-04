#!/usr/bin/env python3
"""
Local Codebase Validator
Comprehensive testing of codebase without requiring deployed server
"""

import os
import sys
import ast
import json
import importlib.util
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, WARNING, SKIP
    message: str
    details: Optional[Dict] = None
    suggestions: List[str] = None

class LocalCodebaseValidator:
    """Validates codebase structure, imports, and basic functionality locally"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.test_results: List[TestResult] = []
        
    def test_project_structure(self) -> TestResult:
        """Test project directory structure"""
        try:
            required_dirs = [
                "backend/app",
                "backend/app/services",
                "backend/app/admin",
                "backend/app/api",
                "frontend/src",
                "frontend/src/app",
                "testing"
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not (self.project_root / dir_path).exists():
                    missing_dirs.append(dir_path)
            
            if missing_dirs:
                return TestResult(
                    test_name="project_structure",
                    status="FAIL",
                    message=f"Missing directories: {', '.join(missing_dirs)}",
                    suggestions=[f"Create missing directory: {d}" for d in missing_dirs]
                )
            
            return TestResult(
                test_name="project_structure",
                status="PASS",
                message="All required directories exist"
            )
            
        except Exception as e:
            return TestResult(
                test_name="project_structure",
                status="FAIL",
                message=f"Error checking structure: {e}"
            )
    
    def test_python_syntax(self) -> TestResult:
        """Test Python files for syntax errors"""
        try:
            python_files = []
            syntax_errors = []
            
            # Find all Python files
            for pattern in ["**/*.py"]:
                python_files.extend(self.backend_dir.glob(pattern))
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        source = f.read()
                    
                    # Parse syntax
                    ast.parse(source)
                    
                except SyntaxError as e:
                    syntax_errors.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "line": e.lineno,
                        "error": str(e)
                    })
                except Exception as e:
                    syntax_errors.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "error": f"Parse error: {e}"
                    })
            
            if syntax_errors:
                return TestResult(
                    test_name="python_syntax",
                    status="FAIL",
                    message=f"Syntax errors in {len(syntax_errors)} files",
                    details={"errors": syntax_errors},
                    suggestions=["Fix syntax errors in flagged files"]
                )
            
            return TestResult(
                test_name="python_syntax",
                status="PASS",
                message=f"All {len(python_files)} Python files have valid syntax"
            )
            
        except Exception as e:
            return TestResult(
                test_name="python_syntax",
                status="FAIL",
                message=f"Syntax check failed: {e}"
            )
    
    def test_import_resolution(self) -> TestResult:
        """Test if critical imports can be resolved"""
        try:
            # Add backend to path for testing
            backend_path = str(self.backend_dir)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            critical_modules = [
                "app.services.auth_service",
                "app.services.robust_auth_service", 
                "app.services.website_service",
                "app.script_token_manager",
                "app.script_generator",
                "app.database",
                "app.auth_integration"
            ]
            
            import_results = []
            failed_imports = []
            
            for module_name in critical_modules:
                try:
                    # Try to import the module
                    spec = importlib.util.find_spec(module_name)
                    if spec is None:
                        failed_imports.append({
                            "module": module_name,
                            "error": "Module not found"
                        })
                    else:
                        import_results.append({
                            "module": module_name,
                            "status": "OK",
                            "file": spec.origin
                        })
                except Exception as e:
                    failed_imports.append({
                        "module": module_name,
                        "error": str(e)
                    })
            
            if failed_imports:
                return TestResult(
                    test_name="import_resolution",
                    status="FAIL",
                    message=f"Failed to resolve {len(failed_imports)} imports",
                    details={
                        "failed": failed_imports,
                        "successful": import_results
                    },
                    suggestions=["Check module paths and dependencies"]
                )
            
            return TestResult(
                test_name="import_resolution",
                status="PASS",
                message=f"All {len(critical_modules)} critical modules can be imported",
                details={"modules": import_results}
            )
            
        except Exception as e:
            return TestResult(
                test_name="import_resolution",
                status="FAIL",
                message=f"Import test failed: {e}"
            )
    
    def test_database_models(self) -> TestResult:
        """Test database model definitions"""
        try:
            # Add backend to path
            backend_path = str(self.backend_dir)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from app.database import Website, VerificationLog, Base
            
            model_tests = []
            
            # Test Website model
            try:
                # Check if we can create a model instance (without saving)
                website = Website(
                    website_id="test_id",
                    website_name="Test",
                    website_url="https://test.com",
                    admin_email="test@test.com",
                    api_key="test_key",
                    secret_key="test_secret"
                )
                
                # Test to_dict method
                website_dict = website.to_dict()
                assert isinstance(website_dict, dict)
                assert 'website_id' in website_dict
                
                model_tests.append({
                    "model": "Website",
                    "status": "OK",
                    "tests": ["instantiation", "to_dict"]
                })
                
            except Exception as e:
                model_tests.append({
                    "model": "Website", 
                    "status": "FAIL",
                    "error": str(e)
                })
            
            # Test VerificationLog model
            try:
                log = VerificationLog(
                    website_id="test_id",
                    session_id="test_session",
                    is_human=True,
                    confidence=0.8
                )
                
                log_dict = log.to_dict()
                assert isinstance(log_dict, dict)
                assert 'session_id' in log_dict
                
                model_tests.append({
                    "model": "VerificationLog",
                    "status": "OK", 
                    "tests": ["instantiation", "to_dict"]
                })
                
            except Exception as e:
                model_tests.append({
                    "model": "VerificationLog",
                    "status": "FAIL",
                    "error": str(e)
                })
            
            # Check for failed models
            failed_models = [m for m in model_tests if m["status"] == "FAIL"]
            
            if failed_models:
                return TestResult(
                    test_name="database_models",
                    status="FAIL",
                    message=f"Failed model tests: {len(failed_models)}",
                    details={"results": model_tests},
                    suggestions=["Fix model definition errors"]
                )
            
            return TestResult(
                test_name="database_models",
                status="PASS",
                message="All database models tested successfully",
                details={"results": model_tests}
            )
            
        except Exception as e:
            return TestResult(
                test_name="database_models",
                status="FAIL",
                message=f"Database model test failed: {e}"
            )
    
    def test_authentication_service(self) -> TestResult:
        """Test authentication service functionality"""
        try:
            # Add backend to path
            backend_path = str(self.backend_dir)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from app.services.robust_auth_service import RobustAuthService, UserRole
            
            # Test service instantiation
            auth_service = RobustAuthService(redis_client=None)  # Test without Redis
            
            tests_passed = []
            tests_failed = []
            
            # Test password hashing
            try:
                password = "test_password_123"
                hashed = auth_service._hash_password(password)
                verified = auth_service._verify_password(password, hashed)
                
                assert verified == True
                tests_passed.append("password_hashing")
                
            except Exception as e:
                tests_failed.append(f"password_hashing: {e}")
            
            # Test user creation (without storage)
            try:
                user = auth_service.create_user(
                    email="test@example.com",
                    password="test_password_123",
                    name="Test User",
                    role=UserRole.ADMIN
                )
                
                assert user.email == "test@example.com"
                assert user.role == UserRole.ADMIN
                tests_passed.append("user_creation")
                
            except Exception as e:
                tests_failed.append(f"user_creation: {e}")
            
            # Test JWT token generation
            try:
                from app.services.robust_auth_service import AuthSession
                from datetime import datetime
                
                session = AuthSession(
                    session_id="test_session",
                    user_id="test_user",
                    email="test@example.com",
                    role=UserRole.ADMIN,
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    ip_address="127.0.0.1",
                    user_agent="test"
                )
                
                token = auth_service.generate_jwt_token(session)
                assert isinstance(token, str) and len(token) > 10
                tests_passed.append("jwt_generation")
                
            except Exception as e:
                tests_failed.append(f"jwt_generation: {e}")
            
            if tests_failed:
                return TestResult(
                    test_name="authentication_service",
                    status="FAIL",
                    message=f"Failed tests: {len(tests_failed)}",
                    details={
                        "passed": tests_passed,
                        "failed": tests_failed
                    },
                    suggestions=["Fix authentication service errors"]
                )
            
            return TestResult(
                test_name="authentication_service",
                status="PASS",
                message=f"All {len(tests_passed)} authentication tests passed",
                details={"passed": tests_passed}
            )
            
        except Exception as e:
            return TestResult(
                test_name="authentication_service",
                status="FAIL",
                message=f"Authentication service test failed: {e}"
            )
    
    def test_script_token_manager(self) -> TestResult:
        """Test script token manager functionality"""
        try:
            # Add backend to path
            backend_path = str(self.backend_dir)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from app.script_token_manager import ScriptTokenManager, ScriptToken, TokenStatus
            
            # Test without Redis for basic functionality
            token_manager = ScriptTokenManager(redis_client=None)
            
            tests_passed = []
            tests_failed = []
            
            # Test token generation
            try:
                token = token_manager.generate_script_token(
                    website_id="test_website",
                    script_version="v1.0",
                    environment="testing"
                )
                
                assert isinstance(token, ScriptToken)
                assert token.website_id == "test_website"
                assert token.status == TokenStatus.PENDING
                tests_passed.append("token_generation")
                
            except Exception as e:
                tests_failed.append(f"token_generation: {e}")
            
            # Test token serialization
            try:
                token_dict = token.to_dict()
                reconstructed = ScriptToken.from_dict(token_dict)
                
                assert reconstructed.website_id == token.website_id
                assert reconstructed.script_token == token.script_token
                tests_passed.append("token_serialization")
                
            except Exception as e:
                tests_failed.append(f"token_serialization: {e}")
            
            # Test configuration methods
            try:
                default_config = token_manager._get_default_config("production", "v1.0")
                rate_limit_config = token_manager._get_default_rate_limit_config("production")
                security_config = token_manager._get_default_security_config("production")
                
                assert isinstance(default_config, dict)
                assert isinstance(rate_limit_config, dict)
                assert isinstance(security_config, dict)
                tests_passed.append("configuration_methods")
                
            except Exception as e:
                tests_failed.append(f"configuration_methods: {e}")
            
            if tests_failed:
                return TestResult(
                    test_name="script_token_manager",
                    status="FAIL",
                    message=f"Failed tests: {len(tests_failed)}",
                    details={
                        "passed": tests_passed,
                        "failed": tests_failed
                    },
                    suggestions=["Fix script token manager errors"]
                )
            
            return TestResult(
                test_name="script_token_manager",
                status="PASS",
                message=f"All {len(tests_passed)} token manager tests passed",
                details={"passed": tests_passed}
            )
            
        except Exception as e:
            return TestResult(
                test_name="script_token_manager",
                status="FAIL",
                message=f"Script token manager test failed: {e}"
            )
    
    def test_flask_app_creation(self) -> TestResult:
        """Test Flask app creation and configuration"""
        try:
            # Add backend to path
            backend_path = str(self.backend_dir)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            # Import main app factory
            from main import create_app
            
            # Test app creation
            app = create_app(config_name='testing')
            
            tests_passed = []
            tests_failed = []
            
            # Test app configuration
            try:
                assert app is not None
                assert hasattr(app, 'config')
                tests_passed.append("app_creation")
            except Exception as e:
                tests_failed.append(f"app_creation: {e}")
            
            # Test blueprints registration
            try:
                blueprint_names = [bp.name for bp in app.blueprints.values()]
                
                expected_blueprints = ['admin_bp', 'api_bp', 'website_bp']
                registered_blueprints = [name for name in expected_blueprints if name in blueprint_names]
                
                if len(registered_blueprints) > 0:
                    tests_passed.append(f"blueprints_registered: {registered_blueprints}")
                else:
                    tests_failed.append("blueprints_registration: No expected blueprints found")
                    
            except Exception as e:
                tests_failed.append(f"blueprints_registration: {e}")
            
            # Test URL rules
            try:
                url_rules = [str(rule) for rule in app.url_map.iter_rules()]
                
                # Check for some critical endpoints
                critical_endpoints = ['/api/status', '/api/admin/login']
                found_endpoints = [ep for ep in critical_endpoints if any(ep in rule for rule in url_rules)]
                
                if len(found_endpoints) > 0:
                    tests_passed.append(f"url_rules: {len(url_rules)} rules, {len(found_endpoints)} critical endpoints")
                else:
                    tests_failed.append(f"url_rules: Critical endpoints not found")
                    
            except Exception as e:
                tests_failed.append(f"url_rules: {e}")
            
            if tests_failed:
                return TestResult(
                    test_name="flask_app_creation",
                    status="WARNING" if tests_passed else "FAIL",
                    message=f"App creation issues: {len(tests_failed)} failed, {len(tests_passed)} passed",
                    details={
                        "passed": tests_passed,
                        "failed": tests_failed
                    },
                    suggestions=["Check Flask app configuration and blueprint registration"]
                )
            
            return TestResult(
                test_name="flask_app_creation",
                status="PASS",
                message=f"Flask app created successfully with {len(tests_passed)} components working",
                details={"passed": tests_passed}
            )
            
        except Exception as e:
            return TestResult(
                test_name="flask_app_creation",
                status="FAIL",
                message=f"Flask app creation failed: {e}",
                details={"traceback": traceback.format_exc()}
            )
    
    def test_frontend_structure(self) -> TestResult:
        """Test frontend structure and configuration"""
        try:
            frontend_files = [
                "package.json",
                "src/main.ts",
                "src/App.vue",
                "src/router/index.ts",
                "src/services/api.ts"
            ]
            
            missing_files = []
            existing_files = []
            
            for file_path in frontend_files:
                full_path = self.frontend_dir / file_path
                if full_path.exists():
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)
            
            # Check package.json for dependencies
            package_json_path = self.frontend_dir / "package.json"
            dependencies_ok = False
            
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    
                    critical_deps = ['vue', 'vue-router', 'axios']
                    found_deps = [dep for dep in critical_deps if dep in deps or dep in dev_deps]
                    
                    if len(found_deps) >= 2:
                        dependencies_ok = True
                        
                except Exception:
                    pass
            
            if missing_files:
                return TestResult(
                    test_name="frontend_structure",
                    status="WARNING",
                    message=f"Missing {len(missing_files)} frontend files",
                    details={
                        "missing": missing_files,
                        "existing": existing_files,
                        "dependencies_ok": dependencies_ok
                    },
                    suggestions=[f"Create missing file: {f}" for f in missing_files]
                )
            
            return TestResult(
                test_name="frontend_structure",
                status="PASS",
                message=f"Frontend structure complete with {len(existing_files)} files",
                details={
                    "existing": existing_files,
                    "dependencies_ok": dependencies_ok
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="frontend_structure",
                status="FAIL",
                message=f"Frontend structure test failed: {e}"
            )
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests"""
        logger.info("🚀 Running comprehensive local codebase validation...")
        
        test_methods = [
            self.test_project_structure,
            self.test_python_syntax,
            self.test_import_resolution,
            self.test_database_models,
            self.test_authentication_service,
            self.test_script_token_manager,
            self.test_flask_app_creation,
            self.test_frontend_structure
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = test_method()
                results.append(result)
                
                status_icon = {
                    "PASS": "✅",
                    "FAIL": "❌", 
                    "WARNING": "⚠️",
                    "SKIP": "⏭️"
                }.get(result.status, "❓")
                
                logger.info(f"{status_icon} {result.test_name}: {result.message}")
                
            except Exception as e:
                result = TestResult(
                    test_name=test_method.__name__,
                    status="FAIL",
                    message=f"Test execution error: {e}"
                )
                results.append(result)
                logger.error(f"❌ {test_method.__name__}: {e}")
        
        # Calculate summary
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "FAIL")
        warnings = sum(1 for r in results if r.status == "WARNING")
        
        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "success_rate": passed / total if total > 0 else 0,
            "results": [
                {
                    "test": r.test_name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "suggestions": r.suggestions
                }
                for r in results
            ]
        }
        
        return summary

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local Codebase Validator")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--output", default="local_validation_report.json", help="Output file")
    args = parser.parse_args()
    
    # Create validator
    validator = LocalCodebaseValidator(project_root=args.project_root)
    
    # Run validation
    summary = validator.run_comprehensive_validation()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"LOCAL CODEBASE VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Warnings: {summary['warnings']} ⚠️")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    
    # Show failed tests
    failed_tests = [r for r in summary['results'] if r['status'] == 'FAIL']
    if failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test['test']}: {test['message']}")
            if test.get('suggestions'):
                for suggestion in test['suggestions']:
                    print(f"    💡 {suggestion}")
    
    # Show warnings
    warning_tests = [r for r in summary['results'] if r['status'] == 'WARNING']
    if warning_tests:
        print(f"\n⚠️  WARNINGS:")
        for test in warning_tests:
            print(f"  - {test['test']}: {test['message']}")
    
    print(f"\nDetailed report saved to: {args.output}")
    
    # Exit with appropriate code
    exit_code = 0 if summary['failed'] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()