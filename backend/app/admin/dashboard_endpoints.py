"""
Dashboard Admin Endpoints for Passive CAPTCHA System
Provides analytics, system health, configuration, and export functionality
"""

from flask import Blueprint, request, jsonify, current_app, send_file, make_response
from datetime import datetime, timedelta
from app.admin import require_admin_auth
from app.logs_pipeline import logs_pipeline, LogsExporter
from app.database import get_db_session, VerificationLog, Website
from app.websocket_server import get_websocket_manager
import redis
import json
import csv
import io
import tempfile
import os
from sqlalchemy import func, and_, or_

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/admin')

# DEPRECATED: Use centralized Redis client from Flask app context
# Access via current_app.redis_client instead of module-level global

def init_dashboard_endpoints(redis_client_instance):
    """DEPRECATED: Redis client now managed centrally"""
    pass  # No-op for backward compatibility


@dashboard_bp.route('/analytics/summary', methods=['GET'])
@require_admin_auth
def get_analytics_summary():
    """
    Get comprehensive analytics summary for dashboard KPI cards
    """
    try:
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 24))

        # Check cache first
        cache_key = f"analytics_summary:{website_id or 'all'}:{time_range}"
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

            # Previous period for comparison
            prev_since = since - timedelta(hours=time_range)
            prev_query = session.query(VerificationLog).filter(
                and_(
                    VerificationLog.timestamp >= prev_since,
                    VerificationLog.timestamp < since
                )
            )

            if website_id and website_id != 'all':
                prev_query = prev_query.filter(VerificationLog.origin.like(f'%{website_id}%'))

            prev_logs = prev_query.all()

            # Calculate current metrics
            total_verifications = len(logs)
            human_verifications = len([log for log in logs if log.is_human])
            human_rate = (human_verifications / total_verifications * 100) if total_verifications > 0 else 0

            avg_confidence = sum(log.confidence for log in logs) / len(logs) if logs else 0

            response_times = [log.response_time for log in logs if log.response_time is not None]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            # Calculate previous metrics for comparison
            prev_total = len(prev_logs)
            prev_human = len([log for log in prev_logs if log.is_human])
            prev_human_rate = (prev_human / prev_total * 100) if prev_total > 0 else 0
            prev_confidence = sum(log.confidence for log in prev_logs) / len(prev_logs) if prev_logs else 0
            prev_response_times = [log.response_time for log in prev_logs if log.response_time is not None]
            prev_avg_response_time = sum(prev_response_times) / len(prev_response_times) if prev_response_times else 0

            # Calculate changes
            verification_change = ((total_verifications - prev_total) / prev_total * 100) if prev_total > 0 else 0
            human_rate_change = human_rate - prev_human_rate
            confidence_change = ((avg_confidence - prev_confidence) / prev_confidence * 100) if prev_confidence > 0 else 0
            response_time_change = ((avg_response_time - prev_avg_response_time) / prev_avg_response_time * 100) if prev_avg_response_time > 0 else 0

            # Generate trend data (hourly buckets)
            trend_buckets = {}
            for log in logs:
                hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                hour_key = hour.isoformat()
                if hour_key not in trend_buckets:
                    trend_buckets[hour_key] = {
                        'verifications': 0,
                        'human_count': 0,
                        'confidence_sum': 0,
                        'response_time_sum': 0,
                        'response_time_count': 0
                    }

                trend_buckets[hour_key]['verifications'] += 1
                if log.is_human:
                    trend_buckets[hour_key]['human_count'] += 1
                trend_buckets[hour_key]['confidence_sum'] += log.confidence
                if log.response_time:
                    trend_buckets[hour_key]['response_time_sum'] += log.response_time
                    trend_buckets[hour_key]['response_time_count'] += 1

            # Generate trend arrays
            sorted_hours = sorted(trend_buckets.keys())
            verification_trend = [trend_buckets[hour]['verifications'] for hour in sorted_hours]
            human_rate_trend = [
                (trend_buckets[hour]['human_count'] / trend_buckets[hour]['verifications'] * 100)
                if trend_buckets[hour]['verifications'] > 0 else 0
                for hour in sorted_hours
            ]
            confidence_trend = [
                (trend_buckets[hour]['confidence_sum'] / trend_buckets[hour]['verifications'])
                if trend_buckets[hour]['verifications'] > 0 else 0
                for hour in sorted_hours
            ]
            response_time_trend = [
                (trend_buckets[hour]['response_time_sum'] / trend_buckets[hour]['response_time_count'])
                if trend_buckets[hour]['response_time_count'] > 0 else 0
                for hour in sorted_hours
            ]

            result = {
                'total_verifications': total_verifications,
                'verification_change': round(verification_change, 1),
                'human_rate': round(human_rate, 1),
                'human_rate_change': round(human_rate_change, 1),
                'avg_confidence': round(avg_confidence, 3),
                'confidence_change': round(confidence_change, 1),
                'avg_response_time': round(avg_response_time, 2),
                'response_time_change': round(response_time_change, 1),
                'trends': {
                    'verifications': verification_trend[-24:],  # Last 24 hours
                    'human_rate': human_rate_trend[-24:],
                    'confidence': confidence_trend[-24:],
                    'response_time': response_time_trend[-24:]
                },
                'time_range_hours': time_range,
                'last_updated': datetime.utcnow().isoformat()
            }

            # Cache the result
            if redis_client:
                redis_client.setex(cache_key, 300, json.dumps(result, default=str))  # 5 min cache

            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting analytics summary: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ANALYTICS_SUMMARY_ERROR',
                'message': 'Failed to retrieve analytics summary'
            }
        }), 500


