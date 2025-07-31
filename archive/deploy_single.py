#!/usr/bin/env python3
"""
Single Clean Deployment for Passive CAPTCHA
No legacy endpoints, single /login endpoint
"""

import os
import sys
import subprocess
import time
import signal

def run_cmd(cmd, desc=""):
    print(f"🔄 {desc}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {desc} - Success")
        return True
    else:
        print(f"❌ {desc} - Failed: {result.stderr}")
        return False

def main():
    print("🚀 PASSIVE CAPTCHA - CLEAN SINGLE DEPLOYMENT")
    print("=" * 60)
    
    # Kill any running processes
    print("🛑 Stopping existing services...")
    subprocess.run("pkill -f start_production.py", shell=True)
    subprocess.run("pkill -f cloudflared", shell=True)
    time.sleep(2)
    
    # Set environment
    os.environ['ADMIN_SECRET'] = 'Admin123'
    os.environ['PORT'] = '5003'
    
    # Start backend
    print("🖥️  Starting backend server...")
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    
    try:
        backend_process = subprocess.Popen(
            ['python', 'start_production.py'],
            cwd=backend_dir,
            env=os.environ.copy()
        )
        
        # Wait for startup
        print("⏳ Waiting for backend startup...")
        time.sleep(15)
        
        # Check if running
        if backend_process.poll() is None:
            print("✅ Backend server is running")
        else:
            print("❌ Backend failed to start")
            return
        
        # Test login endpoint
        print("🔐 Testing login endpoint...")
        test_result = subprocess.run([
            'curl', '-s', 'http://localhost:5003/login'
        ], capture_output=True, text=True)
        
        if test_result.returncode == 0 and 'endpoint' in test_result.stdout:
            print("✅ Login endpoint working")
        else:
            print("❌ Login endpoint test failed")
            print(f"Response: {test_result.stdout}")
        
        # Test POST login
        print("🔑 Testing authentication...")
        auth_result = subprocess.run([
            'curl', '-s', '-X', 'POST', 
            'http://localhost:5003/login',
            '-H', 'Content-Type: application/json',
            '-d', '{"password": "Admin123"}'
        ], capture_output=True, text=True)
        
        if auth_result.returncode == 0 and 'token' in auth_result.stdout:
            print("✅ Authentication working")
        else:
            print("❌ Authentication failed")
            print(f"Response: {auth_result.stdout}")
        
        # Start tunnel
        print("🌐 Starting Cloudflare tunnel...")
        try:
            tunnel_process = subprocess.Popen(
                ['cloudflared', 'tunnel', '--url', 'http://localhost:5003'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for tunnel URL
            print("⏳ Waiting for tunnel URL...")
            tunnel_url = None
            
            for _ in range(30):  # Wait up to 30 seconds
                if tunnel_process.poll() is not None:
                    break
                    
                try:
                    line = tunnel_process.stdout.readline()
                    if 'trycloudflare.com' in line:
                        import re
                        url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                        if url_match:
                            tunnel_url = url_match.group(0)
                            break
                except:
                    pass
                    
                time.sleep(1)
            
            if tunnel_url:
                print(f"✅ Tunnel created: {tunnel_url}")
                
                # Test tunnel
                print("🌐 Testing tunnel...")
                time.sleep(5)
                tunnel_test = subprocess.run([
                    'curl', '-s', f'{tunnel_url}/login'
                ], capture_output=True, text=True)
                
                if tunnel_test.returncode == 0:
                    print("✅ Tunnel working")
                else:
                    print("❌ Tunnel test failed")
            
        except Exception as e:
            print(f"⚠️  Tunnel failed: {e}")
            tunnel_process = None
            tunnel_url = None
        
        # Final status
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT COMPLETE!")
        print("=" * 60)
        
        print(f"\n🌐 ACCESS URLS:")
        print(f"   Local:  http://localhost:5003/")
        print(f"   Login:  http://localhost:5003/login")
        
        if tunnel_url:
            print(f"   Public: {tunnel_url}/")
            print(f"   Tunnel: {tunnel_url}/login")
        
        print(f"\n🔑 CREDENTIALS:")
        print(f"   Password: Admin123")
        
        print(f"\n🧪 TEST COMMANDS:")
        print(f"   # Login:")
        print(f"   curl -X POST http://localhost:5003/login \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d '{{\"password\": \"Admin123\"}}'")
        
        if tunnel_url:
            print(f"\n   # Public login:")
            print(f"   curl -X POST {tunnel_url}/login \\")
            print(f"        -H 'Content-Type: application/json' \\")
            print(f"        -d '{{\"password\": \"Admin123\"}}'")
        
        print(f"\n⚡ PRESS CTRL+C TO STOP")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping deployment...")
            
            if backend_process:
                backend_process.terminate()
                print("✅ Backend stopped")
            
            if 'tunnel_process' in locals() and tunnel_process:
                tunnel_process.terminate()
                print("✅ Tunnel stopped")
            
            print("✅ Deployment stopped")
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

if __name__ == '__main__':
    main()