"""
Comprehensive Prototype API for Passive Captcha Real-time Analytics
Complete demonstration platform with instant deployment capabilities
"""

from flask import Blueprint, request, jsonify, render_template_string
from flask_socketio import emit, join_room, leave_room
from datetime import datetime, timedelta
import json
import random
import uuid
from typing import Dict, List, Any
import logging

# Create prototype blueprint
prototype_bp = Blueprint('prototype', __name__, url_prefix='/prototype')

# Mock data storage for demonstration
class PrototypeDataStore:
    def __init__(self):
        self.active_sessions = {}
        self.analytics_data = []
        self.websites = []
        self.real_time_events = []
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for the prototype"""
        # Demo websites
        demo_websites = [
            {
                'id': 'uidai-home',
                'name': 'UIDAI Home Page',
                'url': 'https://uidai.gov.in/',
                'status': 'active',
                'created_at': datetime.now() - timedelta(days=30),
                'sessions_today': random.randint(150, 300),
                'bot_detections': random.randint(5, 25),
                'success_rate': round(random.uniform(0.85, 0.98), 3)
            },
            {
                'id': 'uidai-about',
                'name': 'UIDAI About Page',
                'url': 'https://uidai.gov.in/about',
                'status': 'active',
                'created_at': datetime.now() - timedelta(days=25),
                'sessions_today': random.randint(80, 180),
                'bot_detections': random.randint(2, 15),
                'success_rate': round(random.uniform(0.90, 0.97), 3)
            }
        ]
        self.websites = demo_websites
        
        # Generate demo analytics data
        for i in range(100):
            event_time = datetime.now() - timedelta(minutes=random.randint(0, 1440))
            self.analytics_data.append({
                'id': str(uuid.uuid4()),
                'website_id': random.choice(['uidai-home', 'uidai-about']),
                'timestamp': event_time,
                'event_type': random.choice(['verification', 'bot_detection', 'session_start', 'suspicious_activity']),
                'confidence_score': round(random.uniform(0.1, 1.0), 3),
                'user_agent': random.choice(['Mozilla/5.0...', 'Chrome/...', 'Safari/...', 'Bot/1.0']),
                'ip_address': f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                'session_duration': random.randint(10, 600),
                'mouse_movements': random.randint(0, 500),
                'keyboard_events': random.randint(0, 100),
                'scroll_events': random.randint(0, 50)
            })

# Global data store instance
data_store = PrototypeDataStore()

@prototype_bp.route('/')
def dashboard():
    """Main prototype dashboard"""
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Passive Captcha - Live Analytics Prototype</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            .header {
                background: rgba(255,255,255,0.95);
                padding: 1rem 2rem;
                box-shadow: 0 2px 20px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
            }
            .header h1 {
                color: #2c3e50;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .live-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #e74c3c;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
            }
            .card {
                background: rgba(255,255,255,0.95);
                border-radius: 15px;
                padding: 1.5rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
                transition: transform 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
            }
            .card h3 {
                color: #2c3e50;
                margin-bottom: 1rem;
                font-size: 1.2rem;
                border-bottom: 2px solid #3498db;
                padding-bottom: 0.5rem;
            }
            .metric {
                display: flex;
                justify-content: space-between;
                margin: 0.5rem 0;
                padding: 0.5rem;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 8px;
            }
            .metric .value {
                font-weight: bold;
                color: #2980b9;
            }
            .chart-container {
                position: relative;
                height: 300px;
                margin: 1rem 0;
            }
            .event-log {
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                padding: 1rem;
            }
            .event-item {
                padding: 0.5rem;
                margin: 0.25rem 0;
                border-left: 4px solid #3498db;
                background: rgba(52, 152, 219, 0.05);
                border-radius: 0 5px 5px 0;
                font-size: 0.9rem;
            }
            .event-bot {
                border-left-color: #e74c3c;
                background: rgba(231, 76, 60, 0.05);
            }
            .event-suspicious {
                border-left-color: #f39c12;
                background: rgba(243, 156, 18, 0.05);
            }
            .status-active {
                color: #27ae60;
                font-weight: bold;
            }
            .api-demo {
                grid-column: 1 / -1;
            }
            .api-endpoint {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 1rem;
                border-radius: 8px;
                margin: 0.5rem 0;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
                overflow-x: auto;
            }
            .btn {
                background: linear-gradient(45deg, #3498db, #2980b9);
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1rem;
                transition: all 0.3s ease;
                margin: 0.5rem;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
            }
            .integration-demo {
                background: #34495e;
                color: white;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>
                🛡️ Passive Captcha Analytics - Live Prototype
                <span class="live-indicator"></span>
                <span style="font-size: 0.7em; color: #7f8c8d;">LIVE</span>
            </h1>
            <p style="margin-top: 0.5rem; color: #7f8c8d;">Real-time bot detection and analytics for Railway deployment</p>
        </div>

        <div class="container">
            <!-- Real-time Metrics -->
            <div class="card">
                <h3>📊 Live Metrics</h3>
                <div class="metric">
                    <span>Active Sessions</span>
                    <span class="value" id="activeSessions">Loading...</span>
                </div>
                <div class="metric">
                    <span>Bot Detections (24h)</span>
                    <span class="value" id="botDetections">Loading...</span>
                </div>
                <div class="metric">
                    <span>Success Rate</span>
                    <span class="value" id="successRate">Loading...</span>
                </div>
                <div class="metric">
                    <span>Uptime</span>
                    <span class="value status-active" id="uptime">Loading...</span>
                </div>
            </div>

            <!-- Website Status -->
            <div class="card">
                <h3>🌐 Protected Websites</h3>
                <div id="websitesList">Loading...</div>
            </div>

            <!-- Detection Trends Chart -->
            <div class="card">
                <h3>📈 Detection Trends</h3>
                <div class="chart-container">
                    <canvas id="trendsChart"></canvas>
                </div>
            </div>

            <!-- Live Activity Feed -->
            <div class="card">
                <h3>🔴 Live Activity Feed</h3>
                <div class="event-log" id="eventLog">
                    <div class="event-item">System initialized - Monitoring started</div>
                </div>
            </div>

            <!-- API Endpoints Demo -->
            <div class="card api-demo">
                <h3>🔌 API Endpoints & Integration</h3>
                <p>Interactive API documentation and testing interface:</p>
                
                <div class="api-endpoint">
                    <strong>GET</strong> /prototype/api/analytics
                    <br>Real-time analytics data
                </div>
                
                <div class="api-endpoint">
                    <strong>POST</strong> /prototype/api/verify
                    <br>Verify user interaction data
                </div>
                
                <div class="api-endpoint">
                    <strong>WebSocket</strong> /prototype/live
                    <br>Real-time event streaming
                </div>

                <button class="btn" onclick="testAPI()">🧪 Test API Endpoints</button>
                <button class="btn" onclick="showIntegration()">📋 View Integration Code</button>
                <button class="btn" onclick="generateDemoData()">🎲 Generate Demo Data</button>

                <div id="integrationCode" class="integration-demo" style="display: none;">
                    <h4>Integration Example - UIDAI Site:</h4>
                    <pre id="codeExample"></pre>
                </div>
            </div>
        </div>

        <script>
            const socket = io('/prototype');
            let trendsChart;

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                initializeCharts();
                loadInitialData();
                setupWebSocket();
                updateMetrics();
                setInterval(updateMetrics, 5000); // Update every 5 seconds
            });

            function initializeCharts() {
                const ctx = document.getElementById('trendsChart').getContext('2d');
                trendsChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Bot Detections',
                            data: [],
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            tension: 0.4
                        }, {
                            label: 'Legitimate Users',
                            data: [],
                            borderColor: '#27ae60',
                            backgroundColor: 'rgba(39, 174, 96, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }

            function setupWebSocket() {
                socket.on('connect', function() {
                    console.log('Connected to real-time analytics');
                    addEventToLog('🟢 Connected to live analytics stream', 'event-item');
                });

                socket.on('analytics_update', function(data) {
                    updateMetricsData(data);
                    updateChart(data);
                });

                socket.on('new_detection', function(data) {
                    const eventClass = data.type === 'bot' ? 'event-bot' : 
                                     data.type === 'suspicious' ? 'event-suspicious' : 'event-item';
                    addEventToLog(`${data.icon} ${data.message}`, eventClass);
                });

                socket.on('website_update', function(data) {
                    updateWebsitesList(data);
                });
            }

            function loadInitialData() {
                fetch('/prototype/api/analytics')
                    .then(response => response.json())
                    .then(data => {
                        updateMetricsData(data);
                        updateWebsitesList(data.websites || []);
                    })
                    .catch(error => console.error('Error loading data:', error));
            }

            function updateMetrics() {
                // Simulate real-time metrics updates
                const sessions = Math.floor(Math.random() * 50) + 100;
                const detections = Math.floor(Math.random() * 10) + 5;
                const successRate = (Math.random() * 0.1 + 0.9).toFixed(3);
                
                document.getElementById('activeSessions').textContent = sessions;
                document.getElementById('botDetections').textContent = detections;
                document.getElementById('successRate').textContent = (successRate * 100) + '%';
                
                // Update uptime
                const startTime = new Date().getTime() - (Math.random() * 86400000); // Random uptime up to 24h
                const uptime = Math.floor((new Date().getTime() - startTime) / 60000);
                document.getElementById('uptime').textContent = uptime + ' minutes';
            }

            function updateMetricsData(data) {
                if (data.metrics) {
                    document.getElementById('activeSessions').textContent = data.metrics.activeSessions || 'N/A';
                    document.getElementById('botDetections').textContent = data.metrics.botDetections || 'N/A';
                    document.getElementById('successRate').textContent = (data.metrics.successRate * 100).toFixed(1) + '%';
                }
            }

            function updateWebsitesList(websites) {
                const container = document.getElementById('websitesList');
                if (!websites || websites.length === 0) return;
                
                container.innerHTML = websites.map(site => `
                    <div class="metric">
                        <div>
                            <strong>${site.name}</strong><br>
                            <small style="color: #7f8c8d;">${site.url}</small>
                        </div>
                        <div class="status-active">${site.status}</div>
                    </div>
                `).join('');
            }

            function updateChart(data) {
                if (!data.chartData) return;
                
                const now = new Date().toLocaleTimeString();
                trendsChart.data.labels.push(now);
                trendsChart.data.datasets[0].data.push(data.chartData.botDetections || Math.floor(Math.random() * 10));
                trendsChart.data.datasets[1].data.push(data.chartData.legitimateUsers || Math.floor(Math.random() * 50) + 20);
                
                // Keep only last 20 data points
                if (trendsChart.data.labels.length > 20) {
                    trendsChart.data.labels.shift();
                    trendsChart.data.datasets.forEach(dataset => dataset.data.shift());
                }
                
                trendsChart.update('none');
            }

            function addEventToLog(message, className = 'event-item') {
                const eventLog = document.getElementById('eventLog');
                const eventItem = document.createElement('div');
                eventItem.className = className;
                eventItem.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> ${message}`;
                eventLog.insertBefore(eventItem, eventLog.firstChild);
                
                // Keep only last 20 events
                while (eventLog.children.length > 20) {
                    eventLog.removeChild(eventLog.lastChild);
                }
            }

            function testAPI() {
                addEventToLog('🧪 Testing API endpoints...', 'event-item');
                
                fetch('/prototype/api/test')
                    .then(response => response.json())
                    .then(data => {
                        addEventToLog(`✅ API Test successful: ${data.message}`, 'event-item');
                    })
                    .catch(error => {
                        addEventToLog(`❌ API Test failed: ${error.message}`, 'event-bot');
                    });
            }

            function showIntegration() {
                const codeExample = `
// Passive Captcha Integration for UIDAI Site
<script src="https://passive-captcha-model-production.up.railway.app/static/passive-captcha-script.js"></script>
<script>
window.PASSIVE_CAPTCHA_CONFIG = {
    apiEndpoint: 'https://passive-captcha-model-production.up.railway.app/api/verify',
    scriptToken: 'your-script-token-here',
    websiteUrl: 'https://uidai.gov.in',
    collectMouseMovements: true,
    collectKeyboardPatterns: true,
    collectScrollBehavior: true,
    debugMode: false
};

// Initialize passive captcha
PassiveCaptcha.init();

// Optional: Handle verification results
PassiveCaptcha.onVerification(function(result) {
    if (result.isBot) {
        console.log('Bot detected with confidence:', result.confidence);
        // Handle bot detection
    } else {
        console.log('Human user verified');
        // Proceed with normal flow
    }
});
</script>

// Server-side verification (Node.js/PHP/Python)
fetch('https://passive-captcha-model-production.up.railway.app/api/verify', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your-api-key'
    },
    body: JSON.stringify({
        sessionData: userInteractionData,
        websiteId: 'uidai-site'
    })
}).then(response => response.json())
  .then(result => {
      if (result.verification.isBot) {
          // Handle bot traffic
      } else {
          // Allow legitimate user
      }
  });
                `;
                
                document.getElementById('codeExample').textContent = codeExample;
                document.getElementById('integrationCode').style.display = 'block';
                addEventToLog('📋 Integration code displayed', 'event-item');
            }

            function generateDemoData() {
                addEventToLog('🎲 Generating demo detection events...', 'event-item');
                
                const events = [
                    { type: 'bot', icon: '🤖', message: 'Bot detected from IP 192.168.1.100 - Suspicious mouse patterns' },
                    { type: 'suspicious', icon: '⚠️', message: 'Suspicious activity detected - Rapid form submission' },
                    { type: 'normal', icon: '✅', message: 'Human user verified - Natural interaction patterns' },
                    { type: 'bot', icon: '🚫', message: 'Automated script blocked - No mouse movement detected' },
                    { type: 'normal', icon: '👤', message: 'New user session started - Collecting behavioral data' }
                ];
                
                events.forEach((event, index) => {
                    setTimeout(() => {
                        const eventClass = event.type === 'bot' ? 'event-bot' : 
                                         event.type === 'suspicious' ? 'event-suspicious' : 'event-item';
                        addEventToLog(`${event.icon} ${event.message}`, eventClass);
                    }, index * 1000);
                });
            }

            // Simulate random events
            setInterval(() => {
                if (Math.random() < 0.3) { // 30% chance every 5 seconds
                    generateDemoData();
                }
            }, 5000);
        </script>
    </body>
    </html>
    """
    return dashboard_html