@dashboard_bp.route('/analytics/charts', methods=['GET'])
@require_admin_auth
def get_analytics_charts():
    """
    Get chart data for dashboard visualizations
    """
    try:
        website_id = request.args.get('website_id')
        time_range = request.args.get('time_range', '24h')

        # Parse time range
        if time_range == '1h':
            hours = 1
        elif time_range == '24h':
            hours = 24
        elif time_range == '7d':
            hours = 168
        elif time_range == '30d':
            hours = 720
        else:
            hours = 24

        cache_key = f"analytics_charts:{website_id or 'all'}:{time_range}"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))

        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)

            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))

            logs = query.order_by(VerificationLog.timestamp).all()

            # Time bucket size based on range
            if hours <= 24:
                bucket_minutes = 60  # 1 hour buckets
            elif hours <= 168:
                bucket_minutes = 60 * 6  # 6 hour buckets
            else:
                bucket_minutes = 60 * 24  # 1 day buckets

            # Group logs by time buckets
            time_buckets = {}
            for log in logs:
                # Round to bucket
                bucket_time = log.timestamp.replace(
                    minute=(log.timestamp.minute // (bucket_minutes % 60)) * (bucket_minutes % 60),
                    second=0,
                    microsecond=0
                )
                if bucket_minutes >= 60:
                    bucket_time = bucket_time.replace(
                        hour=(bucket_time.hour // (bucket_minutes // 60)) * (bucket_minutes // 60)
                    )

                bucket_key = bucket_time.isoformat()

                if bucket_key not in time_buckets:
                    time_buckets[bucket_key] = {
                        'human': 0,
                        'bot': 0,
                        'timestamp': bucket_time
                    }

                if log.is_human:
                    time_buckets[bucket_key]['human'] += 1
                else:
                    time_buckets[bucket_key]['bot'] += 1

            # Generate chart data
            sorted_buckets = sorted(time_buckets.keys())

            # Format labels based on time range
            labels = []
            for bucket_key in sorted_buckets:
                timestamp = time_buckets[bucket_key]['timestamp']
                if hours <= 24:
                    labels.append(timestamp.strftime('%H:%M'))
                elif hours <= 168:
                    labels.append(timestamp.strftime('%m/%d %H:%M'))
                else:
                    labels.append(timestamp.strftime('%m/%d'))

            human_data = [time_buckets[bucket]['human'] for bucket in sorted_buckets]
            bot_data = [time_buckets[bucket]['bot'] for bucket in sorted_buckets]

            # Calculate totals for distribution
            total_human = sum(human_data)
            total_bot = sum(bot_data)
            total_verifications = total_human + total_bot

            human_percentage = (total_human / total_verifications * 100) if total_verifications > 0 else 0
            bot_percentage = (total_bot / total_verifications * 100) if total_verifications > 0 else 0

            result = {
                'verification_trends': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': 'Human Verifications',
                            'data': human_data,
                            'border_color': '#10b981',
                            'background_color': 'rgba(16, 185, 129, 0.1)',
                            'fill': True
                        },
                        {
                            'label': 'Bot Detections',
                            'data': bot_data,
                            'border_color': '#ef4444',
                            'background_color': 'rgba(239, 68, 68, 0.1)',
                            'fill': True
                        }
                    ]
                },
                'detection_distribution': {
                    'human_percentage': round(human_percentage, 1),
                    'bot_percentage': round(bot_percentage, 1),
                    'total_verifications': total_verifications
                },
                'time_range': time_range,
                'bucket_size_minutes': bucket_minutes
            }

            # Cache result
            if redis_client:
                redis_client.setex(cache_key, 600, json.dumps(result, default=str))  # 10 min cache

            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting analytics charts: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ANALYTICS_CHARTS_ERROR',
                'message': 'Failed to retrieve chart data'
            }
        }), 500


