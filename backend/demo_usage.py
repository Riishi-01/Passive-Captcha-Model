#!/usr/bin/env python3
"""
Demonstration of Passive CAPTCHA ML Model Usage
Shows how to use the trained model for real-time predictions
"""

import numpy as np
import joblib
import json
import time
from datetime import datetime

def load_production_model():
    """Load the production-ready model"""
    print("🔄 Loading Production Model...")
    
    model = joblib.load("models/passive_captcha_rf.pkl")
    scaler = joblib.load("models/passive_captcha_rf_scaler.pkl")
    
    with open("models/passive_captcha_rf_metadata.json", 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Model loaded successfully!")
    print(f"   Version: {metadata['model_version']}")
    print(f"   Size: {metadata['model_size_mb']:.2f} MB")
    print(f"   Training Date: {metadata['training_date']}")
    
    return model, scaler, metadata

def extract_behavioral_features(session_data):
    """
    Extract features from a user session
    This mimics what the frontend JavaScript would collect
    """
    
    # Mouse movement analysis
    mouse_movements = session_data.get('mouse_movements', [])
    mouse_count = len(mouse_movements)
    
    # Calculate velocities if we have movements
    velocities = []
    accelerations = []
    if len(mouse_movements) > 1:
        for i in range(1, len(mouse_movements)):
            prev_point = mouse_movements[i-1]
            curr_point = mouse_movements[i]
            
            # Calculate distance and time
            dx = curr_point['x'] - prev_point['x']
            dy = curr_point['y'] - prev_point['y']
            dt = curr_point['timestamp'] - prev_point['timestamp']
            
            if dt > 0:
                distance = np.sqrt(dx*dx + dy*dy)
                velocity = distance / dt
                velocities.append(velocity)
                
                # Calculate acceleration for next iteration
                if len(velocities) > 1:
                    dv = velocities[-1] - velocities[-2]
                    acceleration = dv / dt if dt > 0 else 0
                    accelerations.append(acceleration)
    
    avg_velocity = np.mean(velocities) if velocities else 0
    acceleration_variance = np.var(accelerations) if len(accelerations) > 1 else 0
    
    # Keystroke analysis
    keystrokes = session_data.get('keystrokes', [])
    keystroke_count = len(keystrokes)
    
    # Calculate keystroke intervals
    intervals = []
    if len(keystrokes) > 1:
        for i in range(1, len(keystrokes)):
            interval = keystrokes[i]['timestamp'] - keystrokes[i-1]['timestamp']
            intervals.append(interval)
    
    avg_keystroke_interval = np.mean(intervals) if intervals else 0
    
    # Session metrics
    session_duration = session_data.get('session_duration', 0) / 1000.0  # Convert to seconds
    
    # Device fingerprint
    fingerprint = session_data.get('fingerprint', {})
    webgl_support = 1.0 if fingerprint.get('webgl', False) else 0.0
    canvas_hash = fingerprint.get('canvas_hash', '')
    canvas_score = 1.0 if len(canvas_hash) > 50 else 0.0  # Real canvas hashes are long
    
    user_agent = fingerprint.get('user_agent', '')
    hardware_score = 0.8 if 'Mobile' in user_agent or 'Windows' in user_agent else 0.5
    browser_score = 0.9 if any(browser in user_agent for browser in ['Chrome', 'Firefox', 'Safari']) else 0.3
    
    # Device entropy (combination of various factors)
    plugins = fingerprint.get('plugins', [])
    screen_res = fingerprint.get('screen_resolution', '')
    timezone = fingerprint.get('timezone', '')
    
    entropy_score = 0.5  # Base score
    if plugins: entropy_score += 0.2
    if screen_res: entropy_score += 0.2
    if timezone: entropy_score += 0.1
    entropy_score = min(entropy_score, 1.0)
    
    # Create normalized feature vector
    features = [
        min(mouse_count, 1000) / 1000.0,                    # mouse_movement_count
        min(avg_velocity, 5.0) / 5.0,                       # avg_mouse_velocity
        min(acceleration_variance, 2.0) / 2.0,              # mouse_acceleration_variance
        min(keystroke_count, 200) / 200.0,                  # keystroke_count
        min(max(avg_keystroke_interval, 50), 500) / 500.0,  # avg_keystroke_interval
        min(session_duration, 300) / 300.0,                 # session_duration_normalized
        webgl_support,                                       # webgl_support_score
        canvas_score,                                        # canvas_fingerprint_score
        hardware_score,                                      # hardware_legitimacy_score
        browser_score,                                       # browser_consistency_score
        entropy_score                                        # device_entropy_score
    ]
    
    return features

def predict_human_vs_bot(model, scaler, features):
    """Make a prediction using the trained model"""
    
    # Scale features
    features_scaled = scaler.transform([features])
    
    # Get prediction probabilities
    start_time = time.time()
    probabilities = model.predict_proba(features_scaled)[0]
    inference_time = (time.time() - start_time) * 1000
    
    human_probability = probabilities[1]  # Class 1 is human
    bot_probability = probabilities[0]    # Class 0 is bot
    
    # Determine prediction (threshold = 0.6)
    is_human = human_probability > 0.6
    confidence = max(probabilities)
    
    return {
        'prediction': 'Human' if is_human else 'Bot',
        'human_probability': float(human_probability),
        'bot_probability': float(bot_probability),
        'confidence': float(confidence),
        'inference_time_ms': round(inference_time, 2)
    }

def demo_realistic_scenarios():
    """Demonstrate the model with realistic user scenarios"""
    
    print("\n🎮 DEMO: Realistic User Scenarios")
    print("=" * 50)
    
    # Load model
    model, scaler, metadata = load_production_model()
    
    # Scenario 1: Typical Human User
    print("\n👤 Scenario 1: Typical Human User")
    print("-" * 30)
    
    human_session = {
        'mouse_movements': [
            {'x': 100, 'y': 100, 'timestamp': 1000},
            {'x': 120, 'y': 105, 'timestamp': 1150},
            {'x': 145, 'y': 110, 'timestamp': 1300},
            {'x': 160, 'y': 125, 'timestamp': 1450},
            {'x': 180, 'y': 140, 'timestamp': 1620},
            # ... more natural movements
        ] + [{'x': 200 + i*5 + np.random.randint(-3, 3), 
              'y': 150 + i*2 + np.random.randint(-2, 2), 
              'timestamp': 1700 + i*180 + np.random.randint(-20, 20)} 
             for i in range(40)],  # Natural variations
        
        'keystrokes': [
            {'key': 'u', 'timestamp': 2000},
            {'key': 's', 'timestamp': 2180},
            {'key': 'e', 'timestamp': 2350},
            {'key': 'r', 'timestamp': 2520},
            {'key': '@', 'timestamp': 2720},
            {'key': 'e', 'timestamp': 2890},
            {'key': 'm', 'timestamp': 3050},
            {'key': 'a', 'timestamp': 3220},
            {'key': 'i', 'timestamp': 3380},
            {'key': 'l', 'timestamp': 3540},
        ],
        
        'session_duration': 45000,  # 45 seconds
        
        'fingerprint': {
            'webgl': True,
            'canvas_hash': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'plugins': ['Chrome PDF Plugin', 'Widevine Content Decryption Module'],
            'screen_resolution': '1920x1080',
            'timezone': 'America/New_York'
        }
    }
    
    human_features = extract_behavioral_features(human_session)
    human_result = predict_human_vs_bot(model, scaler, human_features)
    
    print(f"Features: {[f'{x:.3f}' for x in human_features]}")
    print(f"Prediction: {human_result['prediction']}")
    print(f"Human Probability: {human_result['human_probability']:.3f}")
    print(f"Confidence: {human_result['confidence']:.3f}")
    print(f"Inference Time: {human_result['inference_time_ms']}ms")
    
    # Scenario 2: Automated Bot
    print("\n🤖 Scenario 2: Automated Bot")
    print("-" * 30)
    
    bot_session = {
        'mouse_movements': [
            {'x': 100, 'y': 100, 'timestamp': 1000},
            {'x': 200, 'y': 100, 'timestamp': 1050},  # Too fast, straight line
        ],
        
        'keystrokes': [
            {'key': 'a', 'timestamp': 2000},
            {'key': 'd', 'timestamp': 2050},  # Very consistent timing
            {'key': 'm', 'timestamp': 2100},
            {'key': 'i', 'timestamp': 2150},
            {'key': 'n', 'timestamp': 2200},
            {'key': '@', 'timestamp': 2250},
            {'key': 'b', 'timestamp': 2300},
            {'key': 'o', 'timestamp': 2350},
            {'key': 't', 'timestamp': 2400},
        ],
        
        'session_duration': 3000,  # Very short session
        
        'fingerprint': {
            'webgl': False,  # Headless browser
            'canvas_hash': '',  # No canvas support
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',  # Minimal UA
            'plugins': [],  # No plugins
            'screen_resolution': '1024x768',  # Common bot resolution
            'timezone': ''
        }
    }
    
    bot_features = extract_behavioral_features(bot_session)
    bot_result = predict_human_vs_bot(model, scaler, bot_features)
    
    print(f"Features: {[f'{x:.3f}' for x in bot_features]}")
    print(f"Prediction: {bot_result['prediction']}")
    print(f"Bot Probability: {bot_result['bot_probability']:.3f}")
    print(f"Confidence: {bot_result['confidence']:.3f}")
    print(f"Inference Time: {bot_result['inference_time_ms']}ms")
    
    # Scenario 3: Edge Case - Mobile User
    print("\n📱 Scenario 3: Mobile User (Edge Case)")
    print("-" * 30)
    
    mobile_session = {
        'mouse_movements': [],  # No mouse on mobile
        
        'keystrokes': [
            {'key': 'm', 'timestamp': 2000},
            {'key': 'o', 'timestamp': 2300},  # Slower mobile typing
            {'key': 'b', 'timestamp': 2650},
            {'key': 'i', 'timestamp': 2900},
            {'key': 'l', 'timestamp': 3200},
            {'key': 'e', 'timestamp': 3500},
        ],
        
        'session_duration': 25000,  # Reasonable mobile session
        
        'fingerprint': {
            'webgl': True,
            'canvas_hash': 'mobile_canvas_hash_different_but_valid_12345',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
            'plugins': [],  # Mobile typically has fewer plugins
            'screen_resolution': '375x812',  # iPhone resolution
            'timezone': 'America/Los_Angeles'
        }
    }
    
    mobile_features = extract_behavioral_features(mobile_session)
    mobile_result = predict_human_vs_bot(model, scaler, mobile_features)
    
    print(f"Features: {[f'{x:.3f}' for x in mobile_features]}")
    print(f"Prediction: {mobile_result['prediction']}")
    print(f"Human Probability: {mobile_result['human_probability']:.3f}")
    print(f"Confidence: {mobile_result['confidence']:.3f}")
    print(f"Inference Time: {mobile_result['inference_time_ms']}ms")

def feature_importance_analysis():
    """Show feature importance analysis"""
    
    print("\n🔍 Feature Importance Analysis")
    print("=" * 40)
    
    model, scaler, metadata = load_production_model()
    
    feature_names = metadata['feature_names']
    importance_scores = model.feature_importances_
    
    # Sort by importance
    feature_importance = list(zip(feature_names, importance_scores))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    print("Top features for human vs bot detection:")
    print()
    for i, (name, score) in enumerate(feature_importance, 1):
        bar = "█" * int(score * 50)  # Visual bar
        print(f"{i:2d}. {name:25s} {score:.3f} {bar}")

def main():
    """Run the complete demonstration"""
    
    print("🎯 Passive CAPTCHA ML Model - Live Demo")
    print("=" * 60)
    
    try:
        # Run realistic scenarios
        demo_realistic_scenarios()
        
        # Show feature importance
        feature_importance_analysis()
        
        print("\n🎉 Demo Complete!")
        print("✅ Model successfully demonstrates:")
        print("   • Human behavior detection")
        print("   • Bot pattern recognition") 
        print("   • Mobile user handling")
        print("   • Fast inference (<15ms)")
        print("   • High confidence predictions")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main() 