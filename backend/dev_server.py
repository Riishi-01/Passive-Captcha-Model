#!/usr/bin/env python3
"""
Local Development Server with Cloudflare Tunnel Integration
Provides easy setup for development with HTTPS tunneling
"""

import os
import sys
import subprocess
import time
import signal
import threading
import re
from pathlib import Path

class LocalDevManager:
    """
    Manages local development environment with Cloudflare tunnel
    """
    
    def __init__(self):
        self.processes = []
        self.tunnel_urls = {}
        self.running = True
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Check if cloudflared is installed
        try:
            result = subprocess.run(['cloudflared', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            print(f"✅ Cloudflared found: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Cloudflared not found!")
            print("📋 Install instructions:")
            print("   macOS: brew install cloudflared")
            print("   Linux: wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && sudo dpkg -i cloudflared-linux-amd64.deb")
            print("   Windows: Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
            return False
        
        # Check Python dependencies
        try:
            import flask
            import flask_cors
            import flask_limiter
            print("✅ Python dependencies found")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("📋 Install with: pip install -r requirements.txt")
            return False
        
        return True
    
    def start_flask_backend(self):
        """Start Flask backend server"""
        print("🚀 Starting Flask backend server...")
        
        env = os.environ.copy()
        env.update({
            'FLASK_ENV': 'development',
            'FLASK_DEBUG': '1',
            'FLASK_APP': 'app:create_app',
            'DATABASE_URL': 'sqlite:///dev_passive_captcha.db',
            'SECRET_KEY': 'dev-secret-key-change-in-production',
            'ADMIN_SECRET': 'dev-admin-secret',
            'CONFIDENCE_THRESHOLD': '0.6',
            'REDIS_URL': 'redis://localhost:6379',  # Optional for development
            'API_BASE_URL': 'http://localhost:5000',
            'DASHBOARD_BASE_URL': 'http://localhost:5000'
        })
        
        try:
            process = subprocess.Popen(
                [sys.executable, '-m', 'flask', 'run', '--host=0.0.0.0', '--port=5000'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(('flask', process))
            
            # Monitor Flask startup
            def monitor_flask():
                for line in process.stdout:
                    if self.running:
                        print(f"[Flask] {line.strip()}")
                        if "Running on" in line:
                            print("✅ Flask backend started successfully")
            
            threading.Thread(target=monitor_flask, daemon=True).start()
            
            # Wait a moment for Flask to start
            time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Flask backend: {e}")
            return False
    
    def start_cloudflare_tunnel(self, service_name, local_port):
        """Start Cloudflare tunnel for a service"""
        print(f"🌐 Starting Cloudflare tunnel for {service_name}...")
        
        try:
            process = subprocess.Popen(
                ['cloudflared', 'tunnel', '--url', f'http://localhost:{local_port}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append((f'tunnel-{service_name}', process))
            
            # Extract tunnel URL
            def monitor_tunnel():
                tunnel_url = None
                for line in process.stdout:
                    if self.running:
                        if 'trycloudflare.com' in line:
                            # Extract URL from line
                            url_match = re.search(r'https://[a-zA-Z0-9.-]+\.trycloudflare\.com', line)
                            if url_match:
                                tunnel_url = url_match.group(0)
                                self.tunnel_urls[service_name] = tunnel_url
                                print(f"✅ {service_name} tunnel active: {tunnel_url}")
                                break
                        elif 'tunnel' in line.lower() and 'error' in line.lower():
                            print(f"[Tunnel-{service_name}] {line.strip()}")
            
            threading.Thread(target=monitor_tunnel, daemon=True).start()
            
            # Wait for tunnel URL
            timeout = 30
            while timeout > 0 and service_name not in self.tunnel_urls:
                time.sleep(1)
                timeout -= 1
            
            if service_name in self.tunnel_urls:
                return self.tunnel_urls[service_name]
            else:
                print(f"⚠️  Tunnel URL not detected for {service_name} within timeout")
                return None
                
        except Exception as e:
            print(f"❌ Failed to start tunnel for {service_name}: {e}")
            return None
    
    def create_example_website(self, tunnel_url):
        """Create example HTML file with the tunnel URL"""
        print("📝 Creating example integration...")
        
        example_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passive CAPTCHA Development Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        h1 {{
            color: #2563eb;
            margin-bottom: 1rem;
        }}
        
        .form-group {{
            margin-bottom: 1rem;
        }}
        
        label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        
        input {{
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 1rem;
        }}
        
        button {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: background 0.2s ease;
        }}
        
        button:hover {{
            background: #1d4ed8;
        }}
        
        .info {{
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 6px;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .result {{
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 6px;
            display: none;
        }}
        
        .result.success {{
            background: #dcfce7;
            border: 1px solid #86efac;
            color: #166534;
        }}
        
        .result.error {{
            background: #fef2f2;
            border: 1px solid #fca5a5;
            color: #991b1b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Passive CAPTCHA Development Test</h1>
        
        <div class="info">
            <strong>Development Server:</strong> {tunnel_url}<br>
            <strong>Status:</strong> Connected via Cloudflare Tunnel<br>
            <strong>Mode:</strong> Development with hot reload
        </div>
        
        <form id="testForm">
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="message">Message:</label>
                <input type="text" id="message" name="message" placeholder="Type something to generate keystroke data...">
            </div>
            
            <button type="submit" id="submitBtn">Submit with Passive CAPTCHA</button>
        </form>
        
        <div id="result" class="result"></div>
        
        <div class="info" style="margin-top: 2rem;">
            <h3>How it works:</h3>
            <ul>
                <li>Move your mouse around this page</li>
                <li>Type in the input fields</li>
                <li>Click submit to test passive CAPTCHA verification</li>
                <li>The system analyzes your behavior patterns</li>
                <li>Real humans pass automatically, bots are detected</li>
            </ul>
        </div>
    </div>
    
    <!-- Passive CAPTCHA Script -->
    <script type="text/javascript">
        // Development configuration
        const DEV_CONFIG = {{
            api_endpoint: '{tunnel_url}',
            website_id: 'dev-website-123',
            api_token: 'dev-token-456'
        }};
        
        // Simple passive CAPTCHA implementation for development
        class DevPassiveCaptcha {{
            constructor() {{
                this.behaviorData = {{
                    mouseMovements: [],
                    keystrokes: [],
                    startTime: Date.now()
                }};
                this.isTracking = false;
            }}
            
            init() {{
                this.startTracking();
                this.bindToForm();
            }}
            
            startTracking() {{
                if (this.isTracking) return;
                this.isTracking = true;
                
                document.addEventListener('mousemove', (e) => {{
                    this.behaviorData.mouseMovements.push({{
                        x: e.clientX,
                        y: e.clientY,
                        timestamp: Date.now()
                    }});
                    
                    if (this.behaviorData.mouseMovements.length > 50) {{
                        this.behaviorData.mouseMovements.shift();
                    }}
                }});
                
                document.addEventListener('keydown', (e) => {{
                    this.behaviorData.keystrokes.push({{
                        key: e.key,
                        timestamp: Date.now()
                    }});
                    
                    if (this.behaviorData.keystrokes.length > 20) {{
                        this.behaviorData.keystrokes.shift();
                    }}
                }});
            }}
            
            bindToForm() {{
                document.getElementById('testForm').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    
                    const result = await this.verify();
                    this.showResult(result);
                }});
            }}
            
            async verify() {{
                try {{
                    const features = this.extractFeatures();
                    
                    const response = await fetch(`${{DEV_CONFIG.api_endpoint}}/api/verify`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            sessionId: 'dev-session-' + Date.now(),
                            origin: window.location.origin,
                            features: features,
                            mouseMovements: this.behaviorData.mouseMovements.slice(-10),
                            keystrokes: this.behaviorData.keystrokes.slice(-5)
                        }})
                    }});
                    
                    if (!response.ok) {{
                        throw new Error(`HTTP ${{response.status}}`);
                    }}
                    
                    return await response.json();
                    
                }} catch (error) {{
                    console.error('Verification failed:', error);
                    return {{
                        error: true,
                        message: error.message,
                        isHuman: false,
                        confidence: 0
                    }};
                }}
            }}
            
            extractFeatures() {{
                const sessionDuration = Date.now() - this.behaviorData.startTime;
                const movements = this.behaviorData.mouseMovements;
                const keystrokes = this.behaviorData.keystrokes;
                
                return {{
                    mouse_movement_count: movements.length,
                    avg_mouse_velocity: this.calculateAverageVelocity(movements),
                    keystroke_count: keystrokes.length,
                    session_duration: sessionDuration,
                    webgl_support_score: this.checkWebGLSupport() ? 1.0 : 0.0,
                    canvas_fingerprint_score: 0.8,
                    hardware_legitimacy: 0.9,
                    browser_consistency: 0.85
                }};
            }}
            
            calculateAverageVelocity(movements) {{
                if (movements.length < 2) return 0;
                
                let totalVelocity = 0;
                let count = 0;
                
                for (let i = 1; i < movements.length; i++) {{
                    const prev = movements[i - 1];
                    const curr = movements[i];
                    const dx = curr.x - prev.x;
                    const dy = curr.y - prev.y;
                    const dt = curr.timestamp - prev.timestamp;
                    
                    if (dt > 0) {{
                        const velocity = Math.sqrt(dx * dx + dy * dy) / dt;
                        totalVelocity += velocity;
                        count++;
                    }}
                }}
                
                return count > 0 ? totalVelocity / count : 0;
            }}
            
            checkWebGLSupport() {{
                try {{
                    const canvas = document.createElement('canvas');
                    return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
                }} catch (e) {{
                    return false;
                }}
            }}
            
            showResult(result) {{
                const resultEl = document.getElementById('result');
                resultEl.style.display = 'block';
                
                if (result.error) {{
                    resultEl.className = 'result error';
                    resultEl.innerHTML = `
                        <strong>❌ Verification Error</strong><br>
                        Message: ${{result.message}}
                    `;
                }} else if (result.isHuman) {{
                    resultEl.className = 'result success';
                    resultEl.innerHTML = `
                        <strong>✅ Human Verified!</strong><br>
                        Confidence: ${{Math.round(result.confidence * 100)}}%<br>
                        Response Time: ${{result.responseTime}}ms
                    `;
                }} else {{
                    resultEl.className = 'result error';
                    resultEl.innerHTML = `
                        <strong>🤖 Bot Detected</strong><br>
                        Confidence: ${{Math.round(result.confidence * 100)}}%<br>
                        This would trigger additional verification in production.
                    `;
                }}
            }}
        }}
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', () => {{
            const captcha = new DevPassiveCaptcha();
            captcha.init();
            
            console.log('🛡️ Passive CAPTCHA Development Mode Active');
            console.log('API Endpoint:', DEV_CONFIG.api_endpoint);
        }});
    </script>
