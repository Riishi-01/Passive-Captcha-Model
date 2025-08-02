#!/usr/bin/env python3
"""
Server runner for production-grade application
"""

import os
import sys
from app import create_app

def main():
    # Set port
    port = int(os.getenv('PORT', 5003))
    
    # Create app
    print("Creating Flask application...")
    app, socketio = create_app('development')
    
    print(f"Starting server on http://localhost:{port}")
    print(f"Admin login: http://localhost:{port}/admin/login")
    print(f"Health check: http://localhost:{port}/health")
    print("Press Ctrl+C to stop")
    
    try:
        if socketio:
            print("Starting with SocketIO support...")
            socketio.run(app, host='127.0.0.1', port=port, debug=False, use_reloader=False)
        else:
            print("Starting standard Flask server...")
            app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()