"""
Dynamic Script Tag Generation for Multi-Tenant Passive CAPTCHA Platform
Generates token-embedded JavaScript for website integration
"""

import json
from typing import Dict, Any, Optional
from flask import current_app, url_for


class ScriptGenerator:
    """
    Generates token-embedded script tags with website isolation
    """
    
    def __init__(self):
        self.api_endpoint = current_app.config.get('API_BASE_URL', 'https://passive-captcha-api.railway.app')
        self.dashboard_base_url = current_app.config.get('DASHBOARD_BASE_URL', 'https://dashboard.passive-captcha.com')
    
    def generate_embedded_script(self, website_id: str, website_token: str, 
                               website_name: str = None, options: Dict[str, Any] = None) -> str:
        """
        Generate token-embedded script tag with website isolation
        """
        options = options or {}
        
        script_template = f"""
(function(window) {{
    'use strict';
    
    // Embedded website configuration - DO NOT MODIFY
    const WEBSITE_CONFIG = {{
        website_id: '{website_id}',
        api_token: '{website_token}',
        api_endpoint: '{self.api_endpoint}',
        dashboard_url: '{self.dashboard_base_url}/{website_id}',
        website_name: '{website_name or "Unknown"}',
        version: '1.0.0'
    }};
    
    // Passive CAPTCHA Client Implementation
    class PassiveCaptchaClient {{
        constructor() {{
            this.config = WEBSITE_CONFIG;
            this.sessionId = this.generateSessionId();
            this.startTime = Date.now();
            this.behaviorData = {{
                website_id: this.config.website_id,
                session_id: this.sessionId,
                origin: window.location.origin,
                mouseMovements: [],
                keystrokes: [],
                scrollEvents: [],
                fingerprint: null,
                sessionStartTime: this.startTime
            }};
            
            this.isTracking = false;
            this.verificationInProgress = false;
            this.verificationCache = new Map();
            
            // Initialize fingerprinting
            this.collectFingerprint();
        }}
        
        generateSessionId() {{
            return 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        }}
        
        collectFingerprint() {{
            const fingerprint = {{
                userAgent: navigator.userAgent,
                language: navigator.language,
                platform: navigator.platform,
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack,
                hardwareConcurrency: navigator.hardwareConcurrency || 0,
                deviceMemory: navigator.deviceMemory || 0,
                maxTouchPoints: navigator.maxTouchPoints || 0,
                
                // Screen information
                screenWidth: screen.width,
                screenHeight: screen.height,
                screenColorDepth: screen.colorDepth,
                screenPixelDepth: screen.pixelDepth,
                
                // Window information
                windowWidth: window.innerWidth,
                windowHeight: window.innerHeight,
                
                // Timezone
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                timezoneOffset: new Date().getTimezoneOffset(),
                
                // WebGL support
                webglSupport: this.checkWebGLSupport(),
                
                // Canvas fingerprint
                canvasFingerprint: this.generateCanvasFingerprint(),
                
                // Plugin information
                plugins: Array.from(navigator.plugins).map(p => p.name)
            }};
            
            this.behaviorData.fingerprint = fingerprint;
            return fingerprint;
        }}
        
        checkWebGLSupport() {{
            try {{
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                return !!gl;
            }} catch (e) {{
                return false;
            }}
        }}
        
        generateCanvasFingerprint() {{
            try {{
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Draw something unique
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillText('PassiveCAPTCHA fingerprint: ' + Date.now(), 2, 2);
                
                // Draw some shapes
                ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                ctx.fillRect(100, 5, 80, 20);
                
                return canvas.toDataURL();
            }} catch (e) {{
                return null;
            }}
        }}
        
        startBehavioralTracking() {{
            if (this.isTracking) return;
            
            this.isTracking = true;
            
            // Mouse movement tracking
            document.addEventListener('mousemove', (e) => {{
                this.behaviorData.mouseMovements.push({{
                    x: e.clientX,
                    y: e.clientY,
                    timestamp: Date.now()
                }});
                
                // Keep only last 100 movements
                if (this.behaviorData.mouseMovements.length > 100) {{
                    this.behaviorData.mouseMovements.shift();
                }}
            }});
            
            // Keystroke tracking
            document.addEventListener('keydown', (e) => {{
                this.behaviorData.keystrokes.push({{
                    key: e.key === ' ' ? 'Space' : e.key.length === 1 ? e.key : 'Special',
                    keyCode: e.keyCode,
                    timestamp: Date.now(),
                    ctrlKey: e.ctrlKey,
                    shiftKey: e.shiftKey,
                    altKey: e.altKey
                }});
                
                // Keep only last 50 keystrokes
                if (this.behaviorData.keystrokes.length > 50) {{
                    this.behaviorData.keystrokes.shift();
                }}
            }});
            
            // Scroll tracking
            window.addEventListener('scroll', (e) => {{
                this.behaviorData.scrollEvents.push({{
                    scrollY: window.scrollY,
                    scrollX: window.scrollX,
                    timestamp: Date.now()
                }});
                
                // Keep only last 20 scroll events
                if (this.behaviorData.scrollEvents.length > 20) {{
                    this.behaviorData.scrollEvents.shift();
                }}
            }});
        }}
        
        extractFeatures() {{
            const now = Date.now();
            const sessionDuration = now - this.startTime;
            
            // Mouse movement analysis
            const movements = this.behaviorData.mouseMovements;
            let totalDistance = 0;
            let velocities = [];
            
            for (let i = 1; i < movements.length; i++) {{
                const prev = movements[i - 1];
                const curr = movements[i];
                
                const dx = curr.x - prev.x;
                const dy = curr.y - prev.y;
                const dt = curr.timestamp - prev.timestamp;
                
                if (dt > 0) {{
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    totalDistance += distance;
                    velocities.push(distance / dt);
                }}
            }}
            
            const avgVelocity = velocities.length > 0 ? velocities.reduce((a, b) => a + b) / velocities.length : 0;
            
            // Keystroke analysis
            const keystrokes = this.behaviorData.keystrokes;
            const intervals = [];
            
            for (let i = 1; i < keystrokes.length; i++) {{
                intervals.push(keystrokes[i].timestamp - keystrokes[i - 1].timestamp);
            }}
            
            const avgKeystrokeInterval = intervals.length > 0 ? intervals.reduce((a, b) => a + b) / intervals.length : 0;
            const keystrokeVariance = this.calculateVariance(intervals);
            
            // Device and behavior scores
            const fingerprint = this.behaviorData.fingerprint;
            
            return {{
                mouse_movement_count: movements.length,
                avg_mouse_velocity: avgVelocity,
                mouse_acceleration_variance: this.calculateVariance(velocities),
                keystroke_count: keystrokes.length,
                avg_keystroke_interval: avgKeystrokeInterval,
                typing_rhythm_consistency: 1.0 / (1.0 + keystrokeVariance),
                session_duration: sessionDuration,
                scroll_pattern_score: Math.min(this.behaviorData.scrollEvents.length / 10, 1.0),
                webgl_support_score: fingerprint.webglSupport ? 1.0 : 0.0,
                canvas_fingerprint_score: fingerprint.canvasFingerprint ? 0.85 : 0.0,
                hardware_legitimacy: this.calculateHardwareLegitimacy(fingerprint),
                browser_consistency: this.calculateBrowserConsistency(fingerprint),
                plugin_availability: Math.min(fingerprint.plugins.length / 10, 1.0)
            }};
        }}
        
        calculateVariance(values) {{
            if (values.length === 0) return 0;
            
            const mean = values.reduce((a, b) => a + b) / values.length;
            const squaredDiffs = values.map(value => Math.pow(value - mean, 2));
            return squaredDiffs.reduce((a, b) => a + b) / values.length;
        }}
        
        calculateHardwareLegitimacy(fingerprint) {{
            let score = 0.5; // Base score
            
            if (fingerprint.hardwareConcurrency > 0) score += 0.2;
            if (fingerprint.deviceMemory > 0) score += 0.1;
            if (fingerprint.maxTouchPoints >= 0) score += 0.1;
            if (fingerprint.screenWidth > 800 && fingerprint.screenHeight > 600) score += 0.1;
            
            return Math.min(score, 1.0);
        }}
        
        calculateBrowserConsistency(fingerprint) {{
            let score = 0.5; // Base score
            
            // Check for common browser patterns
            const ua = fingerprint.userAgent.toLowerCase();
            if (ua.includes('chrome') || ua.includes('firefox') || ua.includes('safari')) {{
                score += 0.3;
            }}
            
            if (fingerprint.cookieEnabled) score += 0.1;
            if (fingerprint.language && fingerprint.language.length >= 2) score += 0.1;
            
            return Math.min(score, 1.0);
        }}
        
        async verify() {{
            if (this.verificationInProgress) {{
                return {{ error: 'Verification already in progress' }};
            }}
            
            // Check cache first
            const cacheKey = this.sessionId;
            if (this.verificationCache.has(cacheKey)) {{
                const cached = this.verificationCache.get(cacheKey);
                if (Date.now() - cached.timestamp < 60000) {{ // 1 minute cache
                    return cached.result;
                }}
            }}
            
            this.verificationInProgress = true;
            
            try {{
                const features = this.extractFeatures();
                
                const requestData = {{
                    sessionId: this.sessionId,
                    origin: window.location.origin,
                    features: features,
                    behaviorData: {{
                        mouseMovements: this.behaviorData.mouseMovements.slice(-20), // Send last 20
                        keystrokes: this.behaviorData.keystrokes.slice(-10), // Send last 10
                        fingerprint: this.behaviorData.fingerprint
                    }}
                }};
                
                const response = await fetch(`${{this.config.api_endpoint}}/api/v1/verify`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-Website-Token': this.config.api_token,
                        'X-Session-Id': this.sessionId,
                        'Origin': window.location.origin
                    }},
                    body: JSON.stringify(requestData)
                }});
                
                if (!response.ok) {{
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
                
                const result = await response.json();
                
                // Cache result
                this.verificationCache.set(cacheKey, {{
                    result: result,
                    timestamp: Date.now()
                }});
                
                return result;
                
            }} catch (error) {{
                console.error('PassiveCAPTCHA verification failed:', error);
                return {{
                    error: true,
                    message: 'Verification service unavailable',
                    isHuman: false,
                    confidence: 0.0
                }};
            }} finally {{
                this.verificationInProgress = false;
            }}
        }}
        
        init(options = {{}}) {{
            // Start behavioral tracking
            this.startBehavioralTracking();
            
            // Auto-verify option
            if (options.autoVerify) {{
                setTimeout(() => {{
                    this.verify().then(result => {{
                        if (options.onVerified && typeof options.onVerified === 'function') {{
                            options.onVerified(result);
                        }}
                    }});
                }}, options.autoVerifyDelay || 2000);
            }}
            
            // Bind to form elements
            if (options.element) {{
                this.bindToElement(options.element, options);
            }}
        }}
        
        bindToElement(selector, options = {{}}) {{
            const elements = typeof selector === 'string' ? 
                document.querySelectorAll(selector) : [selector];
            
            elements.forEach(element => {{
                if (!element) return;
                
                element.addEventListener('click', async (e) => {{
                    if (options.preventDefault !== false) {{
                        e.preventDefault();
                    }}
                    
                    const result = await this.verify();
                    
                    if (options.onVerified && typeof options.onVerified === 'function') {{
                        options.onVerified(result, element, e);
                    }} else {{
                        // Default behavior
                        if (result.isHuman && result.confidence > 0.7) {{
                            // Allow action to proceed
                            if (element.tagName === 'FORM') {{
                                element.submit();
                            }} else if (element.href) {{
                                window.location.href = element.href;
                            }}
                        }} else {{
                            alert('Security verification failed. Please try again or complete additional verification.');
                        }}
                    }}
                }});
            }});
        }}
        
        getDashboardUrl() {{
            return this.config.dashboard_url;
        }}
        
        getAnalytics() {{
            return {{
                sessionId: this.sessionId,
                sessionDuration: Date.now() - this.startTime,
                mouseMovements: this.behaviorData.mouseMovements.length,
                keystrokes: this.behaviorData.keystrokes.length,
                scrollEvents: this.behaviorData.scrollEvents.length
            }};
        }}
    }}
    
    // Global API
    window.PassiveCaptcha = {{
        init: (options = {{}}) => {{
            const client = new PassiveCaptchaClient();
            client.init(options);
            return client;
        }},
        
        verify: () => {{
            const client = new PassiveCaptchaClient();
            client.startBehavioralTracking();
            
            // Give some time for behavior collection
            return new Promise((resolve) => {{
                setTimeout(async () => {{
                    const result = await client.verify();
                    resolve(result);
                }}, 500);
            }});
        }},
        
        getDashboardUrl: () => WEBSITE_CONFIG.dashboard_url,
        
        getConfig: () => ({{
            website_id: WEBSITE_CONFIG.website_id,
            website_name: WEBSITE_CONFIG.website_name,
            version: WEBSITE_CONFIG.version
        }})
    }};
    
    // Auto-initialize if configured
    if (window.PassiveCaptchaConfig && window.PassiveCaptchaConfig.autoInit) {{
        window.PassiveCaptcha.init(window.PassiveCaptchaConfig);
    }}
    
}})(window);
"""
        
        return script_template.strip()
    
    def generate_html_script_tag(self, website_id: str, website_token: str, 
                                website_name: str = None, options: Dict[str, Any] = None) -> str:
        """
        Generate complete HTML script tag for easy integration
        """
        script_content = self.generate_embedded_script(website_id, website_token, website_name, options)
        
        return f"""<script type="text/javascript">
{script_content}
</script>"""
    
    def generate_integration_example(self, website_id: str, website_token: str, 
                                   website_name: str = None) -> str:
        """
        Generate complete integration example with usage instructions
        """
        script_tag = self.generate_html_script_tag(website_id, website_token, website_name)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{website_name or 'Website'} - Passive CAPTCHA Integration</title>
