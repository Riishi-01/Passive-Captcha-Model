"""
Production-Grade WebSocket Server for Passive CAPTCHA Dashboard
Handles real-time updates, log streaming, and live dashboard data
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request, current_app
import redis
import json
import jwt
from datetime import datetime
from typing import Dict, Any, Set
import logging
from app.logs_pipeline import logs_pipeline, LogType, LogLevel


class WebSocketManager:
    """Manages WebSocket connections and real-time updates"""

    def __init__(self, socketio: SocketIO, redis_client: redis.Redis):
        self.socketio = socketio
        self.redis = redis_client
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.room_connections: Dict[str, Set[str]] = {}

        # Setup event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Validate authentication
                if not self._authenticate_connection(auth):
                    current_app.logger.warning(f"Unauthorized WebSocket connection attempt from {request.remote_addr}")
                    return False

                connection_id = request.sid
                self.active_connections[connection_id] = {
                    'connected_at': datetime.utcnow(),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'rooms': set(),
                    'authenticated': True
                }

                current_app.logger.info(f"WebSocket client connected: {connection_id}")

                # Send welcome message
                emit('connection_established', {
                    'connection_id': connection_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'connected'
                })

                # Log connection event
                if logs_pipeline:
                    logs_pipeline.log_system_event(
                        f"WebSocket connection established",
                        LogLevel.INFO,
                        metadata={
                            'connection_id': connection_id,
                            'ip_address': request.remote_addr
                        }
                    )

                return True

            except Exception as e:
                current_app.logger.error(f"Error handling WebSocket connection: {e}")
                return False

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                connection_id = request.sid

                if connection_id in self.active_connections:
                    # Leave all rooms
                    for room in self.active_connections[connection_id].get('rooms', set()).copy():
                        self._leave_room_internal(connection_id, room)

                    # Remove connection
                    del self.active_connections[connection_id]

                    current_app.logger.info(f"WebSocket client disconnected: {connection_id}")

                    # Log disconnection event
                    if logs_pipeline:
                        logs_pipeline.log_system_event(
                            f"WebSocket connection closed",
                            LogLevel.INFO,
                            metadata={'connection_id': connection_id}
                        )

            except Exception as e:
                current_app.logger.error(f"Error handling WebSocket disconnection: {e}")

        @self.socketio.on('join_dashboard_room')
        def handle_join_dashboard_room(data):
            """Handle joining dashboard room for live updates"""
            try:
                connection_id = request.sid
                website_id = data.get('website_id', 'all')
                room_name = f"dashboard_{website_id}"

                self._join_room_internal(connection_id, room_name)

                emit('dashboard_room_joined', {
                    'room': room_name,
                    'website_id': website_id,
                    'status': 'success'
                })

                # Send initial dashboard data
                self._send_initial_dashboard_data(website_id)

            except Exception as e:
                current_app.logger.error(f"Error joining dashboard room: {e}")
                emit('error', {'message': 'Failed to join dashboard room'})

        @self.socketio.on('leave_dashboard_room')
        def handle_leave_dashboard_room(data):
            """Handle leaving dashboard room"""
            try:
                connection_id = request.sid
                website_id = data.get('website_id', 'all')
                room_name = f"dashboard_{website_id}"

                self._leave_room_internal(connection_id, room_name)

                emit('dashboard_room_left', {
                    'room': room_name,
                    'website_id': website_id,
                    'status': 'success'
                })

            except Exception as e:
                current_app.logger.error(f"Error leaving dashboard room: {e}")
                emit('error', {'message': 'Failed to leave dashboard room'})

        @self.socketio.on('subscribe_logs')
        def handle_subscribe_logs(data):
            """Handle logs subscription with filters"""
            try:
                connection_id = request.sid
                filters = data.get('filters', {})
                room_name = 'logs_stream'

                self._join_room_internal(connection_id, room_name)

                # Store filters for this connection
                if logs_pipeline:
                    logs_pipeline.streaming_manager.join_room(connection_id, room_name, filters)

                emit('logs_subscribed', {
                    'room': room_name,
                    'filters': filters,
                    'status': 'success'
                })

            except Exception as e:
                current_app.logger.error(f"Error subscribing to logs: {e}")
                emit('error', {'message': 'Failed to subscribe to logs'})

        @self.socketio.on('unsubscribe_logs')
        def handle_unsubscribe_logs():
            """Handle logs unsubscription"""
            try:
                connection_id = request.sid
                room_name = 'logs_stream'

                self._leave_room_internal(connection_id, room_name)

                if logs_pipeline:
                    logs_pipeline.streaming_manager.leave_room(connection_id, room_name)

                emit('logs_unsubscribed', {
                    'room': room_name,
                    'status': 'success'
                })

            except Exception as e:
                current_app.logger.error(f"Error unsubscribing from logs: {e}")
                emit('error', {'message': 'Failed to unsubscribe from logs'})

        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping/keepalive"""
            emit('pong', {'timestamp': datetime.utcnow().isoformat()})

        @self.socketio.on('request_dashboard_update')
        def handle_dashboard_update_request(data):
            """Handle manual dashboard update request"""
            try:
                website_id = data.get('website_id', 'all')
                self._send_dashboard_update(website_id)

            except Exception as e:
                current_app.logger.error(f"Error handling dashboard update request: {e}")
                emit('error', {'message': 'Failed to update dashboard'})

    def _authenticate_connection(self, auth) -> bool:
        """Authenticate WebSocket connection"""
        try:
            if not auth or 'token' not in auth:
                return False

            token = auth['token']
            secret = current_app.config.get('ADMIN_SECRET', 'Admin123')

            # For admin connections, verify JWT token
            try:
                decoded = jwt.decode(token, secret, algorithms=['HS256'])
                return decoded.get('admin', False)
            except jwt.InvalidTokenError:
                return False

        except Exception as e:
            current_app.logger.error(f"Authentication error: {e}")
            return False

    def _join_room_internal(self, connection_id: str, room_name: str):
        """Internal method to join room"""
        join_room(room_name)

        if connection_id in self.active_connections:
            self.active_connections[connection_id]['rooms'].add(room_name)

        if room_name not in self.room_connections:
            self.room_connections[room_name] = set()
        self.room_connections[room_name].add(connection_id)

    def _leave_room_internal(self, connection_id: str, room_name: str):
        """Internal method to leave room"""
        leave_room(room_name)

        if connection_id in self.active_connections:
            self.active_connections[connection_id]['rooms'].discard(room_name)

        if room_name in self.room_connections:
            self.room_connections[room_name].discard(connection_id)
            if not self.room_connections[room_name]:
                del self.room_connections[room_name]

    def _send_initial_dashboard_data(self, website_id: str):
        """Send initial dashboard data to client"""
        try:
            if logs_pipeline:
                # Get aggregated metrics
                metrics = logs_pipeline.aggregator.get_verification_metrics(website_id, 24)
                ml_metrics = logs_pipeline.aggregator.get_ml_model_metrics(24)

                emit('dashboard_initial_data', {
                    'website_id': website_id,
                    'metrics': metrics,
                    'ml_metrics': ml_metrics,
                    'timestamp': datetime.utcnow().isoformat()
                })

        except Exception as e:
            current_app.logger.error(f"Error sending initial dashboard data: {e}")

    def _send_dashboard_update(self, website_id: str):
        """Send dashboard update to all clients in room"""
        try:
            room_name = f"dashboard_{website_id}"

            if logs_pipeline:
                # Get updated metrics
                metrics = logs_pipeline.aggregator.get_verification_metrics(website_id, 1)  # Last hour
                ml_metrics = logs_pipeline.aggregator.get_ml_model_metrics(1)

                self.socketio.emit('dashboard_update', {
                    'website_id': website_id,
                    'metrics': metrics,
                    'ml_metrics': ml_metrics,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room_name)

        except Exception as e:
            current_app.logger.error(f"Error sending dashboard update: {e}")

    def broadcast_verification_event(self, verification_data: Dict[str, Any]):
        """Broadcast verification event to all dashboard clients"""
        try:
            # Determine which rooms to broadcast to
            website_id = verification_data.get('website_id', 'unknown')

            # Broadcast to specific website room
            room_name = f"dashboard_{website_id}"
            if room_name in self.room_connections:
                self.socketio.emit('new_verification', verification_data, room=room_name)

            # Broadcast to 'all websites' room
            all_room = "dashboard_all"
            if all_room in self.room_connections:
                self.socketio.emit('new_verification', verification_data, room=all_room)

        except Exception as e:
            current_app.logger.error(f"Error broadcasting verification event: {e}")

    def broadcast_metric_update(self, metric_type: str, value: Any, website_id: str = None):
        """Broadcast metric update to dashboard clients"""
        try:
            update_data = {
                'metric_type': metric_type,
                'value': value,
                'website_id': website_id,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Determine rooms to broadcast to
            rooms = []
            if website_id:
                rooms.append(f"dashboard_{website_id}")
            rooms.append("dashboard_all")

            for room_name in rooms:
                if room_name in self.room_connections:
                    self.socketio.emit('metric_update', update_data, room=room_name)

        except Exception as e:
            current_app.logger.error(f"Error broadcasting metric update: {e}")

    def broadcast_system_alert(self, alert_data: Dict[str, Any]):
        """Broadcast system alert to all connected clients"""
        try:
            self.socketio.emit('system_alert', {
                **alert_data,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            current_app.logger.error(f"Error broadcasting system alert: {e}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            'total_connections': len(self.active_connections),
            'active_rooms': len(self.room_connections),
            'room_details': {
                room: len(connections)
                for room, connections in self.room_connections.items()
            },
            'connections_by_room': dict(self.room_connections)
        }


# Global WebSocket manager instance
websocket_manager = None


def init_websocket_server(app, socketio: SocketIO, redis_client: redis.Redis):
    """Initialize WebSocket server"""
    global websocket_manager
    websocket_manager = WebSocketManager(socketio, redis_client)

    current_app.logger.info("WebSocket server initialized successfully")
    return websocket_manager


def get_websocket_manager():
    """Get the global WebSocket manager instance"""
    return websocket_manager
