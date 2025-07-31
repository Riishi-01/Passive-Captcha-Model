#!/usr/bin/env python3
"""
Master Test Runner for Passive CAPTCHA
Runs all test suites and generates comprehensive reports
"""

import sys
import os
import unittest
import time
import json
from datetime import datetime
from pathlib import Path
import subprocess


class TestRunner:
    """Master test runner"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_suite_dir = Path(__file__).parent
        self.reports_dir = self.test_suite_dir / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_suites': {},
            'summary': {
                'total_tests': 0,
                'total_failures': 0,
                'total_errors': 0,
                'total_skipped': 0,
                'success_rate': 0,
                'duration': 0
            }
        }
        
    def run_test_suite(self, suite_name, test_module):
        """Run a specific test suite"""
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING {suite_name.upper()} TESTS")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Import and run the test module
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            runner = unittest.TextTestRunner(
                verbosity=2,
                stream=sys.stdout,
                buffer=True
            )
            
            result = runner.run(suite)
            
            duration = time.time() - start_time
            
            # Store results
            self.results['test_suites'][suite_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
                'duration': duration,
                'status': 'PASSED' if result.wasSuccessful() else 'FAILED'
            }
            
            # Update totals
            self.results['summary']['total_tests'] += result.testsRun
            self.results['summary']['total_failures'] += len(result.failures)
            self.results['summary']['total_errors'] += len(result.errors)
            self.results['summary']['total_skipped'] += len(result.skipped) if hasattr(result, 'skipped') else 0
            
            print(f"\n✅ {suite_name} tests completed in {duration:.2f}s")
            print(f"   Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
            
            return result.wasSuccessful()
            
        except Exception as e:
            print(f"\n❌ Failed to run {suite_name} tests: {e}")
            self.results['test_suites'][suite_name] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'success_rate': 0,
                'duration': time.time() - start_time,
                'status': 'ERROR',
                'error': str(e)
            }
            return False
            
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 PASSIVE CAPTCHA - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project Root: {self.project_root}")
        print(f"Test Reports: {self.reports_dir}")
        
        overall_start = time.time()
        all_passed = True
        
        # Test suites to run
        test_suites = [
            ('unit_tests', 'unit.test_auth_service'),
            ('api_tests', 'api.test_endpoints'),
            ('deployment_tests', 'deployment.test_render_deploy'),
            ('integration_tests', 'integration.test_end_to_end')
        ]
        
        # Add test suite directory to path
        sys.path.insert(0, str(self.test_suite_dir))
        
        for suite_name, module_name in test_suites:
            try:
                # Import the test module
                test_module = __import__(module_name, fromlist=[''])
                success = self.run_test_suite(suite_name, test_module)
                if not success:
                    all_passed = False
            except ImportError as e:
                print(f"\n⚠️  Could not import {module_name}: {e}")
                all_passed = False
                
        # Calculate final summary
        total_duration = time.time() - overall_start
        self.results['summary']['duration'] = total_duration
        
        if self.results['summary']['total_tests'] > 0:
            self.results['summary']['success_rate'] = (
                (self.results['summary']['total_tests'] - 
                 self.results['summary']['total_failures'] - 
                 self.results['summary']['total_errors']) / 
                self.results['summary']['total_tests'] * 100
            )
        
        self.generate_reports()
        self.print_final_summary()
        
        return all_passed
        
    def generate_reports(self):
        """Generate test reports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON Report
        json_report = self.reports_dir / f'test_results_{timestamp}.json'
        with open(json_report, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        # HTML Report
        html_report = self.reports_dir / f'test_report_{timestamp}.html'
        self.generate_html_report(html_report)
        
        print(f"\n📊 Reports generated:")
        print(f"   JSON: {json_report}")
        print(f"   HTML: {html_report}")
        
    def generate_html_report(self, html_path):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Passive CAPTCHA Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f9ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: white; border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .success {{ color: #16a34a; }}
        .warning {{ color: #ea580c; }}
        .error {{ color: #dc2626; }}
        .test-suite {{ margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 8px; }}
        .suite-header {{ background: #f9fafb; padding: 15px; border-bottom: 1px solid #e5e7eb; }}
        .suite-details {{ padding: 15px; }}
        .status-passed {{ color: #16a34a; font-weight: bold; }}
        .status-failed {{ color: #dc2626; font-weight: bold; }}
        .status-error {{ color: #ea580c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Passive CAPTCHA Test Report</h1>
        <p><strong>Generated:</strong> {self.results['timestamp']}</p>
        <p><strong>Duration:</strong> {self.results['summary']['duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <div class="stat-card">
            <div class="stat-value">{self.results['summary']['total_tests']}</div>
            <div>Total Tests</div>
        </div>
        <div class="stat-card">
            <div class="stat-value success">{self.results['summary']['total_tests'] - self.results['summary']['total_failures'] - self.results['summary']['total_errors']}</div>
            <div>Passed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value warning">{self.results['summary']['total_failures']}</div>
            <div>Failures</div>
        </div>
        <div class="stat-card">
            <div class="stat-value error">{self.results['summary']['total_errors']}</div>
            <div>Errors</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{self.results['summary']['success_rate']:.1f}%</div>
            <div>Success Rate</div>
        </div>
    </div>
    
    <h2>Test Suite Details</h2>
"""
        
        for suite_name, details in self.results['test_suites'].items():
            status_class = f"status-{details['status'].lower()}"
            html_content += f"""
    <div class="test-suite">
        <div class="suite-header">
            <h3>{suite_name.replace('_', ' ').title()}</h3>
            <span class="{status_class}">{details['status']}</span>
        </div>
        <div class="suite-details">
            <p><strong>Tests Run:</strong> {details['tests_run']}</p>
            <p><strong>Failures:</strong> {details['failures']}</p>
            <p><strong>Errors:</strong> {details['errors']}</p>
            <p><strong>Success Rate:</strong> {details['success_rate']:.1f}%</p>
            <p><strong>Duration:</strong> {details['duration']:.2f}s</p>
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(html_path, 'w') as f:
            f.write(html_content)
            
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 70)
        print("🎯 FINAL TEST SUMMARY")
        print("=" * 70)
        
        summary = self.results['summary']
        print(f"Total Tests:     {summary['total_tests']}")
        print(f"Passed:          {summary['total_tests'] - summary['total_failures'] - summary['total_errors']}")
        print(f"Failures:        {summary['total_failures']}")
        print(f"Errors:          {summary['total_errors']}")
        print(f"Success Rate:    {summary['success_rate']:.1f}%")
        print(f"Total Duration:  {summary['duration']:.2f}s")
        
        print("\n📋 Suite Breakdown:")
        for suite_name, details in self.results['test_suites'].items():
            status_icon = "✅" if details['status'] == 'PASSED' else "❌"
            print(f"  {status_icon} {suite_name}: {details['tests_run']} tests, {details['success_rate']:.1f}% success")
            
        if summary['success_rate'] >= 90:
            print("\n🎉 EXCELLENT! Test suite passed with high success rate!")
        elif summary['success_rate'] >= 70:
            print("\n✅ GOOD! Most tests passed, some issues to address.")
        else:
            print("\n⚠️  NEEDS ATTENTION! Many tests failed, review required.")


def main():
    """Main entry point"""
    runner = TestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())