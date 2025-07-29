#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Passive CAPTCHA System
Tests all backend modules, ML components, and API endpoints
"""

import os
import sys
import unittest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import Flask and test client
from flask import Flask
import numpy as np
import pandas as pd

class TestMLModule(unittest.TestCase):
    """Test ML model functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_features = {
            'mouse_movement_count': 45,
            'avg_mouse_velocity': 0.8,
            'keystroke_count': 10,
            'typing_rhythm_variance': 0.4,
            'session_duration': 35,
            'scroll_pattern_score': 0.8,
            'webgl_support_score': 1.0,
            'canvas_fingerprint_score': 0.85,
            'hardware_legitimacy': 0.9,
            'browser_consistency': 0.88,
            'plugin_availability': 0.85
        }
        
    def test_model_loading(self):
        """Test if model loads successfully"""
        try:
            from app.ml import load_model, is_model_loaded
            
            # Test model loading
            result = load_model()
            self.assertTrue(result, "Model should load successfully")
            self.assertTrue(is_model_loaded(), "Model should be loaded")
            
        except ImportError:
            self.skipTest("ML module not available")
    
    def test_feature_extraction(self):
        """Test feature extraction from raw data"""
        try:
            from app.ml import extract_features
            
            # Mock session data
            session_data = {
                'mouseMovements': [
                    {'x': 100, 'y': 200, 'timestamp': 1627234567890},
                    {'x': 150, 'y': 250, 'timestamp': 1627234567950}
                ],
                'keystrokes': [
                    {'key': 'a', 'timestamp': 1627234567900},
                    {'key': 'b', 'timestamp': 1627234568000}
                ],
                'sessionDuration': 15000,
                'fingerprint': {
                    'userAgent': 'Mozilla/5.0 (test)',
                    'screenWidth': 1920,
                    'screenHeight': 1080,
                    'webglVendor': 'NVIDIA Corporation'
                }
            }
            
            features = extract_features(session_data)
            
            # Validate feature structure
            self.assertIsInstance(features, (dict, list))
            if isinstance(features, dict):
                self.assertGreater(len(features), 0, "Features should not be empty")
            
        except ImportError:
            self.skipTest("ML module not available")
    
    def test_prediction_output(self):
        """Test ML prediction output format"""
        try:
            from app.ml import predict_human_probability
            
            # Test with valid features
            prediction = predict_human_probability(self.test_features)
            
            # Validate prediction structure
            self.assertIsInstance(prediction, dict)
            self.assertIn('isHuman', prediction)
            self.assertIn('confidence', prediction)
            self.assertIsInstance(prediction['isHuman'], bool)
            self.assertIsInstance(prediction['confidence'], (int, float))
            self.assertGreaterEqual(prediction['confidence'], 0)
            self.assertLessEqual(prediction['confidence'], 1)
            
        except ImportError:
            self.skipTest("ML module not available")
    
    def test_edge_cases(self):
        """Test ML model with edge case inputs"""
        try:
            from app.ml import extract_features, predict_human_probability
            
            # Test with minimal data
            minimal_data = {
                'mouseMovements': [],
                'keystrokes': [],
                'sessionDuration': 0,
                'fingerprint': {}
            }
            
            # Should not crash with minimal data
            features = extract_features(minimal_data)
            prediction = predict_human_probability(features)
            self.assertIsInstance(prediction, dict)
            
            # Test with extreme values
            extreme_features = {
                'mouse_movement_count': 0,
                'avg_mouse_velocity': 0,
                'keystroke_count': 0,
                'typing_rhythm_variance': 0,
                'session_duration': 0,
                'scroll_pattern_score': 0,
                'webgl_support_score': 0,
                'canvas_fingerprint_score': 0,
                'hardware_legitimacy': 0,
                'browser_consistency': 0,
                'plugin_availability': 0
            }
            
            extreme_prediction = predict_human_probability(extreme_features)
            self.assertIsInstance(extreme_prediction, dict)
            
        except ImportError:
            self.skipTest("ML module not available")


