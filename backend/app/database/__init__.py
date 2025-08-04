"""
Database module for Passive CAPTCHA system
Handles verification logs, analytics, and data persistence
"""

import os
import sqlite3
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from flask import current_app
import json
import logging

Base = declarative_base()
# Global session maker
SessionLocal = None


class Website(Base):
    """
    Table for storing registered websites and their tokens
    """
    __tablename__ = 'websites'

    website_id = Column(String(36), primary_key=True)  # UUID
    website_name = Column(String(255), nullable=False)
    website_url = Column(String(500), nullable=False)
    admin_email = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    secret_key = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='active')  # active, suspended, revoked

    # JSON fields for flexible configuration
    permissions = Column(Text, nullable=True)  # JSON string
    rate_limits = Column(Text, nullable=True)  # JSON string

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'website_id': self.website_id,
            'website_name': self.website_name,
            'website_url': self.website_url,
            'admin_email': self.admin_email,
            'api_key': self.api_key,
            'secret_key': self.secret_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'permissions': json.loads(self.permissions) if self.permissions else [],
            'rate_limits': json.loads(self.rate_limits) if self.rate_limits else {}
        }


class VerificationLog(Base):
    """
    Table for storing verification attempts and results
    """
    __tablename__ = 'verification_logs'

    id = Column(Integer, primary_key=True)
    website_id = Column(String(36), nullable=False, index=True)  # Foreign key to websites
    session_id = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    origin = Column(String(255), nullable=True)

    # ML Model Results
    is_human = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)

    # Features used for classification
    mouse_movement_count = Column(Integer, nullable=True)
    avg_mouse_velocity = Column(Float, nullable=True)
    mouse_acceleration_variance = Column(Float, nullable=True)
    keystroke_count = Column(Integer, nullable=True)
    avg_keystroke_interval = Column(Float, nullable=True)
    typing_rhythm_consistency = Column(Float, nullable=True)
    session_duration_normalized = Column(Float, nullable=True)
    webgl_support_score = Column(Float, nullable=True)
    canvas_uniqueness_score = Column(Float, nullable=True)
    hardware_legitimacy_score = Column(Float, nullable=True)
    browser_consistency_score = Column(Float, nullable=True)

    # Metadata
    response_time = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'origin': self.origin,
            'is_human': self.is_human,
            'confidence': self.confidence,
            'features': {
                'mouse_movement_count': self.mouse_movement_count,
                'avg_mouse_velocity': self.avg_mouse_velocity,
                'mouse_acceleration_variance': self.mouse_acceleration_variance,
                'keystroke_count': self.keystroke_count,
                'avg_keystroke_interval': self.avg_keystroke_interval,
                'typing_rhythm_consistency': self.typing_rhythm_consistency,
                'session_duration_normalized': self.session_duration_normalized,
                'webgl_support_score': self.webgl_support_score,
                'canvas_uniqueness_score': self.canvas_uniqueness_score,
                'hardware_legitimacy_score': self.hardware_legitimacy_score,
                'browser_consistency_score': self.browser_consistency_score
            },
            'response_time': self.response_time,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


def init_db():
    """
    Initialize database connection and create tables
    """
    try:
        database_url = current_app.config.get('DATABASE_URL', 'sqlite:///passive_captcha.db')

        # Handle Railway PostgreSQL URL format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        # Configure engine with appropriate settings for production
        engine_kwargs = {
            'echo': False,
            'pool_pre_ping': True,  # Verify connections before use
            'pool_recycle': 3600,   # Recycle connections every hour
        }

        # Add SQLite-specific settings
        if database_url.startswith('sqlite:'):
            engine_kwargs.update({
                'pool_timeout': 20,
                'pool_recycle': -1,
                'connect_args': {'check_same_thread': False}
            })
        # Add PostgreSQL-specific settings
        elif 'postgresql://' in database_url:
            engine_kwargs.update({
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
            })

        engine = create_engine(database_url, **engine_kwargs)

        # Create tables
        Base.metadata.create_all(engine)

        # Create session maker
        global SessionLocal
        SessionLocal = sessionmaker(bind=engine)

        current_app.logger.info(f"Database initialized successfully with URL: {database_url}")
        return True

    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {str(e)}")
        return False


