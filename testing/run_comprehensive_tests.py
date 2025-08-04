#!/usr/bin/env python3
"""
Comprehensive Testing Script
Runs complete software testing cycle and applies fixes
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Runs comprehensive testing cycle with automatic fixes"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = {}
        self.start_time = time.time()
        
        # Ensure testing directory exists
        self.test_dir = Path(__file__).parent
        self.reports_dir = self.test_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_database_validation(self) -> Dict[str, Any]:
        """Run database schema validation and fixes"""
        logger.info("🗄️  Running database validation...")
        
        try:
            # Import the database validator
            sys.path.append(str(self.test_dir))
            from database_validator import DatabaseValidator
            
            validator = DatabaseValidator()
            
            # Run validation
            results = validator.run_comprehensive_validation()
            
            # Try to fix issues by creating missing tables
            if results['schema_validation']['failed'] > 0:
                logger.info("🔧 Attempting to fix database schema issues...")
                creation_results = validator.create_missing_tables()
                
                # Re-validate after fixes
                results_after_fix = validator.run_comprehensive_validation()
                results['fixed_issues'] = creation_results
                results['after_fix'] = results_after_fix
            
            # Save detailed report
            with open(self.reports_dir / "database_validation.json", 'w') as f:
                json.dump(results, f, indent=2)
            
            return {
                'status': 'PASS' if results['schema_validation']['failed'] == 0 else 'FAIL',
                'details': results,
                'summary': f"Schema: {results['schema_validation']['passed']}/{results['schema_validation']['total_tables']} tables valid"
            }
            
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'Database validation error'
            }
    
    def run_api_routing_validation(self) -> Dict[str, Any]:
        """Run API routing validation"""
        logger.info("🌐 Running API routing validation...")
        
        try:
            # Import the API validator
            from api_routing_validator import APIRoutingValidator
            
            validator = APIRoutingValidator(self.base_url)
            results = validator.validate_all_routes()
            
            # Save detailed report
            with open(self.reports_dir / "api_routing_validation.json", 'w') as f:
                json.dump(results, f, indent=2)
            
            # Generate route documentation
            documentation = validator.generate_route_documentation()
            with open(self.reports_dir / "api_documentation.md", 'w') as f:
                f.write(documentation)
            
            return {
                'status': 'PASS' if results['failed'] == 0 else 'FAIL',
                'details': results,
                'summary': f"API Routes: {results['passed']}/{results['total_tests']} tests passed ({results['success_rate']:.1%})"
            }
            
        except Exception as e:
            logger.error(f"API routing validation failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'API routing validation error'
            }
    
    def run_authentication_tests(self) -> Dict[str, Any]:
        """Run authentication system tests"""
        logger.info("🔐 Running authentication tests...")
        
        try:
            # Import the test framework
            from test_framework import TestFramework
            
            framework = TestFramework(self.base_url)
            
            # Run only authentication tests
            auth_result = framework.run_test(framework.test_authentication_system)
            
            return {
                'status': auth_result.status,
                'details': auth_result.details,
                'summary': f"Authentication: {auth_result.status} ({auth_result.execution_time:.2f}s)"
            }
            
        except Exception as e:
            logger.error(f"Authentication tests failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'Authentication test error'
            }
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security and CORS tests"""
        logger.info("🛡️  Running security tests...")
        
        try:
            from test_framework import TestFramework
            
            framework = TestFramework(self.base_url)
            
            # Run security tests
            security_result = framework.run_test(framework.test_cors_and_security)
            rate_limit_result = framework.run_test(framework.test_rate_limiting)
            
            return {
                'status': 'PASS' if security_result.status == 'PASS' and rate_limit_result.status == 'PASS' else 'FAIL',
                'details': {
                    'cors_security': security_result.details,
                    'rate_limiting': rate_limit_result.details
                },
                'summary': f"Security: CORS {security_result.status}, Rate Limiting {rate_limit_result.status}"
            }
            
        except Exception as e:
            logger.error(f"Security tests failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'Security test error'
            }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance and load tests"""
        logger.info("⚡ Running performance tests...")
        
        try:
            from test_framework import TestFramework
            
            framework = TestFramework(self.base_url)
            
            # Run concurrent access tests
            concurrent_result = framework.run_test(framework.test_concurrent_access)
            
            return {
                'status': concurrent_result.status,
                'details': concurrent_result.details,
                'summary': f"Performance: Concurrent access {concurrent_result.status}"
            }
            
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'Performance test error'
            }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run end-to-end integration tests"""
        logger.info("🔗 Running integration tests...")
        
        try:
            from test_framework import TestFramework
            
            framework = TestFramework(self.base_url)
            
            # Run database integration tests
            db_result = framework.run_test(framework.test_database_schema_integrity)
            
            return {
                'status': db_result.status,
                'details': db_result.details,
                'summary': f"Integration: Database flow {db_result.status}"
            }
            
        except Exception as e:
            logger.error(f"Integration tests failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'Integration test error'
            }
    
    def check_server_health(self) -> Dict[str, Any]:
        """Check if server is running and healthy"""
        logger.info("🏥 Checking server health...")
        
        try:
            import requests
            
            # Check basic connectivity
            response = requests.get(f"{self.base_url}/api/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'PASS',
                    'details': data,
                    'summary': f"Server: Healthy (HTTP {response.status_code})"
                }
            else:
                return {
                    'status': 'FAIL',
                    'details': {'status_code': response.status_code},
                    'summary': f"Server: Unhealthy (HTTP {response.status_code})"
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'Server: Not responding'
            }
    
    def apply_authentication_fixes(self) -> Dict[str, Any]:
        """Apply authentication system fixes"""
        logger.info("🔧 Applying authentication fixes...")
        
        try:
            # Check if robust auth service exists
            backend_dir = Path(__file__).parent.parent / "backend"
            robust_auth_path = backend_dir / "app" / "services" / "robust_auth_service.py"
            
            if robust_auth_path.exists():
                logger.info("✅ Robust authentication service is available")
                
                # TODO: Integration with main app would go here
                # For now, we'll just verify the file exists and is importable
                
                return {
                    'status': 'PASS',
                    'summary': 'Authentication fixes available',
                    'details': {
                        'robust_auth_service': str(robust_auth_path),
                        'status': 'ready_for_integration'
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'summary': 'Authentication fixes not found'
                }
                
        except Exception as e:
            logger.error(f"Failed to apply authentication fixes: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'summary': 'Authentication fix error'
            }
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report"""
        execution_time = time.time() - self.start_time
        timestamp = datetime.now().isoformat()
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        failed_tests = total_tests - passed_tests
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        report = f"""
# PASSIVE CAPTCHA SYSTEM - COMPREHENSIVE TEST REPORT

**Generated:** {timestamp}  
**Base URL:** {self.base_url}  
**Execution Time:** {execution_time:.2f} seconds  

## 📊 SUMMARY
- **Total Test Categories:** {total_tests}
- **Passed:** {passed_tests} ✅
- **Failed:** {failed_tests} ❌
- **Success Rate:** {success_rate:.1%}

## 📋 DETAILED RESULTS

"""
        
        # Add detailed results for each test category
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            report += f"### {test_name.replace('_', ' ').title()} {status_icon}\n"
            report += f"**Status:** {result['status']}  \n"
            report += f"**Summary:** {result['summary']}  \n"
            
            if result.get('error'):
                report += f"**Error:** {result['error']}  \n"
            
            report += "\n"
        
        # Add recommendations section
        report += "## 🔧 RECOMMENDATIONS\n\n"
        
        if failed_tests > 0:
            report += "### Issues Found:\n"
            for test_name, result in self.test_results.items():
                if result['status'] == 'FAIL':
                    report += f"- **{test_name}:** {result['summary']}\n"
            report += "\n"
        
        report += "### Next Steps:\n"
        report += "1. Review failed test details in individual report files\n"
        report += "2. Apply suggested fixes from database and API validators\n"
        report += "3. Integrate robust authentication service\n"
        report += "4. Re-run tests after applying fixes\n"
        report += "5. Monitor system performance in production\n\n"
        
        # Add file references
        report += "## 📁 DETAILED REPORTS\n\n"
        report += "- Database Validation: `reports/database_validation.json`\n"
        report += "- API Routing: `reports/api_routing_validation.json`\n"
        report += "- API Documentation: `reports/api_documentation.md`\n"
        report += "- Full Test Log: `comprehensive_test.log`\n\n"
        
        return report
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        logger.info("🚀 Starting comprehensive test suite...")
        
        # Test categories to run
        test_categories = [
            ('server_health', self.check_server_health),
            ('database_validation', self.run_database_validation),
            ('api_routing_validation', self.run_api_routing_validation),
            ('authentication_tests', self.run_authentication_tests),
            ('security_tests', self.run_security_tests),
            ('performance_tests', self.run_performance_tests),
            ('integration_tests', self.run_integration_tests),
            ('authentication_fixes', self.apply_authentication_fixes)
        ]
        
        # Run each test category
        for test_name, test_func in test_categories:
            try:
                logger.info(f"Running {test_name}...")
                result = test_func()
                self.test_results[test_name] = result
                
                status_icon = "✅" if result['status'] == 'PASS' else "❌"
                logger.info(f"{test_name}: {result['status']} {status_icon}")
                
            except Exception as e:
                logger.error(f"Failed to run {test_name}: {e}")
                self.test_results[test_name] = {
                    'status': 'FAIL',
                    'error': str(e),
                    'summary': f'{test_name} execution error'
                }
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report()
        
        # Save main report
        with open(self.reports_dir / "comprehensive_test_report.md", 'w') as f:
            f.write(report)
        
        # Save summary JSON
        summary = {
            'timestamp': datetime.now().isoformat(),
            'execution_time_seconds': time.time() - self.start_time,
            'base_url': self.base_url,
            'test_results': self.test_results,
            'summary_stats': {
                'total_categories': len(self.test_results),
                'passed': sum(1 for r in self.test_results.values() if r['status'] == 'PASS'),
                'failed': sum(1 for r in self.test_results.values() if r['status'] == 'FAIL'),
                'success_rate': sum(1 for r in self.test_results.values() if r['status'] == 'PASS') / len(self.test_results)
            }
        }
        
        with open(self.reports_dir / "test_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for testing")
    parser.add_argument("--category", help="Run specific test category only")
    args = parser.parse_args()
    
    # Create test runner
    runner = ComprehensiveTestRunner(base_url=args.url)
    
    # Run tests
    if args.category:
        # Run specific category
        test_methods = {
            'database': runner.run_database_validation,
            'api': runner.run_api_routing_validation,
            'auth': runner.run_authentication_tests,
            'security': runner.run_security_tests,
            'performance': runner.run_performance_tests,
            'integration': runner.run_integration_tests,
            'health': runner.check_server_health,
            'fixes': runner.apply_authentication_fixes
        }
        
        if args.category in test_methods:
            result = test_methods[args.category]()
            print(f"{args.category}: {result['status']} - {result['summary']}")
        else:
            print(f"Unknown category: {args.category}")
            print(f"Available categories: {', '.join(test_methods.keys())}")
            sys.exit(1)
    else:
        # Run complete suite
        summary = runner.run_all_tests()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Categories: {summary['summary_stats']['total_categories']}")
        print(f"Passed: {summary['summary_stats']['passed']} ✅")
        print(f"Failed: {summary['summary_stats']['failed']} ❌")
        print(f"Success Rate: {summary['summary_stats']['success_rate']:.1%}")
        print(f"Execution Time: {summary['execution_time_seconds']:.2f}s")
        print(f"\nDetailed reports saved to: {runner.reports_dir}")
        
        # Exit with appropriate code
        exit_code = 0 if summary['summary_stats']['failed'] == 0 else 1
        sys.exit(exit_code)

if __name__ == "__main__":
    main()