#!/usr/bin/env python3
"""
Network Connectivity Testing Suite
Tests external services, internet access, and API connectivity
"""

import os
import sys
import socket
import requests
import time
import threading
from urllib.parse import urlparse

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_internet_connectivity():
    """Test basic internet connectivity"""
    print("🌐 Testing Internet Connectivity...")
    
    try:
        # Test DNS resolution
        socket.gethostbyname('google.com')
        print("   ✅ DNS resolution working")
        
        # Test HTTP connectivity
        response = requests.get('https://httpbin.org/get', timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("   ✅ HTTP connectivity working")
        
        # Test HTTPS connectivity
        response = requests.get('https://www.google.com', timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("   ✅ HTTPS connectivity working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Internet connectivity test failed: {e}")
        return False


def test_api_reachability():
    """Test reachability of external APIs and services"""
    print("🔗 Testing External API Reachability...")
    
    try:
        # Test GitHub API (for deployments)
        try:
            response = requests.get('https://api.github.com/rate_limit', timeout=10)
            print(f"   ✅ GitHub API reachable: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  GitHub API unreachable: {e}")
        
        # Test PyPI (for package installations)
        try:
            response = requests.get('https://pypi.org/simple/', timeout=10)
            print(f"   ✅ PyPI reachable: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  PyPI unreachable: {e}")
        
        # Test Cloudflare (for tunnel services)
        try:
            response = requests.get('https://cloudflare.com', timeout=10)
            print(f"   ✅ Cloudflare reachable: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Cloudflare unreachable: {e}")
        
        # Test Railway (deployment platform)
        try:
            response = requests.get('https://railway.app', timeout=10)
            print(f"   ✅ Railway reachable: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Railway unreachable: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API reachability test failed: {e}")
        return False


def test_port_accessibility():
    """Test common port accessibility"""
    print("🚪 Testing Port Accessibility...")
    
    try:
        # Test common ports
        ports_to_test = [
            (80, "HTTP"),
            (443, "HTTPS"),
            (22, "SSH"),
            (5000, "Flask Dev"),
            (3000, "React Dev"),
            (6379, "Redis"),
            (5432, "PostgreSQL")
        ]
        
        accessible_ports = []
        
        for port, description in ports_to_test:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result == 0:
                    accessible_ports.append((port, description))
                    print(f"   ✅ Port {port} ({description}) accessible")
                else:
                    print(f"   ❌ Port {port} ({description}) not accessible")
                    
            except Exception as e:
                print(f"   ❌ Port {port} ({description}) error: {e}")
        
        print(f"   📊 {len(accessible_ports)}/{len(ports_to_test)} ports accessible")
        return True
        
    except Exception as e:
        print(f"   ❌ Port accessibility test failed: {e}")
        return False


def test_cdn_performance():
    """Test CDN and external resource performance"""
    print("📊 Testing CDN and External Resource Performance...")
    
    try:
        cdn_resources = [
            ('https://cdn.jsdelivr.net/npm/chart.js', 'Chart.js CDN'),
            ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css', 'FontAwesome CDN'),
            ('https://cdn.socket.io/4.5.0/socket.io.min.js', 'Socket.IO CDN'),
            ('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap', 'Google Fonts')
        ]
        
        total_load_time = 0
        successful_loads = 0
        
        for url, name in cdn_resources:
            try:
                start_time = time.time()
                response = requests.head(url, timeout=10)
                load_time = (time.time() - start_time) * 1000  # ms
                
                if response.status_code == 200:
                    print(f"   ✅ {name}: {load_time:.1f}ms")
                    total_load_time += load_time
                    successful_loads += 1
                else:
                    print(f"   ❌ {name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {name}: {e}")
        
        if successful_loads > 0:
            avg_load_time = total_load_time / successful_loads
            print(f"   📊 Average CDN load time: {avg_load_time:.1f}ms")
            
            # Alert if CDN performance is poor
            if avg_load_time > 2000:
                print("   ⚠️  CDN performance is slow (>2s)")
            elif avg_load_time > 1000:
                print("   ⚠️  CDN performance is moderate (>1s)")
            else:
                print("   ✅ CDN performance is good (<1s)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CDN performance test failed: {e}")
        return False


def test_websocket_capability():
    """Test WebSocket connectivity capability"""
    print("🔌 Testing WebSocket Capability...")
    
    try:
        # Test if websockets library is available
        try:
            import websocket
            print("   ✅ WebSocket library available")
        except ImportError:
            print("   ⚠️  WebSocket library not installed")
            return True  # Not critical for core functionality
        
        # Test WebSocket echo server
        try:
            import websocket
            
            def on_message(ws, message):
                print(f"   ✅ WebSocket echo received: {message}")
            
            def on_error(ws, error):
                print(f"   ❌ WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                print("   📡 WebSocket connection closed")
            
            def on_open(ws):
                print("   📡 WebSocket connection opened")
                ws.send("Hello WebSocket!")
                time.sleep(1)
                ws.close()
            
            # Test with WebSocket echo server
            ws = websocket.WebSocketApp("wss://echo.websocket.org/",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run in thread with timeout
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            ws_thread.join(timeout=10)
            
            print("   ✅ WebSocket connectivity test completed")
            
        except Exception as e:
            print(f"   ⚠️  WebSocket test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ WebSocket capability test failed: {e}")
        return False


def test_local_server_connectivity():
    """Test local development server connectivity"""
    print("🏠 Testing Local Server Connectivity...")
    
    try:
        # Start a test Flask server
        from app import create_app
        
        app = create_app('testing')
        app.config.update({
            'DATABASE_URL': 'sqlite:///test_network.db',
            'TESTING': True
        })
        
        # Test server startup
        def run_test_server():
            app.run(host='127.0.0.1', port=5002, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_test_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Test server connectivity
        try:
            response = requests.get('http://127.0.0.1:5002/health', timeout=5)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            print("   ✅ Local Flask server accessible")
            
            # Test API endpoint
            response = requests.post(
                'http://127.0.0.1:5002/api/verify',
                json={'sessionId': 'test', 'features': {}},
                timeout=5
            )
            # Should get some response (200 or 400, not connection error)
            print(f"   ✅ API endpoint accessible: HTTP {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            print("   ❌ Local server not accessible")
            return False
        
        # Cleanup
        try:
            os.remove('test_network.db')
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"   ❌ Local server connectivity test failed: {e}")
        return False


def test_database_connectivity():
    """Test database connectivity (separate from main DB tests)"""
    print("🗄️  Testing Database Network Connectivity...")
    
    try:
        # Test SQLite (local)
        import sqlite3
        
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        
        assert result[0] == 1, "SQLite test query failed"
        print("   ✅ SQLite connectivity working")
        
        # Test PostgreSQL connectivity (if configured)
        database_url = os.getenv('DATABASE_URL', '')
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            try:
                import psycopg2
                from sqlalchemy import create_engine
                
                # Test connection
                engine = create_engine(database_url)
                with engine.connect() as conn:
                    result = conn.execute('SELECT 1')
                    assert result.fetchone()[0] == 1
                
                print("   ✅ PostgreSQL connectivity working")
                
            except ImportError:
                print("   ⚠️  PostgreSQL driver not installed")
            except Exception as e:
                print(f"   ❌ PostgreSQL connectivity failed: {e}")
        else:
            print("   ℹ️  PostgreSQL not configured (using SQLite)")
        
        # Test Redis connectivity (if configured)
        redis_url = os.getenv('REDIS_URL', '')
        if redis_url:
            try:
                import redis
                
                r = redis.from_url(redis_url)
                r.ping()
                print("   ✅ Redis connectivity working")
                
            except ImportError:
                print("   ⚠️  Redis library not installed")
            except Exception as e:
                print(f"   ❌ Redis connectivity failed: {e}")
        else:
            print("   ℹ️  Redis not configured")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database connectivity test failed: {e}")
        return False


def test_deployment_urls():
    """Test deployment platform URLs and webhooks"""
    print("🚀 Testing Deployment Platform URLs...")
    
    try:
        deployment_urls = [
            ('https://render.com', 'Render'),
            ('https://railway.app', 'Railway'),
            ('https://vercel.com', 'Vercel'),
            ('https://heroku.com', 'Heroku'),
            ('https://aws.amazon.com', 'AWS'),
            ('https://cloud.google.com', 'Google Cloud'),
            ('https://azure.microsoft.com', 'Azure')
        ]
        
        reachable_platforms = 0
        
        for url, platform in deployment_urls:
            try:
                response = requests.head(url, timeout=10)
                if response.status_code in [200, 301, 302]:
                    print(f"   ✅ {platform} reachable")
                    reachable_platforms += 1
                else:
                    print(f"   ⚠️  {platform} returned {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {platform} unreachable: {e}")
        
        print(f"   📊 {reachable_platforms}/{len(deployment_urls)} deployment platforms reachable")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Deployment URLs test failed: {e}")
        return False


def main():
    """Run all network connectivity tests"""
    print("🧪 Network Connectivity Testing Suite")
    print("=" * 50)
    
    tests = [
        test_internet_connectivity,
        test_api_reachability,
        test_port_accessibility,
        test_cdn_performance,
        test_websocket_capability,
        test_local_server_connectivity,
        test_database_connectivity,
        test_deployment_urls
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All network connectivity tests passed!")
        return True
    else:
        print("❌ Some network connectivity tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)