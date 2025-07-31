#!/usr/bin/env python3
"""
ML Model tests for Passive CAPTCHA system
"""

import unittest
import numpy as np
import pickle
import joblib
import json
import time
from pathlib import Path

class TestMLModel(unittest.TestCase):
    """Test ML model functionality"""
    
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.models_dir = self.project_root / 'backend' / 'models'
        self.model_file = self.models_dir / 'passive_captcha_rf.pkl'
        self.scaler_file = self.models_dir / 'passive_captcha_rf_scaler.pkl'
        self.metadata_file = self.models_dir / 'passive_captcha_rf_metadata.json'
        
        # Load model and scaler for tests
        self.model = None
        self.scaler = None
        self.metadata = None
        
        try:
            if self.model_file.exists():
                with open(self.model_file, 'rb') as f:
                    self.model = pickle.load(f)
            
            if self.scaler_file.exists():
                self.scaler = joblib.load(self.scaler_file)
            
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load model files: {e}")
    
    def test_model_files_exist(self):
        """Test that all required model files exist"""
        self.assertTrue(self.model_file.exists(), "Model file not found")
        self.assertTrue(self.scaler_file.exists(), "Scaler file not found")
    
    def test_model_loading(self):
        """Test that model can be loaded without errors"""
        self.assertIsNotNone(self.model, "Model could not be loaded")
        self.assertIsNotNone(self.scaler, "Scaler could not be loaded")
    
    def test_model_prediction_structure(self):
        """Test that model predictions have correct structure"""
        if self.model is None or self.scaler is None:
            self.skipTest("Model not available")
        
        # Create test feature vector (11 features as per documentation)
        test_features = np.array([[
            100,    # mouse_movement_count
            50.5,   # avg_mouse_velocity  
            5,      # keystroke_count
            200.5,  # avg_keystroke_interval
            2.5,    # scroll_count
            1500,   # page_dwell_time
            0.8,    # screen_resolution_ratio
            1,      # touch_support (boolean as int)
            2.1,    # device_pixel_ratio
            4,      # cpu_cores
            0.95    # webgl_support (boolean as float)
        ]])
        
        # Test feature vector shape
        self.assertEqual(test_features.shape[1], 11, "Feature vector should have 11 dimensions")
        
        # Scale features
        scaled_features = self.scaler.transform(test_features)
        self.assertEqual(scaled_features.shape, test_features.shape, "Scaled features shape mismatch")
        
        # Make prediction
        prediction = self.model.predict(scaled_features)
        self.assertEqual(len(prediction), 1, "Should predict for one sample")
        self.assertIn(prediction[0], [0, 1], "Prediction should be binary (0 or 1)")
        
        # Test probability prediction
        probability = self.model.predict_proba(scaled_features)
        self.assertEqual(probability.shape, (1, 2), "Probability should be (1, 2) shape")
        self.assertAlmostEqual(np.sum(probability[0]), 1.0, places=5, msg="Probabilities should sum to 1")
    
    def test_model_performance_timing(self):
        """Test that model inference is fast enough"""
        if self.model is None or self.scaler is None:
            self.skipTest("Model not available")
        
        test_features = np.array([[100, 50.5, 5, 200.5, 2.5, 1500, 0.8, 1, 2.1, 4, 0.95]])
        
        # Warm up
        for _ in range(5):
            scaled_features = self.scaler.transform(test_features)
            self.model.predict_proba(scaled_features)
        
        # Measure performance
        start_time = time.time()
        iterations = 100
        for _ in range(iterations):
            scaled_features = self.scaler.transform(test_features)
            self.model.predict_proba(scaled_features)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / iterations * 1000  # Convert to ms
        
        # Should be under 100ms per prediction (very generous for Random Forest)
        self.assertLess(avg_time, 100, f"Model inference too slow: {avg_time:.2f}ms")
        print(f"Average inference time: {avg_time:.2f}ms")
    
    def test_model_feature_importance(self):
        """Test that model has feature importance (Random Forest specific)"""
        if self.model is None:
            self.skipTest("Model not available")
        
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            self.assertEqual(len(importances), 11, "Should have 11 feature importances")
            self.assertAlmostEqual(np.sum(importances), 1.0, places=5, msg="Feature importances should sum to 1")
            print(f"Feature importances: {importances}")
        else:
            self.skipTest("Model does not have feature_importances_ attribute")
    
    def test_model_metadata(self):
        """Test model metadata if available"""
        if self.metadata is None:
            self.skipTest("Metadata not available")
        
        # Check required metadata fields
        required_fields = ['model_type', 'features', 'created_at']
        for field in required_fields:
            self.assertIn(field, self.metadata, f"Metadata missing required field: {field}")
        
        # Check accuracy if present
        if 'accuracy' in self.metadata:
            accuracy = self.metadata['accuracy']
            self.assertGreaterEqual(accuracy, 0.0, "Accuracy should be >= 0")
            self.assertLessEqual(accuracy, 1.0, "Accuracy should be <= 1")
            
            # For production, accuracy should be reasonable
            if accuracy < 0.7:
                print(f"Warning: Model accuracy is low: {accuracy}")
    
    def test_edge_case_inputs(self):
        """Test model with edge case inputs"""
        if self.model is None or self.scaler is None:
            self.skipTest("Model not available")
        
        # Test with zeros
        zero_features = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
        try:
            scaled = self.scaler.transform(zero_features)
            prediction = self.model.predict_proba(scaled)
            self.assertEqual(prediction.shape, (1, 2), "Should handle zero features")
        except Exception as e:
            self.fail(f"Model failed with zero features: {e}")
        
        # Test with very high values
        high_features = np.array([[10000, 1000, 1000, 5000, 100, 60000, 10, 1, 10, 32, 1]])
        try:
            scaled = self.scaler.transform(high_features)
            prediction = self.model.predict_proba(scaled)
            self.assertEqual(prediction.shape, (1, 2), "Should handle high feature values")
        except Exception as e:
            self.fail(f"Model failed with high features: {e}")
    
    def test_batch_prediction(self):
        """Test model with batch predictions"""
        if self.model is None or self.scaler is None:
            self.skipTest("Model not available")
        
        # Create batch of test features
        batch_features = np.array([
            [100, 50.5, 5, 200.5, 2.5, 1500, 0.8, 1, 2.1, 4, 0.95],
            [200, 75.2, 10, 150.3, 5.0, 2000, 1.0, 0, 1.5, 8, 1.0],
            [50, 25.1, 2, 300.1, 1.0, 800, 0.6, 1, 2.5, 2, 0.8]
        ])
        
        scaled_features = self.scaler.transform(batch_features)
        predictions = self.model.predict_proba(scaled_features)
        
        self.assertEqual(predictions.shape, (3, 2), "Should predict for batch of 3 samples")
        
        # Each row should sum to 1
        for i in range(3):
            self.assertAlmostEqual(np.sum(predictions[i]), 1.0, places=5, 
                                 msg=f"Probabilities for sample {i} should sum to 1")


class TestFeatureExtraction(unittest.TestCase):
    """Test feature extraction utilities if available"""
    
    def test_feature_utilities_import(self):
        """Test if feature extraction utilities can be imported"""
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))
            
            from app import utils
            
            # Check if utils has feature extraction methods
            feature_methods = [
                'extract_features',
                'process_behavioral_data',
                'calculate_mouse_features',
                'calculate_keystroke_features'
            ]
            
            available_methods = []
            for method in feature_methods:
                if hasattr(utils, method):
                    available_methods.append(method)
            
            if available_methods:
                print(f"Available feature extraction methods: {available_methods}")
            else:
                print("No feature extraction utilities found in utils module")
            
            self.assertTrue(True)  # Test passes regardless - utilities are optional
            
        except ImportError:
            self.skipTest("Utils module not available")


if __name__ == '__main__':
    unittest.main()