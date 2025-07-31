#!/usr/bin/env python3
"""
Create a simple test model for testing purposes
"""

import pickle
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from pathlib import Path

# Create simple test data
np.random.seed(42)
X = np.random.rand(100, 11)  # 11 features as per documentation
y = np.random.randint(0, 2, 100)  # Binary classification

# Create and train a simple model
model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X, y)

# Create and fit scaler
scaler = StandardScaler()
scaler.fit(X)

# Save model and scaler
models_dir = Path('../backend/models')
models_dir.mkdir(exist_ok=True)

# Save with protocol 2 for compatibility
with open(models_dir / 'passive_captcha_rf_test.pkl', 'wb') as f:
    pickle.dump(model, f, protocol=2)

joblib.dump(scaler, models_dir / 'passive_captcha_rf_scaler_test.pkl')

print("Test model and scaler created successfully")

# Test loading
with open(models_dir / 'passive_captcha_rf_test.pkl', 'rb') as f:
    loaded_model = pickle.load(f)

loaded_scaler = joblib.load(models_dir / 'passive_captcha_rf_scaler_test.pkl')

# Test prediction
test_sample = np.random.rand(1, 11)
scaled_sample = loaded_scaler.transform(test_sample)
prediction = loaded_model.predict_proba(scaled_sample)

print(f"Test prediction successful: {prediction}")
print("Test model files are working correctly")