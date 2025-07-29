#!/usr/bin/env python3
"""
Comprehensive ML Model Testing for Passive CAPTCHA System
Validates model performance, accuracy, edge cases, and robustness
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
from pathlib import Path
import pytest

# Performance tracking
performance_results = {
    'inference_times': [],
    'accuracy_scores': [],
    'edge_case_results': [],
    'stress_test_results': []
}

@pytest.fixture(scope="session")
def model():
    """Load the trained model"""
    model_path = "models/passive_captcha_rf.pkl"
    if not os.path.exists(model_path):
        pytest.skip("Model file not found")
    return joblib.load(model_path)

@pytest.fixture(scope="session") 
def scaler():
    """Load the trained scaler"""
    scaler_path = "models/passive_captcha_rf_scaler.pkl"
    if not os.path.exists(scaler_path):
        pytest.skip("Scaler file not found")
    return joblib.load(scaler_path)

@pytest.fixture(scope="session")
def metadata():
    """Load the model metadata"""
    metadata_path = "models/passive_captcha_rf_metadata.json"
    if not os.path.exists(metadata_path):
        return {}
    with open(metadata_path, 'r') as f:
        return json.load(f)

def test_model_loading():
    """Test model loading and initialization"""
    print("\n🔄 Testing Model Loading...")
    print("-" * 40)
    
    try:
        # Test model file existence
        model_path = "models/passive_captcha_rf.pkl"
        scaler_path = "models/passive_captcha_rf_scaler.pkl"
        metadata_path = "models/passive_captcha_rf_metadata.json"
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return False
            
        if not os.path.exists(scaler_path):
            print(f"❌ Scaler file not found: {scaler_path}")
            return False
            
        if not os.path.exists(metadata_path):
            print(f"❌ Metadata file not found: {metadata_path}")
            return False
        
        print(f"✅ Model files exist")
        
        # Test loading
        start_time = time.time()
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        load_time = (time.time() - start_time) * 1000
        
        print(f"✅ Model loaded successfully in {load_time:.2f}ms")
        print(f"📊 Model algorithm: {metadata.get('algorithm', 'Unknown')}")
        print(f"📊 Model accuracy: {metadata.get('accuracy', 'Unknown')}")
        print(f"📊 Feature count: {metadata.get('features', 'Unknown')}")
        
        return True, model, scaler, metadata
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False, None, None, None


def test_inference_speed(model, scaler, iterations=100):
    """Test model inference speed under various conditions"""
    print(f"\n⚡ Testing Inference Speed ({iterations} iterations)...")
    print("-" * 40)
    
    # Sample feature vectors
    human_features = np.array([[45, 0.8, 10, 0.4, 35, 0.8, 1.0, 0.85, 0.9, 0.88, 0.85]])
    bot_features = np.array([[2, 2.5, 80, 0.05, 3, 0.1, 0.0, 0.0, 0.2, 0.1, 0.0]])
    mixed_features = np.array([[20, 1.2, 30, 0.6, 15, 0.5, 0.8, 0.6, 0.7, 0.5, 0.4]])
    
    test_cases = [
        ("Human-like", human_features),
        ("Bot-like", bot_features),
        ("Mixed signals", mixed_features)
    ]
    
    for case_name, features in test_cases:
        print(f"\n📝 Testing {case_name} features:")
        
        times = []
        predictions = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Scale features
            scaled_features = scaler.transform(features)
            
            # Predict
            prediction = model.predict(scaled_features)[0]
            confidence = model.predict_proba(scaled_features)[0].max()
            
            end_time = time.time()
            
            inference_time = (end_time - start_time) * 1000  # Convert to ms
            times.append(inference_time)
            predictions.append((prediction, confidence))
        
        # Calculate statistics
        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)
        p95_time = np.percentile(times, 95)
        
        performance_results['inference_times'].extend(times)
        
        print(f"   ⏱️  Average: {avg_time:.3f}ms")
        print(f"   ⚡ Fastest: {min_time:.3f}ms")
        print(f"   🐌 Slowest: {max_time:.3f}ms")
        print(f"   📊 95th percentile: {p95_time:.3f}ms")
        
        # Check SRS requirement (<100ms)
        if p95_time < 100:
            print(f"   ✅ PASSES SRS requirement (<100ms)")
        else:
            print(f"   ❌ FAILS SRS requirement ({p95_time:.3f}ms >= 100ms)")
        
        # Show prediction consistency
        unique_predictions = set(predictions)
        print(f"   🎯 Prediction consistency: {len(unique_predictions)} unique results")
        
        if len(unique_predictions) == 1:
            pred, conf = predictions[0]
            print(f"   📈 Consistent prediction: {'Human' if pred == 1 else 'Bot'} (confidence: {conf:.3f})")
        else:
            print(f"   ⚠️  Inconsistent predictions detected")


def test_edge_cases(model, scaler):
    """Test model behavior with edge case inputs"""
    print("\n🔍 Testing Edge Cases...")
    print("-" * 40)
    
    edge_cases = [
        {
            'name': 'All zeros',
            'features': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'expected': 'bot'
        },
        {
            'name': 'All maximum values',
            'features': [1000, 5.0, 200, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            'expected': 'uncertain'
        },
        {
            'name': 'Minimal human interaction',
            'features': [5, 0.1, 1, 0.8, 10, 0.2, 1.0, 0.9, 0.8, 0.7, 0.6],
            'expected': 'human'
        },
        {
            'name': 'Bot-like automation',
            'features': [150, 3.0, 100, 0.01, 2, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0],
            'expected': 'bot'
        },
        {
            'name': 'Missing WebGL (common bot pattern)',
            'features': [30, 0.6, 15, 0.5, 20, 0.4, 0.0, 0.0, 0.8, 0.9, 0.7],
            'expected': 'bot'
        },
        {
            'name': 'Legitimate mobile user',
            'features': [25, 0.4, 8, 0.6, 25, 0.3, 0.8, 0.6, 0.9, 0.8, 0.5],
            'expected': 'human'
        }
    ]
    
    edge_case_results = []
    
    for case in edge_cases:
        print(f"\n📝 Testing: {case['name']}")
        
        try:
            # Prepare features
            features = np.array([case['features']])
            scaled_features = scaler.transform(features)
            
            # Predict
            start_time = time.time()
            prediction = model.predict(scaled_features)[0]
            probabilities = model.predict_proba(scaled_features)[0]
            end_time = time.time()
            
            inference_time = (end_time - start_time) * 1000
            
            human_prob = probabilities[1]
            classification = 'human' if prediction == 1 else 'bot'
            
            result = {
                'case': case['name'],
                'prediction': classification,
                'human_probability': human_prob,
                'inference_time': inference_time,
                'expected': case['expected'],
                'correct': (classification == case['expected']) or case['expected'] == 'uncertain'
            }
            
            edge_case_results.append(result)
            performance_results['edge_case_results'].append(result)
            
            print(f"   🤖 Prediction: {classification}")
            print(f"   📊 Human probability: {human_prob:.3f}")
            print(f"   ⏱️  Inference time: {inference_time:.3f}ms")
            print(f"   🎯 Expected: {case['expected']}")
            
            if result['correct']:
                print(f"   ✅ CORRECT")
            else:
                print(f"   ❌ INCORRECT (expected {case['expected']}, got {classification})")
                
        except Exception as e:
            print(f"   🚫 ERROR: {e}")
            edge_case_results.append({
                'case': case['name'],
                'error': str(e),
                'correct': False
            })
    
    # Summary
    correct_count = sum(1 for r in edge_case_results if r.get('correct', False))
    total_count = len(edge_case_results)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"\n📊 Edge Case Summary:")
    print(f"   ✅ Correct: {correct_count}/{total_count}")
    print(f"   📈 Accuracy: {accuracy:.1f}%")
    
    return edge_case_results


def test_feature_importance_stability(model):
    """Test feature importance and model stability"""
    print("\n🔬 Testing Feature Importance & Stability...")
    print("-" * 40)
    
    try:
        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            
            feature_names = [
                'mouse_movement_count',
                'avg_mouse_velocity', 
                'keystroke_count',
                'typing_rhythm_variance',
                'session_duration',
                'scroll_pattern_score',
                'webgl_support_score',
                'canvas_fingerprint_score',
                'hardware_legitimacy',
                'browser_consistency',
                'plugin_availability'
            ]
            
            print("📊 Feature Importance Rankings:")
            
            # Sort by importance
            importance_pairs = list(zip(feature_names, importances))
            importance_pairs.sort(key=lambda x: x[1], reverse=True)
            
            for i, (feature, importance) in enumerate(importance_pairs, 1):
                bar_length = int(importance * 50)  # Scale for visualization
                bar = "█" * bar_length + "░" * (20 - bar_length)
                print(f"   {i:2d}. {feature:25} {bar} {importance:.4f}")
            
            # Validate critical features have reasonable importance
            critical_features = ['webgl_support_score', 'canvas_fingerprint_score', 'mouse_movement_count']
            critical_importance = sum(importances[feature_names.index(f)] for f in critical_features if f in feature_names)
            
            print(f"\n🎯 Critical Features Importance: {critical_importance:.3f}")
            
            if critical_importance > 0.3:
                print("   ✅ Critical features have good importance")
            else:
                print("   ⚠️  Critical features may have low importance")
                
        else:
            print("❌ Model doesn't support feature importance")
            
    except Exception as e:
        print(f"❌ Feature importance test failed: {e}")


def test_model_robustness(model, scaler, num_tests=50):
    """Test model robustness with noisy inputs"""
    print(f"\n🛡️  Testing Model Robustness ({num_tests} noisy samples)...")
    print("-" * 40)
    
    # Base human and bot features
    base_human = np.array([45, 0.8, 10, 0.4, 35, 0.8, 1.0, 0.85, 0.9, 0.88, 0.85])
    base_bot = np.array([2, 2.5, 80, 0.05, 3, 0.1, 0.0, 0.0, 0.2, 0.1, 0.0])
    
    human_consistency = []
    bot_consistency = []
    
    for noise_level in [0.1, 0.2, 0.3]:
        print(f"\n🌪️  Testing with {noise_level*100}% noise level:")
        
        human_predictions = []
        bot_predictions = []
        
        for _ in range(num_tests):
            # Add noise to base features
            noise_human = base_human + np.random.normal(0, noise_level, len(base_human))
            noise_bot = base_bot + np.random.normal(0, noise_level, len(base_bot))
            
            # Ensure valid ranges (clip negative values)
            noise_human = np.clip(noise_human, 0, None)
            noise_bot = np.clip(noise_bot, 0, None)
            
            try:
                # Predict
                human_scaled = scaler.transform([noise_human])
                bot_scaled = scaler.transform([noise_bot])
                
                human_pred = model.predict(human_scaled)[0]
                bot_pred = model.predict(bot_scaled)[0]
                
                human_predictions.append(human_pred)
                bot_predictions.append(bot_pred)
                
            except Exception as e:
                print(f"   ⚠️  Prediction failed with noise: {e}")
        
        # Calculate consistency
        human_accuracy = (sum(human_predictions) / len(human_predictions)) * 100 if human_predictions else 0
        bot_accuracy = ((len(bot_predictions) - sum(bot_predictions)) / len(bot_predictions)) * 100 if bot_predictions else 0
        
        human_consistency.append(human_accuracy)
        bot_consistency.append(bot_accuracy)
        
        print(f"   👤 Human classification accuracy: {human_accuracy:.1f}%")
        print(f"   🤖 Bot classification accuracy: {bot_accuracy:.1f}%")
        
        if human_accuracy > 70 and bot_accuracy > 70:
            print(f"   ✅ ROBUST at {noise_level*100}% noise")
        else:
            print(f"   ⚠️  SENSITIVE to {noise_level*100}% noise")
    
    # Overall robustness score
    avg_robustness = (np.mean(human_consistency) + np.mean(bot_consistency)) / 2
    print(f"\n🎯 Overall Robustness Score: {avg_robustness:.1f}%")
    
    if avg_robustness > 80:
        print("🏆 EXCELLENT robustness")
    elif avg_robustness > 60:
        print("✅ GOOD robustness")
    else:
        print("⚠️  LOW robustness - may be sensitive to input variations")


def test_stress_conditions(model, scaler):
    """Test model under stress conditions"""
    print("\n💪 Testing Stress Conditions...")
    print("-" * 40)
    
    stress_tests = [
        {
            'name': 'Rapid fire predictions (1000 requests)',
            'test': lambda: rapid_fire_test(model, scaler, 1000)
        },
        {
            'name': 'Memory pressure test',
            'test': lambda: memory_pressure_test(model, scaler)
        },
        {
            'name': 'Concurrent predictions simulation',
            'test': lambda: concurrent_test(model, scaler, 10)
        }
    ]
    
    stress_results = []
    
    for test_case in stress_tests:
        print(f"\n🔥 {test_case['name']}:")
        
        try:
            start_time = time.time()
            result = test_case['test']()
            end_time = time.time()
            
            duration = end_time - start_time
            
            stress_result = {
                'name': test_case['name'],
                'duration': duration,
                'result': result,
                'success': True
            }
            
            print(f"   ⏱️  Duration: {duration:.2f}s")
            print(f"   ✅ PASSED")
            
        except Exception as e:
            stress_result = {
                'name': test_case['name'],
                'error': str(e),
                'success': False
            }
            print(f"   ❌ FAILED: {e}")
        
        stress_results.append(stress_result)
        performance_results['stress_test_results'].append(stress_result)
    
    return stress_results


def rapid_fire_test(model, scaler, num_requests):
    """Simulate rapid API requests"""
    features = np.array([[45, 0.8, 10, 0.4, 35, 0.8, 1.0, 0.85, 0.9, 0.88, 0.85]])
    
    times = []
    for _ in range(num_requests):
        start = time.time()
        scaled = scaler.transform(features)
        pred = model.predict(scaled)
        end = time.time()
        times.append(end - start)
    
    avg_time = np.mean(times) * 1000
    max_time = np.max(times) * 1000
    
    print(f"     📊 Average: {avg_time:.3f}ms")
    print(f"     📊 Maximum: {max_time:.3f}ms")
    
    return {'avg_time': avg_time, 'max_time': max_time}


def memory_pressure_test(model, scaler):
    """Test with large batch of features"""
    # Create large batch
    batch_size = 1000
    features = np.random.rand(batch_size, 11)
    
    start_time = time.time()
    scaled_features = scaler.transform(features)
    predictions = model.predict(scaled_features)
    end_time = time.time()
    
    duration = end_time - start_time
    throughput = batch_size / duration
    
    print(f"     📊 Batch size: {batch_size}")
    print(f"     📊 Duration: {duration:.3f}s")
    print(f"     📊 Throughput: {throughput:.1f} predictions/sec")
    
    return {'batch_size': batch_size, 'throughput': throughput}


def concurrent_test(model, scaler, num_threads):
    """Simulate concurrent predictions"""
    import threading
    
    results = []
    features = np.array([[45, 0.8, 10, 0.4, 35, 0.8, 1.0, 0.85, 0.9, 0.88, 0.85]])
    
    def worker():
        start = time.time()
        scaled = scaler.transform(features)
        pred = model.predict(scaled)
        end = time.time()
        results.append(end - start)
    
    threads = []
    start_time = time.time()
    
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    end_time = time.time()
    
    total_duration = end_time - start_time
    avg_individual = np.mean(results) * 1000
    
    print(f"     📊 Threads: {num_threads}")
    print(f"     📊 Total duration: {total_duration:.3f}s")
    print(f"     📊 Avg individual: {avg_individual:.3f}ms")
    
    return {'threads': num_threads, 'total_duration': total_duration, 'avg_individual': avg_individual}


def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE MODEL TEST REPORT")
    print("=" * 60)
    
    # Performance summary
    if performance_results['inference_times']:
        avg_inference = np.mean(performance_results['inference_times'])
        p95_inference = np.percentile(performance_results['inference_times'], 95)
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Average inference time: {avg_inference:.3f}ms")
        print(f"   95th percentile: {p95_inference:.3f}ms")
        print(f"   SRS requirement (<100ms): {'✅ PASS' if p95_inference < 100 else '❌ FAIL'}")
    
    # Edge case summary
    if performance_results['edge_case_results']:
        correct_cases = sum(1 for r in performance_results['edge_case_results'] if r.get('correct', False))
        total_cases = len(performance_results['edge_case_results'])
        edge_accuracy = (correct_cases / total_cases) * 100
        
        print(f"\n🔍 EDGE CASE TESTING:")
        print(f"   Test cases: {total_cases}")
        print(f"   Correct predictions: {correct_cases}")
        print(f"   Edge case accuracy: {edge_accuracy:.1f}%")
    
    # Stress test summary
    if performance_results['stress_test_results']:
        successful_stress = sum(1 for r in performance_results['stress_test_results'] if r.get('success', False))
        total_stress = len(performance_results['stress_test_results'])
        
        print(f"\n💪 STRESS TESTING:")
        print(f"   Tests completed: {total_stress}")
        print(f"   Successful: {successful_stress}")
        print(f"   Success rate: {(successful_stress/total_stress)*100:.1f}%")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    # Calculate overall score
    scores = []
    
    if performance_results['inference_times']:
        perf_score = 100 if p95_inference < 100 else max(0, 100 - (p95_inference - 100))
        scores.append(('Performance', perf_score))
    
    if performance_results['edge_case_results']:
        scores.append(('Edge Cases', edge_accuracy))
    
    if performance_results['stress_test_results']:
        stress_score = (successful_stress / total_stress) * 100
        scores.append(('Stress Tests', stress_score))
    
    if scores:
        overall_score = np.mean([score for _, score in scores])
        
        print(f"   Overall score: {overall_score:.1f}%")
        
        if overall_score >= 90:
            print("   🏆 EXCELLENT - Production ready!")
        elif overall_score >= 75:
            print("   ✅ GOOD - Ready for deployment")
        elif overall_score >= 60:
            print("   ⚠️  FAIR - Consider improvements")
        else:
            print("   ❌ POOR - Needs significant work")
    
    print(f"\n📅 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Run comprehensive model testing"""
    print("🧪 COMPREHENSIVE ML MODEL TESTING")
    print("=" * 60)
    
    # Load model
    success, model, scaler, metadata = test_model_loading()
    if not success:
        print("❌ Cannot proceed without loaded model")
        return
    
    # Run all tests
    try:
        test_inference_speed(model, scaler, iterations=100)
        test_edge_cases(model, scaler)
        test_feature_importance_stability(model)
        test_model_robustness(model, scaler, num_tests=30)
        test_stress_conditions(model, scaler)
        
        # Generate final report
        generate_test_report()
        
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 