</head>
<body>
    <h1>Passive CAPTCHA Integration Example</h1>
    
    <!-- Your website content -->
    <form id="protected-form">
        <input type="email" placeholder="Email" required>
        <input type="password" placeholder="Password" required>
        <button type="submit" id="submit-btn">Submit</button>
    </form>
    
    <!-- Passive CAPTCHA Script - Place before closing </body> tag -->
{script_tag}
    
    <script>
        // Initialize Passive CAPTCHA
        const captcha = PassiveCaptcha.init({{
            element: '#submit-btn',
            onVerified: (result, element, event) => {{
                if (result.isHuman && result.confidence > 0.7) {{
                    console.log('✅ Human verified with confidence:', result.confidence);
                    // Allow form submission
                    document.getElementById('protected-form').submit();
                }} else {{
                    console.log('❌ Verification failed:', result);
                    alert('Security verification failed. Please try again.');
                }}
            }}
        }});
        
        // Access dashboard
        console.log('Dashboard URL:', PassiveCaptcha.getDashboardUrl());
    </script>
</body>
</html>"""
    
    def generate_npm_package_info(self, website_id: str, website_token: str) -> Dict[str, Any]:
        """
        Generate information for NPM package integration
        """
        return {
            "name": f"@passive-captcha/client-{website_id}",
            "version": "1.0.0",
            "description": f"Passive CAPTCHA client for website {website_id}",
            "main": "index.js",
            "config": {
                "website_id": website_id,
                "api_token": website_token,
                "api_endpoint": self.api_endpoint,
                "dashboard_url": f"{self.dashboard_base_url}/{website_id}"
            },
            "usage": {
                "import": "import PassiveCaptcha from '@passive-captcha/client';",
                "initialize": "const captcha = PassiveCaptcha.init({ element: '#submit-btn' });",
                "verify": "const result = await PassiveCaptcha.verify();"
            },
            "installation": f"npm install @passive-captcha/client-{website_id}"
        }

# Global instance
script_generator = None

def init_script_generator(app):
    """Initialize script generator with Flask app"""
    global script_generator
    
    with app.app_context():
        script_generator = ScriptGenerator()
        
    print("✅ Script generator initialized")