</body>
</html>"""
        
        # Write example file
        example_path = Path(__file__).parent / 'dev_example.html'
        with open(example_path, 'w') as f:
            f.write(example_html)
        
        print(f"✅ Example integration created: {example_path}")
        return str(example_path)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print("\\n🛑 Shutting down development server...")
            self.running = False
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def cleanup(self):
        """Clean up running processes"""
        print("🧹 Cleaning up processes...")
        
        for name, process in self.processes:
            try:
                print(f"   Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"   Error stopping {name}: {e}")
    
    def start_development_environment(self):
        """Start complete development environment"""
        print("🚀 Starting Passive CAPTCHA Development Environment")
        print("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Start Flask backend
        if not self.start_flask_backend():
            return False
        
        # Start Cloudflare tunnel
        backend_tunnel_url = self.start_cloudflare_tunnel('backend', 5000)
        
        if not backend_tunnel_url:
            print("❌ Failed to establish tunnel")
            self.cleanup()
            return False
        
        # Create example integration
        example_path = self.create_example_website(backend_tunnel_url)
        
        # Print success information
        print("\\n" + "=" * 60)
        print("🎉 Development Environment Ready!")
        print("=" * 60)
        print(f"📍 Backend API: {backend_tunnel_url}")
        print(f"🌐 Example Integration: file://{example_path}")
        print(f"📊 Health Check: {backend_tunnel_url}/health")
        print(f"🔧 Admin Dashboard: {backend_tunnel_url}/admin/dashboard")
        print("=" * 60)
        print()
        print("🧪 Testing Instructions:")
        print("1. Open the example HTML file in your browser")
        print("2. Move your mouse and type in the form fields")
        print("3. Click submit to test passive CAPTCHA verification")
        print("4. Check the browser console for detailed logs")
        print()
        print("📝 API Registration:")
        print(f"   curl -X POST {backend_tunnel_url}/api/v1/websites/register \\\\")
        print('     -H "Content-Type: application/json" \\\\')
        print('     -d \'{"name": "My Website", "url": "https://example.com", "admin_email": "admin@example.com"}\'')
        print()
        print("🛑 Press Ctrl+C to stop the development server")
        print("=" * 60)
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        return True

def main():
    """Main entry point"""
    dev_manager = LocalDevManager()
    success = dev_manager.start_development_environment()
    
    if not success:
        print("❌ Failed to start development environment")
        sys.exit(1)

if __name__ == "__main__":
    main()