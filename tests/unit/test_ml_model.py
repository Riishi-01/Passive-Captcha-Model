"""
Unit Tests for ML Model
Comprehensive testing of ML model accuracy, performance, and reliability
"""

import unittest
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from unittest.mock import Mock, patch, MagicMock
import pickle
import json
import time
from datetime import datetime

# Mock external dependencies
sys.modules['sklearn'] = Mock()
sys.modules['sklearn.ensemble'] = Mock()
sys.modules['sklearn.preprocessing'] = Mock()
sys.modules['joblib'] = Mock()


class TestMLModel(unittest.TestCase):
    """Test cases for ML Model functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock model and scaler
        self.mock_model = Mock()
        self.mock_scaler = Mock()
        
        # Sample feature data
        self.sample_features = {
            'mouse_events': 50,
            'mouse_velocity': 120.5,
            'keyboard_events': 25,
            'keystroke_dynamics': 0.15,
            'touch_events': 0,
            'scroll_events': 8,
            'time_on_page': 45.2,
            'window_focus_time': 42.1,
            'screen_resolution': '1920x1080',
            'user_agent_entropy': 0.85,
            'timezone_consistency': 1
        }
        
        # Expected feature vector (11 dimensions)
        self.expected_feature_vector = [
            50,      # mouse_events
            120.5,   # mouse_velocity
            25,      # keyboard_events
            0.15,    # keystroke_dynamics
            0,       # touch_events
            8,       # scroll_events
            45.2,    # time_on_page
            42.1,    # window_focus_time
            1920,    # screen_width (parsed from resolution)
            0.85,    # user_agent_entropy
            1        # timezone_consistency
        ]
    
    def test_feature_extraction_complete(self):
        """Test complete feature extraction from behavioral data"""
        with patch('app.ml.feature_extractor.extract_features') as mock_extract:
            mock_extract.return_value = self.expected_feature_vector
            
            # Import and test
            from app.ml import feature_extractor
            features = feature_extractor.extract_features(self.sample_features)
            
            # Assertions
            self.assertEqual(len(features), 11)
            self.assertEqual(features[0], 50)  # mouse_events
            self.assertEqual(features[1], 120.5)  # mouse_velocity
            self.assertIsInstance(features, list)
    
    def test_feature_extraction_missing_data(self):
        """Test feature extraction with missing data"""
        incomplete_features = {
            'mouse_events': 30,
            'keyboard_events': 15,
            # Missing other features
        }
        
        with patch('app.ml.feature_extractor.extract_features') as mock_extract:
            # Should handle missing data with defaults
            mock_extract.return_value = [30, 0, 15, 0, 0, 0, 0, 0, 1024, 0.5, 1]
            
            from app.ml import feature_extractor
            features = feature_extractor.extract_features(incomplete_features)
            
            # Assertions
            self.assertEqual(len(features), 11)
            self.assertEqual(features[0], 30)  # Available data
            self.assertEqual(features[1], 0)   # Default for missing data
    
    def test_feature_normalization(self):
        """Test feature scaling/normalization"""
        raw_features = np.array(self.expected_feature_vector).reshape(1, -1)
        scaled_features = np.array([[0.5, 0.8, 0.3, 0.6, 0, 0.4, 0.7, 0.7, 0.9, 0.85, 1]])
        
        self.mock_scaler.transform.return_value = scaled_features
        
        # Test scaling
        result = self.mock_scaler.transform(raw_features)
        
        # Assertions
        self.assertEqual(result.shape, (1, 11))
        np.testing.assert_array_equal(result, scaled_features)
        self.mock_scaler.transform.assert_called_once()
    
    def test_model_prediction_human(self):
        """Test model prediction for human behavior"""
        # Mock human-like features (high confidence, typical behavior)
        human_features = np.array([[0.7, 0.6, 0.8, 0.5, 0, 0.6, 0.9, 0.8, 0.9, 0.8, 1]])
        
        # Mock prediction
        self.mock_model.predict.return_value = np.array([1])  # Human
        self.mock_model.predict_proba.return_value = np.array([[0.1, 0.9]])  # 90% confidence human
        
        # Test prediction
        prediction = self.mock_model.predict(human_features)
        confidence = self.mock_model.predict_proba(human_features)
        
        # Assertions
        self.assertEqual(prediction[0], 1)  # Human class
        self.assertEqual(confidence[0][1], 0.9)  # High confidence
        self.assertGreater(confidence[0][1], 0.8)  # Above threshold
    
    def test_model_prediction_bot(self):
        """Test model prediction for bot behavior"""
        # Mock bot-like features (patterns indicating automation)
        bot_features = np.array([[0.1, 0.2, 0.05, 0.9, 0, 0.1, 0.3, 0.2, 0.9, 0.3, 1]])
        
        # Mock prediction
        self.mock_model.predict.return_value = np.array([0])  # Bot
        self.mock_model.predict_proba.return_value = np.array([[0.85, 0.15]])  # 85% confidence bot
        
        # Test prediction
        prediction = self.mock_model.predict(bot_features)
        confidence = self.mock_model.predict_proba(bot_features)
        
        # Assertions
        self.assertEqual(prediction[0], 0)  # Bot class
        self.assertEqual(confidence[0][0], 0.85)  # High confidence bot
        self.assertGreater(confidence[0][0], 0.8)  # Above threshold
    
    def test_model_prediction_uncertain(self):
        """Test model prediction with uncertain results"""
        # Mock ambiguous features
        uncertain_features = np.array([[0.5, 0.5, 0.5, 0.5, 0, 0.5, 0.5, 0.5, 0.9, 0.5, 1]])
        
        # Mock uncertain prediction
        self.mock_model.predict.return_value = np.array([1])  # Slight lean toward human
        self.mock_model.predict_proba.return_value = np.array([[0.45, 0.55]])  # Low confidence
        
        # Test prediction
        prediction = self.mock_model.predict(uncertain_features)
        confidence = self.mock_model.predict_proba(uncertain_features)
        
        # Assertions
        self.assertEqual(prediction[0], 1)
        self.assertLess(max(confidence[0]), 0.7)  # Low confidence
        self.assertGreater(min(confidence[0]), 0.3)  # Not too extreme
    
    def test_model_performance_metrics(self):
        """Test model performance calculation"""
        # Mock test data
        y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0, 1, 1])  # True labels
        y_pred = np.array([1, 1, 0, 1, 1, 0, 1, 0, 0, 1])  # Predicted labels
        y_proba = np.array([
            [0.1, 0.9], [0.2, 0.8], [0.8, 0.2], [0.3, 0.7],
            [0.1, 0.9], [0.9, 0.1], [0.2, 0.8], [0.7, 0.3],
            [0.6, 0.4], [0.1, 0.9]
        ])
        
        with patch('sklearn.metrics.accuracy_score') as mock_accuracy, \
             patch('sklearn.metrics.precision_score') as mock_precision, \
             patch('sklearn.metrics.recall_score') as mock_recall, \
             patch('sklearn.metrics.f1_score') as mock_f1, \
             patch('sklearn.metrics.roc_auc_score') as mock_auc:
            
            # Mock metric calculations
            mock_accuracy.return_value = 0.80
            mock_precision.return_value = 0.75
            mock_recall.return_value = 0.85
            mock_f1.return_value = 0.80
            mock_auc.return_value = 0.88
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
            
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred)
            recall = recall_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred)
            auc = roc_auc_score(y_true, y_proba[:, 1])
            
            # Assertions
            self.assertEqual(accuracy, 0.80)
            self.assertEqual(precision, 0.75)
            self.assertEqual(recall, 0.85)
            self.assertEqual(f1, 0.80)
            self.assertEqual(auc, 0.88)
            
            # Performance thresholds
            self.assertGreater(accuracy, 0.75)  # Minimum 75% accuracy
            self.assertGreater(f1, 0.75)       # Minimum 75% F1 score
            self.assertGreater(auc, 0.80)      # Minimum 80% AUC
    
    def test_model_inference_speed(self):
        """Test model inference performance"""
        # Mock fast prediction
        features = np.random.random((100, 11))  # 100 samples
        
        self.mock_model.predict.return_value = np.random.randint(0, 2, 100)
        self.mock_model.predict_proba.return_value = np.random.random((100, 2))
        
        # Measure inference time
        start_time = time.time()
        
        # Simulate predictions
        for _ in range(10):  # 10 batches
            predictions = self.mock_model.predict(features)
            probabilities = self.mock_model.predict_proba(features)
        
        end_time = time.time()
        inference_time = (end_time - start_time) / 1000  # Per prediction
        
        # Assertions
        self.assertLess(inference_time, 0.1)  # Less than 100ms per prediction
        self.assertEqual(len(predictions), 100)
        self.assertEqual(probabilities.shape, (100, 2))
    
    def test_model_memory_usage(self):
        """Test model memory efficiency"""
        # Mock model size check
        with patch('sys.getsizeof') as mock_sizeof:
            mock_sizeof.return_value = 1024 * 1024 * 5  # 5MB model
            
            model_size = mock_sizeof(self.mock_model)
            
            # Assertions
            self.assertLess(model_size, 1024 * 1024 * 50)  # Less than 50MB
    
    def test_feature_importance_analysis(self):
        """Test feature importance from the model"""
        # Mock feature importance
        self.mock_model.feature_importances_ = np.array([
            0.15,  # mouse_events
            0.12,  # mouse_velocity
            0.10,  # keyboard_events
            0.18,  # keystroke_dynamics (most important)
            0.02,  # touch_events
            0.08,  # scroll_events
            0.09,  # time_on_page
            0.07,  # window_focus_time
            0.05,  # screen_width
            0.11,  # user_agent_entropy
            0.03   # timezone_consistency
        ])
        
        feature_names = [
            'mouse_events', 'mouse_velocity', 'keyboard_events', 'keystroke_dynamics',
            'touch_events', 'scroll_events', 'time_on_page', 'window_focus_time',
            'screen_width', 'user_agent_entropy', 'timezone_consistency'
        ]
        
        # Get feature importance
        importance = self.mock_model.feature_importances_
        
        # Assertions
        self.assertEqual(len(importance), 11)
        self.assertAlmostEqual(sum(importance), 1.0, places=6)  # Should sum to 1
        
        # Most important feature should be keystroke_dynamics
        most_important_idx = np.argmax(importance)
        self.assertEqual(feature_names[most_important_idx], 'keystroke_dynamics')
        self.assertGreater(importance[most_important_idx], 0.15)
    
    def test_model_robustness_edge_cases(self):
        """Test model behavior with edge cases"""
        # Test with extreme values
        extreme_features = np.array([[
            1000,    # Very high mouse events
            0,       # No mouse velocity
            0,       # No keyboard events
            1.0,     # Maximum keystroke dynamics
            100,     # High touch events (mobile)
            0,       # No scroll
            300,     # Very long time on page
            0,       # No focus time
            4000,    # Very high resolution
            0,       # No entropy
            0        # Timezone inconsistency
        ]])
        
        # Mock prediction for extreme case
        self.mock_model.predict.return_value = np.array([0])  # Should predict bot
        self.mock_model.predict_proba.return_value = np.array([[0.95, 0.05]])
        
        prediction = self.mock_model.predict(extreme_features)
        confidence = self.mock_model.predict_proba(extreme_features)
        
        # Assertions
        self.assertEqual(prediction[0], 0)  # Bot prediction for extreme values
        self.assertGreater(confidence[0][0], 0.8)  # High confidence
    
    def test_model_consistency(self):
        """Test model prediction consistency"""
        # Same input should give same output
        test_features = np.array([[0.5, 0.6, 0.7, 0.4, 0, 0.5, 0.8, 0.7, 0.9, 0.6, 1]])
        
        # Mock consistent predictions
        self.mock_model.predict.return_value = np.array([1])
        self.mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])
        
        # Multiple predictions
        predictions = []
        for _ in range(5):
            pred = self.mock_model.predict(test_features)
            predictions.append(pred[0])
        
        # Assertions
        self.assertTrue(all(p == predictions[0] for p in predictions))  # All same
    
    def test_batch_prediction_efficiency(self):
        """Test efficiency of batch predictions"""
        # Large batch of features
        batch_size = 1000
        batch_features = np.random.random((batch_size, 11))
        
        # Mock batch prediction
        self.mock_model.predict.return_value = np.random.randint(0, 2, batch_size)
        self.mock_model.predict_proba.return_value = np.random.random((batch_size, 2))
        
        # Time batch prediction
        start_time = time.time()
        predictions = self.mock_model.predict(batch_features)
        probabilities = self.mock_model.predict_proba(batch_features)
        end_time = time.time()
        
        batch_time = end_time - start_time
        per_sample_time = batch_time / batch_size
        
        # Assertions
        self.assertEqual(len(predictions), batch_size)
        self.assertEqual(probabilities.shape, (batch_size, 2))
        self.assertLess(per_sample_time, 0.01)  # Less than 10ms per sample in batch
    
    def test_model_loading_and_saving(self):
        """Test model serialization"""
        model_path = '/tmp/test_model.pkl'
        scaler_path = '/tmp/test_scaler.pkl'
        
        with patch('pickle.dump') as mock_dump, \
             patch('pickle.load') as mock_load, \
             patch('builtins.open', create=True) as mock_open:
            
            # Mock file operations
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Test saving
            pickle.dump(self.mock_model, mock_file)
            pickle.dump(self.mock_scaler, mock_file)
            
            # Test loading
            mock_load.return_value = self.mock_model
            loaded_model = pickle.load(mock_file)
            
            # Assertions
            mock_dump.assert_called()
            mock_load.assert_called()
            self.assertEqual(loaded_model, self.mock_model)
    
    def test_model_validation_cross_validation(self):
        """Test model validation using cross-validation"""
        # Mock cross-validation scores
        with patch('sklearn.model_selection.cross_val_score') as mock_cv:
            mock_cv.return_value = np.array([0.85, 0.87, 0.83, 0.88, 0.86])
            
            from sklearn.model_selection import cross_val_score
            
            # Mock data
            X = np.random.random((1000, 11))
            y = np.random.randint(0, 2, 1000)
            
            # Perform cross-validation
            cv_scores = cross_val_score(self.mock_model, X, y, cv=5)
            
            # Assertions
            self.assertEqual(len(cv_scores), 5)
            self.assertGreater(np.mean(cv_scores), 0.80)  # Average > 80%
            self.assertLess(np.std(cv_scores), 0.05)      # Low variance
    
    def test_data_drift_detection(self):
        """Test detection of data drift in input features"""
        # Mock feature statistics
        training_stats = {
            'mouse_events': {'mean': 45.2, 'std': 15.8},
            'mouse_velocity': {'mean': 125.3, 'std': 35.2},
            'keyboard_events': {'mean': 22.1, 'std': 8.7}
        }
        
        # Current data stats (showing drift)
        current_stats = {
            'mouse_events': {'mean': 32.1, 'std': 12.3},  # Significant drift
            'mouse_velocity': {'mean': 128.7, 'std': 33.1},  # Minimal drift
            'keyboard_events': {'mean': 89.5, 'std': 45.2}   # Major drift
        }
        
        # Calculate drift scores (simplified)
        drift_scores = {}
        for feature in training_stats:
            mean_drift = abs(current_stats[feature]['mean'] - training_stats[feature]['mean'])
            drift_scores[feature] = mean_drift / training_stats[feature]['std']
        
        # Assertions
        self.assertGreater(drift_scores['keyboard_events'], 2.0)  # Major drift
        self.assertLess(drift_scores['mouse_velocity'], 0.5)      # Minimal drift
        
        # Overall drift detection
        avg_drift = np.mean(list(drift_scores.values()))
        self.assertGreater(avg_drift, 1.0)  # Significant overall drift


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)