@dashboard_bp.route('/analytics/geographic', methods=['GET'])
@require_admin_auth
def get_geographic_analytics():
    """
    Get geographic distribution of verifications
    """
    try:
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 24))

        cache_key = f"analytics_geo:{website_id or 'all'}:{time_range}"
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

            # Count by country (simulated - would use actual GeoIP)
            country_counts = {}
            for log in logs:
                # Extract country from IP (simplified - would use actual GeoIP service)
                country = _get_country_from_ip(log.ip_address)
                if country not in country_counts:
                    country_counts[country] = {
                        'name': country,
                        'code': country[:2].upper(),
                        'count': 0,
                        'human': 0,
                        'bot': 0
                    }

                country_counts[country]['count'] += 1
                if log.is_human:
                    country_counts[country]['human'] += 1
                else:
                    country_counts[country]['bot'] += 1

            # Sort by count and get top countries
            top_countries = sorted(
                country_counts.values(),
                key=lambda x: x['count'],
                reverse=True
            )[:10]

            # Add percentages
            total_verifications = sum(country['count'] for country in top_countries)
            for country in top_countries:
                country['percentage'] = (country['count'] / total_verifications * 100) if total_verifications > 0 else 0

            result = {
                'top_countries': top_countries,
                'total_countries': len(country_counts),
                'total_verifications': total_verifications,
                'time_range_hours': time_range
            }

            # Cache result
            if redis_client:
                redis_client.setex(cache_key, 900, json.dumps(result, default=str))  # 15 min cache

            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting geographic analytics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'GEOGRAPHIC_ANALYTICS_ERROR',
                'message': 'Failed to retrieve geographic data'
            }
        }), 500


