#!/usr/bin/env python3
"""
Machine Learning Model Testing Suite
Tests ML model functionality, inference, and feature engineering
"""

import os
import sys
import numpy as np
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_model_loading():
    """Test ML model loading and initialization"""
    print("🤖 Testing ML Model Loading...")
    
    try:
        from app import create_app
        from app.ml import load_model, is_model_loaded, get_model_info
        
        app = create_app('testing')
        
        with app.app_context():
            # Test model loading
            result = load_model()
            assert result, "Model loading should return True"
            
            # Test model status
            loaded = is_model_loaded()
            assert loaded, "Model should be loaded"
            
            # Test model info
            info = get_model_info()
            assert info is not None, "Model info should be available"
            assert 'algorithm' in info, "Model info should contain algorithm"
            
            print(f"   ✅ Model loaded: {info.get('algorithm', 'Unknown')}")
            print(f"   📊 Features: {info.get('features', 'Unknown')}")
            print(f"   📈 Accuracy: {info.get('accuracy', 'N/A')}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Model loading test failed: {e}")
        return False


def test_feature_extraction():
    """Test feature extraction from behavioral data"""
    print("🔍 Testing Feature Extraction...")
    
    try:
        from app import create_app
        from app.ml import extract_features
        
        app = create_app('testing')
        
        with app.app_context():
            # Test with valid behavioral data
            test_data = {
                'mouseMovements': [
                    {'x': 100, 'y': 150, 'timestamp': 1000},
                    {'x': 120, 'y': 155, 'timestamp': 1100},
                    {'x': 140, 'y': 160, 'timestamp': 1200},
                    {'x': 160, 'y': 165, 'timestamp': 1300},
                    {'x': 180, 'y': 170, 'timestamp': 1400}
                ],
                'keystrokes': [
                    {'key': 'a', 'timestamp': 2000},
                    {'key': 'b', 'timestamp': 2150},
                    {'key': 'c', 'timestamp': 2300},
                    {'key': 'd', 'timestamp': 2450}
                ],
                'sessionDuration': 5000,
                'fingerprint': {
                    'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                    'webglSupport': True,
                    'canvasFingerprint': 'test_canvas_data_123',
                    'plugins': ['Chrome PDF Plugin']
                }
            }
            
            features = extract_features(test_data)
            
            # Validate features
            assert isinstance(features, dict), "Features should be a dictionary"
            assert len(features) >= 10, f"Expected at least 10 features, got {len(features)}"
            
            # Check feature ranges (should be normalized)
            for feature_name, feature_value in features.items():
                if feature_value is not None:
                    assert isinstance(feature_value, (int, float)), f"Feature {feature_name} should be numeric, got {type(feature_value)}"
                    # Most features should be in reasonable range (0-10 for counts, 0-1 for normalized)
                    assert -1 <= feature_value <= 100, f"Feature {feature_name} out of range: {feature_value}"
            
            print(f"   ✅ Features extracted: {len(features)} dimensions")
            sample_features = list(features.items())[:5]
            print(f"   📊 Feature sample: {[(k, f'{v:.3f}' if isinstance(v, (int, float)) else str(v)) for k, v in sample_features]}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Feature extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prediction_inference():
    """Test ML model prediction and inference"""
    print("🎯 Testing ML Prediction Inference...")
    
    try:
        from app import create_app
        from app.ml import predict_human_probability, extract_features
        
        app = create_app('testing')
        
        with app.app_context():
            # Test human-like behavior
            human_data = {
                'mouseMovements': [
                    {'x': 100 + i*20 + np.random.randint(-5, 5), 
                     'y': 150 + i*10 + np.random.randint(-3, 3), 
                     'timestamp': 1000 + i*200 + np.random.randint(-50, 50)} 
                    for i in range(30)
                ],
                'keystrokes': [
                    {'key': chr(97 + i), 'timestamp': 3000 + i*180 + np.random.randint(-30, 30)} 
                    for i in range(10)
                ],
                'sessionDuration': 45000,
                'fingerprint': {
                    'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'webglSupport': True,
                    'canvasFingerprint': 'complex_canvas_fingerprint_with_many_details_123456',
                    'plugins': ['Chrome PDF Plugin', 'Widevine Content Decryption Module'],
                    'language': 'en-US',
                    'platform': 'MacIntel'
                }
            }
            
            # Extract features and predict
            human_features = extract_features(human_data)
            human_result = predict_human_probability(human_features)
            
            # Validate prediction format
            assert isinstance(human_result, dict), "Prediction should return a dictionary"
            assert 'isHuman' in human_result, "Prediction should contain 'isHuman'"
            assert 'confidence' in human_result, "Prediction should contain 'confidence'"
            assert isinstance(human_result['isHuman'], bool), "isHuman should be boolean"
            assert isinstance(human_result['confidence'], (int, float)), "Confidence should be numeric"
            assert 0 <= human_result['confidence'] <= 1, "Confidence should be between 0 and 1"
            
            print(f"   ✅ Human-like prediction: {'Human' if human_result['isHuman'] else 'Bot'}")
            print(f"   📊 Confidence: {human_result['confidence']:.3f}")
            
            # Test bot-like behavior
            bot_data = {
                'mouseMovements': [
                    {'x': 100 + i*10, 'y': 150, 'timestamp': 1000 + i*50} 
                    for i in range(5)  # Very few, linear movements
                ],
                'keystrokes': [
                    {'key': chr(97 + i), 'timestamp': 2000 + i*100} 
                    for i in range(3)  # Very consistent timing
                ],
                'sessionDuration': 2000,  # Very short session
                'fingerprint': {
                    'userAgent': 'HeadlessChrome/91.0.4472.124',
                    'webglSupport': False,
                    'canvasFingerprint': '',
                    'plugins': [],
                    'language': '',
                    'platform': 'Linux x86_64'
                }
            }
            
            bot_features = extract_features(bot_data)
            bot_result = predict_human_probability(bot_features)
            
            print(f"   ✅ Bot-like prediction: {'Human' if bot_result['isHuman'] else 'Bot'}")
            print(f"   📊 Confidence: {bot_result['confidence']:.3f}")
            
            # Performance test
            start_time = time.time()
            for _ in range(100):
                predict_human_probability(human_features)
            end_time = time.time()
            
            avg_inference_time = (end_time - start_time) / 100 * 1000  # ms
            print(f"   ⚡ Average inference time: {avg_inference_time:.2f}ms")
            
            # Inference should be fast (< 50ms)
            assert avg_inference_time < 50, f"Inference too slow: {avg_inference_time:.2f}ms"
            
            return True
            
    except Exception as e:
        print(f"   ❌ Prediction inference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and robustness"""
    print("🔬 Testing Edge Cases and Robustness...")
    
    try:
        from app import create_app
        from app.ml import extract_features, predict_human_probability
        
        app = create_app('testing')
        
        with app.app_context():
            # Test empty data
            empty_data = {}
            empty_features = extract_features(empty_data)
            empty_result = predict_human_probability(empty_features)
            
            assert isinstance(empty_result, dict), "Should handle empty data gracefully"
            print("   ✅ Empty data handling works")
            
            # Test minimal data
            minimal_data = {
                'mouseMovements': [{'x': 100, 'y': 150, 'timestamp': 1000}],
                'keystrokes': [],
                'sessionDuration': 1000
            }
            minimal_features = extract_features(minimal_data)
            minimal_result = predict_human_probability(minimal_features)
            
            assert isinstance(minimal_result, dict), "Should handle minimal data gracefully"
            print("   ✅ Minimal data handling works")
            
            # Test with None values
            none_features = [None] * 11
            none_result = predict_human_probability(none_features)
            
            assert isinstance(none_result, dict), "Should handle None features gracefully"
            print("   ✅ None feature handling works")
            
            # Test with extreme values
            extreme_data = {
                'mouseMovements': [
                    {'x': 999999, 'y': 999999, 'timestamp': 1000},
                    {'x': -999999, 'y': -999999, 'timestamp': 2000}
                ],
                'keystrokes': [
                    {'key': 'a', 'timestamp': 1000},
                    {'key': 'b', 'timestamp': 999999999}
                ],
                'sessionDuration': 999999999
            }
            extreme_features = extract_features(extreme_data)
            extreme_result = predict_human_probability(extreme_features)
            
            assert isinstance(extreme_result, dict), "Should handle extreme values gracefully"
            print("   ✅ Extreme value handling works")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Edge case test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_consistency():
    """Test model prediction consistency"""
    print("🔄 Testing Model Consistency...")
    
    try:
        from app import create_app
        from app.ml import extract_features, predict_human_probability
        
        app = create_app('testing')
        
        with app.app_context():
            # Test same input multiple times
            test_data = {
                'mouseMovements': [
                    {'x': 100, 'y': 150, 'timestamp': 1000},
                    {'x': 120, 'y': 155, 'timestamp': 1100},
                    {'x': 140, 'y': 160, 'timestamp': 1200}
                ],
                'keystrokes': [
                    {'key': 'a', 'timestamp': 2000},
                    {'key': 'b', 'timestamp': 2150}
                ],
                'sessionDuration': 5000
            }
            
            features = extract_features(test_data)
            
            # Run prediction multiple times
            results = []
            for _ in range(10):
                result = predict_human_probability(features)
                results.append(result)
            
            # Check consistency
            first_result = results[0]
            for result in results[1:]:
                assert result['isHuman'] == first_result['isHuman'], "Predictions should be consistent"
                assert abs(result['confidence'] - first_result['confidence']) < 0.001, "Confidence should be consistent"
            
            print(f"   ✅ Model predictions are consistent across {len(results)} runs")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Model consistency test failed: {e}")
        return False


def test_model_files():
    """Test model file integrity"""
    print("📁 Testing Model File Integrity...")
    
    try:
        model_dir = Path('models')
        
        # Check required files exist
        required_files = [
            'passive_captcha_rf.pkl',
            'passive_captcha_rf_scaler.pkl',
            'passive_captcha_rf_metadata.json'
        ]
        
        for filename in required_files:
            file_path = model_dir / filename
            assert file_path.exists(), f"Required model file missing: {filename}"
            assert file_path.stat().st_size > 0, f"Model file is empty: {filename}"
        
        print(f"   ✅ All {len(required_files)} model files present and non-empty")
        
        # Check metadata
        import json
        metadata_path = model_dir / 'passive_captcha_rf_metadata.json'
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        required_metadata_keys = ['model_version', 'feature_names', 'training_date']
        for key in required_metadata_keys:
            assert key in metadata, f"Missing metadata key: {key}"
        
        print(f"   ✅ Model metadata is valid")
        print(f"   📊 Model version: {metadata.get('model_version', 'Unknown')}")
        print(f"   📅 Training date: {metadata.get('training_date', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model file integrity test failed: {e}")
        return False


def main():
    """Run all ML model tests"""
    print("🧪 ML Model Testing Suite")
    print("=" * 50)
    
    tests = [
        test_model_loading,
        test_feature_extraction,
        test_prediction_inference,
        test_edge_cases,
        test_model_consistency,
        test_model_files
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
        print("🎉 All ML model tests passed!")
        return True
    else:
        print("❌ Some ML model tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)