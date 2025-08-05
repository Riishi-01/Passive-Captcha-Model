"""
Admin module for Passive CAPTCHA dashboard
Provides analytics, monitoring, and management endpoints
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template_string
import jwt

from app.database import get_analytics_data, cleanup_old_data, get_db_session, VerificationLog

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)


def verify_admin_token(token):
    """
    Verify admin authentication token
    """
    try:
        secret = current_app.config.get('ADMIN_SECRET', 'admin-secret-key')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload.get('admin', False)
    except:
        return False


def require_admin_auth(f):
    """
    Decorator to require admin authentication (updated to use robust auth service)
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header required'
                }
            }), 401

        token = auth_header.split(' ')[1]

        # Use robust authentication service instead of old verify_admin_token
        try:
            from app.services.robust_auth_service import get_robust_auth_service
            auth_service = get_robust_auth_service()
            
            if not auth_service:
                return jsonify({
                    'error': {
                        'code': 'SERVICE_UNAVAILABLE',
                        'message': 'Authentication service unavailable'
                    }
                }), 503

            # Validate JWT token
            payload = auth_service.validate_jwt_token(token)
            if not payload:
                return jsonify({
                    'error': {
                        'code': 'INVALID_TOKEN',
                        'message': 'Invalid or expired token'
                    }
                }), 401

            # Get session
            session = auth_service.validate_session(payload['session_id'])
            if not session:
                return jsonify({
                    'error': {
                        'code': 'SESSION_EXPIRED',
                        'message': 'Session expired or invalid'
                    }
                }), 401

            # Add user to request context
            request.current_user = {
                'user_id': session.user_id,
                'email': session.email,
                'role': session.role.value
            }
            request.current_session = session
            
        except Exception as e:
            current_app.logger.error(f"Auth error in require_admin_auth: {e}")
            return jsonify({
                'error': {
                    'code': 'AUTH_ERROR',
                    'message': 'Authentication error'
                }
            }), 401

        return f(*args, **kwargs)

    return decorated_function


# REMOVED: Duplicate login route - now handled by modern admin API
# @admin_bp.route('/login', methods=['POST'])
# Use app/api/admin_endpoints.py for all admin authentication


# REMOVED: Conflicting /analytics route - use dedicated analytics_endpoints.py instead
# @admin_bp.route('/analytics', methods=['GET'])
# Route conflicts with app.admin.analytics_endpoints blueprint routes


@admin_bp.route('/logs', methods=['GET'])
@require_admin_auth
def get_verification_logs():
    """
    Get recent verification logs with filtering
    """
    try:
        # Query parameters
        limit = min(int(request.args.get('limit', 50)), 1000)
        offset = int(request.args.get('offset', 0))
        is_human = request.args.get('is_human')
        origin = request.args.get('origin')
        hours = int(request.args.get('hours', 24))

        # Build query
        session = get_db_session()
        query = session.query(VerificationLog)

        # Apply time filter
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(VerificationLog.timestamp >= since)

        # Apply filters
        if is_human is not None:
            is_human_bool = is_human.lower() == 'true'
            query = query.filter(VerificationLog.is_human == is_human_bool)

        if origin:
            query = query.filter(VerificationLog.origin.ilike(f'%{origin}%'))

        # Get total count for pagination
        total_count = query.count()

        # Apply pagination and ordering
        logs = query.order_by(VerificationLog.timestamp.desc()).offset(offset).limit(limit).all()

        # Convert to dictionaries
        logs_data = [log.to_dict() for log in logs]

        # Close session
        session.close()

        return jsonify({
            'logs': logs_data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            },
            'filters': {
                'hours': hours,
                'is_human': is_human,
                'origin': origin
            }
        }), 200

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'INVALID_PARAMETER',
                'message': f'Invalid parameter: {str(e)}'
            }
        }), 400

    except Exception as e:
        print(f"Error in get_verification_logs: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Error retrieving logs'
            }
        }), 500


@admin_bp.route('/stats', methods=['GET'])
@require_admin_auth
def get_system_stats():
    """
    Get system performance and health statistics
    """
    try:
        from app.ml import get_model_info, is_model_loaded
        from app.database import get_last_verification_time

        # Database statistics
        session = get_db_session()
        total_verifications = session.query(VerificationLog).count()
        last_24h_count = session.query(VerificationLog).filter(
            VerificationLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        session.close()

        # Model information
        model_info = get_model_info()

        # System health
        system_stats = {
            'database': {
                'total_verifications': total_verifications,
                'last_24h_verifications': last_24h_count,
                'last_verification': get_last_verification_time(),
                'status': 'healthy'
            },
            'model': {
                'loaded': is_model_loaded(),
                'info': model_info,
                'status': 'healthy' if is_model_loaded() else 'error'
            },
            'api': {
                'status': 'healthy',
                'version': '1.0',
                'uptime': 'healthy'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        return jsonify(system_stats), 200

    except Exception as e:
        print(f"Error in get_system_stats: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Error retrieving system stats'
            }
        }), 500


@admin_bp.route('/cleanup', methods=['POST'])
@require_admin_auth
def cleanup_data():
    """
    Clean up old verification logs
    """
    try:
        data = request.get_json() or {}
        days = int(data.get('days', 30))

        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({
                'error': {
                    'code': 'INVALID_PARAMETER',
                    'message': 'Days must be between 1 and 365'
                }
            }), 400

        deleted_count = cleanup_old_data(days)

        return jsonify({
            'deleted_records': deleted_count,
            'cutoff_days': days,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'INVALID_PARAMETER',
                'message': f'Invalid parameter: {str(e)}'
            }
        }), 400

    except Exception as e:
        print(f"Error in cleanup_data: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Error during cleanup'
            }
        }), 500