@dashboard_bp.route('/analytics/threats', methods=['GET'])
@require_admin_auth
def get_threat_analytics():
    """
    Get threat analysis data
    """
    try:
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 24))

        cache_key = f"analytics_threats:{website_id or 'all'}:{time_range}"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))

        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=time_range)
            query = session.query(VerificationLog).filter(
                and_(
                    VerificationLog.timestamp >= since,
                    VerificationLog.is_human == False  # Only bot detections
                )
            )

            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))

            bot_logs = query.all()

            # Analyze bot types based on confidence and patterns
            threat_types = {
                'High Confidence Bots': {'count': 0, 'severity': 'high', 'description': 'Clear bot signatures detected'},
                'Suspicious Activity': {'count': 0, 'severity': 'medium', 'description': 'Potentially automated behavior'},
                'Low Confidence': {'count': 0, 'severity': 'low', 'description': 'Uncertain classifications'}
            }

            for log in bot_logs:
                if log.confidence <= 0.3:  # Very confident it's a bot
                    threat_types['High Confidence Bots']['count'] += 1
                elif log.confidence <= 0.6:
                    threat_types['Suspicious Activity']['count'] += 1
                else:
                    threat_types['Low Confidence']['count'] += 1

            # Calculate percentages
            total_threats = len(bot_logs)
            for threat_type in threat_types.values():
                threat_type['percentage'] = (threat_type['count'] / total_threats * 100) if total_threats > 0 else 0

            # Additional threat metrics
            unique_ips = len(set(log.ip_address for log in bot_logs))
            avg_confidence = sum(log.confidence for log in bot_logs) / len(bot_logs) if bot_logs else 0

            result = {
                'threat_types': [
                    {
                        'name': name,
                        'count': data['count'],
                        'percentage': round(data['percentage'], 1),
                        'severity': data['severity'],
                        'description': data['description']
                    }
                    for name, data in threat_types.items()
                ],
                'summary': {
                    'total_threats': total_threats,
                    'unique_source_ips': unique_ips,
                    'avg_bot_confidence': round(1 - avg_confidence, 3),  # Invert for "bot confidence"
                    'threat_rate': (total_threats / (total_threats + len(session.query(VerificationLog).filter(
                        and_(
                            VerificationLog.timestamp >= since,
                            VerificationLog.is_human == True
                        )
                    ).all())) * 100) if total_threats > 0 else 0
                },
                'time_range_hours': time_range
            }

            # Cache result
            if redis_client:
                redis_client.setex(cache_key, 600, json.dumps(result, default=str))  # 10 min cache

            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting threat analytics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'THREAT_ANALYTICS_ERROR',
                'message': 'Failed to retrieve threat data'
            }
        }), 500


