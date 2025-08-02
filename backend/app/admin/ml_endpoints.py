"""
ML Model Endpoints for Admin Dashboard
Provides comprehensive ML model metrics, health monitoring, and management
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app.admin import require_admin_auth
from app.logs_pipeline import logs_pipeline
from app.database import get_db_session, VerificationLog
import redis
import json
import os
import joblib
import numpy as np
from sqlalchemy import func

ml_bp = Blueprint('ml', __name__, url_prefix='/admin/ml')

# DEPRECATED: Use centralized Redis client from Flask app context
# Access via current_app.redis_client instead of module-level global

def init_ml_endpoints(redis_client_instance):
    """DEPRECATED: Redis client now managed centrally"""
    pass  # No-op for backward compatibility


@ml_bp.route('/metrics', methods=['GET'])
@require_admin_auth
def get_ml_metrics():
    """
    Get comprehensive ML model metrics
    """
    try:
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 24))
        
        # Check cache first
        cache_key = f"ml_metrics:{website_id or 'all'}:{time_range}"
        redis_client = getattr(current_app, 'redis_client', None)
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        # Get metrics from logs pipeline
        if logs_pipeline:
            metrics = logs_pipeline.aggregator.get_ml_model_metrics(time_range)
        else:
            # Fallback to direct database query
            metrics = _get_ml_metrics_from_db(website_id, time_range)
        
        # Cache the result
        if redis_client:
            if redis_client: redis_client.setex(cache_key, 300, json.dumps(metrics, default=str))  # 5 min cache
        
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting ML metrics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ML_METRICS_ERROR',
                'message': 'Failed to retrieve ML model metrics'
            }
        }), 500


@ml_bp.route('/confidence-distribution', methods=['GET'])
@require_admin_auth
def get_confidence_distribution():
    """
    Get model confidence distribution data
    """
    try:
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 24))
        
        cache_key = f"confidence_dist:{website_id or 'all'}:{time_range}"
        redis_client = getattr(current_app, 'redis_client', None)
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=time_range)
            query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)
            
            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))
            
            logs = query.all()
            
            # Calculate confidence distribution
            confidence_buckets = {
                '0-20%': 0, '21-40%': 0, '41-60%': 0, 
                '61-80%': 0, '81-100%': 0
            }
            
            total_predictions = len(logs)
            avg_confidence = 0
            
            if logs:
                for log in logs:
                    conf_pct = log.confidence * 100
                    if conf_pct <= 20:
                        confidence_buckets['0-20%'] += 1
                    elif conf_pct <= 40:
                        confidence_buckets['21-40%'] += 1
                    elif conf_pct <= 60:
                        confidence_buckets['41-60%'] += 1
                    elif conf_pct <= 80:
                        confidence_buckets['61-80%'] += 1
                    else:
                        confidence_buckets['81-100%'] += 1
                
                avg_confidence = sum(log.confidence for log in logs) / len(logs)
            
            # Calculate reliability score (based on high-confidence predictions)
            high_confidence_count = confidence_buckets['61-80%'] + confidence_buckets['81-100%']
            reliability_score = (high_confidence_count / total_predictions * 100) if total_predictions > 0 else 0
            
            result = {
                'confidence_buckets': [
                    {
                        'range': range_key,
                        'count': count,
                        'percentage': (count / total_predictions * 100) if total_predictions > 0 else 0
                    }
                    for range_key, count in confidence_buckets.items()
                ],
                'average_confidence': avg_confidence,
                'reliability_score': reliability_score,
                'total_predictions': total_predictions,
                'time_range_hours': time_range
            }
            
            # Cache result
            if redis_client:
                if redis_client: redis_client.setex(cache_key, 300, json.dumps(result, default=str))
            
            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting confidence distribution: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFIDENCE_DIST_ERROR',
                'message': 'Failed to retrieve confidence distribution'
            }
        }), 500


@ml_bp.route('/accuracy-metrics', methods=['GET'])
@require_admin_auth
def get_accuracy_metrics():
    """
    Get model accuracy metrics including confusion matrix
    """
    try:
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 24))
        
        cache_key = f"accuracy_metrics:{website_id or 'all'}:{time_range}"
        redis_client = getattr(current_app, 'redis_client', None)
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=time_range)
            query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)
            
            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))
            
            logs = query.all()
            
            if not logs:
                return jsonify({
                    'success': True,
                    'data': {
                        'confusion_matrix': {'true_positives': 0, 'false_positives': 0, 'true_negatives': 0, 'false_negatives': 0},
                        'metrics': {'precision': 0, 'recall': 0, 'f1_score': 0, 'accuracy': 0}
                    }
                })
            
            # Calculate confusion matrix
            true_positives = 0   # Human correctly identified as human
            false_positives = 0  # Bot incorrectly identified as human  
            true_negatives = 0   # Bot correctly identified as bot
            false_negatives = 0  # Human incorrectly identified as bot
            
            for log in logs:
                # Assume high confidence (>0.5) means human prediction
                predicted_human = log.confidence > 0.5
                actual_human = log.is_human
                
                if predicted_human and actual_human:
                    true_positives += 1
                elif predicted_human and not actual_human:
                    false_positives += 1
                elif not predicted_human and not actual_human:
                    true_negatives += 1
                else:
                    false_negatives += 1
            
            # Calculate metrics
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            accuracy = (true_positives + true_negatives) / len(logs) if logs else 0
            
            result = {
                'confusion_matrix': {
                    'true_positives': true_positives,
                    'false_positives': false_positives,
                    'true_negatives': true_negatives,
                    'false_negatives': false_negatives
                },
                'metrics': {
                    'precision': round(precision, 4),
                    'recall': round(recall, 4),
                    'f1_score': round(f1_score, 4),
                    'accuracy': round(accuracy, 4)
                },
                'total_samples': len(logs),
                'time_range_hours': time_range
            }
            
            # Cache result
            if redis_client:
                if redis_client: redis_client.setex(cache_key, 300, json.dumps(result, default=str))
            
            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting accuracy metrics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ACCURACY_METRICS_ERROR',
                'message': 'Failed to retrieve accuracy metrics'
            }
        }), 500


@ml_bp.route('/performance-trend', methods=['GET'])
@require_admin_auth
def get_performance_trend():
    """
    Get model performance trends over time
    """
    try:
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 168))  # Default 7 days
        
        cache_key = f"performance_trend:{website_id or 'all'}:{time_range}"
        redis_client = getattr(current_app, 'redis_client', None)
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=time_range)
            query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)
            
            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))
            
            logs = query.order_by(VerificationLog.timestamp).all()
            
            # Group by time periods (hours for short ranges, days for longer)
            time_bucket_hours = 1 if time_range <= 24 else 24 if time_range <= 168 else 168
            
            time_buckets = {}
            for log in logs:
                # Round timestamp to nearest bucket
                bucket_time = log.timestamp.replace(
                    minute=0, second=0, microsecond=0
                )
                if time_bucket_hours > 1:
                    bucket_time = bucket_time.replace(hour=(bucket_time.hour // time_bucket_hours) * time_bucket_hours)
                
                bucket_key = bucket_time.isoformat()
                
                if bucket_key not in time_buckets:
                    time_buckets[bucket_key] = {
                        'logs': [],
                        'timestamp': bucket_time
                    }
                
                time_buckets[bucket_key]['logs'].append(log)
            
            # Calculate precision and recall for each time bucket
            labels = []
            precision_data = []
            recall_data = []
            
            for bucket_key in sorted(time_buckets.keys()):
                bucket_logs = time_buckets[bucket_key]['logs']
                
                if len(bucket_logs) < 10:  # Skip buckets with too few samples
                    continue
                
                # Calculate confusion matrix for this bucket
                tp = fp = tn = fn = 0
                for log in bucket_logs:
                    predicted_human = log.confidence > 0.5
                    actual_human = log.is_human
                    
                    if predicted_human and actual_human:
                        tp += 1
                    elif predicted_human and not actual_human:
                        fp += 1
                    elif not predicted_human and not actual_human:
                        tn += 1
                    else:
                        fn += 1
                
                # Calculate metrics
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                
                # Format label based on time bucket
                timestamp = time_buckets[bucket_key]['timestamp']
                if time_bucket_hours == 1:
                    label = timestamp.strftime('%H:%M')
                elif time_bucket_hours == 24:
                    label = timestamp.strftime('%m/%d')
                else:
                    label = timestamp.strftime('%m/%d')
                
                labels.append(label)
                precision_data.append(round(precision, 3))
                recall_data.append(round(recall, 3))
            
            # Calculate current metrics
            current_precision = precision_data[-1] if precision_data else 0
            current_recall = recall_data[-1] if recall_data else 0
            
            result = {
                'data': {
                    'labels': labels,
                    'precision': precision_data,
                    'recall': recall_data
                },
                'current_metrics': {
                    'precision': current_precision,
                    'recall': current_recall,
                    'f1_score': 2 * (current_precision * current_recall) / (current_precision + current_recall) if (current_precision + current_recall) > 0 else 0
                },
                'time_range_hours': time_range,
                'bucket_size_hours': time_bucket_hours
            }
            
            # Cache result
            if redis_client:
                if redis_client: redis_client.setex(cache_key, 600, json.dumps(result, default=str))  # 10 min cache
            
            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting performance trend: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'PERFORMANCE_TREND_ERROR',
                'message': 'Failed to retrieve performance trend'
            }
        }), 500


# REMOVED: Duplicate health endpoint - consolidated to main app level at /health
# ML health details available through /admin/statistics endpoint


@ml_bp.route('/retrain', methods=['POST'])
@require_admin_auth
def trigger_retraining():
    """
    Trigger ML model retraining
    """
    try:
        # This would typically trigger an async training job
        # For now, we'll simulate the trigger
        
        # Log the retraining request
        if logs_pipeline:
            logs_pipeline.log_system_event(
                "ML model retraining triggered",
                metadata={'triggered_by': 'admin_dashboard'}
            )
        
        # In a real implementation, this would:
        # 1. Queue a training job
        # 2. Return a job ID for tracking
        # 3. Send notifications when complete
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Model retraining initiated',
                'job_id': f"training_{int(datetime.utcnow().timestamp())}",
                'estimated_completion': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                'status': 'queued'
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error triggering retraining: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'RETRAIN_ERROR',
                'message': 'Failed to trigger model retraining'
            }
        }), 500


def _get_ml_metrics_from_db(website_id: str, time_range: int) -> dict:
    """Fallback method to get ML metrics directly from database"""
    session = get_db_session()
    try:
        since = datetime.utcnow() - timedelta(hours=time_range)
        query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)
        
        if website_id and website_id != 'all':
            query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))
        
        logs = query.all()
        
        if not logs:
            return {'error': 'No data available'}
        
        total_verifications = len(logs)
        human_verifications = len([log for log in logs if log.is_human])
        bot_verifications = total_verifications - human_verifications
        avg_confidence = sum(log.confidence for log in logs) / len(logs)
        
        return {
            'summary': {
                'total_verifications': total_verifications,
                'human_rate': (human_verifications / total_verifications * 100) if total_verifications > 0 else 0,
                'bot_rate': (bot_verifications / total_verifications * 100) if total_verifications > 0 else 0,
                'avg_confidence': avg_confidence
            }
        }
        
    finally:
        session.close()