class TestDatabaseModule(unittest.TestCase):
    """Test database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_database_initialization(self):
        """Test database initialization"""
        try:
            # Mock Flask app context
            app = Flask(__name__)
            app.config['DATABASE_URL'] = f'sqlite:///{self.test_db_path}'
            
            with app.app_context():
                from app.database import init_db
                result = init_db()
                self.assertTrue(result, "Database should initialize successfully")
                self.assertTrue(os.path.exists(self.test_db_path), "Database file should be created")
                
        except ImportError:
            self.skipTest("Database module not available")
    
    def test_verification_logging(self):
        """Test verification log creation"""
        try:
            app = Flask(__name__)
            app.config['DATABASE_URL'] = f'sqlite:///{self.test_db_path}'
            
            with app.app_context():
                from app.database import init_db, log_verification
                
                init_db()
                
                # Test logging
                log_id = log_verification(
                    session_id='test_session_123',
                    ip_address='127.0.0.1',
                    user_agent='Test Agent',
                    origin='test.com',
                    is_human=True,
                    confidence=0.85,
                    features={'mouse_movement_count': 45},
                    response_time=95
                )
                
                self.assertIsNotNone(log_id, "Log ID should be returned")
                self.assertIsInstance(log_id, int, "Log ID should be integer")
                
        except ImportError:
            self.skipTest("Database module not available")
    
    def test_analytics_data(self):
        """Test analytics data retrieval"""
        try:
            app = Flask(__name__)
            app.config['DATABASE_URL'] = f'sqlite:///{self.test_db_path}'
            
            with app.app_context():
                from app.database import init_db, get_analytics_data, log_verification
                
                init_db()
                
                # Add some test data
                log_verification('test1', '127.0.0.1', 'Agent', 'test.com', True, 0.9, {}, 50)
                log_verification('test2', '127.0.0.1', 'Agent', 'test.com', False, 0.3, {}, 75)
                
                # Get analytics
                analytics = get_analytics_data(hours=24)
                
                # Validate structure
                self.assertIsInstance(analytics, dict)
                self.assertIn('totalVerifications', analytics)
                self.assertIn('trends', analytics)
                self.assertIn('topOrigins', analytics)
                
                # Validate data
                self.assertGreaterEqual(analytics['totalVerifications'], 2)
                self.assertIsInstance(analytics['trends'], list)
                self.assertIsInstance(analytics['topOrigins'], list)
                
        except ImportError:
            self.skipTest("Database module not available")


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoint functionality"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        
        # Create test app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['DATABASE_URL'] = f'sqlite:///{self.test_db_path}'
        self.app.config['ADMIN_SECRET'] = 'test-secret'
        
        try:
            # Register blueprints
            from app.api import api_bp
            from app.admin import admin_bp
            
            self.app.register_blueprint(api_bp, url_prefix='/api')
            self.app.register_blueprint(admin_bp, url_prefix='/admin')
            
            self.client = self.app.test_client()
            
            # Initialize database
            with self.app.app_context():
                from app.database import init_db
                init_db()
                
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 200, "Health endpoint should return 200")
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('timestamp', data)
    
    def test_status_endpoint(self):
        """Test status endpoint"""
        response = self.client.get('/api/status')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('api', data)
        self.assertIn('version', data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'operational')
    
    def test_verify_endpoint_validation(self):
        """Test verification endpoint input validation"""
        # Test with empty data
        response = self.client.post('/api/verify', 
                                  headers={'Content-Type': 'application/json'},
                                  data='{}')
        
        # Should handle empty data gracefully
        self.assertIn(response.status_code, [200, 400])
        
        # Test with invalid content type
        response = self.client.post('/api/verify', data='invalid')
        self.assertEqual(response.status_code, 400)
    
    def test_admin_authentication(self):
        """Test admin authentication"""
        # Test login with correct password
        response = self.client.post('/admin/login',
                                  headers={'Content-Type': 'application/json'},
                                  data=json.dumps({'password': 'test-secret'}))
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertIn('expires_in', data)
        
        # Test login with wrong password
        response = self.client.post('/admin/login',
                                  headers={'Content-Type': 'application/json'},
                                  data=json.dumps({'password': 'wrong-password'}))
        
        self.assertEqual(response.status_code, 401)
    
    def test_rate_limiting_simulation(self):
        """Test rate limiting behavior (simulation)"""
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = self.client.get('/api/status')
            responses.append(response.status_code)
        
        # All should succeed for status endpoint (no rate limiting)
        self.assertTrue(all(code == 200 for code in responses))
    
    def test_error_handling(self):
        """Test error handling for non-existent endpoints"""
        response = self.client.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)


class TestFeatureEngineering(unittest.TestCase):
    """Test feature engineering functions"""
    
    def test_mouse_feature_extraction(self):
        """Test mouse movement feature extraction"""
        try:
            from app.ml import extract_features
            
            # Sample mouse data
            mouse_data = [
                {'x': 100, 'y': 100, 'timestamp': 1000},
                {'x': 150, 'y': 120, 'timestamp': 1100},
                {'x': 200, 'y': 140, 'timestamp': 1200}
            ]
            
            session_data = {
                'mouseMovements': mouse_data,
                'keystrokes': [],
                'sessionDuration': 1000,
                'fingerprint': {}
            }
            
            features = extract_features(session_data)
            
            # Should handle mouse data without errors
            self.assertIsNotNone(features)
            
        except ImportError:
            self.skipTest("ML module not available")
    
    def test_keystroke_feature_extraction(self):
        """Test keystroke feature extraction"""
        try:
            from app.ml import extract_features
            
            # Sample keystroke data
            keystroke_data = [
                {'key': 'h', 'timestamp': 1000},
                {'key': 'e', 'timestamp': 1150},
                {'key': 'l', 'timestamp': 1300},
                {'key': 'l', 'timestamp': 1450},
                {'key': 'o', 'timestamp': 1600}
            ]
            
            session_data = {
                'mouseMovements': [],
                'keystrokes': keystroke_data,
                'sessionDuration': 1000,
                'fingerprint': {}
            }
            
            features = extract_features(session_data)
            
            # Should handle keystroke data without errors
            self.assertIsNotNone(features)
            
        except ImportError:
            self.skipTest("ML module not available")
    
    def test_fingerprint_feature_extraction(self):
        """Test device fingerprint feature extraction"""
        try:
            from app.ml import extract_features
            
            # Sample fingerprint data
            fingerprint_data = {
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'screenWidth': 1920,
                'screenHeight': 1080,
                'webglVendor': 'NVIDIA Corporation',
                'canvasFingerprint': 'canvas_hash_123',
                'hardwareConcurrency': 8,
                'platform': 'Win32'
            }
            
            session_data = {
                'mouseMovements': [],
                'keystrokes': [],
                'sessionDuration': 1000,
                'fingerprint': fingerprint_data
            }
            
            features = extract_features(session_data)
            
            # Should handle fingerprint data without errors
            self.assertIsNotNone(features)
            
        except ImportError:
            self.skipTest("ML module not available")


class TestModelPerformance(unittest.TestCase):
    """Test ML model performance characteristics"""
    
    def test_inference_speed(self):
        """Test model inference speed"""
        try:
            from app.ml import predict_human_probability, is_model_loaded
            
            if not is_model_loaded():
                self.skipTest("Model not loaded")
            
            test_features = {
                'mouse_movement_count': 45,
                'avg_mouse_velocity': 0.8,
                'keystroke_count': 10,
                'typing_rhythm_variance': 0.4,
                'session_duration': 35,
                'scroll_pattern_score': 0.8,
                'webgl_support_score': 1.0,
                'canvas_fingerprint_score': 0.85,
                'hardware_legitimacy': 0.9,
                'browser_consistency': 0.88,
                'plugin_availability': 0.85
            }
            
            # Measure inference time
            start_time = time.time()
            prediction = predict_human_probability(test_features)
            end_time = time.time()
            
            inference_time = (end_time - start_time) * 1000  # Convert to ms
            
            # Should be faster than 100ms (SRS requirement)
            self.assertLess(inference_time, 100, f"Inference time {inference_time}ms should be < 100ms")
            
            # Validate prediction
            self.assertIsInstance(prediction, dict)
            self.assertIn('confidence', prediction)
            
        except ImportError:
            self.skipTest("ML module not available")
    
    def test_batch_prediction_performance(self):
        """Test performance with multiple predictions"""
        try:
            from app.ml import predict_human_probability, is_model_loaded
            
            if not is_model_loaded():
                self.skipTest("Model not loaded")
            
            test_features = {
                'mouse_movement_count': 45,
                'avg_mouse_velocity': 0.8,
                'keystroke_count': 10,
                'typing_rhythm_variance': 0.4,
                'session_duration': 35,
                'scroll_pattern_score': 0.8,
                'webgl_support_score': 1.0,
                'canvas_fingerprint_score': 0.85,
                'hardware_legitimacy': 0.9,
                'browser_consistency': 0.88,
                'plugin_availability': 0.85
            }
            
            # Run 10 predictions
            start_time = time.time()
            for _ in range(10):
                prediction = predict_human_probability(test_features)
            end_time = time.time()
            
            avg_time = ((end_time - start_time) / 10) * 1000  # ms per prediction
            
            # Average should still be fast
            self.assertLess(avg_time, 50, f"Average inference time {avg_time}ms should be < 50ms")
            
        except ImportError:
            self.skipTest("ML module not available")


def run_unit_tests():
    """Run all unit tests and generate report"""
    print("🧪 Starting Comprehensive Unit Testing...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestMLModule,
        TestDatabaseModule,
        TestAPIEndpoints,
        TestFeatureEngineering,
        TestModelPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 UNIT TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"✅ Tests Passed: {passed}")
    print(f"❌ Tests Failed: {failures}")
    print(f"🚫 Tests Errors: {errors}")
    print(f"⏭️  Tests Skipped: {skipped}")
    print(f"📈 Total Tests: {total_tests}")
    
    if failures > 0:
        print(f"\n💥 FAILURES ({failures}):")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print(f"\n🔥 ERRORS ({errors}):")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🏆 EXCELLENT: Unit tests passed with high success rate!")
    elif success_rate >= 75:
        print("✅ GOOD: Most unit tests passed successfully!")
    else:
        print("⚠️  WARNING: Low unit test success rate - review failures!")
    
    return result.wasSuccessful(), success_rate


if __name__ == "__main__":
    success, rate = run_unit_tests() 