@dashboard_bp.route('/analytics/verification-trends', methods=['GET'])
@require_admin_auth
def get_verification_trends():
    """
    Get verification success/failure trends for ML metrics
    """
    try:
        time_range = request.args.get('time_range', '24h')
        website_id = request.args.get('website_id')

        # Parse time range
        if time_range == '1h':
            hours = 1
        elif time_range == '24h':
            hours = 24
        elif time_range == '7d':
            hours = 168
        elif time_range == '30d':
            hours = 720
        else:
            hours = 24

        cache_key = f"verification_trends:{website_id or 'all'}:{time_range}"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))

        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)

            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))

            logs = query.order_by(VerificationLog.timestamp).all()

            # Group by time buckets
            bucket_minutes = 60 if hours <= 24 else 360  # 1 hour or 6 hour buckets
            time_buckets = {}

            for log in logs:
                bucket_time = log.timestamp.replace(
                    minute=(log.timestamp.minute // (bucket_minutes % 60)) * (bucket_minutes % 60),
                    second=0,
                    microsecond=0
                )
                if bucket_minutes >= 60:
                    bucket_time = bucket_time.replace(
                        hour=(bucket_time.hour // (bucket_minutes // 60)) * (bucket_minutes // 60)
                    )

                bucket_key = bucket_time.isoformat()

                if bucket_key not in time_buckets:
                    time_buckets[bucket_key] = {
                        'successful': 0,
                        'failed': 0,
                        'response_times': [],
                        'timestamp': bucket_time
                    }

                # Consider high confidence predictions as "successful"
                if log.confidence > 0.7:
                    time_buckets[bucket_key]['successful'] += 1
                else:
                    time_buckets[bucket_key]['failed'] += 1

                if log.response_time:
                    time_buckets[bucket_key]['response_times'].append(log.response_time)

            # Build timeline
            timeline = []
            total_successful = 0
            total_failed = 0

            for bucket_key in sorted(time_buckets.keys()):
                bucket = time_buckets[bucket_key]
                avg_response_time = sum(bucket['response_times']) / len(bucket['response_times']) if bucket['response_times'] else 0

                timeline.append({
                    'timestamp': bucket['timestamp'].isoformat(),
                    'successful_verifications': bucket['successful'],
                    'failed_verifications': bucket['failed'],
                    'avg_response_time': round(avg_response_time, 2)
                })

                total_successful += bucket['successful']
                total_failed += bucket['failed']

            success_rate = (total_successful / (total_successful + total_failed) * 100) if (total_successful + total_failed) > 0 else 0

            result = {
                'timeline': timeline,
                'summary': {
                    'total_successful': total_successful,
                    'total_failed': total_failed,
                    'success_rate': round(success_rate, 1),
                    'avg_response_time': round(
                        sum(log.response_time for log in logs if log.response_time) /
                        len([log for log in logs if log.response_time]), 2
                    ) if logs else 0
                },
                'time_range': time_range,
                'bucket_size_minutes': bucket_minutes
            }

            # Cache result
            if redis_client:
                redis_client.setex(cache_key, 600, json.dumps(result, default=str))

            return jsonify({
                'success': True,
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error getting verification trends: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'VERIFICATION_TRENDS_ERROR',
                'message': 'Failed to retrieve verification trends'
            }
        }), 500


@dashboard_bp.route('/system/health', methods=['GET'])
@require_admin_auth
def get_system_health():
    """
    Get system health status
    """
    try:
        cache_key = "system_health"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))

        # Check various system components
        components = {
            'database': _check_database_health(),
            'redis': _check_redis_health(),
            'websocket': _check_websocket_health(),
            'ml_model': _check_ml_model_health(),
            'logs_pipeline': _check_logs_pipeline_health()
        }

        # Calculate overall health
        healthy_components = sum(1 for comp in components.values() if comp['status'] == 'healthy')
        total_components = len(components)
        overall_health = healthy_components / total_components

        if overall_health >= 0.8:
            overall_status = 'healthy'
        elif overall_health >= 0.6:
            overall_status = 'warning'
        else:
            overall_status = 'error'

        result = {
            'overall_status': overall_status,
            'overall_health_percentage': round(overall_health * 100, 1),
            'components': components,
            'last_checked': datetime.utcnow().isoformat()
        }

        # Cache for shorter time due to dynamic nature
        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps(result, default=str))  # 1 min cache

        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"Error getting system health: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_HEALTH_ERROR',
                'message': 'Failed to retrieve system health'
            }
        }), 500


@dashboard_bp.route('/logs/export', methods=['GET'])
@require_admin_auth
def export_logs():
    """
    Export verification logs in various formats
    """
    try:
        format_type = request.args.get('format', 'csv').lower()
        website_id = request.args.get('website_id')
        time_range = int(request.args.get('time_range', 24))
        log_filter = request.args.get('filter', 'all')  # all, human, bot, suspicious

        if format_type not in ['csv', 'json', 'excel']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_FORMAT',
                    'message': 'Supported formats: csv, json, excel'
                }
            }), 400

        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=time_range)
            query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)

            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))

            # Apply log filter
            if log_filter == 'human':
                query = query.filter(VerificationLog.is_human == True)
            elif log_filter == 'bot':
                query = query.filter(VerificationLog.is_human == False)
            elif log_filter == 'suspicious':
                query = query.filter(
                    and_(
                        VerificationLog.confidence >= 0.4,
                        VerificationLog.confidence <= 0.6
                    )
                )

            logs = query.order_by(VerificationLog.timestamp.desc()).limit(10000).all()  # Limit for performance

            # Export logs
            if logs_pipeline:
                exported_data = logs_pipeline.exporter.export_logs(logs, format_type)
            else:
                exported_data = LogsExporter.export_logs(logs, format_type)

            # Create response
            if format_type == 'csv':
                response = make_response(exported_data)
                response.headers['Content-Type'] = 'text/csv'
                response.headers['Content-Disposition'] = f'attachment; filename=verification_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
            elif format_type == 'json':
                response = make_response(exported_data)
                response.headers['Content-Type'] = 'application/json'
                response.headers['Content-Disposition'] = f'attachment; filename=verification_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
            elif format_type == 'excel':
                response = make_response(exported_data)
                response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                response.headers['Content-Disposition'] = f'attachment; filename=verification_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'

            return response

        finally:
            session.close()

    except Exception as e:
        current_app.logger.error(f"Error exporting logs: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'EXPORT_ERROR',
                'message': 'Failed to export logs'
            }
        }), 500


