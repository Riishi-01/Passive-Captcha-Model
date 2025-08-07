"""
Robust Logging System
Structured logging with multiple outputs and performance monitoring
"""

import os
import logging
import json
import time
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, request, has_request_context


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        if has_request_context():
            log_entry['request'] = {
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry['extra'] = log_entry.get('extra', {})
                log_entry['extra'][key] = value
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class PerformanceLogger:
    """Performance monitoring logger"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.info("Operation completed", extra={
                'duration_ms': round(duration * 1000, 2),
                'performance_metric': True
            })


def setup_logging(app: Flask) -> logging.Logger:
    """Set up comprehensive logging for the application"""
    from app.core.config import get_config
    config = get_config()
    
    # Create logs directory
    log_dir = os.path.dirname(config.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Set log level
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove default handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler for development
    if config.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            config.log_file,
            maxBytes=config.log_max_size,
            backupCount=config.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # Use structured formatter for production
        if config.environment.value == 'production':
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s %(name)-12s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
            )
            file_handler.setFormatter(file_formatter)
        
        root_logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    # Set Flask app logger
    app.logger.setLevel(log_level)
    
    # Log startup information
    app.logger.info("Logging system initialized", extra={
        'log_level': config.log_level,
        'log_file': config.log_file,
        'environment': config.environment.value,
        'structured_logging': config.environment.value == 'production'
    })
    
    return app.logger


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance"""
    logger = logging.getLogger('performance')
    return PerformanceLogger(logger)


def log_request_info(app: Flask):
    """Add request logging middleware"""
    
    @app.before_request
    def log_request():
        start_time = time.time()
        request.start_time = start_time
        
        app.logger.info("Request started", extra={
            'method': request.method,
            'url': request.url,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'request_id': id(request)
        })
    
    @app.after_request
    def log_response(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            app.logger.info("Request completed", extra={
                'method': request.method,
                'url': request.url,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'request_id': id(request)
            })
        
        return response
    
    @app.errorhandler(Exception)
    def log_exception(error):
        app.logger.error("Unhandled exception occurred", extra={
            'method': request.method if has_request_context() else 'N/A',
            'url': request.url if has_request_context() else 'N/A',
            'error_type': type(error).__name__,
            'error_message': str(error)
        }, exc_info=True)
        
        # Return JSON error response for API endpoints
        if has_request_context() and request.path.startswith('/api/'):
            return {
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An internal server error occurred'
                }
            }, 500
        
        # Re-raise the exception for default Flask handling
        raise error