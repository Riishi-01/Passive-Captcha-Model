"""
Analytics Endpoints for Admin Dashboard
Provides comprehensive analytics data for the frontend dashboard
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from functools import wraps
import traceback

from app.services import get_auth_service
from app.database import get_db_session
from app.ml import get_model_info, is_model_loaded

analytics_bp = Blueprint('analytics', __name__, url_prefix='/admin/analytics')

def require_auth(f):
    """Decorator to require authentication for analytics endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header required'
                }
            }), 401
        
        token = auth_header.split(' ')[1]
        auth_service = get_auth_service()
        
        if not auth_service:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Authentication service unavailable'
                }
            }), 503
        
        user = auth_service.validate_token(token)
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired token'
                }
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


@analytics_bp.route('/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        time_range = request.args.get('timeRange', '24h')
        
        # Calculate hours based on time range
        if time_range == '24h':
            hours = 24
        elif time_range == '7d':
            hours = 168
        elif time_range == '30d':
            hours = 720
        else:
            hours = 24
        
        # Calculate start time
        start_time = datetime.now() - timedelta(hours=hours)
        
        session = get_db_session()
        try:
            # Get verification statistics
            verification_query = """
                SELECT 
                    COUNT(*) as total_verifications,
                    AVG(CASE WHEN is_human = 1 THEN 1.0 ELSE 0.0 END) * 100 as human_rate,
                    AVG(confidence) * 100 as avg_confidence,
                    AVG(response_time) as avg_response_time
                FROM verifications 
                WHERE timestamp >= ?
            """
            
            result = session.execute(verification_query, (start_time,)).fetchone()
            
            # Get previous period for comparison
            prev_start = start_time - timedelta(hours=hours)
            prev_query = """
                SELECT 
                    COUNT(*) as prev_total,
                    AVG(CASE WHEN is_human = 1 THEN 1.0 ELSE 0.0 END) * 100 as prev_human_rate,
                    AVG(confidence) * 100 as prev_confidence,
                    AVG(response_time) as prev_response_time
                FROM verifications 
                WHERE timestamp >= ? AND timestamp < ?
            """
            
            prev_result = session.execute(prev_query, (prev_start, start_time)).fetchone()
            
            # Calculate changes
            verification_change = 0
            human_rate_change = 0
            confidence_change = 0
            response_time_change = 0
            
            if prev_result and prev_result.prev_total > 0:
                verification_change = ((result.total_verifications - prev_result.prev_total) / prev_result.prev_total) * 100
                if prev_result.prev_human_rate:
                    human_rate_change = result.human_rate - prev_result.prev_human_rate
                if prev_result.prev_confidence:
                    confidence_change = result.avg_confidence - prev_result.prev_confidence
                if prev_result.prev_response_time:
                    response_time_change = ((result.avg_response_time - prev_result.prev_response_time) / prev_result.prev_response_time) * 100
            
            stats = {
                'totalVerifications': result.total_verifications or 0,
                'humanRate': round(result.human_rate or 0, 1),
                'avgConfidence': round(result.avg_confidence or 0, 1),
                'avgResponseTime': round(result.avg_response_time or 0, 1),
                'verificationChange': round(verification_change, 1),
                'humanRateChange': round(human_rate_change, 1),
                'confidenceChange': round(confidence_change, 1),
                'responseTimeChange': round(response_time_change, 1)
            }
            
            return jsonify({
                'success': True,
                'data': stats,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve dashboard statistics'
            }
        }), 500


@analytics_bp.route('/charts', methods=['GET'])
@require_auth
def get_chart_data():
    """Get chart data for dashboard visualizations"""
    try:
        time_range = request.args.get('timeRange', '24h')
        
        if time_range == '24h':
            hours = 24
            interval = 1  # 1 hour intervals
        elif time_range == '7d':
            hours = 168
            interval = 6  # 6 hour intervals
        elif time_range == '30d':
            hours = 720
            interval = 24  # 24 hour intervals
        else:
            hours = 24
            interval = 1
        
        start_time = datetime.now() - timedelta(hours=hours)
        
        session = get_db_session()
        try:
            # Get hourly verification data
            chart_query = """
                SELECT 
                    datetime((timestamp / ?) * ?, 'unixepoch') as time_bucket,
                    SUM(CASE WHEN is_human = 1 THEN 1 ELSE 0 END) as human_count,
                    SUM(CASE WHEN is_human = 0 THEN 1 ELSE 0 END) as bot_count,
                    AVG(confidence) as avg_confidence
                FROM verifications 
                WHERE timestamp >= ?
                GROUP BY time_bucket
                ORDER BY time_bucket
            """
            
            interval_seconds = interval * 3600  # Convert hours to seconds
            results = session.execute(chart_query, (interval_seconds, interval_seconds, start_time)).fetchall()
            
            chart_data = []
            for row in results:
                chart_data.append({
                    'timestamp': row.time_bucket,
                    'human': row.human_count or 0,
                    'bot': row.bot_count or 0,
                    'confidence': round(row.avg_confidence or 0, 2)
                })
            
            return jsonify({
                'success': True,
                'data': chart_data,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting chart data: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve chart data'
            }
        }), 500


