"""
Logs Endpoints for Admin Dashboard
Provides timeline logs and activity feeds for the dashboard
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from functools import wraps
import uuid

from app.services import get_auth_service
from app.database import get_db_session

logs_bp = Blueprint('logs', __name__, url_prefix='/admin/logs')

def require_auth(f):
    """Decorator to require authentication for logs endpoints"""
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


@logs_bp.route('/timeline', methods=['GET'])
@require_auth
def get_timeline_logs():
    """Get timeline logs for the dashboard activity feed"""
    try:
        filter_type = request.args.get('filter', 'all')
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)

        session = get_db_session()
        try:
            # Base query for verification logs
            base_query = """
                SELECT
                    id,
                    timestamp,
                    is_human,
                    confidence,
                    ip_address,
                    user_agent,
                    website_origin,
                    features,
                    response_time
                FROM verifications
                WHERE 1=1
            """

            params = []

            # Apply filters
            if filter_type == 'human':
                base_query += " AND is_human = 1"
            elif filter_type == 'bot':
                base_query += " AND is_human = 0"
            elif filter_type == 'high_confidence':
                base_query += " AND confidence > 0.8"
            elif filter_type == 'low_confidence':
                base_query += " AND confidence < 0.5"

            # Add ordering and pagination
            base_query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            results = session.execute(base_query, params).fetchall()

            # Transform to timeline log format
            logs = []
            for row in results:
                log_type = 'verification'
                level = 'info'

                # Determine log level based on confidence and classification
                if row.confidence < 0.3:
                    level = 'error'
                elif row.confidence < 0.6:
                    level = 'warning'
                elif row.is_human and row.confidence > 0.9:
                    level = 'success'

                # Create descriptive message
                classification = 'Human' if row.is_human else 'Bot'
                confidence_pct = round(row.confidence * 100, 1)

                message = f"{classification} detected with {confidence_pct}% confidence"
                if row.website_origin:
                    message += f" from {row.website_origin}"

                logs.append({
                    'id': str(row.id),
                    'timestamp': row.timestamp.isoformat() if hasattr(row.timestamp, 'isoformat') else str(row.timestamp),
                    'type': log_type,
                    'level': level,
                    'message': message,
                    'details': {
                        'classification': classification,
                        'confidence': row.confidence,
                        'ip_address': row.ip_address,
                        'user_agent': row.user_agent,
                        'website_origin': row.website_origin,
                        'response_time': row.response_time,
                        'features': row.features
                    }
                })

            # Check if there are more logs
            count_query = "SELECT COUNT(*) FROM verifications WHERE 1=1"
            if filter_type == 'human':
                count_query += " AND is_human = 1"
            elif filter_type == 'bot':
                count_query += " AND is_human = 0"
            elif filter_type == 'high_confidence':
                count_query += " AND confidence > 0.8"
            elif filter_type == 'low_confidence':
                count_query += " AND confidence < 0.5"

            total_count = session.execute(count_query).fetchone()[0]
            has_more = offset + limit < total_count

            return jsonify({
                'success': True,
                'data': {
                    'logs': logs,
                    'hasMore': has_more,
                    'total': total_count,
                    'offset': offset,
                    'limit': limit
                },
                'timestamp': datetime.now().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting timeline logs: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve timeline logs'
            }
        }), 500


@logs_bp.route('/activity', methods=['GET'])
@require_auth
def get_activity_logs():
    """Get recent activity logs for live feed"""
    try:
        limit = request.args.get('limit', 20, type=int)
        since = request.args.get('since')  # ISO timestamp for real-time updates

        session = get_db_session()
        try:
            # Get recent verifications
            query = """
                SELECT
                    id,
                    timestamp,
                    is_human,
                    confidence,
                    ip_address,
                    website_origin,
                    response_time
                FROM verifications
            """

            params = []

            if since:
                try:
                    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                    query += " WHERE timestamp > ?"
                    params.append(since_dt)
                except ValueError:
                    # Invalid timestamp, ignore since parameter
                    pass

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            results = session.execute(query, params).fetchall()

            # Transform to activity log format
            activities = []
            for row in results:
                classification = 'human' if row.is_human else 'bot'
                confidence_pct = round(row.confidence * 100, 1)

                activity = {
                    'id': str(row.id),
                    'timestamp': row.timestamp.isoformat() if hasattr(row.timestamp, 'isoformat') else str(row.timestamp),
                    'type': 'verification',
                    'classification': classification,
                    'confidence': confidence_pct,
                    'source': row.website_origin or 'Unknown',
                    'ip': row.ip_address or 'Unknown',
                    'responseTime': row.response_time or 0
                }

                activities.append(activity)

            return jsonify({
                'success': True,
                'data': {
                    'activities': activities,
                    'count': len(activities),
                    'latest_timestamp': activities[0]['timestamp'] if activities else None
                },
                'timestamp': datetime.now().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting activity logs: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve activity logs'
            }
        }), 500


@logs_bp.route('/export', methods=['GET'])
@require_auth
def export_logs():
    """Export logs in various formats"""
    try:
        format_type = request.args.get('format', 'json')  # json, csv, excel
        time_range = request.args.get('timeRange', '24h')
        filter_type = request.args.get('filter', 'all')

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
            # Get filtered logs
            query = """
                SELECT
                    id,
                    timestamp,
                    is_human,
                    confidence,
                    ip_address,
                    user_agent,
                    website_origin,
                    response_time,
                    features
                FROM verifications
                WHERE timestamp >= ?
            """

            params = [start_time]

            # Apply filters
            if filter_type == 'human':
                query += " AND is_human = 1"
            elif filter_type == 'bot':
                query += " AND is_human = 0"

            query += " ORDER BY timestamp DESC"

            results = session.execute(query, params).fetchall()

            # For now, return a download URL (in a real implementation, you'd generate the file)
            download_url = f"/admin/downloads/logs_{format_type}_{int(datetime.now().timestamp())}.{format_type}"

            return jsonify({
                'success': True,
                'data': {
                    'download_url': download_url,
                    'format': format_type,
                    'record_count': len(results),
                    'generated_at': datetime.now().isoformat()
                },
                'timestamp': datetime.now().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error exporting logs: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to export logs'
            }
        }), 500


@logs_bp.route('/stats', methods=['GET'])
@require_auth
def get_logs_stats():
    """Get logs statistics for the dashboard"""
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
            # Get comprehensive stats
            stats_query = """
                SELECT
                    COUNT(*) as total_logs,
                    SUM(CASE WHEN is_human = 1 THEN 1 ELSE 0 END) as human_logs,
                    SUM(CASE WHEN is_human = 0 THEN 1 ELSE 0 END) as bot_logs,
                    AVG(confidence) as avg_confidence,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    COUNT(DISTINCT website_origin) as unique_origins
                FROM verifications
                WHERE timestamp >= ?
            """

            result = session.execute(stats_query, (start_time,)).fetchone()

            stats = {
                'total_logs': result.total_logs or 0,
                'human_logs': result.human_logs or 0,
                'bot_logs': result.bot_logs or 0,
                'avg_confidence': round(result.avg_confidence or 0, 3),
                'unique_ips': result.unique_ips or 0,
                'unique_origins': result.unique_origins or 0,
                'time_range': time_range
            }

            return jsonify({
                'success': True,
                'data': stats,
                'timestamp': datetime.now().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting logs stats: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve logs statistics'
            }
        }), 500
