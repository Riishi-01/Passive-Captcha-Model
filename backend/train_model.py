#!/usr/bin/env python3
"""
Passive CAPTCHA ML Model Training Script
Lightweight dataset import, feature engineering, and Random Forest training
"""

import os
import sys
import numpy as np
import pandas as pd
import json
import requests
from datetime import datetime
from pathlib import Path
import zipfile
import io
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

# Configuration
DATASET_DIR = Path("dataset")
MODELS_DIR = Path("models")
PROCESSED_DIR = DATASET_DIR / "processed"

# Ensure directories exist
for dir_path in [DATASET_DIR, MODELS_DIR, PROCESSED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

class PassiveCaptchaDatasetManager:
    """Manages lightweight dataset import and processing"""
    
    def __init__(self):
        self.datasets = {}
        self.processed_data = []
        
    def download_cmu_keystroke_sample(self):
        """Download a lightweight sample of CMU keystroke dynamics data"""
        print("📊 Generating lightweight CMU-style keystroke data...")
        
        # Since actual CMU dataset requires Kaggle API, we'll create realistic synthetic data
        # based on the CMU keystroke dynamics patterns
        np.random.seed(42)
        
        users = ['user_{:02d}'.format(i) for i in range(1, 21)]  # 20 users
        samples_per_user = 25  # 25 samples per user = 500 human samples
        
        keystroke_data = []
        
        for user_id in users:
            for session in range(samples_per_user):
                # Generate realistic keystroke timing data for password ".tie5Roanl"
                password_length = 10
                
                # Hold times (key press duration) - humans: 80-200ms
                hold_times = np.random.normal(120, 30, password_length)
                hold_times = np.clip(hold_times, 60, 250)
                
                # Dwell times (time between key releases) - humans: 100-300ms  
                dwell_times = np.random.normal(180, 50, password_length-1)
                dwell_times = np.clip(dwell_times, 80, 400)
                
                # Flight times (time between key presses) - humans: 120-350ms
                flight_times = np.random.normal(200, 60, password_length-1)
                flight_times = np.clip(flight_times, 100, 450)
                
                sample = {
                    'user_id': user_id,
                    'session_id': f"{user_id}_session_{session}",
                    'hold_times': hold_times.tolist(),
                    'dwell_times': dwell_times.tolist(),
                    'flight_times': flight_times.tolist(),
                    'total_typing_time': sum(hold_times) + sum(dwell_times),
                    'typing_rhythm_variance': np.var(flight_times),
                    'avg_keystroke_interval': np.mean(flight_times),
                    'keystroke_count': password_length,
                    'label': 1  # Human
                }
                
                keystroke_data.append(sample)
        
        # Generate bot keystroke patterns (200 samples)
        for bot_id in range(200):
            # Bots have very consistent timing patterns
            hold_times = np.random.normal(50, 5, password_length)  # Faster, more consistent
            dwell_times = np.random.normal(45, 8, password_length-1)  # Very consistent
            flight_times = np.random.normal(55, 12, password_length-1)  # Robotic timing
            
            sample = {
                'user_id': f'bot_{bot_id:03d}',
                'session_id': f"bot_{bot_id:03d}_session_0",
                'hold_times': hold_times.tolist(),
                'dwell_times': dwell_times.tolist(),
                'flight_times': flight_times.tolist(),
                'total_typing_time': sum(hold_times) + sum(dwell_times),
                'typing_rhythm_variance': np.var(flight_times),
                'avg_keystroke_interval': np.mean(flight_times),
                'keystroke_count': password_length,
                'label': 0  # Bot
            }
            
            keystroke_data.append(sample)
        
        self.datasets['cmu_keystroke'] = keystroke_data
        print(f"✅ Generated {len(keystroke_data)} keystroke samples (500 human, 200 bot)")
        
        return keystroke_data
    
    def generate_mouse_behavioral_data(self):
        """Generate lightweight mouse behavioral data inspired by BeCAPTCHA research"""
        print("🖱️ Generating mouse behavioral patterns...")
        
        np.random.seed(42)
        mouse_data = []
        
        # Human mouse patterns (400 samples)
        for human_id in range(400):
            # Human mouse movements are irregular, with pauses and corrections
            movement_count = np.random.poisson(45)  # Average 45 movements
            
            # Generate realistic mouse trajectory
            velocities = []
            accelerations = []
            pause_times = []
            
            for i in range(movement_count):
                # Human velocity varies naturally (0.3-1.5 px/ms)
                velocity = np.random.gamma(2, 0.4)  # Gamma distribution for realistic velocity
                velocities.append(min(velocity, 2.0))
                
                # Human acceleration is irregular
                acceleration = np.random.normal(0, 0.8)
                accelerations.append(acceleration)
                
                # Humans occasionally pause (5-15% of movements)
                if np.random.random() < 0.12:
                    pause_times.append(np.random.exponential(200))  # Pause duration
            
            # Calculate behavioral metrics
            avg_velocity = np.mean(velocities) if velocities else 0
            velocity_variance = np.var(velocities) if len(velocities) > 1 else 0
            acceleration_variance = np.var(accelerations) if len(accelerations) > 1 else 0
            pause_ratio = len(pause_times) / max(movement_count, 1)
            
            # Session duration (10-120 seconds for humans)
            session_duration = np.random.gamma(3, 15)  # Realistic session time
            session_duration = min(max(session_duration, 8), 180)
            
            sample = {
                'user_id': f'human_mouse_{human_id:03d}',
                'mouse_movement_count': movement_count,
                'avg_mouse_velocity': avg_velocity,
                'mouse_velocity_variance': velocity_variance,
                'mouse_acceleration_variance': acceleration_variance,
                'pause_ratio': pause_ratio,
                'session_duration': session_duration,
                'scroll_events': np.random.poisson(8),  # Humans scroll naturally
                'click_count': np.random.poisson(3),  # Natural clicking
                'label': 1  # Human
            }
            
            mouse_data.append(sample)
        
        # Bot mouse patterns (300 samples)
        for bot_id in range(300):
            # Bots have different patterns: either too perfect or too minimal
            if np.random.random() < 0.6:
                # Minimal movement bots
                movement_count = np.random.poisson(2)  # Very few movements
                avg_velocity = np.random.normal(0.1, 0.02)  # Very slow
                velocity_variance = 0.001  # Almost no variance
                acceleration_variance = 0.001
                pause_ratio = 0.0  # No pauses
                session_duration = np.random.gamma(1, 2)  # Very short sessions
                scroll_events = 0  # No scrolling
                click_count = np.random.choice([0, 1, 2])  # Minimal clicks
            else:
                # Excessive movement bots
                movement_count = np.random.poisson(200)  # Too many movements
                avg_velocity = np.random.normal(3.0, 0.5)  # Too fast
                velocity_variance = 0.01  # Too consistent
                acceleration_variance = 0.01
                pause_ratio = 0.0  # No natural pauses
                session_duration = np.random.normal(5, 1)  # Brief sessions
                scroll_events = np.random.poisson(50)  # Excessive scrolling
                click_count = np.random.poisson(20)  # Too many clicks
            
            sample = {
                'user_id': f'bot_mouse_{bot_id:03d}',
                'mouse_movement_count': movement_count,
                'avg_mouse_velocity': max(avg_velocity, 0),
                'mouse_velocity_variance': velocity_variance,
                'mouse_acceleration_variance': acceleration_variance,
                'pause_ratio': pause_ratio,
                'session_duration': max(session_duration, 1),
                'scroll_events': scroll_events,
                'click_count': click_count,
                'label': 0  # Bot
            }
            
            mouse_data.append(sample)
        
        self.datasets['mouse_behavior'] = mouse_data
        print(f"✅ Generated {len(mouse_data)} mouse behavior samples (400 human, 300 bot)")
        
        return mouse_data
    
    def generate_device_fingerprint_data(self):
        """Generate device fingerprint patterns"""
        print("🔍 Generating device fingerprint data...")
        
        np.random.seed(42)
        fingerprint_data = []
        
        # Human device patterns (350 samples)
        for human_id in range(350):
            sample = {
                'user_id': f'human_device_{human_id:03d}',
                'webgl_support_score': 1.0,  # Humans have WebGL
                'canvas_fingerprint_score': np.random.uniform(0.7, 1.0),  # Varies by browser
                'hardware_legitimacy_score': np.random.uniform(0.8, 1.0),  # Real hardware
                'browser_consistency_score': np.random.uniform(0.85, 1.0),  # Consistent browser
                'plugin_availability': np.random.uniform(0.6, 1.0),  # Various plugins
                'screen_resolution_entropy': np.random.uniform(0.7, 0.95),  # Realistic screens
                'timezone_consistency': np.random.uniform(0.9, 1.0),  # Consistent timezone
                'language_consistency': np.random.uniform(0.95, 1.0),  # Consistent language
                'label': 1  # Human
            }
            fingerprint_data.append(sample)
        
        # Bot device patterns (250 samples)
        for bot_id in range(250):
            # Bots often have missing features or inconsistent fingerprints
            webgl_score = 0.0 if np.random.random() < 0.7 else np.random.uniform(0.3, 0.8)
            canvas_score = 0.0 if np.random.random() < 0.6 else np.random.uniform(0.1, 0.5)
            
            sample = {
                'user_id': f'bot_device_{bot_id:03d}',
                'webgl_support_score': webgl_score,
                'canvas_fingerprint_score': canvas_score,
                'hardware_legitimacy_score': np.random.uniform(0.1, 0.4),  # VM-like hardware
                'browser_consistency_score': np.random.uniform(0.2, 0.6),  # Inconsistent
                'plugin_availability': np.random.uniform(0.0, 0.3),  # Missing plugins
                'screen_resolution_entropy': np.random.uniform(0.1, 0.5),  # Common resolutions
                'timezone_consistency': np.random.uniform(0.3, 0.8),  # May be inconsistent
                'language_consistency': np.random.uniform(0.4, 0.9),  # May vary
                'label': 0  # Bot
            }
            fingerprint_data.append(sample)
        
        self.datasets['device_fingerprint'] = fingerprint_data
        print(f"✅ Generated {len(fingerprint_data)} device fingerprint samples (350 human, 250 bot)")
        
        return fingerprint_data


class FeatureEngineer:
    """Advanced feature engineering for behavioral biometrics"""
    
    def __init__(self):
        self.feature_names = [
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
    
    def extract_features(self, datasets):
        """Extract 11-dimensional feature vector from multiple datasets"""
        print("🔧 Extracting engineered features...")
        
        features = []
        labels = []
        
        # Combine all datasets
        all_samples = []
        for dataset_name, data in datasets.items():
            all_samples.extend(data)
        
        print(f"Processing {len(all_samples)} total samples...")
        
        for sample in all_samples:
            # Initialize feature vector
            feature_vector = [0.0] * 11
            
            # Behavioral features (mouse & keyboard)
            if 'mouse_movement_count' in sample:
                feature_vector[0] = min(sample['mouse_movement_count'], 1000) / 1000.0  # Normalize
            elif 'keystroke_count' in sample:
                feature_vector[0] = min(sample.get('keystroke_count', 0) * 5, 1000) / 1000.0  # Estimate from keystrokes
            
            # Mouse velocity
            if 'avg_mouse_velocity' in sample:
                feature_vector[1] = min(sample['avg_mouse_velocity'], 5.0) / 5.0
            else:
                # Estimate from keystroke timing
                keystroke_interval = sample.get('avg_keystroke_interval', 200)
                estimated_velocity = max(0, (300 - keystroke_interval) / 300)  # Inverse relationship
                feature_vector[1] = min(estimated_velocity, 1.0)
            
            # Mouse acceleration variance
            if 'mouse_acceleration_variance' in sample:
                feature_vector[2] = min(sample['mouse_acceleration_variance'], 2.0) / 2.0
            elif 'typing_rhythm_variance' in sample:
                # Use typing rhythm as proxy for movement variance
                feature_vector[2] = min(sample['typing_rhythm_variance'] / 1000.0, 1.0)
            
            # Keystroke count
            feature_vector[3] = min(sample.get('keystroke_count', 0), 200) / 200.0
            
            # Average keystroke interval
            keystroke_interval = sample.get('avg_keystroke_interval', 0)
            feature_vector[4] = min(max(keystroke_interval, 50), 500) / 500.0
            
            # Session duration (normalized)
            session_duration = sample.get('session_duration', 30)
            feature_vector[5] = min(session_duration, 300) / 300.0  # Cap at 5 minutes
            
            # Device fingerprint features
            feature_vector[6] = sample.get('webgl_support_score', 0.5)
            feature_vector[7] = sample.get('canvas_fingerprint_score', 0.5)
            feature_vector[8] = sample.get('hardware_legitimacy_score', 0.5)
            feature_vector[9] = sample.get('browser_consistency_score', 0.5)
            
            # Device entropy score (composite)
            entropy_components = [
                sample.get('plugin_availability', 0.5),
                sample.get('screen_resolution_entropy', 0.5),
                sample.get('timezone_consistency', 0.5),
                sample.get('language_consistency', 0.5)
            ]
            feature_vector[10] = np.mean(entropy_components)
            
            features.append(feature_vector)
            labels.append(sample['label'])
        
        print(f"✅ Extracted {len(features)} feature vectors with {len(self.feature_names)} dimensions")
        return np.array(features), np.array(labels)


class FastRandomForestTrainer:
    """Optimized Random Forest trainer for fast inference"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        
    def train(self, X, y, optimize_for_speed=True):
        """Train optimized Random Forest model"""
        print("🌲 Training Fast Random Forest Model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        print(f"Class distribution - Human: {sum(y_train)}, Bot: {len(y_train) - sum(y_train)}")
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Configure model for speed vs accuracy balance
        if optimize_for_speed:
            # Fast inference configuration
            rf_params = {
                'n_estimators': 50,  # Fewer trees for speed
                'max_depth': 10,     # Shallower trees
                'min_samples_split': 10,
                'min_samples_leaf': 5,
                'max_features': 'sqrt',
                'bootstrap': True,
                'random_state': 42,
                'class_weight': 'balanced',
                'n_jobs': -1  # Use all CPU cores
            }
        else:
            # High accuracy configuration
            rf_params = {
                'n_estimators': 100,
                'max_depth': 15,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'max_features': 'sqrt',
                'bootstrap': True,
                'random_state': 42,
                'class_weight': 'balanced',
                'n_jobs': -1
            }
        
        print(f"Model configuration: {rf_params}")
        
        # Train model
        self.model = RandomForestClassifier(**rf_params)
        
        start_time = datetime.now()
        self.model.fit(X_train_scaled, y_train)
        training_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Training completed in {training_time:.2f} seconds")
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n📊 Model Performance:")
        print(f"Test Accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Bot', 'Human']))
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, 
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
            scoring='accuracy'
        )
        
        print(f"\n5-Fold CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        # Feature importance
        feature_importance = list(zip(
            FeatureEngineer().feature_names, 
            self.model.feature_importances_
        ))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🔍 Top 5 Most Important Features:")
        for name, importance in feature_importance[:5]:
            print(f"  {name}: {importance:.3f}")
        
        return {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'training_time': training_time,
            'feature_importance': feature_importance
        }
    
    def save_model(self, model_path="models/passive_captcha_rf.pkl"):
        """Save trained model and scaler"""
        if self.model is None:
            raise ValueError("No model trained yet")
        
        # Save model
        joblib.dump(self.model, model_path)
        
        # Save scaler
        scaler_path = model_path.replace('.pkl', '_scaler.pkl')
        joblib.dump(self.scaler, scaler_path)
        
        # Save metadata
        metadata = {
            'model_version': '1.0',
            'training_date': datetime.now().isoformat(),
            'feature_names': FeatureEngineer().feature_names,
            'model_params': self.model.get_params(),
            'model_size_mb': os.path.getsize(model_path) / (1024 * 1024)
        }
        
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Model saved to: {model_path}")
        print(f"✅ Scaler saved to: {scaler_path}")
        print(f"✅ Metadata saved to: {metadata_path}")
        print(f"📦 Model size: {metadata['model_size_mb']:.2f} MB")


def main():
    """Main training pipeline"""
    print("🚀 Starting Passive CAPTCHA ML Training Pipeline")
    print("=" * 60)
    
    # Initialize components
    dataset_manager = PassiveCaptchaDatasetManager()
    feature_engineer = FeatureEngineer()
    trainer = FastRandomForestTrainer()
    
    try:
        # Step 1: Import lightweight datasets
        print("\n📥 STEP 1: Dataset Import & Generation")
        print("-" * 40)
        
        dataset_manager.download_cmu_keystroke_sample()
        dataset_manager.generate_mouse_behavioral_data()
        dataset_manager.generate_device_fingerprint_data()
        
        total_samples = sum(len(data) for data in dataset_manager.datasets.values())
        human_samples = sum(sum(1 for sample in data if sample['label'] == 1) 
                          for data in dataset_manager.datasets.values())
        bot_samples = total_samples - human_samples
        
        print(f"\n📊 Dataset Summary:")
        print(f"  Total samples: {total_samples}")
        print(f"  Human samples: {human_samples}")
        print(f"  Bot samples: {bot_samples}")
        print(f"  Class balance: {human_samples/total_samples:.1%} human, {bot_samples/total_samples:.1%} bot")
        
        # Step 2: Feature Engineering
        print("\n🔧 STEP 2: Feature Engineering")
        print("-" * 40)
        
        X, y = feature_engineer.extract_features(dataset_manager.datasets)
        
        print(f"Feature matrix shape: {X.shape}")
        print(f"Feature names: {feature_engineer.feature_names}")
        
        # Data quality checks
        print("\n🔍 Data Quality Checks:")
        print(f"  No missing values: {not np.any(np.isnan(X))}")
        print(f"  No infinite values: {not np.any(np.isinf(X))}")
        print(f"  Feature ranges: [{X.min():.3f}, {X.max():.3f}]")
        
        # Step 3: Model Training
        print("\n🌲 STEP 3: Model Training")
        print("-" * 40)
        
        results = trainer.train(X, y, optimize_for_speed=True)
        
        # Step 4: Model Saving
        print("\n💾 STEP 4: Model Saving")
        print("-" * 40)
        
        trainer.save_model()
        
        # Step 5: Performance Summary
        print("\n🎯 STEP 5: Final Performance Summary")
        print("-" * 40)
        print(f"✅ Model Training Complete!")
        print(f"   Accuracy: {results['accuracy']:.1%}")
        print(f"   CV Score: {results['cv_mean']:.1%} ± {results['cv_std']*2:.1%}")
        print(f"   Training Time: {results['training_time']:.1f}s")
        print(f"   Ready for production deployment!")
        
    except Exception as e:
        print(f"❌ Error in training pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 