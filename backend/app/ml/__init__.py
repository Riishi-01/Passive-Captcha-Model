"""
Machine Learning module for Passive CAPTCHA system
Handles Random Forest model training, feature engineering, and inference
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import json
import time
from datetime import datetime
from flask import current_app

# Global variables for model and scaler
model = None
scaler = None
model_loaded = False


def load_model():
    """
    Load trained Random Forest model and scaler
    """
    global model, scaler, model_loaded

    try:
        model_path = current_app.config.get('MODEL_PATH', 'models/passive_captcha_rf.pkl')
        scaler_path = model_path.replace('.pkl', '_scaler.pkl')

        if os.path.exists(model_path):
            model = joblib.load(model_path)
            print(f"Model loaded from: {model_path}")

            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
                print(f"Scaler loaded from: {scaler_path}")
            else:
                print("Warning: No scaler found, creating default scaler")
                scaler = StandardScaler()

            model_loaded = True
            return True
        else:
            print(f"Model file not found: {model_path}")
            print("Creating and training new model...")
            return create_default_model()

    except Exception as e:
        print(f"Error loading model: {e}")
        return create_default_model()


def create_default_model():
    """
    Create and train a default Random Forest model with synthetic data
    """
    global model, scaler, model_loaded

    try:
        print("Generating synthetic training data...")
        X_train, y_train = generate_synthetic_training_data()

        # Initialize scaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        # Train Random Forest model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42
        )

        model.fit(X_train_scaled, y_train)

        # Save model and scaler
        os.makedirs('models', exist_ok=True)
        model_path = 'models/passive_captcha_rf.pkl'
        scaler_path = 'models/passive_captcha_rf_scaler.pkl'

        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        model_loaded = True
        print("Default model trained and saved successfully")
        return True

    except Exception as e:
        print(f"Error creating default model: {e}")
        return False


def generate_synthetic_training_data():
    """
    Generate synthetic training data for human vs bot classification
    """
    np.random.seed(42)

    # Generate human-like samples (1000 samples)
    human_samples = []
    for _ in range(1000):
        sample = [
            np.random.randint(20, 200),           # mouse_movement_count
            np.random.uniform(0.3, 1.5),         # avg_mouse_velocity
            np.random.randint(10, 100),          # keystroke_count
            np.random.uniform(0.1, 0.8),         # typing_rhythm_variance
            np.random.uniform(10, 120),          # session_duration (normalized)
            np.random.uniform(0.4, 0.9),         # scroll_pattern_score
            np.random.uniform(0.7, 1.0),         # webgl_support_score
            np.random.uniform(0.6, 1.0),         # canvas_fingerprint_score
            np.random.uniform(0.5, 1.0),         # hardware_legitimacy
            np.random.uniform(0.6, 1.0),         # browser_consistency
            np.random.uniform(0.3, 0.9)          # plugin_availability
        ]
        human_samples.append(sample)

    # Generate bot-like samples (1000 samples)
    bot_samples = []
    for _ in range(1000):
        sample = [
            np.random.randint(0, 50),            # mouse_movement_count (fewer movements)
            np.random.uniform(0.1, 0.4),        # avg_mouse_velocity (more mechanical)
            np.random.randint(0, 30),           # keystroke_count (fewer keystrokes)
            np.random.uniform(0.8, 1.0),        # typing_rhythm_variance (too consistent)
            np.random.uniform(1, 15),           # session_duration (shorter sessions)
            np.random.uniform(0.1, 0.5),        # scroll_pattern_score (unnatural scrolling)
            np.random.uniform(0.0, 0.6),        # webgl_support_score (often missing)
            np.random.uniform(0.0, 0.5),        # canvas_fingerprint_score (limited)
            np.random.uniform(0.0, 0.4),        # hardware_legitimacy (suspicious)
            np.random.uniform(0.0, 0.5),        # browser_consistency (inconsistent)
            np.random.uniform(0.0, 0.3)         # plugin_availability (limited)
        ]
        bot_samples.append(sample)

    # Combine data
    X = np.array(human_samples + bot_samples)
    y = np.array([1] * 1000 + [0] * 1000)  # 1 for human, 0 for bot

    return X, y


def extract_features(request_data):
    """
    Extract 11-dimensional feature vector from request data
    """
    try:
        features = {}

        # Behavioral features
        mouse_movements = request_data.get('mouseMovements', [])
        keystrokes = request_data.get('keystrokes', [])
        session_duration = request_data.get('sessionDuration', 0)
        fingerprint = request_data.get('fingerprint', {})

        # Mouse movement features
        features['mouse_movement_count'] = len(mouse_movements)

        if mouse_movements:
            velocities = calculate_mouse_velocities(mouse_movements)
            features['avg_mouse_velocity'] = np.mean(velocities) if velocities else 0
        else:
            features['avg_mouse_velocity'] = 0

        # Keystroke features
        features['keystroke_count'] = len(keystrokes)

        if keystrokes:
            intervals = calculate_keystroke_intervals(keystrokes)
            features['typing_rhythm_variance'] = np.std(intervals) / np.mean(intervals) if intervals else 0
        else:
            features['typing_rhythm_variance'] = 0

        # Session features
        features['session_duration'] = min(session_duration / 1000, 300) / 300  # Normalize to 0-1
        features['scroll_pattern_score'] = calculate_scroll_pattern_score(request_data.get('scrollEvents', []))

        # Device fingerprint features
        features['webgl_support_score'] = calculate_webgl_score(fingerprint)
        features['canvas_fingerprint_score'] = calculate_canvas_score(fingerprint)
        features['hardware_legitimacy'] = calculate_hardware_legitimacy(fingerprint)
        features['browser_consistency'] = calculate_browser_consistency(fingerprint)
        features['plugin_availability'] = calculate_plugin_score(fingerprint)

        return features

    except Exception as e:
        print(f"Error extracting features: {e}")
        return get_default_features()


def calculate_mouse_velocities(mouse_movements):
    """Calculate velocities from mouse movement data"""
    velocities = []

    for i in range(1, len(mouse_movements)):
        prev = mouse_movements[i-1]
        curr = mouse_movements[i]

        dx = curr['x'] - prev['x']
        dy = curr['y'] - prev['y']
        dt = curr['timestamp'] - prev['timestamp']

        if dt > 0:
            distance = np.sqrt(dx**2 + dy**2)
            velocity = distance / dt
            velocities.append(velocity)

    return velocities


def calculate_keystroke_intervals(keystrokes):
    """Calculate intervals between keystrokes"""
    intervals = []

    for i in range(1, len(keystrokes)):
        interval = keystrokes[i]['timestamp'] - keystrokes[i-1]['timestamp']
        if interval > 0:
            intervals.append(interval)

    return intervals


def calculate_scroll_pattern_score(scroll_events):
    """Calculate naturalness score of scroll patterns"""
    if not scroll_events:
        return 0.5  # Neutral score

    # Simple heuristic: natural scrolling has some variance
    if len(scroll_events) < 2:
        return 0.3

    positions = [event['y'] for event in scroll_events]
    variance = np.var(positions)

    # Normalize variance to 0-1 score
    score = min(variance / 10000, 1.0)
    return max(0.1, score)


def calculate_webgl_score(fingerprint):
    """Calculate WebGL support legitimacy score"""
    webgl_vendor = fingerprint.get('webglVendor', '')

    if not webgl_vendor:
        return 0.1  # No WebGL support (suspicious)

    # Common legitimate WebGL vendors
    legitimate_vendors = ['NVIDIA', 'AMD', 'Intel', 'Apple', 'Google']

    for vendor in legitimate_vendors:
        if vendor.lower() in webgl_vendor.lower():
            return 0.9

    return 0.6  # Unknown but present vendor


def calculate_canvas_score(fingerprint):
    """Calculate canvas fingerprint uniqueness score"""
    canvas_fp = fingerprint.get('canvasFingerprint', '')

    if not canvas_fp:
        return 0.2  # No canvas fingerprint (suspicious)

    # Heuristic: longer fingerprints tend to be more legitimate
    if len(canvas_fp) > 50:
        return 0.8
    elif len(canvas_fp) > 20:
        return 0.6
    else:
        return 0.3


def calculate_hardware_legitimacy(fingerprint):
    """Calculate hardware configuration legitimacy"""
    user_agent = fingerprint.get('userAgent', '')
    hardware_concurrency = fingerprint.get('hardwareConcurrency', 0)
    screen_width = fingerprint.get('screenWidth', 0)
    screen_height = fingerprint.get('screenHeight', 0)

    score = 0.5  # Base score

    # Check for reasonable hardware specs
    if 1 <= hardware_concurrency <= 32:
        score += 0.2

    if 800 <= screen_width <= 3840 and 600 <= screen_height <= 2160:
        score += 0.2

    # Check for suspicious user agent patterns
    if user_agent and len(user_agent) > 50:
        score += 0.1

    return min(score, 1.0)


def calculate_browser_consistency(fingerprint):
    """Calculate consistency between user agent and capabilities"""
    user_agent = fingerprint.get('userAgent', '').lower()

    score = 0.5  # Base score

    # Basic checks for browser consistency
    if 'chrome' in user_agent and fingerprint.get('webglVendor'):
        score += 0.3
    elif 'firefox' in user_agent:
        score += 0.2
    elif 'safari' in user_agent:
        score += 0.2

    return min(score, 1.0)


def calculate_plugin_score(fingerprint):
    """Calculate plugin availability score"""
    # For now, return a neutral score
    # In production, this would check for common plugins
    return 0.5


def get_default_features():
    """Return default feature vector when extraction fails"""
    return {
        'mouse_movement_count': 0,
        'avg_mouse_velocity': 0,
        'keystroke_count': 0,
        'typing_rhythm_variance': 0,
        'session_duration': 0,
        'scroll_pattern_score': 0.5,
        'webgl_support_score': 0.5,
        'canvas_fingerprint_score': 0.5,
        'hardware_legitimacy': 0.5,
        'browser_consistency': 0.5,
        'plugin_availability': 0.5
    }


def predict_human_probability(features):
    """
    Predict if the user is human based on extracted features
    """
    global model, scaler, model_loaded

    if not model_loaded or model is None:
        print("Model not loaded, returning default prediction")
        return {'isHuman': True, 'confidence': 0.5}

    try:
        # Convert features to array
        feature_vector = [
            features['mouse_movement_count'],
            features['avg_mouse_velocity'],
            features['keystroke_count'],
            features['typing_rhythm_variance'],
            features['session_duration'],
            features['scroll_pattern_score'],
            features['webgl_support_score'],
            features['canvas_fingerprint_score'],
            features['hardware_legitimacy'],
            features['browser_consistency'],
            features['plugin_availability']
        ]

        # Scale features
        feature_array = np.array(feature_vector).reshape(1, -1)
        if scaler:
            feature_array = scaler.transform(feature_array)

        # Make prediction
        start_time = time.time()
        probabilities = model.predict_proba(feature_array)[0]
        inference_time = (time.time() - start_time) * 1000  # Convert to ms

        human_probability = probabilities[1]  # Class 1 is human
        confidence_threshold = current_app.config.get('CONFIDENCE_THRESHOLD', 0.6)

        is_human = human_probability >= confidence_threshold

        return {
            'isHuman': bool(is_human),
            'confidence': float(human_probability),
            'inferenceTime': round(inference_time, 2)
        }

    except Exception as e:
        print(f"Error during prediction: {e}")
        return {'isHuman': True, 'confidence': 0.5}


def is_model_loaded():
    """Check if ML model is loaded and ready"""
    return model_loaded and model is not None


def get_model_info():
    """Get information about the loaded model"""
    if not model_loaded or model is None:
        return {'status': 'not_loaded'}

    return {
        'status': 'loaded',
        'algorithm': 'Random Forest',
        'n_estimators': getattr(model, 'n_estimators', 'unknown'),
        'features': 11,
        'classes': ['bot', 'human']
    }
