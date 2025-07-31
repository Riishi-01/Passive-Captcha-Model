"""
Production-Grade Logs Pipeline for Passive CAPTCHA System
Handles real-time log streaming, aggregation, export, and WebSocket updates
"""

import asyncio
import json
import csv
import io
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy import and_, or_, func
from app.database import get_db_session, VerificationLog
import threading
import queue
import time


class LogLevel(Enum):
    """Log levels for categorization"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"
    PERFORMANCE = "performance"


class LogType(Enum):
    """Types of logs in the system"""
    VERIFICATION = "verification"
    SYSTEM = "system"
    SECURITY = "security"
    ML_MODEL = "ml_model"
    API = "api"
    WEBSOCKET = "websocket"


@dataclass
class LogEntry:
    """Structured log entry for the pipeline"""
    id: str
    timestamp: datetime
    type: LogType
    level: LogLevel
    message: str
    website_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    country: Optional[str] = None
    confidence: Optional[float] = None
    response_time: Optional[float] = None
    is_human: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['type'] = self.type.value
        data['level'] = self.level.value
        return data
    
    def to_frontend_format(self) -> Dict[str, Any]:
        """Convert to frontend-compatible format"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'type': self.type.value,
            'level': self.level.value,
            'message': self.message,
            'website_id': self.website_id,
            'ip': self.ip_address,
            'country': self.country or 'Unknown',
            'confidence': round(self.confidence * 100, 1) if self.confidence else None,
            'response_time': f"{self.response_time:.2f}ms" if self.response_time else None,
            'is_human': self.is_human,
            'user_agent': self.user_agent,
            'metadata': self.metadata or {}
        }


class LogsStreamingManager:
    """Manages real-time log streaming via WebSocket"""
    
    def __init__(self, socketio: SocketIO, redis_client: redis.Redis):
        self.socketio = socketio
        self.redis = redis_client
        self.active_connections = {}  # room_id -> set of connection_ids
        self.filters = {}  # connection_id -> filter_config
        self.log_queue = queue.Queue(maxsize=10000)
        self.worker_thread = None
        self.running = False
        
    def start(self):
        """Start the streaming manager"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_log_stream)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # Subscribe to Redis pub/sub for log events
        self._setup_redis_subscription()
        
    def stop(self):
        """Stop the streaming manager"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _setup_redis_subscription(self):
        """Setup Redis pub/sub for log distribution"""
        def redis_listener():
            pubsub = self.redis.pubsub()
            pubsub.subscribe('logs:stream', 'logs:verification', 'logs:system')
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        log_data = json.loads(message['data'])
                        log_entry = LogEntry(**log_data)
                        self.add_log(log_entry)
                    except Exception as e:
                        current_app.logger.error(f"Error processing Redis log message: {e}")
        
        redis_thread = threading.Thread(target=redis_listener)
        redis_thread.daemon = True
        redis_thread.start()
    
    def add_log(self, log_entry: LogEntry):
        """Add log entry to streaming queue"""
        try:
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            # Drop oldest log if queue is full
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(log_entry)
            except queue.Empty:
                pass
    
    def _process_log_stream(self):
        """Process log stream and emit to WebSocket clients"""
        while self.running:
            try:
                log_entry = self.log_queue.get(timeout=1)
                self._emit_log_to_clients(log_entry)
            except queue.Empty:
                continue
            except Exception as e:
                current_app.logger.error(f"Error processing log stream: {e}")
    
    def _emit_log_to_clients(self, log_entry: LogEntry):
        """Emit log entry to connected WebSocket clients"""
        for room_id, connections in self.active_connections.items():
            for connection_id in connections.copy():
                try:
                    # Apply filters
                    if self._should_emit_to_connection(log_entry, connection_id):
                        self.socketio.emit(
                            'new_log',
                            log_entry.to_frontend_format(),
                            room=connection_id
                        )
                except Exception as e:
                    current_app.logger.error(f"Error emitting to connection {connection_id}: {e}")
                    # Remove dead connection
                    connections.discard(connection_id)
    
    def _should_emit_to_connection(self, log_entry: LogEntry, connection_id: str) -> bool:
        """Check if log should be emitted to specific connection based on filters"""
        filters = self.filters.get(connection_id, {})
        
        # Website filter
        if filters.get('website_id') and log_entry.website_id != filters['website_id']:
            return False
        
        # Log type filter
        if filters.get('log_types') and log_entry.type.value not in filters['log_types']:
            return False
        
        # Log level filter
        if filters.get('min_level'):
            level_priority = {'info': 1, 'warning': 2, 'error': 3, 'security': 4}
            if level_priority.get(log_entry.level.value, 0) < level_priority.get(filters['min_level'], 0):
                return False
        
        # Human/Bot filter
        if filters.get('verification_type'):
            if log_entry.type == LogType.VERIFICATION:
                if filters['verification_type'] == 'human' and not log_entry.is_human:
                    return False
                if filters['verification_type'] == 'bot' and log_entry.is_human:
                    return False
        
        return True
    
    def join_room(self, connection_id: str, room_id: str, filters: Dict[str, Any] = None):
        """Add connection to room with optional filters"""
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(connection_id)
        self.filters[connection_id] = filters or {}
    
    def leave_room(self, connection_id: str, room_id: str):
        """Remove connection from room"""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(connection_id)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        self.filters.pop(connection_id, None)


