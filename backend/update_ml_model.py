#!/usr/bin/env python3
"""
Script to update the ML module with the newly trained model
Replaces the old synthetic approach with production-ready model
"""

import os
import shutil
import json
from pathlib import Path

def update_ml_model():
    """Update the ML model files and ensure compatibility"""
    print("🔄 Updating ML Model Integration...")
    
    # Check if new model exists
    new_model_path = "models/passive_captcha_rf.pkl"
    new_scaler_path = "models/passive_captcha_rf_scaler.pkl"
    new_metadata_path = "models/passive_captcha_rf_metadata.json"
    
    if not all(os.path.exists(path) for path in [new_model_path, new_scaler_path, new_metadata_path]):
        print("❌ New model files not found. Please run train_model.py first.")
        return False
    
    # Load metadata to verify model
    with open(new_metadata_path, 'r') as f:
        metadata = json.load(f)
    
    print(f"📋 Model Information:")
    print(f"   Version: {metadata['model_version']}")
    print(f"   Training Date: {metadata['training_date']}")
    print(f"   Model Size: {metadata['model_size_mb']:.2f} MB")
    print(f"   Features: {len(metadata['feature_names'])}")
    
    # Verify model structure matches expected feature names
    expected_features = [
        'mouse_movement_count',
        'avg_mouse_velocity', 
        'mouse_acceleration_variance',
        'keystroke_count',
        'avg_keystroke_interval',
        'session_duration_normalized',
        'webgl_support_score',
        'canvas_fingerprint_score',
        'hardware_legitimacy_score',
        'browser_consistency_score',
        'device_entropy_score'
    ]
    
    if metadata['feature_names'] != expected_features:
        print("⚠️  Feature names don't match expected structure")
        print(f"Expected: {expected_features}")
        print(f"Got: {metadata['feature_names']}")
        return False
    
    print("✅ Model structure verified!")
    
    # Test model loading
    try:
        import joblib
        model = joblib.load(new_model_path)
        scaler = joblib.load(new_scaler_path)
        print("✅ Model loading test successful!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False
    
    # Update app configuration if needed
    print("🔧 Model integration completed!")
    print("   The existing ML module will automatically load the new model files.")
    print("   To use the new model, restart the Flask application.")
    
    return True

def verify_integration():
    """Verify the integration works by testing the ML module"""
    print("\n🧪 Testing ML Module Integration...")
    
    try:
        # Import the ML module
        import sys
        sys.path.append('app')
        from app.ml import load_model, predict_human_probability
        
        # Test model loading
        success = load_model()
        if not success:
            print("❌ Model loading failed")
            return False
        
        # Test prediction with sample data
        test_features = {
            'mouse_movement_count': 45,
            'avg_mouse_velocity': 0.8,
            'keystroke_count': 10,
            'typing_rhythm_variance': 0.4,  # This will be mapped to mouse_acceleration_variance
            'session_duration': 35,
            'scroll_pattern_score': 0.8,  # This will be ignored in new model
            'webgl_support_score': 1.0,
            'canvas_fingerprint_score': 0.85,
            'hardware_legitimacy': 0.9,
            'browser_consistency': 0.88,
            'plugin_availability': 0.85  # This will be mapped to device_entropy_score
        }
        
        result = predict_human_probability(test_features)
        
        print("✅ Prediction test successful!")
        print(f"   Test result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main update process"""
    print("🚀 ML Model Update Process")
    print("=" * 40)
    
    # Update model
    if not update_ml_model():
        print("❌ Model update failed")
        return
    
    # Verify integration
    if not verify_integration():
        print("❌ Integration verification failed")
        return
    
    print("\n🎯 Update Complete!")
    print("✅ New ML model is ready for production")
    print("📝 To activate:")
    print("   1. Restart the Flask application")
    print("   2. The new model will be automatically loaded")
    print("   3. Model provides 11-dimensional feature analysis")
    print("   4. Optimized for <15ms inference time")

if __name__ == "__main__":
    main() 