"""
Machine Learning module for Passive CAPTCHA system
Handles Random Forest model training, feature engineering, and inference
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import json
import time
from datetime import datetime
from flask import current_app

# Global variables for ensemble model and scaler
ensemble_model = None
scaler = None
model_loaded = False
model_performance = {
    'accuracy': 0.0,
    'precision': 0.0,
    'recall': 0.0,
    'f1_score': 0.0,
    'last_trained': None
}


def load_model():
    """
    Load trained ensemble model and scaler
    """
    global ensemble_model, scaler, model_loaded, model_performance

    try:
        model_path = current_app.config.get('MODEL_PATH', 'models/passive_captcha_ensemble.pkl')
        scaler_path = model_path.replace('.pkl', '_scaler.pkl')
        performance_path = model_path.replace('.pkl', '_performance.json')

        if os.path.exists(model_path):
            ensemble_model = joblib.load(model_path)
            print(f"Ensemble model loaded from: {model_path}")

            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
                print(f"Scaler loaded from: {scaler_path}")
            else:
                print("Warning: No scaler found, creating robust scaler")
                scaler = RobustScaler()

            # Load performance metrics
            if os.path.exists(performance_path):
                with open(performance_path, 'r') as f:
                    model_performance = json.load(f)
                print(f"Model performance: {model_performance}")

            model_loaded = True
            return True
        else:
            print(f"Ensemble model file not found: {model_path}")
            print("Creating and training new ensemble model...")
            return create_default_ensemble_model()

    except Exception as e:
        print(f"Error loading ensemble model: {e}")
        return create_default_ensemble_model()


def create_default_ensemble_model():
    """
    Create and train an ensemble model with synthetic data
    """
    global ensemble_model, scaler, model_loaded, model_performance

    try:
        print("Generating enhanced synthetic training data...")
        X_train, X_test, y_train, y_test = generate_enhanced_training_data()

        # Initialize robust scaler (better for outliers)
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Create ensemble model with different algorithms
        rf_model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42,
            bootstrap=True,
            oob_score=True
        )

        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        # Create voting ensemble
        ensemble_model = VotingClassifier(
            estimators=[
                ('rf', rf_model),
                ('gb', gb_model)
            ],
            voting='soft'  # Use predicted probabilities
        )

        print("Training ensemble model...")
        ensemble_model.fit(X_train_scaled, y_train)

        # Evaluate model performance
        y_pred = ensemble_model.predict(X_test_scaled)
        y_pred_proba = ensemble_model.predict_proba(X_test_scaled)
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        model_performance = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred)),
            'recall': float(recall_score(y_test, y_pred)),
            'f1_score': float(f1_score(y_test, y_pred)),
            'last_trained': datetime.now().isoformat()
        }

        print(f"Model Performance:")
        print(f"  Accuracy: {model_performance['accuracy']:.3f}")
        print(f"  Precision: {model_performance['precision']:.3f}")
        print(f"  Recall: {model_performance['recall']:.3f}")
        print(f"  F1 Score: {model_performance['f1_score']:.3f}")

        # Save ensemble model, scaler, and performance
        os.makedirs('models', exist_ok=True)
        model_path = 'models/passive_captcha_ensemble.pkl'
        scaler_path = 'models/passive_captcha_ensemble_scaler.pkl'
        performance_path = 'models/passive_captcha_ensemble_performance.json'

        joblib.dump(ensemble_model, model_path)
        joblib.dump(scaler, scaler_path)
        
        with open(performance_path, 'w') as f:
            json.dump(model_performance, f, indent=2)

        model_loaded = True
        print("Enhanced ensemble model trained and saved successfully")
        return True

    except Exception as e:
        print(f"Error creating ensemble model: {e}")
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


def generate_enhanced_training_data():
    """
    Generate enhanced synthetic training data with more realistic patterns
    """
    np.random.seed(42)
    
    # Enhanced human-like samples (1500 samples for better diversity)
    human_samples = []
    for _ in range(1500):
        # Generate realistic human behavioral patterns
        base_mouse_count = np.random.randint(30, 250)
        base_velocity = np.random.uniform(0.4, 2.0)
        base_keystrokes = np.random.randint(15, 120)
        base_session = np.random.uniform(20, 180)
        
        # Add natural variation patterns
        velocity_variation = np.random.uniform(0.85, 1.15)
        interaction_multiplier = np.random.uniform(0.9, 1.1)
        
        sample = [
            int(base_mouse_count * interaction_multiplier),  # mouse_movement_count
            base_velocity * velocity_variation,              # avg_mouse_velocity
            np.random.randint(8, 80) * interaction_multiplier,  # keystroke_count
            np.random.uniform(0.15, 0.85),                  # typing_rhythm_variance
            min(base_session / 300, 1.0),                   # session_duration (normalized)
            np.random.uniform(0.5, 0.95),                   # scroll_pattern_score
            np.random.uniform(0.75, 1.0),                   # webgl_support_score
            np.random.uniform(0.65, 1.0),                   # canvas_fingerprint_score
            np.random.uniform(0.6, 1.0),                    # hardware_legitimacy
            np.random.uniform(0.65, 1.0),                   # browser_consistency
            np.random.uniform(0.4, 0.9)                     # plugin_availability
        ]
        human_samples.append(sample)
    
    # Enhanced bot-like samples (1500 samples with more sophisticated patterns)
    bot_samples = []
    for _ in range(1500):
        # Different bot categories
        bot_type = np.random.choice(['simple', 'advanced', 'headless'])
        
        if bot_type == 'simple':
            # Basic automation bots
            sample = [
                np.random.randint(0, 15),                   # very few mouse movements
                np.random.uniform(0.05, 0.25),             # mechanical velocity
                np.random.randint(0, 10),                  # minimal keystrokes
                np.random.uniform(0.9, 1.0),               # too consistent typing
                np.random.uniform(1, 20) / 300,            # short sessions
                np.random.uniform(0.0, 0.3),               # poor scroll patterns
                np.random.uniform(0.0, 0.4),               # limited webgl
                np.random.uniform(0.0, 0.3),               # basic canvas
                np.random.uniform(0.0, 0.3),               # suspicious hardware
                np.random.uniform(0.0, 0.4),               # inconsistent browser
                np.random.uniform(0.0, 0.2)                # limited plugins
            ]
        elif bot_type == 'advanced':
            # More sophisticated bots trying to mimic humans
            sample = [
                np.random.randint(10, 60),                 # some mouse movements
                np.random.uniform(0.2, 0.6),              # moderate velocity
                np.random.randint(5, 40),                  # some keystrokes
                np.random.uniform(0.7, 0.95),             # still too consistent
                np.random.uniform(15, 60) / 300,          # medium sessions
                np.random.uniform(0.2, 0.6),              # better scroll patterns
                np.random.uniform(0.4, 0.8),              # decent webgl
                np.random.uniform(0.3, 0.7),              # better canvas
                np.random.uniform(0.2, 0.6),              # moderate hardware
                np.random.uniform(0.3, 0.7),              # better browser consistency
                np.random.uniform(0.1, 0.5)               # limited plugins
            ]
        else:  # headless
            # Headless browsers
            sample = [
                np.random.randint(0, 30),                  # limited movements
                np.random.uniform(0.1, 0.4),              # mechanical patterns
                np.random.randint(0, 25),                 # few keystrokes
                np.random.uniform(0.8, 1.0),              # very consistent
                np.random.uniform(5, 45) / 300,           # controlled sessions
                np.random.uniform(0.1, 0.4),              # unnatural scrolling
                np.random.uniform(0.0, 0.5),              # limited/missing webgl
                np.random.uniform(0.0, 0.4),              # basic canvas
                np.random.uniform(0.1, 0.4),              # suspicious specs
                np.random.uniform(0.2, 0.6),              # browser inconsistencies
                np.random.uniform(0.0, 0.3)               # minimal plugins
            ]
        
        bot_samples.append(sample)
    
    # Combine and create labels
    X = np.array(human_samples + bot_samples)
    y = np.array([1] * 1500 + [0] * 1500)  # 1 for human, 0 for bot
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    return X_train, X_test, y_train, y_test


def predict_human_probability(features):
    """
    Predict if the user is human based on extracted features using ensemble model
    """
    global ensemble_model, scaler, model_loaded

    if not model_loaded or ensemble_model is None:
        print("Ensemble model not loaded, returning default prediction")
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