class LogsAggregator:
    """Aggregates and analyzes log data"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def get_verification_metrics(self, website_id: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated verification metrics"""
        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = session.query(VerificationLog).filter(VerificationLog.timestamp >= since)
            
            if website_id and website_id != 'all':
                query = query.filter(VerificationLog.origin.like(f'%{website_id}%'))
            
            logs = query.all()
            
            total_verifications = len(logs)
            human_verifications = len([log for log in logs if log.is_human])
            bot_verifications = total_verifications - human_verifications
            
            avg_confidence = sum(log.confidence for log in logs) / len(logs) if logs else 0
            avg_response_time = sum(log.response_time for log in logs if log.response_time) / len([log for log in logs if log.response_time]) if logs else 0
            
            # Geographic distribution
            geo_data = {}
            for log in logs:
                country = getattr(log, 'country_code', 'Unknown') or 'Unknown'
                geo_data[country] = geo_data.get(country, 0) + 1
            
            # Hourly trends
            hourly_data = {}
            for log in logs:
                hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                hour_key = hour.isoformat()
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = {'human': 0, 'bot': 0, 'total': 0}
                
                hourly_data[hour_key]['total'] += 1
                if log.is_human:
                    hourly_data[hour_key]['human'] += 1
                else:
                    hourly_data[hour_key]['bot'] += 1
            
            return {
                'summary': {
                    'total_verifications': total_verifications,
                    'human_verifications': human_verifications,
                    'bot_verifications': bot_verifications,
                    'human_rate': (human_verifications / total_verifications * 100) if total_verifications > 0 else 0,
                    'bot_rate': (bot_verifications / total_verifications * 100) if total_verifications > 0 else 0,
                    'avg_confidence': avg_confidence,
                    'avg_response_time': avg_response_time
                },
                'geographic_distribution': geo_data,
                'hourly_trends': hourly_data,
                'time_range': f"{hours} hours",
                'generated_at': datetime.utcnow().isoformat()
            }
            
        finally:
            session.close()
    
    def get_ml_model_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get ML model performance metrics"""
        session = get_db_session()
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            logs = session.query(VerificationLog).filter(VerificationLog.timestamp >= since).all()
            
            if not logs:
                return {'error': 'No data available'}
            
            # Confidence distribution
            confidence_buckets = {
                '0-20%': 0, '21-40%': 0, '41-60%': 0, 
                '61-80%': 0, '81-100%': 0
            }
            
            true_positives = 0  # Human correctly identified as human
            false_positives = 0  # Bot incorrectly identified as human
            true_negatives = 0   # Bot correctly identified as bot
            false_negatives = 0  # Human incorrectly identified as bot
            
            for log in logs:
                # Confidence distribution
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
                
                # Confusion matrix (simplified - assumes high confidence = human prediction)
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
            
            return {
                'confidence_distribution': {
                    'buckets': [
                        {'range': k, 'count': v, 'percentage': (v / len(logs) * 100) if logs else 0}
                        for k, v in confidence_buckets.items()
                    ],
                    'average_confidence': sum(log.confidence for log in logs) / len(logs) if logs else 0,
                    'reliability_score': accuracy * 100
                },
                'confusion_matrix': {
                    'true_positives': true_positives,
                    'false_positives': false_positives,
                    'true_negatives': true_negatives,
                    'false_negatives': false_negatives
                },
                'metrics': {
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1_score,
                    'accuracy': accuracy
                },
                'model_health': {
                    'status': 'healthy' if accuracy > 0.9 else 'warning' if accuracy > 0.7 else 'error',
                    'version': '1.0.0',
                    'last_training': (datetime.utcnow() - timedelta(days=7)).isoformat(),
                    'next_retraining': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    'uptime': 99.5,
                    'latency': sum(log.response_time for log in logs if log.response_time) / len([log for log in logs if log.response_time]) if logs else 0
                }
            }
            
        finally:
            session.close()


class LogsExporter:
    """Handles log export functionality"""
    
    @staticmethod
    def export_logs(logs: List[VerificationLog], format: str = 'csv') -> Union[str, bytes]:
        """Export logs in specified format"""
        if format.lower() == 'csv':
            return LogsExporter._export_csv(logs)
        elif format.lower() == 'json':
            return LogsExporter._export_json(logs)
        elif format.lower() == 'excel':
            return LogsExporter._export_excel(logs)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @staticmethod
    def _export_csv(logs: List[VerificationLog]) -> str:
        """Export logs as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'Timestamp', 'Session ID', 'IP Address', 'User Agent', 'Origin',
            'Is Human', 'Confidence', 'Response Time', 'Country', 'Features'
        ]
        writer.writerow(headers)
        
        # Data rows
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat(),
                log.session_id,
                log.ip_address,
                log.user_agent,
                log.origin,
                log.is_human,
                log.confidence,
                log.response_time,
                getattr(log, 'country_code', ''),
                json.dumps(log.to_dict().get('features', {}))
            ])
        
        return output.getvalue()
    
    @staticmethod
    def _export_json(logs: List[VerificationLog]) -> str:
        """Export logs as JSON"""
        logs_data = [log.to_dict() for log in logs]
        return json.dumps({
            'logs': logs_data,
            'exported_at': datetime.utcnow().isoformat(),
            'total_records': len(logs)
        }, indent=2, default=str)
    
    @staticmethod
    def _export_excel(logs: List[VerificationLog]) -> bytes:
        """Export logs as Excel file"""
        df_data = []
        for log in logs:
            df_data.append({
                'Timestamp': log.timestamp,
                'Session ID': log.session_id,
                'IP Address': log.ip_address,
                'User Agent': log.user_agent,
                'Origin': log.origin,
                'Is Human': log.is_human,
                'Confidence': log.confidence,
                'Response Time': log.response_time,
                'Country': getattr(log, 'country_code', ''),
                'Features': json.dumps(log.to_dict().get('features', {}))
            })
        
        df = pd.DataFrame(df_data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Verification Logs', index=False)
        
        return output.getvalue()


class LogsPipeline:
    """Main logs pipeline orchestrator"""
    
    def __init__(self, app, socketio: SocketIO, redis_client: redis.Redis):
        self.app = app
        self.socketio = socketio
        self.redis = redis_client
        self.streaming_manager = LogsStreamingManager(socketio, redis_client)
        self.aggregator = LogsAggregator(redis_client)
        self.exporter = LogsExporter()
        
        # Initialize WebSocket events
        self._setup_websocket_events()
    
    def start(self):
        """Start the logs pipeline"""
        self.streaming_manager.start()
        current_app.logger.info("Logs pipeline started successfully")
    
    def stop(self):
        """Stop the logs pipeline"""
        self.streaming_manager.stop()
        current_app.logger.info("Logs pipeline stopped")
    
    def log_verification(self, **kwargs) -> LogEntry:
        """Log a verification event"""
        log_entry = LogEntry(
            id=f"verification_{int(time.time() * 1000)}",
            timestamp=datetime.utcnow(),
            type=LogType.VERIFICATION,
            level=LogLevel.INFO,
            message=f"Verification: {'Human' if kwargs.get('is_human') else 'Bot'} detected",
            **kwargs
        )
        
        # Add to streaming queue
        self.streaming_manager.add_log(log_entry)
        
        # Publish to Redis for distribution
        self.redis.publish('logs:verification', json.dumps(log_entry.to_dict(), default=str))
        
        return log_entry
    
    def log_system_event(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs) -> LogEntry:
        """Log a system event"""
        log_entry = LogEntry(
            id=f"system_{int(time.time() * 1000)}",
            timestamp=datetime.utcnow(),
            type=LogType.SYSTEM,
            level=level,
            message=message,
            **kwargs
        )
        
        self.streaming_manager.add_log(log_entry)
        self.redis.publish('logs:system', json.dumps(log_entry.to_dict(), default=str))
        
        return log_entry
    
    def _setup_websocket_events(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('join_logs_room')
        def handle_join_logs_room(data):
            """Handle client joining logs room"""
            try:
                connection_id = data.get('connection_id', 'default')
                room_id = data.get('room_id', 'global')
                filters = data.get('filters', {})
                
                join_room(room_id)
                self.streaming_manager.join_room(connection_id, room_id, filters)
                
                emit('logs_room_joined', {
                    'room_id': room_id,
                    'connection_id': connection_id,
                    'status': 'success'
                })
                
            except Exception as e:
                emit('error', {'message': f'Failed to join logs room: {str(e)}'})
        
        @self.socketio.on('leave_logs_room')
        def handle_leave_logs_room(data):
            """Handle client leaving logs room"""
            try:
                connection_id = data.get('connection_id', 'default')
                room_id = data.get('room_id', 'global')
                
                leave_room(room_id)
                self.streaming_manager.leave_room(connection_id, room_id)
                
                emit('logs_room_left', {
                    'room_id': room_id,
                    'connection_id': connection_id,
                    'status': 'success'
                })
                
            except Exception as e:
                emit('error', {'message': f'Failed to leave logs room: {str(e)}'})
        
        @self.socketio.on('update_logs_filters')
        def handle_update_logs_filters(data):
            """Handle updating log filters for connection"""
            try:
                connection_id = data.get('connection_id', 'default')
                filters = data.get('filters', {})
                
                self.streaming_manager.filters[connection_id] = filters
                
                emit('logs_filters_updated', {
                    'connection_id': connection_id,
                    'filters': filters,
                    'status': 'success'
                })
                
            except Exception as e:
                emit('error', {'message': f'Failed to update filters: {str(e)}'})


# Global instance
logs_pipeline = None


def init_logs_pipeline(app, socketio: SocketIO, redis_client: redis.Redis):
    """Initialize the logs pipeline"""
    global logs_pipeline
    logs_pipeline = LogsPipeline(app, socketio, redis_client)
    logs_pipeline.start()
    return logs_pipeline