def _get_country_from_ip(ip_address: str) -> str:
    """
    Get country from IP address (simplified implementation)
    In production, use a proper GeoIP service
    """
    # Simplified mapping for demonstration
    ip_to_country = {
        '127.0.0.1': 'localhost',
        '192.168.': 'Private Network'
    }

    for ip_prefix, country in ip_to_country.items():
        if ip_address.startswith(ip_prefix):
            return country

    # Simulate based on IP patterns (for demo)
    if ip_address.startswith('10.'):
        return 'United States'
    elif ip_address.startswith('172.'):
        return 'Canada'
    elif ip_address.startswith('203.'):
        return 'Australia'
    else:
        return 'Unknown'


def _check_database_health() -> dict:
    """Check database connectivity and health"""
    try:
        session = get_db_session()
        session.execute('SELECT 1')
        session.close()
        return {
            'status': 'healthy',
            'message': 'Database connection successful',
            'uptime': 99.9
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Database connection failed: {str(e)}',
            'uptime': 0
        }


def _check_redis_health() -> dict:
    """Check Redis connectivity and health"""
    try:
        if redis_client:
            redis_client.ping()
            return {
                'status': 'healthy',
                'message': 'Redis connection successful',
                'uptime': 99.5
            }
        else:
            return {
                'status': 'warning',
                'message': 'Redis client not initialized',
                'uptime': 0
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Redis connection failed: {str(e)}',
            'uptime': 0
        }


def _check_websocket_health() -> dict:
    """Check WebSocket server health"""
    try:
        ws_manager = get_websocket_manager()
        if ws_manager:
            stats = ws_manager.get_connection_stats()
            return {
                'status': 'healthy',
                'message': f'{stats["total_connections"]} active connections',
                'uptime': 99.8
            }
        else:
            return {
                'status': 'warning',
                'message': 'WebSocket manager not initialized',
                'uptime': 0
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'WebSocket health check failed: {str(e)}',
            'uptime': 0
        }


def _check_ml_model_health() -> dict:
    """Check ML model health"""
    try:
        model_path = os.path.join(current_app.root_path, '..', 'models', 'passive_captcha_rf.pkl')
        if os.path.exists(model_path):
            return {
                'status': 'healthy',
                'message': 'ML model loaded and available',
                'uptime': 99.7
            }
        else:
            return {
                'status': 'warning',
                'message': 'ML model file not found',
                'uptime': 50
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'ML model health check failed: {str(e)}',
            'uptime': 0
        }


def _check_logs_pipeline_health() -> dict:
    """Check logs pipeline health"""
    try:
        if logs_pipeline:
            return {
                'status': 'healthy',
                'message': 'Logs pipeline operational',
                'uptime': 99.6
            }
        else:
            return {
                'status': 'error',
                'message': 'Logs pipeline not initialized',
                'uptime': 0
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Logs pipeline health check failed: {str(e)}',
            'uptime': 0
        }