@analytics_bp.route('/detection', methods=['GET'])
@require_auth
def get_detection_data():
    """Get human vs bot detection statistics"""
    try:
        time_range = request.args.get('timeRange', '24h')
        
        if time_range == '24h':
            hours = 24
        elif time_range == '7d':
            hours = 168
        elif time_range == '30d':
            hours = 720
        else:
            hours = 24
        
        start_time = datetime.now() - timedelta(hours=hours)
        
        session = get_db_session()
        try:
            detection_query = """
                SELECT 
                    SUM(CASE WHEN is_human = 1 THEN 1 ELSE 0 END) as human_count,
                    SUM(CASE WHEN is_human = 0 THEN 1 ELSE 0 END) as bot_count,
                    COUNT(*) as total_count
                FROM verifications 
                WHERE timestamp >= ?
            """
            
            result = session.execute(detection_query, (start_time,)).fetchone()
            
            human_count = result.human_count or 0
            bot_count = result.bot_count or 0
            total = result.total_count or 0
            
            detection_data = {
                'human': human_count,
                'bot': bot_count,
                'humanPercentage': round((human_count / total) * 100, 1) if total > 0 else 0,
                'botPercentage': round((bot_count / total) * 100, 1) if total > 0 else 0
            }
            
            return jsonify({
                'success': True,
                'data': detection_data,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting detection data: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve detection data'
            }
        }), 500


@analytics_bp.route('/geographic', methods=['GET'])
@require_auth
def get_geographic_data():
    """Get geographic distribution of verifications"""
    try:
        time_range = request.args.get('timeRange', '24h')
        
        if time_range == '24h':
            hours = 24
        elif time_range == '7d':
            hours = 168
        elif time_range == '30d':
            hours = 720
        else:
            hours = 24
        
        start_time = datetime.now() - timedelta(hours=hours)
        
        session = get_db_session()
        try:
            # Get geographic data (assuming we have country data in verifications)
            geo_query = """
                SELECT 
                    COALESCE(country, 'Unknown') as country,
                    COUNT(*) as count
                FROM verifications 
                WHERE timestamp >= ?
                GROUP BY country
                ORDER BY count DESC
                LIMIT 10
            """
            
            results = session.execute(geo_query, (start_time,)).fetchall()
            total_verifications = sum(row.count for row in results)
            
            geographic_data = []
            for row in results:
                geographic_data.append({
                    'country': row.country,
                    'count': row.count,
                    'percentage': round((row.count / total_verifications) * 100, 1) if total_verifications > 0 else 0
                })
            
            return jsonify({
                'success': True,
                'data': geographic_data,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting geographic data: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve geographic data'
            }
        }), 500


@analytics_bp.route('/threats', methods=['GET'])
@require_auth
def get_threat_analysis():
    """Get threat analysis data"""
    try:
        time_range = request.args.get('timeRange', '24h')
        
        if time_range == '24h':
            hours = 24
        elif time_range == '7d':
            hours = 168
        elif time_range == '30d':
            hours = 720
        else:
            hours = 24
        
        start_time = datetime.now() - timedelta(hours=hours)
        
        session = get_db_session()
        try:
            # Get threat data based on low confidence scores and bot classifications
            threat_query = """
                SELECT 
                    CASE 
                        WHEN confidence < 0.3 AND is_human = 0 THEN 'Automated Scripts'
                        WHEN confidence < 0.5 AND is_human = 0 THEN 'Suspicious Activity'
                        WHEN confidence < 0.7 AND is_human = 0 THEN 'Low Confidence Bots'
                        ELSE 'Other'
                    END as threat_type,
                    COUNT(*) as count
                FROM verifications 
                WHERE timestamp >= ? AND is_human = 0
                GROUP BY threat_type
                ORDER BY count DESC
            """
            
            results = session.execute(threat_query, (start_time,)).fetchall()
            total_threats = sum(row.count for row in results)
            
            threat_data = []
            for row in results:
                if row.threat_type != 'Other':
                    severity = 'high' if 'Automated' in row.threat_type else 'medium' if 'Suspicious' in row.threat_type else 'low'
                    threat_data.append({
                        'type': row.threat_type,
                        'severity': severity,
                        'count': row.count,
                        'percentage': round((row.count / total_threats) * 100, 1) if total_threats > 0 else 0
                    })
            
            return jsonify({
                'success': True,
                'data': threat_data,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting threat analysis: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve threat analysis'
            }
        }), 500