@admin_bp.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """
    Serve modern admin dashboard HTML page
    """
    import os
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modern_dashboard.html')

    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard_html = f.read()
        return dashboard_html
    except FileNotFoundError:
        # Fallback to basic dashboard
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passive CAPTCHA Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; }
        .header { background: #2563eb; color: white; padding: 1rem 2rem; }
        .header h1 { font-size: 1.5rem; font-weight: 600; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 1.5rem; }
        .card h3 { font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem; color: #374151; }
        .stat-value { font-size: 2rem; font-weight: 700; color: #2563eb; }
        .stat-label { font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem; }
        .btn { background: #2563eb; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
        .btn:hover { background: #1d4ed8; }
        .status-healthy { color: #059669; font-weight: 600; }
        .status-error { color: #dc2626; font-weight: 600; }
        .login-form { max-width: 400px; margin: 4rem auto; }
        .input { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 6px; margin-bottom: 1rem; }
        #dashboard { display: none; }
        .error { color: #dc2626; margin-top: 0.5rem; }
    </style>
</head>
<body>
    <div id="login-section">
        <div class="login-form">
            <div class="card">
                <h3>Admin Login</h3>
                <input type="password" id="password" class="input" placeholder="Enter admin password">
                <button onclick="login()" class="btn">Login</button>
                <div id="login-error" class="error"></div>
            </div>
        </div>
    </div>

    <div id="dashboard">
        <div class="header">
            <h1>Passive CAPTCHA Admin Dashboard</h1>
        </div>

        <div class="container">
            <div class="grid" id="stats-grid">
                <!-- Stats will be loaded here -->
            </div>

            <div class="card">
                <h3>Recent Verification Logs</h3>
                <button onclick="loadLogs()" class="btn">Refresh Logs</button>
                <div id="logs-container" style="margin-top: 1rem;">
                    <!-- Logs will be loaded here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let authToken = localStorage.getItem('admin_token');

        if (authToken) {
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
            loadDashboard();
        }

        async function login() {
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('login-error');

            try {
                const response = await fetch('/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });

                const data = await response.json();

                if (response.ok) {
                    authToken = data.token;
                    localStorage.setItem('admin_token', authToken);
                    document.getElementById('login-section').style.display = 'none';
                    document.getElementById('dashboard').style.display = 'block';
                    loadDashboard();
                } else {
                    errorDiv.textContent = data.error.message;
                }
            } catch (error) {
                errorDiv.textContent = 'Login failed. Please try again.';
            }
        }

        async function loadDashboard() {
            await Promise.all([loadStats(), loadAnalytics(), loadLogs()]);
        }

        async function loadStats() {
            try {
                const response = await fetch('/admin/stats', {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                const data = await response.json();

                const statsGrid = document.getElementById('stats-grid');
                statsGrid.innerHTML = `
                    <div class="card">
                        <h3>Database Status</h3>
                        <div class="stat-value">${data.database.total_verifications}</div>
                        <div class="stat-label">Total Verifications</div>
                        <div class="status-healthy">Status: ${data.database.status}</div>
                    </div>
                    <div class="card">
                        <h3>ML Model Status</h3>
                        <div class="stat-value">${data.model.loaded ? 'Loaded' : 'Error'}</div>
                        <div class="stat-label">Model: ${data.model.info.algorithm || 'Unknown'}</div>
                        <div class="${data.model.status === 'healthy' ? 'status-healthy' : 'status-error'}">
                            Status: ${data.model.status}
                        </div>
                    </div>
                    <div class="card">
                        <h3>24 Hour Activity</h3>
                        <div class="stat-value">${data.database.last_24h_verifications}</div>
                        <div class="stat-label">Verifications</div>
                        <div class="status-healthy">API: ${data.api.status}</div>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }

        async function loadAnalytics() {
            try {
                const response = await fetch('/admin/analytics?hours=24', {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                const data = await response.json();
                console.log('Analytics:', data);
            } catch (error) {
                console.error('Failed to load analytics:', error);
            }
        }

        async function loadLogs() {
            try {
                const response = await fetch('/admin/logs?limit=10', {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                const data = await response.json();

                const logsContainer = document.getElementById('logs-container');
                const logs = data.logs.map(log => `
                    <div style="border-bottom: 1px solid #e5e7eb; padding: 0.75rem 0;">
                        <strong>${log.isHuman ? 'Human' : 'Bot'}</strong>
                        (${(log.confidence * 100).toFixed(1)}% confidence) -
                        ${log.origin || 'Unknown origin'} -
                        ${new Date(log.timestamp).toLocaleString()}
                    </div>
                `).join('');

                logsContainer.innerHTML = logs || '<p>No recent logs found.</p>';
            } catch (error) {
                console.error('Failed to load logs:', error);
            }
        }

        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (authToken && document.getElementById('dashboard').style.display !== 'none') {
                loadDashboard();
            }
        }, 30000);
    </script>
</body>
</html>
    """

    return render_template_string(dashboard_html)


@admin_bp.errorhandler(401)
def handle_unauthorized(e):
    """Handle unauthorized access errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Admin authentication required'
        }
    }), 401


@admin_bp.errorhandler(403)
def handle_forbidden(e):
    """Handle forbidden access errors"""
    return jsonify({
        'error': {
            'code': 'FORBIDDEN',
            'message': 'Access forbidden'
        }
    }), 403
