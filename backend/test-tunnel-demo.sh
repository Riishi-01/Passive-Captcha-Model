#!/bin/bash

# Demo script to show Cloudflare tunnel setup
echo "🌐 CLOUDFLARE TUNNEL DEMO"
echo "========================="
echo ""
echo "This demonstrates what happens on your VPS:"
echo ""

# Check if cloudflared is available
if command -v cloudflared &> /dev/null; then
    echo "✅ cloudflared is installed (version: $(cloudflared --version | cut -d' ' -f3))"
else
    echo "❌ cloudflared not found - it will be installed on VPS"
    exit 1
fi

echo ""
echo "1. Starting a test HTTP server on port 8000..."

# Start a simple HTTP server
python3 -c "
import http.server
import socketserver
import threading
import time

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{\"status\": \"healthy\", \"service\": \"passive-captcha-demo\"}')
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Passive CAPTCHA Demo</h1><p>Server is running!</p>')

def start_server():
    with socketserver.TCPServer(('', 8000), MyHandler) as httpd:
        httpd.serve_forever()

# Start server in background
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

print('Demo server started on http://localhost:8000')
print('Testing health endpoint...')

time.sleep(1)
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000/health')
    print(f'Health check: {response.read().decode()}')
except:
    print('Health check failed')

print()
print('Demo server is ready. In production, this would be your Flask app.')
print('Now you would run: cloudflared tunnel --url http://localhost:8000')
print()
print('This creates a public HTTPS URL like: https://random-words-123.trycloudflare.com')
print('The tunnel provides:')
print('  ✅ Public HTTPS access')
print('  ✅ No port forwarding needed')
print('  ✅ No firewall configuration')
print('  ✅ DDoS protection')
print('  ✅ Global CDN distribution')
print()
print('Press Ctrl+C to stop')

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('\nDemo stopped')
" &

# Get the PID of the Python server
SERVER_PID=$!

echo ""
echo "2. Test the local server:"
sleep 2
curl -s http://localhost:8000/health || echo "Server starting..."

echo ""
echo "3. In production, you would run:"
echo "   cloudflared tunnel --url http://localhost:5000"
echo ""
echo "4. This creates a public URL like:"
echo "   🌐 https://random-words-1234.trycloudflare.com"
echo ""
echo "5. Your CAPTCHA API would be accessible at:"
echo "   https://random-words-1234.trycloudflare.com/api/verify"
echo ""

# Stop the demo server
kill $SERVER_PID 2>/dev/null

echo "Demo complete! On your VPS, run: ./vps-deploy.sh deploy" 