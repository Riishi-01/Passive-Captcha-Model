"""
Alerts Endpoints for Admin Dashboard
Provides alerts and notifications for the dashboard
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from functools import wraps
import uuid

from app.services import get_auth_service
from app.database import get_db_session

alerts_bp = Blueprint('alerts', __name__, url_prefix='/admin/alerts')

def require_auth(f):
    """Decorator to require authentication for alerts endpoints"""
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


@alerts_bp.route('/recent', methods=['GET'])
@require_auth
def get_recent_alerts():
    """Get recent alerts for the dashboard"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        session = get_db_session()
        try:
            # Generate dynamic alerts based on system conditions
            alerts = []
            
            # Check for high bot activity
            recent_time = datetime.now() - timedelta(hours=1)
            bot_query = """
                SELECT COUNT(*) as bot_count 
                FROM verifications 
                WHERE timestamp >= ? AND is_human = 0
            """
            bot_result = session.execute(bot_query, (recent_time,)).fetchone()
            bot_count = bot_result.bot_count or 0
            
            if bot_count > 50:  # High bot activity threshold
                alerts.append({
                    'id': str(uuid.uuid4()),
                    'type': 'warning',
                    'title': 'High Bot Activity',
                    'message': f'Detected {bot_count} bot attempts in the last hour',
                    'timestamp': datetime.now().isoformat(),
                    'websiteId': None,
                    'resolved': False
                })
            
            # Check for low confidence scores
            low_confidence_query = """
                SELECT COUNT(*) as low_conf_count 
                FROM verifications 
                WHERE timestamp >= ? AND confidence < 0.5
            """
            conf_result = session.execute(low_confidence_query, (recent_time,)).fetchone()
            low_conf_count = conf_result.low_conf_count or 0
            
            if low_conf_count > 20:
                alerts.append({
                    'id': str(uuid.uuid4()),
                    'type': 'info',
                    'title': 'Low Confidence Detections',
                    'message': f'{low_conf_count} verifications with confidence below 50%',
                    'timestamp': datetime.now().isoformat(),
                    'websiteId': None,
                    'resolved': False
                })
            
            # Check for recent errors (simulated)
            error_query = """
                SELECT COUNT(*) as total_recent 
                FROM verifications 
                WHERE timestamp >= ?
            """
            recent_result = session.execute(error_query, (recent_time,)).fetchone()
            recent_total = recent_result.total_recent or 0
            
            if recent_total == 0:
                alerts.append({
                    'id': str(uuid.uuid4()),
                    'type': 'error',
                    'title': 'No Recent Activity',
                    'message': 'No verifications recorded in the last hour',
                    'timestamp': datetime.now().isoformat(),
                    'websiteId': None,
                    'resolved': False
                })
            
            # Add a success alert if system is healthy
            if recent_total > 0 and bot_count < 10:
                alerts.append({
                    'id': str(uuid.uuid4()),
                    'type': 'success',
                    'title': 'System Operating Normally',
                    'message': f'Processing {recent_total} verifications with low bot activity',
                    'timestamp': datetime.now().isoformat(),
                    'websiteId': None,
                    'resolved': False
                })
            
            # Sort by timestamp (most recent first) and limit
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            alerts = alerts[:limit]
            
            return jsonify({
                'success': True,
                'data': alerts,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting recent alerts: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve recent alerts'
            }
        }), 500


@alerts_bp.route('/<alert_id>/resolve', methods=['POST'])
@require_auth
def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    try:
        # In a real implementation, you would update the alert in the database
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'data': {
                'alert_id': alert_id,
                'resolved': True,
                'resolved_at': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error resolving alert {alert_id}: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to resolve alert'
            }
        }), 500


@alerts_bp.route('/summary', methods=['GET'])
@require_auth
def get_alerts_summary():
    """Get alerts summary statistics"""
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
            # Calculate alert-worthy conditions
            bot_query = """
                SELECT COUNT(*) as bot_count 
                FROM verifications 
                WHERE timestamp >= ? AND is_human = 0
            """
            bot_result = session.execute(bot_query, (start_time,)).fetchone()
            bot_count = bot_result.bot_count or 0
            
            error_conditions = 0
            warning_conditions = 0
            info_conditions = 0
            
            # Count different alert conditions
            if bot_count > 100:
                error_conditions += 1
            elif bot_count > 50:
                warning_conditions += 1
            else:
                info_conditions += 1
            
            summary = {
                'total_alerts': error_conditions + warning_conditions + info_conditions,
                'error_count': error_conditions,
                'warning_count': warning_conditions,
                'info_count': info_conditions,
                'resolved_count': 0  # Would be calculated from database in real implementation
            }
            
            return jsonify({
                'success': True,
                'data': summary,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        current_app.logger.error(f"Error getting alerts summary: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve alerts summary'
            }
        }), 500