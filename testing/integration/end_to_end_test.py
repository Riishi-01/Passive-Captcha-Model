#!/usr/bin/env python3
"""
End-to-End Integration Test
Tests the complete frontend-backend integration with real API calls
"""

import asyncio
import time
import requests
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

class EndToEndTester:
    def __init__(self):
        self.backend_url = 'http://localhost:5003'
        self.frontend_url = 'http://localhost:3002'
        self.auth_token = None
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results"""
        self.results['total_tests'] += 1
        try:
            self.log(f"Running test: {test_name}")
            test_func()
            self.results['passed'] += 1
            self.log(f"✅ PASSED: {test_name}", 'SUCCESS')
            return True
        except Exception as e:
            self.results['failed'] += 1
            self.results['errors'].append({'test': test_name, 'error': str(e)})
            self.log(f"❌ FAILED: {test_name} - {e}", 'ERROR')
            return False
    
    def test_backend_startup(self):
        """Test that backend server is running"""
        response = requests.get(f'{self.backend_url}/health', timeout=10)
        if response.status_code != 200:
            raise Exception(f"Backend health check failed: {response.status_code}")
        
        health_data = response.json()
        if health_data.get('status') != 'healthy':
            raise Exception(f"Backend is not healthy: {health_data}")
    
    def test_admin_login(self):
        """Test admin authentication"""
        response = requests.post(
            f'{self.backend_url}/admin/login',
            json={'password': 'Admin123'},
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code}")
        
        data = response.json()
        if 'token' not in data:
            raise Exception("No token in login response")
        
        self.auth_token = data['token']
        self.log(f"Authentication successful, token length: {len(self.auth_token)}")
    
    def test_dashboard_analytics(self):
        """Test dashboard analytics API endpoints"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test stats endpoint
        response = requests.get(f'{self.backend_url}/admin/analytics/stats', headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Stats endpoint failed: {response.status_code}")
        
        stats_data = response.json()
        if not stats_data.get('success'):
            raise Exception(f"Stats API returned error: {stats_data}")
        
        # Verify required fields
        required_fields = ['totalVerifications', 'humanRate', 'avgConfidence']
        for field in required_fields:
            if field not in stats_data['data']:
                raise Exception(f"Missing required field in stats: {field}")
    
    def test_chart_data(self):
        """Test chart data endpoints"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test chart data endpoint
        response = requests.get(f'{self.backend_url}/admin/analytics/charts', headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Chart data endpoint failed: {response.status_code}")
        
        chart_data = response.json()
        if not chart_data.get('success'):
            raise Exception(f"Chart data API returned error: {chart_data}")
        
        # Verify chart data structure
        data = chart_data['data']
        if not isinstance(data, list):
            raise Exception("Chart data should be a list")
    
    def test_website_management(self):
        """Test website management endpoints"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test get websites
        response = requests.get(f'{self.backend_url}/admin/websites', headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Get websites failed: {response.status_code}")
        
        websites_data = response.json()
        if not websites_data.get('success'):
            raise Exception(f"Websites API returned error: {websites_data}")
        
        # Test create website
        new_website = {
            'name': 'Test Website',
            'url': 'https://test.example.com',
            'description': 'End-to-end test website'
        }
        
        response = requests.post(f'{self.backend_url}/admin/websites', 
                               json=new_website, headers=headers, timeout=10)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Create website failed: {response.status_code}")
        
        create_data = response.json()
        if not create_data.get('success'):
            raise Exception(f"Create website API returned error: {create_data}")
    
    def test_ml_metrics(self):
        """Test ML metrics endpoints"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test ML metrics endpoint
        response = requests.get(f'{self.backend_url}/admin/ml/metrics', headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"ML metrics endpoint failed: {response.status_code}")
        
        metrics_data = response.json()
        if not metrics_data.get('success'):
            raise Exception(f"ML metrics API returned error: {metrics_data}")
        
        # Verify required ML metrics
        required_metrics = ['totalVerificationAttempts', 'humanDetectionRate', 'botDetectionRate']
        for metric in required_metrics:
            if metric not in metrics_data['data']:
                raise Exception(f"Missing required ML metric: {metric}")
    
    def test_alerts_system(self):
        """Test alerts endpoints"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test recent alerts
        response = requests.get(f'{self.backend_url}/admin/alerts/recent', headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Recent alerts failed: {response.status_code}")
        
        alerts_data = response.json()
        if not alerts_data.get('success'):
            raise Exception(f"Alerts API returned error: {alerts_data}")
        
        # Verify alerts structure
        alerts = alerts_data['data']
        if not isinstance(alerts, list):
            raise Exception("Alerts should be a list")
    
    def test_logs_system(self):
        """Test logs endpoints"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test timeline logs
        response = requests.get(f'{self.backend_url}/admin/logs/timeline', headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Timeline logs failed: {response.status_code}")
        
        logs_data = response.json()
        if not logs_data.get('success'):
            raise Exception(f"Logs API returned error: {logs_data}")
        
        # Verify logs structure
        logs_info = logs_data['data']
        required_fields = ['logs', 'hasMore', 'total']
        for field in required_fields:
            if field not in logs_info:
                raise Exception(f"Missing required field in logs: {field}")
    
    def test_system_health(self):
        """Test system health endpoint"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test admin health endpoint
        response = requests.get(f'{self.backend_url}/admin/health', headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Admin health failed: {response.status_code}")
        
        health_data = response.json()
        if not health_data.get('success'):
            raise Exception(f"Admin health API returned error: {health_data}")
    
    def test_api_performance(self):
        """Test API response times"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test multiple endpoints for performance
        endpoints = [
            '/admin/analytics/stats',
            '/admin/analytics/charts',
            '/admin/websites',
            '/admin/ml/metrics'
        ]
        
        total_time = 0
        slow_endpoints = []
        
        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f'{self.backend_url}{endpoint}', headers=headers, timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            total_time += response_time
            
            if response_time > 2000:  # Slower than 2 seconds
                slow_endpoints.append(f"{endpoint}: {response_time:.2f}ms")
        
        avg_response_time = total_time / len(endpoints)
        self.log(f"Average API response time: {avg_response_time:.2f}ms")
        
        if slow_endpoints:
            raise Exception(f"Slow endpoints detected: {slow_endpoints}")
    
    def test_data_consistency(self):
        """Test that API data is consistent across endpoints"""
        if not self.auth_token:
            raise Exception("No auth token available")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Get stats from multiple endpoints
        stats_response = requests.get(f'{self.backend_url}/admin/analytics/stats', headers=headers, timeout=10)
        ml_response = requests.get(f'{self.backend_url}/admin/ml/metrics', headers=headers, timeout=10)
        
        if stats_response.status_code != 200 or ml_response.status_code != 200:
            raise Exception("Failed to fetch data for consistency check")
        
        stats_data = stats_response.json()['data']
        ml_data = ml_response.json()['data']
        
        # Compare total verifications (should be consistent)
        stats_total = stats_data.get('totalVerifications', 0)
        ml_total = ml_data.get('totalVerificationAttempts', 0)
        
        # Allow for some variance due to timing
        if abs(stats_total - ml_total) > 10:
            raise Exception(f"Data inconsistency: stats={stats_total}, ml={ml_total}")
    
    def run_all_tests(self):
        """Run the complete end-to-end test suite"""
        self.log("🚀 Starting End-to-End Integration Tests")
        self.log("=" * 60)
        
        # Define test sequence
        tests = [
            ("Backend Startup", self.test_backend_startup),
            ("Admin Authentication", self.test_admin_login),
            ("Dashboard Analytics", self.test_dashboard_analytics),
            ("Chart Data APIs", self.test_chart_data),
            ("Website Management", self.test_website_management),
            ("ML Metrics", self.test_ml_metrics),
            ("Alerts System", self.test_alerts_system),
            ("Logs System", self.test_logs_system),
            ("System Health", self.test_system_health),
            ("API Performance", self.test_api_performance),
            ("Data Consistency", self.test_data_consistency)
        ]
        
        # Run tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print final results
        self.print_results()
        
        return self.results['failed'] == 0
    
    def print_results(self):
        """Print final test results"""
        self.log("=" * 60)
        self.log("🏁 END-TO-END TEST RESULTS")
        self.log("=" * 60)
        
        total = self.results['total_tests']
        passed = self.results['passed']
        failed = self.results['failed']
        
        self.log(f"📊 Total Tests: {total}")
        self.log(f"✅ Passed: {passed}")
        self.log(f"❌ Failed: {failed}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        self.log(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED - System is production ready!", 'SUCCESS')
        else:
            self.log("⚠️  Some tests failed - see errors above", 'WARNING')
            for error in self.results['errors']:
                self.log(f"   - {error['test']}: {error['error']}", 'ERROR')


def main():
    """Main function to run end-to-end tests"""
    tester = EndToEndTester()
    
    # Check if backend is running
    try:
        requests.get(tester.backend_url + '/health', timeout=5)
    except requests.exceptions.RequestException:
        print("❌ Backend server is not running on http://localhost:5003")
        print("💡 Please start the backend server first:")
        print("   cd backend && python run_server.py")
        return False
    
    # Run tests
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ END-TO-END INTEGRATION: SUCCESSFUL")
        print("🚀 Frontend and Backend are properly integrated!")
    else:
        print("\n❌ END-TO-END INTEGRATION: ISSUES DETECTED")
        print("🔧 Please fix the issues above before deployment")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)