@prototype_bp.route('/api/analytics')
def get_analytics():
    """Get current analytics data"""
    try:
        # Calculate metrics from demo data
        total_sessions = len(data_store.analytics_data)
        bot_detections = len([d for d in data_store.analytics_data if d['event_type'] == 'bot_detection'])
        success_rate = 1 - (bot_detections / max(total_sessions, 1))
        
        # Recent activity (last hour)
        recent_time = datetime.now() - timedelta(hours=1)
        recent_data = [d for d in data_store.analytics_data if d['timestamp'] > recent_time]
        
        return jsonify({
            'success': True,
            'metrics': {
                'activeSessions': len(data_store.active_sessions),
                'botDetections': bot_detections,
                'successRate': success_rate,
                'totalEvents': total_sessions,
                'recentActivity': len(recent_data)
            },
            'websites': data_store.websites,
            'chartData': {
                'botDetections': bot_detections,
                'legitimateUsers': total_sessions - bot_detections
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@prototype_bp.route('/api/verify', methods=['POST'])
def verify_interaction():
    """Verify user interaction data"""
    try:
        data = request.get_json()
        
        # Simulate ML model prediction
        confidence_score = random.uniform(0.1, 1.0)
        is_bot = confidence_score < 0.3 or random.random() < 0.1  # 10% chance of bot detection
        
        # Store interaction data
        interaction_id = str(uuid.uuid4())
        data_store.analytics_data.append({
            'id': interaction_id,
            'timestamp': datetime.now(),
            'event_type': 'verification',
            'confidence_score': confidence_score,
            'is_bot': is_bot,
            'session_data': data.get('sessionData', {}),
            'website_id': data.get('websiteId', 'unknown')
        })
        
        return jsonify({
            'success': True,
            'verification': {
                'id': interaction_id,
                'isBot': is_bot,
                'confidence': confidence_score,
                'riskLevel': 'high' if is_bot else 'low',
                'recommendations': ['Block user'] if is_bot else ['Allow access'],
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@prototype_bp.route('/api/test')
def test_api():
    """Test API endpoint"""
    return jsonify({
        'success': True,
        'message': 'API is working correctly',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/prototype/api/analytics',
            '/prototype/api/verify',
            '/prototype/api/websites',
            '/prototype/live (WebSocket)'
        ]
    })

@prototype_bp.route('/api/websites')
def get_websites():
    """Get protected websites list"""
    return jsonify({
        'success': True,
        'websites': data_store.websites,
        'count': len(data_store.websites)
    })

@prototype_bp.route('/integration-demo')
def integration_demo():
    """Demo page showing UIDAI site integration"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UIDAI Integration Demo - Passive Captcha</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #f5f5f5;
            }
            .demo-container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }
            .uidai-header {
                background: linear-gradient(135deg, #000046 0%, #1cb5e0 100%);
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .demo-form {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            .form-group input {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
            .submit-btn {
                background: #007bff;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .status-panel {
                background: #e9ecef;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }
            .status-item {
                margin: 10px 0;
                padding: 10px;
                border-left: 4px solid #007bff;
                background: white;
            }
            .bot-detected {
                border-left-color: #dc3545;
                background: #f8d7da;
            }
            .human-verified {
                border-left-color: #28a745;
                background: #d4edda;
            }
        </style>
        <!-- Passive Captcha Integration -->
        <script src="/static/passive-captcha-script.js"></script>
    </head>
    <body>
        <div class="demo-container">
            <div class="uidai-header">
                <h1>🏛️ UIDAI Service Portal</h1>
                <p>Secure access protected by Passive Captcha technology</p>
            </div>

            <div class="demo-form">
                <h3>Aadhaar Service Request</h3>
                <form id="demoForm">
                    <div class="form-group">
                        <label for="aadhaar">Aadhaar Number:</label>
                        <input type="text" id="aadhaar" name="aadhaar" placeholder="Enter 12-digit Aadhaar number">
                    </div>
                    <div class="form-group">
                        <label for="mobile">Mobile Number:</label>
                        <input type="tel" id="mobile" name="mobile" placeholder="Enter mobile number">
                    </div>
                    <div class="form-group">
                        <label for="service">Service Type:</label>
                        <select id="service" name="service" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                            <option value="">Select service</option>
                            <option value="download">Download Aadhaar</option>
                            <option value="update">Update Information</option>
                            <option value="verify">Verify Aadhaar</option>
                        </select>
                    </div>
                    <button type="submit" class="submit-btn">Submit Request</button>
                </form>
            </div>

            <div class="status-panel">
                <h3>🛡️ Passive Captcha Status</h3>
                <div id="captchaStatus">
                    <div class="status-item">
                        <strong>Protection Status:</strong> <span id="protectionStatus">Initializing...</span>
                    </div>
                    <div class="status-item">
                        <strong>Session ID:</strong> <span id="sessionId">Generating...</span>
                    </div>
                    <div class="status-item">
                        <strong>Behavioral Analysis:</strong> <span id="behaviorStatus">Monitoring...</span>
                    </div>
                    <div class="status-item">
                        <strong>Risk Assessment:</strong> <span id="riskLevel">Calculating...</span>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Configure Passive Captcha
            window.PASSIVE_CAPTCHA_CONFIG = {
                apiEndpoint: '/prototype/api/verify',
                websiteUrl: window.location.origin,
                collectMouseMovements: true,
                collectKeyboardPatterns: true,
                collectScrollBehavior: true,
                debugMode: true
            };

            // Initialize status display
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('protectionStatus').textContent = 'Active ✅';
                document.getElementById('sessionId').textContent = 'PC-' + Math.random().toString(36).substr(2, 9);
                document.getElementById('behaviorStatus').textContent = 'Collecting data...';
                document.getElementById('riskLevel').textContent = 'Low Risk ✅';

                // Simulate real-time updates
                setInterval(updateStatus, 3000);
            });

            // Handle form submission with passive captcha
            document.getElementById('demoForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Simulate verification process
                document.getElementById('behaviorStatus').textContent = 'Analyzing patterns...';
                
                setTimeout(() => {
                    const isBot = Math.random() < 0.2; // 20% chance of bot detection
                    
                    if (isBot) {
                        showBotDetection();
                    } else {
                        showHumanVerification();
                    }
                }, 2000);
            });

            function updateStatus() {
                const statuses = [
                    'Monitoring mouse patterns...',
                    'Analyzing keyboard timing...',
                    'Tracking scroll behavior...',
                    'Processing interaction data...'
                ];
                
                const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
                document.getElementById('behaviorStatus').textContent = randomStatus;
            }

            function showBotDetection() {
                const statusPanel = document.getElementById('captchaStatus');
                statusPanel.innerHTML = `
                    <div class="status-item bot-detected">
                        <strong>🤖 BOT DETECTED!</strong><br>
                        Suspicious interaction patterns identified. Access denied for security.
                    </div>
                    <div class="status-item">
                        <strong>Detection Reason:</strong> Automated mouse movements and timing patterns
                    </div>
                `;
            }

            function showHumanVerification() {
                const statusPanel = document.getElementById('captchaStatus');
                statusPanel.innerHTML = `
                    <div class="status-item human-verified">
                        <strong>✅ HUMAN VERIFIED!</strong><br>
                        Natural interaction patterns detected. Processing your request...
                    </div>
                    <div class="status-item">
                        <strong>Confidence Score:</strong> 98.7% Human
                    </div>
                `;
                
                // Simulate successful form processing
                setTimeout(() => {
                    alert('Request submitted successfully! You will receive an OTP shortly.');
                }, 1500);
            }
        </script>
    </body>
    </html>
    """)

# WebSocket events for real-time updates
def init_websocket_events(socketio):
    """Initialize WebSocket events for the prototype"""
    
    @socketio.on('connect', namespace='/prototype')
    def handle_connect():
        """Handle client connection"""
        emit('connected', {'message': 'Connected to Passive Captcha Analytics'})
        logging.info('Client connected to prototype namespace')
    
    @socketio.on('disconnect', namespace='/prototype') 
    def handle_disconnect():
        """Handle client disconnection"""
        logging.info('Client disconnected from prototype namespace')
    
    @socketio.on('request_update', namespace='/prototype')
    def handle_update_request():
        """Handle request for data update"""
        # Send current analytics data
        total_sessions = len(data_store.analytics_data)
        bot_detections = len([d for d in data_store.analytics_data if d['event_type'] == 'bot_detection'])
        
        emit('analytics_update', {
            'metrics': {
                'activeSessions': len(data_store.active_sessions),
                'botDetections': bot_detections,
                'successRate': 1 - (bot_detections / max(total_sessions, 1))
            },
            'chartData': {
                'botDetections': bot_detections,
                'legitimateUsers': total_sessions - bot_detections
            },
            'timestamp': datetime.now().isoformat()
        })

# Function to send periodic updates
def send_periodic_updates(socketio):
    """Send periodic updates to connected clients"""
    import threading
    import time
    
    def update_loop():
        while True:
            try:
                # Generate random detection event
                if random.random() < 0.3:  # 30% chance
                    event_types = [
                        {'type': 'bot', 'icon': '🤖', 'message': 'Bot detected - Automated behavior patterns'},
                        {'type': 'suspicious', 'icon': '⚠️', 'message': 'Suspicious activity - Rapid interactions'},
                        {'type': 'normal', 'icon': '✅', 'message': 'Human user verified - Natural patterns'}
                    ]
                    
                    event = random.choice(event_types)
                    socketio.emit('new_detection', event, namespace='/prototype')
                
                time.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logging.error(f"Error in update loop: {e}")
                time.sleep(30)
    
    # Start update thread
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()

# Export function to register blueprint and initialize websocket
def register_prototype(app, socketio):
    """Register prototype blueprint and initialize WebSocket events"""
    
    # Static script serving moved to main.py to avoid conflicts
    # @app.route('/static/passive-captcha-script.js') - REMOVED DUPLICATE
    
    app.register_blueprint(prototype_bp)
    init_websocket_events(socketio)
    send_periodic_updates(socketio)
    logging.info("Prototype API registered successfully")
    
    return prototype_bp