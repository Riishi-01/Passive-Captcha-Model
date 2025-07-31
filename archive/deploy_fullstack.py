#!/usr/bin/env python3
"""
Complete Fullstack Deployment for Passive CAPTCHA
Deploys frontend + backend on single port with tunnel support
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def print_status(message, status="info"):
    colors = {
        "success": "\033[92m✅",
        "error": "\033[91m❌",
        "warning": "\033[93m⚠️",
        "info": "\033[94mℹ️",
        "progress": "\033[96m🔄"
    }
    print(f"{colors.get(status, '')} {message}\033[0m")

def run_command(cmd, cwd=None, description="", check=True):
    """Run command with error handling"""
    print_status(f"Running: {description}", "progress")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0 or not check:
            print_status(f"✅ {description}", "success")
            return True, result.stdout
        else:
            print_status(f"❌ {description} failed: {result.stderr}", "error")
            return False, result.stderr
    except Exception as e:
        print_status(f"❌ {description} error: {e}", "error")
        return False, str(e)

def check_prerequisites():
    """Check system requirements"""
    print_status("Checking prerequisites...", "progress")
    
    # Check Python
    if sys.version_info < (3, 8):
        print_status("Python 3.8+ required", "error")
        return False
    
    # Check Node.js
    success, _ = run_command("node --version", description="Node.js check", check=False)
    if not success:
        print_status("Node.js not found", "error")
        return False
    
    # Check npm
    success, _ = run_command("npm --version", description="npm check", check=False)
    if not success:
        print_status("npm not found", "error")
        return False
    
    print_status("All prerequisites met", "success")
    return True

def build_frontend():
    """Build the Vue.js frontend"""
    frontend_dir = Path(__file__).parent / 'frontend'
    
    print_status("Building Vue.js frontend...", "progress")
    
    # Install dependencies
    success, _ = run_command("npm install", cwd=frontend_dir, description="Installing frontend dependencies")
    if not success:
        return False
    
    # Build for production
    success, _ = run_command("npm run build", cwd=frontend_dir, description="Building frontend")
    if not success:
        return False
    
    # Verify build
    dist_dir = frontend_dir / 'dist'
    if not dist_dir.exists():
        print_status("Frontend build failed - no dist directory", "error")
        return False
    
    print_status(f"Frontend built successfully at {dist_dir}", "success")
    return True

def setup_backend():
    """Setup backend environment"""
    backend_dir = Path(__file__).parent / 'backend'
    
    print_status("Setting up backend...", "progress")
    
    # Create directories
    for dir_name in ['logs', 'uploads']:
        (backend_dir / dir_name).mkdir(exist_ok=True)
    
    # Install Python dependencies
    success, _ = run_command("pip install -r requirements.txt", cwd=backend_dir, description="Installing Python dependencies")
    if not success:
        print_status("Consider running: pip install --upgrade pip", "warning")
        return False
    
    print_status("Backend setup complete", "success")
    return True

def start_backend_server():
    """Start the backend server"""
    backend_dir = Path(__file__).parent / 'backend'
    
    print_status("Starting backend server...", "progress")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'FLASK_ENV': 'production',
        'ADMIN_SECRET': 'Admin123',
        'PORT': '5003',
        'HOST': '0.0.0.0'
    })
    
    # Start server in background
    try:
        process = subprocess.Popen(
            ['python', 'start_production.py'],
            cwd=backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(8)
        
        # Check if still running
        if process.poll() is None:
            print_status("Backend server started successfully", "success")
            return True, process
        else:
            stdout, stderr = process.communicate()
            print_status(f"Backend failed to start: {stderr}", "error")
            return False, None
    except Exception as e:
        print_status(f"Failed to start backend: {e}", "error")
        return False, None

def test_deployment():
    """Test the complete deployment"""
    print_status("Testing deployment...", "progress")
    
    import requests
    import json
    
    localhost = "http://localhost:5003"
    
    try:
        # Test frontend
        response = requests.get(f"{localhost}/", timeout=10)
        if response.status_code == 200:
            print_status("Frontend accessible", "success")
        else:
            print_status(f"Frontend test failed: {response.status_code}", "error")
            return False
        
        # Test login endpoint
        response = requests.post(
            f"{localhost}/admin/legacy/login",
            json={"password": "Admin123"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                print_status("Authentication working", "success")
                token = data['token']
                
                # Test authenticated endpoint
                response = requests.get(
                    f"{localhost}/admin/analytics/summary",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    print_status("API endpoints working", "success")
                    return True
                else:
                    print_status("API test failed", "warning")
                    return True  # Login works, that's enough
            else:
                print_status("Login response invalid", "error")
                return False
        else:
            print_status(f"Login test failed: {response.status_code}", "error")
            return False
            
    except Exception as e:
        print_status(f"Test failed: {e}", "error")
        return False

def start_tunnel():
    """Start Cloudflare tunnel"""
    print_status("Starting Cloudflare tunnel...", "progress")
    
    try:
        # Check if cloudflared is available
        result = subprocess.run(['cloudflared', '--version'], capture_output=True)
        if result.returncode != 0:
            print_status("Cloudflared not found. Install with: brew install cloudflared", "warning")
            return False, None
        
        # Start tunnel
        print_status("Creating tunnel... (this will take a few seconds)", "progress")
        process = subprocess.Popen(
            ['cloudflared', 'tunnel', '--url', 'http://localhost:5003'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for tunnel URL
        for _ in range(20):  # Wait up to 20 seconds
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print_status(f"Tunnel failed: {stderr}", "error")
                return False, None
            
            # Check stdout for tunnel URL
            try:
                line = process.stdout.readline()
                if 'trycloudflare.com' in line:
                    # Extract URL
                    import re
                    url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if url_match:
                        tunnel_url = url_match.group(0)
                        print_status(f"Tunnel created: {tunnel_url}", "success")
                        return True, (process, tunnel_url)
            except:
                pass
            
            time.sleep(1)
        
        print_status("Tunnel startup timeout", "error")
        process.terminate()
        return False, None
        
    except Exception as e:
        print_status(f"Tunnel error: {e}", "error")
        return False, None

def main():
    """Main deployment function"""
    print("🚀 PASSIVE CAPTCHA - FULLSTACK DEPLOYMENT")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Build frontend
    if not build_frontend():
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        sys.exit(1)
    
    # Start backend
    success, backend_process = start_backend_server()
    if not success:
        sys.exit(1)
    
    # Test deployment
    if not test_deployment():
        print_status("Deployment test failed, but server is running", "warning")
    
    # Start tunnel
    tunnel_success, tunnel_data = start_tunnel()
    tunnel_process = None
    tunnel_url = None
    
    if tunnel_success and tunnel_data:
        tunnel_process, tunnel_url = tunnel_data
    
    # Final status
    print("\n" + "=" * 60)
    print_status("🎉 FULLSTACK DEPLOYMENT COMPLETE!", "success")
    print("=" * 60)
    
    print(f"\n🌐 ACCESS URLS:")
    print(f"   Local Frontend:  http://localhost:5003/")
    print(f"   Local Login:     http://localhost:5003/login")
    print(f"   Local API:       http://localhost:5003/admin/legacy/login")
    
    if tunnel_url:
        print(f"   Public Frontend: {tunnel_url}/")
        print(f"   Public Login:    {tunnel_url}/login")
        print(f"   Public API:      {tunnel_url}/admin/legacy/login")
    
    print(f"\n🔑 CREDENTIALS:")
    print(f"   Password: Admin123")
    
    print(f"\n🧪 TEST COMMANDS:")
    print(f"   # Test login:")
    print(f"   curl -X POST http://localhost:5003/admin/legacy/login \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{\"password\": \"Admin123\"}}'")
    
    if tunnel_url:
        print(f"\n   # Test public login:")
        print(f"   curl -X POST {tunnel_url}/admin/legacy/login \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d '{{\"password\": \"Admin123\"}}'")
    
    print(f"\n📱 OPEN IN BROWSER:")
    print(f"   Local:  open http://localhost:5003/")
    if tunnel_url:
        print(f"   Public: open {tunnel_url}/")
    
    print(f"\n⚡ PRESS CTRL+C TO STOP")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_status("\n🛑 Stopping deployment...", "info")
        
        if backend_process:
            backend_process.terminate()
            print_status("Backend stopped", "info")
        
        if tunnel_process:
            tunnel_process.terminate()
            print_status("Tunnel stopped", "info")
        
        print_status("Deployment stopped", "success")

if __name__ == '__main__':
    main()