def get_db_session():
    """Get a database session"""
    if SessionLocal is None:
        init_db()
    return SessionLocal()


def log_verification(session_id, ip_address, user_agent, origin, is_human, confidence, features, response_time):
    """
    Log a verification attempt with individual features
    """
    try:
        session = get_db_session()

        # Extract individual features from the features list/dict
        if isinstance(features, list) and len(features) >= 11:
            # Features are in a list format
            feature_values = {
                'mouse_movement_count': int(features[0]) if features[0] is not None else None,
                'avg_mouse_velocity': float(features[1]) if features[1] is not None else None,
                'mouse_acceleration_variance': float(features[2]) if features[2] is not None else None,
                'keystroke_count': int(features[3]) if features[3] is not None else None,
                'avg_keystroke_interval': float(features[4]) if features[4] is not None else None,
                'typing_rhythm_consistency': float(features[5]) if features[5] is not None else None,
                'session_duration_normalized': float(features[6]) if features[6] is not None else None,
                'webgl_support_score': float(features[7]) if features[7] is not None else None,
                'canvas_uniqueness_score': float(features[8]) if features[8] is not None else None,
                'hardware_legitimacy_score': float(features[9]) if features[9] is not None else None,
                'browser_consistency_score': float(features[10]) if features[10] is not None else None
            }
        elif isinstance(features, dict):
            # Features are in dictionary format
            feature_values = {
                'mouse_movement_count': features.get('mouse_movement_count'),
                'avg_mouse_velocity': features.get('avg_mouse_velocity'),
                'mouse_acceleration_variance': features.get('mouse_acceleration_variance'),
                'keystroke_count': features.get('keystroke_count'),
                'avg_keystroke_interval': features.get('avg_keystroke_interval'),
                'typing_rhythm_consistency': features.get('typing_rhythm_consistency'),
                'session_duration_normalized': features.get('session_duration_normalized'),
                'webgl_support_score': features.get('webgl_support_score'),
                'canvas_uniqueness_score': features.get('canvas_uniqueness_score'),
                'hardware_legitimacy_score': features.get('hardware_legitimacy_score'),
                'browser_consistency_score': features.get('browser_consistency_score')
            }
        else:
            # Default values if features format is unexpected
            feature_values = {
                'mouse_movement_count': None,
                'avg_mouse_velocity': None,
                'mouse_acceleration_variance': None,
                'keystroke_count': None,
                'avg_keystroke_interval': None,
                'typing_rhythm_consistency': None,
                'session_duration_normalized': None,
                'webgl_support_score': None,
                'canvas_uniqueness_score': None,
                'hardware_legitimacy_score': None,
                'browser_consistency_score': None
            }

        log_entry = VerificationLog(
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            origin=origin,
            is_human=is_human,
            confidence=confidence,
            response_time=response_time,
            **feature_values
        )

        session.add(log_entry)
        session.commit()
        session.close()

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to log verification: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def get_analytics_data(hours=24):
    """
    Get analytics data for the specified time period
    """
    try:
        session = get_db_session()

        # Calculate time threshold
        threshold = datetime.utcnow() - timedelta(hours=hours)

        # Get logs within the time period
        logs = session.query(VerificationLog).filter(
            VerificationLog.timestamp >= threshold
        ).all()

        if not logs:
            session.close()
            return {
                'totalVerifications': 0,
                'humanRate': 0,
                'avgConfidence': 0,
                'avgResponseTime': 0,
                'trends': [],
                'topOrigins': []
            }

        # Calculate statistics
        total_verifications = len(logs)
        human_count = sum(1 for log in logs if log.is_human)
        human_rate = (human_count / total_verifications) * 100 if total_verifications > 0 else 0

        avg_confidence = sum(log.confidence for log in logs) / total_verifications
        response_times = [log.response_time for log in logs if log.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Group by hour for trends
        hourly_data = {}
        for log in logs:
            hour_key = log.timestamp.strftime('%H')
            if hour_key not in hourly_data:
                hourly_data[hour_key] = {'humans': 0, 'bots': 0}

            if log.is_human:
                hourly_data[hour_key]['humans'] += 1
            else:
                hourly_data[hour_key]['bots'] += 1

        trends = [
            {'hour': hour, 'humans': data['humans'], 'bots': data['bots']}
            for hour, data in sorted(hourly_data.items())
        ]

        # Top origins
        origin_counts = {}
        for log in logs:
            if log.origin:
                origin_counts[log.origin] = origin_counts.get(log.origin, 0) + 1

        top_origins = [
            {'origin': origin, 'count': count}
            for origin, count in sorted(origin_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        session.close()

        return {
            'totalVerifications': total_verifications,
            'humanRate': round(human_rate, 1),
            'avgConfidence': round(avg_confidence * 100, 1),
            'avgResponseTime': round(avg_response_time, 0),
            'trends': trends,
            'topOrigins': top_origins
        }

    except Exception as e:
        current_app.logger.error(f"Failed to get analytics data: {str(e)}")
        if 'session' in locals():
            session.close()
        return {
            'totalVerifications': 0,
            'humanRate': 0,
            'avgConfidence': 0,
            'avgResponseTime': 0,
            'trends': [],
            'topOrigins': []
        }


def get_recent_logs(limit=50):
    """
    Get recent verification logs
    """
    try:
        session = get_db_session()

        logs = session.query(VerificationLog).order_by(
            VerificationLog.timestamp.desc()
        ).limit(limit).all()

        result = [log.to_dict() for log in logs]
        session.close()

        return result

    except Exception as e:
        current_app.logger.error(f"Failed to get recent logs: {str(e)}")
        if 'session' in locals():
            session.close()
        return []


def get_last_verification_time():
    """
    Get timestamp of the last verification
    """
    try:
        last_log = get_db_session().query(VerificationLog)\
            .order_by(VerificationLog.timestamp.desc())\
            .first()

        if last_log:
            return last_log.timestamp.isoformat() + 'Z'
        else:
            return None

    except Exception as e:
        print(f"Error getting last verification time: {e}")
        return None


def cleanup_old_data(days=30):
    """
    Clean up verification logs older than specified days
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted_count = get_db_session().query(VerificationLog)\
            .filter(VerificationLog.timestamp < cutoff_date)\
            .delete()

        get_db_session().commit()

        print(f"Cleaned up {deleted_count} old verification logs")
        return deleted_count

    except Exception as e:
        print(f"Error cleaning up old data: {e}")
        get_db_session().rollback()
        return 0


def get_verification_stats():
    """
    Get overall verification statistics
    """
    try:
        session = get_db_session()

        total_verifications = session.query(VerificationLog).count()

        if total_verifications == 0:
            session.close()
            return {
                'totalVerifications': 0,
                'humanVerifications': 0,
                'botVerifications': 0,
                'humanRate': 0,
                'avgConfidence': 0
            }

        human_verifications = session.query(VerificationLog).filter(
            VerificationLog.is_human == True
        ).count()

        bot_verifications = total_verifications - human_verifications
        human_rate = (human_verifications / total_verifications) * 100

        avg_confidence_result = session.query(
            VerificationLog.confidence
        ).all()

        avg_confidence = sum(row[0] for row in avg_confidence_result) / len(avg_confidence_result) if avg_confidence_result else 0

        session.close()

        return {
            'totalVerifications': total_verifications,
            'humanVerifications': human_verifications,
            'botVerifications': bot_verifications,
            'humanRate': round(human_rate, 1),
            'avgConfidence': round(avg_confidence * 100, 1)
        }

    except Exception as e:
        current_app.logger.error(f"Failed to get verification stats: {str(e)}")
        if 'session' in locals():
            session.close()
        return {
            'totalVerifications': 0,
            'humanVerifications': 0,
            'botVerifications': 0,
            'humanRate': 0,
            'avgConfidence': 0
        }


def search_logs(filters=None, limit=100):
    """
    Search verification logs with filters
    """
    try:
        session = get_db_session()

        query = session.query(VerificationLog)

        if filters:
            if 'session_id' in filters:
                query = query.filter(VerificationLog.session_id.like(f"%{filters['session_id']}%"))

            if 'ip_address' in filters:
                query = query.filter(VerificationLog.ip_address.like(f"%{filters['ip_address']}%"))

            if 'origin' in filters:
                query = query.filter(VerificationLog.origin.like(f"%{filters['origin']}%"))

            if 'is_human' in filters:
                query = query.filter(VerificationLog.is_human == filters['is_human'])

            if 'min_confidence' in filters:
                query = query.filter(VerificationLog.confidence >= filters['min_confidence'])

            if 'max_confidence' in filters:
                query = query.filter(VerificationLog.confidence <= filters['max_confidence'])

            if 'start_date' in filters:
                query = query.filter(VerificationLog.timestamp >= filters['start_date'])

            if 'end_date' in filters:
                query = query.filter(VerificationLog.timestamp <= filters['end_date'])

        logs = query.order_by(VerificationLog.timestamp.desc()).limit(limit).all()

        result = [log.to_dict() for log in logs]
        session.close()

        return result

    except Exception as e:
        current_app.logger.error(f"Failed to search logs: {str(e)}")
        if 'session' in locals():
            session.close()
        return []


# Cleanup function for scheduled tasks
def scheduled_cleanup():
    """
    Perform scheduled database maintenance
    """
    try:
        # Clean up logs older than 30 days
        cleanup_old_data(days=30)

        # Could add other maintenance tasks here
        # - Vacuum database
        # - Update statistics
        # - Compress old data

        print("Scheduled database cleanup completed")
        return True

    except Exception as e:
        print(f"Error in scheduled cleanup: {e}")
        return False


# Multi-tenant database functions

def store_website_registration(website_data):
    """Store website registration in database"""
    try:
        session = get_db_session()

        website = Website(
            website_id=website_data['website_id'],
            website_name=website_data['website_name'],
            website_url=website_data['website_url'],
            admin_email=website_data['admin_email'],
            api_key=website_data['api_key'],
            secret_key=website_data['secret_key'],
            created_at=datetime.fromisoformat(website_data['created_at']),
            status=website_data.get('status', 'active'),
            permissions=json.dumps(website_data.get('permissions', [])),
            rate_limits=json.dumps(website_data.get('rate_limits', {}))
        )

        session.add(website)
        session.commit()
        session.close()

        return True

    except Exception as e:
        print(f"Error storing website registration: {e}")
        return False


def get_website_by_api_key(api_key):
    """Get website information by API key"""
    try:
        session = get_db_session()
        website = session.query(Website).filter(Website.api_key == api_key).first()

        if website:
            result = website.to_dict()
            session.close()
            return result

        session.close()
        return None

    except Exception as e:
        print(f"Error retrieving website by API key: {e}")
        return None


def get_website_by_id(website_id):
    """Get website information by ID"""
    try:
        session = get_db_session()
        website = session.query(Website).filter(Website.website_id == website_id).first()

        if website:
            result = website.to_dict()
            session.close()
            return result

        session.close()
        return None

    except Exception as e:
        print(f"Error retrieving website by ID: {e}")
        return None


def get_websites_by_admin(admin_email):
    """Get all websites registered by an admin"""
    try:
        session = get_db_session()
        websites = session.query(Website).filter(Website.admin_email == admin_email).all()

        results = [website.to_dict() for website in websites]
        session.close()

        return results

    except Exception as e:
        print(f"Error retrieving websites by admin: {e}")
        return []


def update_website_status(website_id, status):
    """Update website status"""
    try:
        session = get_db_session()
        website = session.query(Website).filter(Website.website_id == website_id).first()

        if website:
            website.status = status
            session.commit()
            session.close()
            return True

        session.close()
        return False

    except Exception as e:
        print(f"Error updating website status: {e}")
        return False


def log_verification_with_website(website_id, session_id, ip_address, user_agent, origin,
                                is_human, confidence, features, response_time):
    """
    Log a verification attempt with website isolation
    """
    try:
        session = get_db_session()

        # Extract individual features from the features list/dict
        if isinstance(features, list) and len(features) >= 11:
            # Features are in a list format
            feature_values = {
                'mouse_movement_count': int(features[0]) if features[0] is not None else None,
                'avg_mouse_velocity': float(features[1]) if features[1] is not None else None,
                'mouse_acceleration_variance': float(features[2]) if features[2] is not None else None,
                'keystroke_count': int(features[3]) if features[3] is not None else None,
                'avg_keystroke_interval': float(features[4]) if features[4] is not None else None,
                'typing_rhythm_consistency': float(features[5]) if features[5] is not None else None,
                'session_duration_normalized': float(features[6]) if features[6] is not None else None,
                'webgl_support_score': float(features[7]) if features[7] is not None else None,
                'canvas_uniqueness_score': float(features[8]) if features[8] is not None else None,
                'hardware_legitimacy_score': float(features[9]) if features[9] is not None else None,
                'browser_consistency_score': float(features[10]) if features[10] is not None else None
            }
        elif isinstance(features, dict):
            # Features are in dictionary format
            feature_values = {
                'mouse_movement_count': features.get('mouse_movement_count'),
                'avg_mouse_velocity': features.get('avg_mouse_velocity'),
                'mouse_acceleration_variance': features.get('mouse_acceleration_variance'),
                'keystroke_count': features.get('keystroke_count'),
                'avg_keystroke_interval': features.get('avg_keystroke_interval'),
                'typing_rhythm_consistency': features.get('typing_rhythm_consistency'),
                'session_duration_normalized': features.get('session_duration_normalized'),
                'webgl_support_score': features.get('webgl_support_score'),
                'canvas_uniqueness_score': features.get('canvas_uniqueness_score'),
                'hardware_legitimacy_score': features.get('hardware_legitimacy_score'),
                'browser_consistency_score': features.get('browser_consistency_score')
            }
        else:
            # Default empty values
            feature_values = {
                'mouse_movement_count': None,
                'avg_mouse_velocity': None,
                'mouse_acceleration_variance': None,
                'keystroke_count': None,
                'avg_keystroke_interval': None,
                'typing_rhythm_consistency': None,
                'session_duration_normalized': None,
                'webgl_support_score': None,
                'canvas_uniqueness_score': None,
                'hardware_legitimacy_score': None,
                'browser_consistency_score': None
            }

        verification = VerificationLog(
            website_id=website_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            origin=origin,
            is_human=is_human,
            confidence=confidence,
            response_time=response_time,
            **feature_values
        )

        session.add(verification)
        session.commit()
        session.close()

        return True

    except Exception as e:
        print(f"Error logging verification: {e}")
        return False


def get_analytics_data_for_website(website_id, hours=24):
    """
    Get analytics data for a specific website
    """
    try:
        session = get_db_session()

        # Calculate time range
        since = datetime.utcnow() - timedelta(hours=hours)

        # Get all verifications for this website in the time range
        verifications = session.query(VerificationLog).filter(
            VerificationLog.website_id == website_id,
            VerificationLog.timestamp >= since
        ).all()

        # Calculate analytics
        total_verifications = len(verifications)
        human_count = sum(1 for v in verifications if v.is_human)
        bot_count = total_verifications - human_count

        avg_confidence = sum(v.confidence for v in verifications) / total_verifications if total_verifications > 0 else 0
        avg_response_time = sum(v.response_time for v in verifications if v.response_time) / total_verifications if total_verifications > 0 else 0

        # Get unique sessions and origins
        unique_sessions = len(set(v.session_id for v in verifications))
        unique_origins = len(set(v.origin for v in verifications if v.origin))

        session.close()

        return {
            'website_id': website_id,
            'time_range_hours': hours,
            'total_verifications': total_verifications,
            'human_detections': human_count,
            'bot_detections': bot_count,
            'human_percentage': (human_count / total_verifications * 100) if total_verifications > 0 else 0,
            'average_confidence': round(avg_confidence, 3),
            'average_response_time_ms': round(avg_response_time, 2),
            'unique_sessions': unique_sessions,
            'unique_origins': unique_origins,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        print(f"Error getting analytics data for website {website_id}: {e}")
        return {
            'website_id': website_id,
            'error': 'Failed to retrieve analytics data',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
