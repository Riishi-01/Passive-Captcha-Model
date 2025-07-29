#!/usr/bin/env python3
"""
Main entry point for Passive CAPTCHA Backend Application
Production-ready Flask server with ML model and admin dashboard
"""

import os
from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"Starting Passive CAPTCHA API server on port {port}")
    print(f"Admin dashboard available at: http://localhost:{port}/admin/dashboard")
    print(f"API status endpoint: http://localhost:{port}/health")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 