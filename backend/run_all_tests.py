#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner
Runs all tests (database, API, ML, network, deployment) and provides summary
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def run_test_suite(test_file, description):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per test suite
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        return {
            'name': description,
            'file': test_file,
            'success': success,
            'duration': duration,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ Test suite timed out after 2 minutes")
        return {
            'name': description,
            'file': test_file,
            'success': False,
            'duration': 120,
            'returncode': -1,
            'error': 'Timeout'
        }
    except Exception as e:
        print(f"❌ Test suite crashed: {e}")
        return {
            'name': description,
            'file': test_file,
            'success': False,
            'duration': 0,
            'returncode': -1,
            'error': str(e)
        }


def main():
    """Run all test suites and provide comprehensive summary"""
    print("🚀 Passive CAPTCHA Platform - Comprehensive Test Suite")
    print("=" * 80)
    print("Testing database, API endpoints, ML model, network, and deployment readiness")
    print("=" * 80)
    
    # Test suites to run
    test_suites = [
        ('test_database_connectivity.py', 'Database Connectivity & Multi-tenancy'),
        ('test_api_endpoints.py', 'API Endpoints & Multi-tenant Features'),
        ('test_ml_model.py', 'ML Model & Feature Engineering'),
        ('test_network_connectivity.py', 'Network Connectivity & External Services'),
        ('test_deployment.py', 'Deployment Readiness & Configuration')
    ]
    
    results = []
    total_start_time = time.time()
    
    # Run each test suite
    for test_file, description in test_suites:
        if Path(test_file).exists():
            result = run_test_suite(test_file, description)
            results.append(result)
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append({
                'name': description,
                'file': test_file,
                'success': False,
                'duration': 0,
                'returncode': -1,
                'error': 'File not found'
            })
    
    total_duration = time.time() - total_start_time
    
    # Generate comprehensive summary
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    
    passed_suites = sum(1 for r in results if r['success'])
    failed_suites = len(results) - passed_suites
    
    print(f"📈 Overall Results: {passed_suites}/{len(results)} test suites passed")
    print(f"⏱️  Total execution time: {total_duration:.1f} seconds")
    print()
    
    # Detailed results
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        duration = f"{result['duration']:.1f}s"
        
        print(f"{status} | {result['name']:<45} | {duration:>8}")
        
        if not result['success'] and 'error' in result:
            print(f"         Error: {result['error']}")
    
    print(f"\n{'='*80}")
    
    # System status assessment
    if passed_suites == len(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ System is fully operational and ready for production deployment")
        print("🚀 Multi-tenant passive CAPTCHA platform is working correctly")
        
        print("\n📋 Deployment Checklist:")
        print("   ✅ Database connectivity and multi-tenancy working")
        print("   ✅ API endpoints responding correctly")
        print("   ✅ ML model loading and inference working")
        print("   ✅ Network connectivity established")
        print("   ✅ Deployment configuration validated")
        
    elif passed_suites >= len(results) * 0.8:  # 80% pass rate
        print("⚠️  MOSTLY PASSING - Minor issues detected")
        print("🔧 Most systems are operational but some issues need attention")
        print("📝 Review failed tests and fix issues before production deployment")
        
    else:
        print("❌ MULTIPLE FAILURES - Significant issues detected")
        print("🚨 System has critical issues that must be resolved")
        print("🔧 Fix all failing tests before attempting deployment")
    
    # Specific recommendations
    print(f"\n{'='*80}")
    print("🔍 DETAILED ANALYSIS")
    print(f"{'='*80}")
    
    # Analyze each component
    component_status = {
        'Database': False,
        'API': False,
        'ML Model': False,
        'Network': False,
        'Deployment': False
    }
    
    for result in results:
        if 'Database' in result['name']:
            component_status['Database'] = result['success']
        elif 'API' in result['name']:
            component_status['API'] = result['success']
        elif 'ML' in result['name']:
            component_status['ML Model'] = result['success']
        elif 'Network' in result['name']:
            component_status['Network'] = result['success']
        elif 'Deployment' in result['name']:
            component_status['Deployment'] = result['success']
    
    for component, status in component_status.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component:<15}: {'Operational' if status else 'Issues detected'}")
    
    print(f"\n{'='*80}")
    print("📚 NEXT STEPS")
    print(f"{'='*80}")
    
    if all(component_status.values()):
        print("🎯 Ready for production deployment!")
        print("   1. Set up production environment variables")
        print("   2. Configure production database (PostgreSQL recommended)")
        print("   3. Set up Redis for production rate limiting")
        print("   4. Deploy to Railway/Render/Vercel")
        print("   5. Test production deployment")
        
    else:
        failed_components = [comp for comp, status in component_status.items() if not status]
        print(f"🔧 Fix issues in: {', '.join(failed_components)}")
        print("   1. Review test output above for specific error details")
        print("   2. Fix identified issues")
        print("   3. Re-run tests: python run_all_tests.py")
        print("   4. Repeat until all tests pass")
    
    print(f"\n{'='*80}")
    print("📖 Documentation and Resources:")
    print("   📋 Multi-tenant Architecture: MULTI_TENANT_ARCHITECTURE.md")
    print("   🚀 Implementation Summary: IMPLEMENTATION_SUMMARY.md")
    print("   🔧 Environment Config: config.env.example")
    print("   🐳 Docker Setup: docker-compose.yml")
    print(f"{'='*80}")
    
    # Return appropriate exit code
    return 0 if passed_suites == len(results) else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)