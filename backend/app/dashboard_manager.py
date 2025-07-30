"""
Isolated Dashboard System for Multi-Tenant Passive CAPTCHA Platform
Generates website-specific dashboards with real-time capabilities
"""

from datetime import datetime
from typing import Dict, Any, Optional
from flask import current_app
import json


class DashboardManager:
    """
    Creates isolated dashboards for specific websites with real-time features
    """
    
    def __init__(self):
        self.api_endpoint = current_app.config.get('API_BASE_URL', 'https://passive-captcha-api.railway.app')
        self.websocket_endpoint = current_app.config.get('WEBSOCKET_URL', 'wss://ws.passive-captcha.com')
    
    def create_website_dashboard(self, website_id: str, website_name: str) -> str:
        """
        Create isolated dashboard for specific website
        """
        dashboard_config = {
            'website_id': website_id,
            'website_name': website_name,
            'websocket_room': f"dashboard_{website_id}",
            'api_endpoints': {
                'analytics': f'/api/v1/websites/{website_id}/analytics',
                'logs': f'/api/v1/websites/{website_id}/logs',
                'status': f'/api/v1/websites/{website_id}/status',
                'script': f'/api/v1/websites/{website_id}/script'
            },
            'real_time_features': [
                'live_verification_count',
                'confidence_distribution',
                'geographic_analysis',
                'threat_detection_alerts',
                'performance_metrics'
            ]
        }
        
        return self.render_dashboard_template(dashboard_config)
    
    def render_dashboard_template(self, config: Dict[str, Any]) -> str:
        """
        Generate dashboard HTML with real-time capabilities
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['website_name']} - Passive CAPTCHA Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #2563eb;
            margin-bottom: 0.5rem;
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            color: #6b7280;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .status-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
        }}
        
        .status-active {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }}
        
        .stat-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }}
        
        .stat-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .stat-icon {{
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            color: white;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}
        
        .stat-change {{
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        
        .stat-change.positive {{
            color: #059669;
        }}
        
        .stat-change.negative {{
            color: #dc2626;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        
        .chart-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 1rem;
        }}
        
        .logs-section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        
        .logs-header {{
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .logs-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #1f2937;
        }}
        
        .refresh-btn {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: background 0.2s ease;
        }}
        
        .refresh-btn:hover {{
            background: #1d4ed8;
        }}
        
        .log-entry {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem;
            border-bottom: 1px solid #e5e7eb;
            transition: background 0.2s ease;
        }}
        
        .log-entry:hover {{
            background: #f9fafb;
        }}
        
        .log-entry:last-child {{
            border-bottom: none;
        }}
        
        .log-result {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .result-badge {{
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        .result-human {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .result-bot {{
            background: #fef2f2;
            color: #991b1b;
        }}
        
        .log-details {{
            font-size: 0.875rem;
            color: #6b7280;
        }}
        
        .connection-status {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            z-index: 1000;
        }}
        
        .connected {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .disconnected {{
            background: #fef2f2;
            color: #991b1b;
        }}
        
        .controls-panel {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        
        .controls-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .control-label {{
            font-size: 0.875rem;
            font-weight: 500;
            color: #374151;
        }}
        
        .control-input {{
            padding: 0.5rem;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 0.875rem;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-container {{
                padding: 1rem;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="connection-status disconnected" id="connectionStatus">
        <i class="fas fa-circle"></i> Connecting...
    </div>
    
    <div class="dashboard-container">
        <div class="header">
            <h1><i class="fas fa-shield-alt"></i> {config['website_name']}</h1>
            <div class="subtitle">
                <span>Passive CAPTCHA Security Dashboard</span>
                <span class="status-badge status-active">Active</span>
                <span id="websiteId">ID: {config['website_id']}</span>
            </div>
        </div>
        
        <div class="controls-panel">
            <div class="controls-grid">
                <div class="control-group">
                    <label class="control-label">Time Range</label>
                    <select class="control-input" id="timeRange">
                        <option value="1">Last Hour</option>
                        <option value="6">Last 6 Hours</option>
                        <option value="24" selected>Last 24 Hours</option>
                        <option value="72">Last 3 Days</option>
                        <option value="168">Last Week</option>
                    </select>
                </div>
                <div class="control-group">
                    <label class="control-label">Auto Refresh</label>
                    <select class="control-input" id="autoRefresh">
                        <option value="0">Disabled</option>
                        <option value="10000">10 seconds</option>
                        <option value="30000" selected>30 seconds</option>
                        <option value="60000">1 minute</option>
                    </select>
                </div>
                <div class="control-group">
                    <label class="control-label">Actions</label>
                    <button class="refresh-btn" onclick="refreshAllData()">
                        <i class="fas fa-sync-alt"></i> Refresh Now
                    </button>
                </div>
            </div>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Stats cards will be populated by JavaScript -->
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3 class="chart-title">Verification Trends</h3>
                <canvas id="verificationChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Detection Distribution</h3>
                <canvas id="distributionChart" width="200" height="200"></canvas>
            </div>
        </div>
        
        <div class="logs-section">
            <div class="logs-header">
                <h3 class="logs-title">Recent Verifications</h3>
                <button class="refresh-btn" onclick="loadLogs()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
            <div id="logsContainer">
                <!-- Logs will be populated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script>
        // Dashboard Configuration
        const DASHBOARD_CONFIG = {{
            website_id: '{config['website_id']}',
            website_name: '{config['website_name']}',
            api_endpoint: '{self.api_endpoint}',
            websocket_endpoint: '{self.websocket_endpoint}',
            endpoints: {json.dumps(config['api_endpoints'])}
        }};
        
        // Global variables
        let socket = null;
        let dashboardToken = localStorage.getItem('dashboard_token');
        let verificationChart = null;
        let distributionChart = null;
        let autoRefreshInterval = null;
        
        // Dashboard Manager Class
        class DashboardManager {{
            constructor() {{
                this.isConnected = false;
                this.lastUpdate = null;
                this.stats = {{}};
            }}
            
            async init() {{
                await this.setupWebSocket();
                await this.loadInitialData();
                this.setupEventListeners();
                this.startAutoRefresh();
            }}
            
            async setupWebSocket() {{
                try {{
                    socket = io(DASHBOARD_CONFIG.websocket_endpoint);
                    
                    socket.on('connect', () => {{
                        console.log('Connected to WebSocket');
                        this.isConnected = true;
                        this.updateConnectionStatus(true);
                        
                        // Join dashboard room
                        socket.emit('join_dashboard', {{
                            website_id: DASHBOARD_CONFIG.website_id,
                            token: dashboardToken
                        }});
                    }});
                    
                    socket.on('disconnect', () => {{
                        console.log('Disconnected from WebSocket');
                        this.isConnected = false;
                        this.updateConnectionStatus(false);
                    }});
                    
                    socket.on('new_verification', (data) => {{
                        this.handleNewVerification(data);
                    }});
                    
                    socket.on('live_stats_update', (stats) => {{
                        this.updateLiveStats(stats);
                    }});
                    
                }} catch (error) {{
                    console.error('WebSocket setup failed:', error);
                    this.updateConnectionStatus(false);
                }}
            }}
            
            updateConnectionStatus(connected) {{
                const statusEl = document.getElementById('connectionStatus');
                if (connected) {{
                    statusEl.className = 'connection-status connected';
                    statusEl.innerHTML = '<i class="fas fa-circle"></i> Connected';
                }} else {{
                    statusEl.className = 'connection-status disconnected';
                    statusEl.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
                }}
            }}
            
            async loadInitialData() {{
                await Promise.all([
                    this.loadStats(),
                    this.loadCharts(),
                    this.loadLogs()
                ]);
            }}
            
            async loadStats() {{
                try {{
                    const hours = document.getElementById('timeRange').value;
                    const response = await fetch(`${{DASHBOARD_CONFIG.api_endpoint}}${{DASHBOARD_CONFIG.endpoints.analytics}}?hours=${{hours}}`, {{
                        headers: {{
                            'Authorization': `Bearer ${{dashboardToken}}`,
                            'X-Website-Token': localStorage.getItem('api_key')
                        }}
                    }});
                    
                    if (!response.ok) throw new Error('Failed to load stats');
                    
                    const data = await response.json();
                    this.stats = data.analytics;
                    this.renderStats(this.stats);
                    
                }} catch (error) {{
                    console.error('Failed to load stats:', error);
                }}
            }}
            
            renderStats(stats) {{
                const statsGrid = document.getElementById('statsGrid');
                statsGrid.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-header">
                            <span class="stat-title">Total Verifications</span>
                            <div class="stat-icon" style="background: #3b82f6;">
                                <i class="fas fa-chart-line"></i>
                            </div>
                        </div>
                        <div class="stat-value">${{stats.total_verifications || 0}}</div>
                        <div class="stat-change positive">
                            <i class="fas fa-arrow-up"></i> Active monitoring
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-header">
                            <span class="stat-title">Human Detection Rate</span>
                            <div class="stat-icon" style="background: #10b981;">
                                <i class="fas fa-user-check"></i>
                            </div>
                        </div>
                        <div class="stat-value">${{Math.round(stats.human_percentage || 0)}}%</div>
                        <div class="stat-change positive">
                            <i class="fas fa-arrow-up"></i> ${{stats.human_detections || 0}} humans
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-header">
                            <span class="stat-title">Bot Detections</span>
                            <div class="stat-icon" style="background: #ef4444;">
                                <i class="fas fa-robot"></i>
                            </div>
                        </div>
                        <div class="stat-value">${{stats.bot_detections || 0}}</div>
                        <div class="stat-change negative">
                            <i class="fas fa-shield-alt"></i> Blocked threats
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-header">
                            <span class="stat-title">Average Confidence</span>
                            <div class="stat-icon" style="background: #8b5cf6;">
                                <i class="fas fa-bullseye"></i>
                            </div>
                        </div>
                        <div class="stat-value">${{Math.round((stats.average_confidence || 0) * 100)}}%</div>
                        <div class="stat-change positive">
                            <i class="fas fa-check"></i> High accuracy
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-header">
                            <span class="stat-title">Response Time</span>
                            <div class="stat-icon" style="background: #f59e0b;">
                                <i class="fas fa-tachometer-alt"></i>
                            </div>
                        </div>
                        <div class="stat-value">${{Math.round(stats.average_response_time_ms || 0)}}ms</div>
                        <div class="stat-change positive">
                            <i class="fas fa-bolt"></i> Fast processing
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-header">
                            <span class="stat-title">Unique Sessions</span>
                            <div class="stat-icon" style="background: #06b6d4;">
                                <i class="fas fa-users"></i>
                            </div>
                        </div>
                        <div class="stat-value">${{stats.unique_sessions || 0}}</div>
                        <div class="stat-change positive">
                            <i class="fas fa-globe"></i> Active users
                        </div>
                    </div>
                `;
            }}
            
            async loadCharts() {{
                // Initialize verification trends chart
                const ctx1 = document.getElementById('verificationChart').getContext('2d');
                verificationChart = new Chart(ctx1, {{
                    type: 'line',
                    data: {{
                        labels: ['6h ago', '5h ago', '4h ago', '3h ago', '2h ago', '1h ago', 'Now'],
                        datasets: [{{
                            label: 'Human Verifications',
                            data: [12, 19, 15, 25, 22, 18, 24],
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            tension: 0.4
                        }}, {{
                            label: 'Bot Detections',
                            data: [3, 5, 2, 8, 4, 3, 6],
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'top'
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
                
                // Initialize distribution chart
                const ctx2 = document.getElementById('distributionChart').getContext('2d');
                distributionChart = new Chart(ctx2, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Human', 'Bot', 'Uncertain'],
                        datasets: [{{
                            data: [this.stats.human_detections || 0, this.stats.bot_detections || 0, 2],
                            backgroundColor: ['#10b981', '#ef4444', '#f59e0b']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'bottom'
                            }}
                        }}
                    }}
                }});
            }}
            
            async loadLogs() {{
                try {{
                    const response = await fetch(`${{DASHBOARD_CONFIG.api_endpoint}}/api/v1/admin/logs?limit=20&website_id=${{DASHBOARD_CONFIG.website_id}}`, {{
                        headers: {{
                            'Authorization': `Bearer ${{dashboardToken}}`
                        }}
                    }});
                    
                    if (!response.ok) throw new Error('Failed to load logs');
                    
                    const data = await response.json();
                    this.renderLogs(data.logs || []);
                    
                }} catch (error) {{
                    console.error('Failed to load logs:', error);
                    document.getElementById('logsContainer').innerHTML = `
                        <div class="log-entry">
                            <div class="log-details" style="color: #ef4444;">
                                <i class="fas fa-exclamation-triangle"></i> 
                                Failed to load verification logs
                            </div>
                        </div>
                    `;
                }}
            }}
            
            renderLogs(logs) {{
                const logsContainer = document.getElementById('logsContainer');
                
                if (!logs || logs.length === 0) {{
                    logsContainer.innerHTML = `
                        <div class="log-entry">
                            <div class="log-details">
                                <i class="fas fa-info-circle"></i> 
                                No verification logs found for the selected time period
                            </div>
                        </div>
                    `;
                    return;
                }}
                
                logsContainer.innerHTML = logs.map(log => `
                    <div class="log-entry">
                        <div class="log-result">
                            <span class="result-badge ${{log.is_human ? 'result-human' : 'result-bot'}}">
                                ${{log.is_human ? 'Human' : 'Bot'}}
                            </span>
                            <span>${{Math.round((log.confidence || 0) * 100)}}% confidence</span>
                        </div>
                        <div class="log-details">
                            ${{log.origin || 'Unknown origin'}} • 
                            ${{new Date(log.timestamp).toLocaleString()}}
                        </div>
                    </div>
                `).join('');
            }}
            
            handleNewVerification(data) {{
                // Add real-time verification to the logs
                const logsContainer = document.getElementById('logsContainer');
                const newLogEntry = document.createElement('div');
                newLogEntry.className = 'log-entry';
                newLogEntry.style.background = '#f0f9ff';
                newLogEntry.innerHTML = `
                    <div class="log-result">
                        <span class="result-badge ${{data.isHuman ? 'result-human' : 'result-bot'}}">
                            ${{data.isHuman ? 'Human' : 'Bot'}}
                        </span>
                        <span>${{Math.round((data.confidence || 0) * 100)}}% confidence</span>
                    </div>
                    <div class="log-details">
                        ${{data.origin || 'Unknown origin'}} • 
                        ${{new Date().toLocaleString()}} • 
                        <strong>LIVE</strong>
                    </div>
                `;
                
                logsContainer.insertBefore(newLogEntry, logsContainer.firstChild);
                
                // Remove oldest entry if more than 20
                if (logsContainer.children.length > 20) {{
                    logsContainer.removeChild(logsContainer.lastChild);
                }}
                
                // Refresh stats
                setTimeout(() => this.loadStats(), 1000);
            }}
            
            setupEventListeners() {{
                // Time range change
                document.getElementById('timeRange').addEventListener('change', () => {{
                    this.loadStats();
                    this.loadCharts();
                }});
                
                // Auto refresh change
                document.getElementById('autoRefresh').addEventListener('change', (e) => {{
                    this.startAutoRefresh();
                }});
            }}
            
            startAutoRefresh() {{
                if (autoRefreshInterval) {{
                    clearInterval(autoRefreshInterval);
                }}
                
                const interval = parseInt(document.getElementById('autoRefresh').value);
                if (interval > 0) {{
                    autoRefreshInterval = setInterval(() => {{
                        this.loadStats();
                    }}, interval);
                }}
            }}
        }}
        
        // Global functions
        async function refreshAllData() {{
            const dashboard = new DashboardManager();
            await dashboard.loadInitialData();
        }}
        
        async function loadLogs() {{
            const dashboard = new DashboardManager();
            await dashboard.loadLogs();
        }}
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', async () => {{
            const dashboard = new DashboardManager();
            await dashboard.init();
        }});
    </script>
</body>
</html>"""

# Global instance
dashboard_manager = None

def init_dashboard_manager(app):
    """Initialize dashboard manager with Flask app"""
    global dashboard_manager
    
    with app.app_context():
        dashboard_manager = DashboardManager()
        
    print("✅ Dashboard manager initialized")