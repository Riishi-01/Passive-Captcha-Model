/**
 * Passive CAPTCHA Data Collection Script
 * Version: 2.0.0
 * 
 * This script collects passive behavioral data to detect bots
 * without user interaction. It monitors mouse movements, keyboard patterns,
 * scroll behavior, timing data, and device characteristics.
 */

(function() {
    'use strict';
    
    // Configuration
    const CONFIG = window.PASSIVE_CAPTCHA_CONFIG || {
        apiEndpoint: '{API_ENDPOINT}',
        scriptToken: '{SCRIPT_TOKEN}',
        websiteUrl: window.location.origin,
        collectMouseMovements: true,
        collectKeyboardPatterns: true,
        collectScrollBehavior: true,
        collectTimingData: true,
        collectDeviceInfo: true,
        samplingRate: 0.1, // 10% of interactions
        batchSize: 50,
        sendInterval: 30000, // 30 seconds
        debugMode: false
    };
    
    // Data collection state
    const state = {
        sessionId: generateSessionId(),
        isInitialized: false,
        dataQueue: [],
        lastSendTime: Date.now(),
        mouseData: {
            movements: [],
            clicks: [],
            lastPosition: { x: 0, y: 0 },
            velocity: [],
            acceleration: []
        },
        keyboardData: {
            keystrokes: [],
            timingPatterns: [],
            typingSpeed: []
        },
        scrollData: {
            scrollEvents: [],
            scrollVelocity: [],
            scrollPattern: []
        },
        timingData: {
            pageLoadTime: null,
            domReadyTime: null,
            firstInteractionTime: null,
            sessionDuration: 0
        },
        deviceInfo: null,
        behaviorMetrics: {
            mouseEntropy: 0,
            keyboardRhythm: 0,
            scrollConsistency: 0,
            humanLikelihood: 0
        }
    };
    
    // Initialize the passive CAPTCHA system
    function init() {
        if (state.isInitialized) return;
        
        try {
            log('Initializing Passive CAPTCHA...');
            
            // Collect device information
            if (CONFIG.collectDeviceInfo) {
                collectDeviceInfo();
            }
            
            // Set up event listeners
            setupEventListeners();
            
            // Start timing measurements
            if (CONFIG.collectTimingData) {
                setupTimingCollection();
            }
            
            // Start periodic data sending
            setupDataSending();
            
            // Activate the token with the server
            activateToken();
            
            state.isInitialized = true;
            log('Passive CAPTCHA initialized successfully');
            
        } catch (error) {
            console.error('Passive CAPTCHA initialization failed:', error);
        }
    }
    
    // Generate unique session ID
    function generateSessionId() {
        return 'pcs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Setup event listeners for data collection
    function setupEventListeners() {
        // Mouse movement tracking
        if (CONFIG.collectMouseMovements) {
            setupMouseTracking();
        }
        
        // Keyboard pattern tracking
        if (CONFIG.collectKeyboardPatterns) {
            setupKeyboardTracking();
        }
        
        // Scroll behavior tracking
        if (CONFIG.collectScrollBehavior) {
            setupScrollTracking();
        }
        
        // Page lifecycle events
        document.addEventListener('visibilitychange', handleVisibilityChange);
        window.addEventListener('beforeunload', handleBeforeUnload);
    }
    
    // Mouse tracking setup
    function setupMouseTracking() {
        let lastMouseTime = Date.now();
        let mouseMoveCount = 0;
        
        document.addEventListener('mousemove', function(event) {
            if (!shouldSample()) return;
            
            const now = Date.now();
            const deltaTime = now - lastMouseTime;
            const deltaX = event.clientX - state.mouseData.lastPosition.x;
            const deltaY = event.clientY - state.mouseData.lastPosition.y;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            const velocity = deltaTime > 0 ? distance / deltaTime : 0;
            
            // Calculate acceleration
            const lastVelocity = state.mouseData.velocity.length > 0 ? 
                state.mouseData.velocity[state.mouseData.velocity.length - 1] : 0;
            const acceleration = deltaTime > 0 ? (velocity - lastVelocity) / deltaTime : 0;
            
            // Store movement data
            state.mouseData.movements.push({
                x: event.clientX,
                y: event.clientY,
                timestamp: now,
                velocity: velocity,
                acceleration: acceleration,
                pressure: event.pressure || 0,
                deltaTime: deltaTime
            });
            
            state.mouseData.velocity.push(velocity);
            state.mouseData.acceleration.push(acceleration);
            state.mouseData.lastPosition = { x: event.clientX, y: event.clientY };
            
            // Limit data size
            if (state.mouseData.movements.length > 200) {
                state.mouseData.movements = state.mouseData.movements.slice(-100);
                state.mouseData.velocity = state.mouseData.velocity.slice(-100);
                state.mouseData.acceleration = state.mouseData.acceleration.slice(-100);
            }
            
            lastMouseTime = now;
            mouseMoveCount++;
            
            // Set first interaction time
            if (!state.timingData.firstInteractionTime) {
                state.timingData.firstInteractionTime = now - performance.timing.navigationStart;
            }
        });
        
        // Mouse click tracking
        document.addEventListener('click', function(event) {
            if (!shouldSample()) return;
            
            state.mouseData.clicks.push({
                x: event.clientX,
                y: event.clientY,
                timestamp: Date.now(),
                button: event.button,
                ctrlKey: event.ctrlKey,
                shiftKey: event.shiftKey,
                altKey: event.altKey
            });
            
            // Limit click data
            if (state.mouseData.clicks.length > 50) {
                state.mouseData.clicks = state.mouseData.clicks.slice(-25);
            }
        });
    }
    
    // Keyboard tracking setup
    function setupKeyboardTracking() {
        let lastKeyTime = Date.now();
        let keystrokeCount = 0;
        
        document.addEventListener('keydown', function(event) {
            if (!shouldSample()) return;
            
            const now = Date.now();
            const deltaTime = now - lastKeyTime;
            
            // Don't log actual key values for privacy
            state.keyboardData.keystrokes.push({
                timestamp: now,
                deltaTime: deltaTime,
                keyCode: event.keyCode,
                ctrlKey: event.ctrlKey,
                shiftKey: event.shiftKey,
                altKey: event.altKey,
                repeat: event.repeat
            });
            
            state.keyboardData.timingPatterns.push(deltaTime);
            
            // Calculate typing speed (words per minute approximation)
            if (keystrokeCount > 0 && deltaTime < 5000) { // Within 5 seconds
                const wpm = (60000 / deltaTime) * 0.2; // Approximate 5 chars = 1 word
                state.keyboardData.typingSpeed.push(wpm);
            }
            
            // Limit data size
            if (state.keyboardData.keystrokes.length > 100) {
                state.keyboardData.keystrokes = state.keyboardData.keystrokes.slice(-50);
                state.keyboardData.timingPatterns = state.keyboardData.timingPatterns.slice(-50);
                state.keyboardData.typingSpeed = state.keyboardData.typingSpeed.slice(-50);
            }
            
            lastKeyTime = now;
            keystrokeCount++;
            
            // Set first interaction time
            if (!state.timingData.firstInteractionTime) {
                state.timingData.firstInteractionTime = now - performance.timing.navigationStart;
            }
        });
    }
    
    // Scroll tracking setup
    function setupScrollTracking() {
        let lastScrollTime = Date.now();
        let lastScrollY = window.pageYOffset;
        
        window.addEventListener('scroll', function() {
            if (!shouldSample()) return;
            
            const now = Date.now();
            const deltaTime = now - lastScrollTime;
            const currentScrollY = window.pageYOffset;
            const deltaY = currentScrollY - lastScrollY;
            const velocity = deltaTime > 0 ? Math.abs(deltaY) / deltaTime : 0;
            
            state.scrollData.scrollEvents.push({
                scrollY: currentScrollY,
                deltaY: deltaY,
                timestamp: now,
                deltaTime: deltaTime,
                velocity: velocity
            });
            
            state.scrollData.scrollVelocity.push(velocity);
            
            // Detect scroll patterns
            if (state.scrollData.scrollEvents.length > 5) {
                const recentEvents = state.scrollData.scrollEvents.slice(-5);
                const avgVelocity = recentEvents.reduce((sum, event) => sum + event.velocity, 0) / 5;
                const velocityVariance = recentEvents.reduce((sum, event) => 
                    sum + Math.pow(event.velocity - avgVelocity, 2), 0) / 5;
                
                state.scrollData.scrollPattern.push({
                    avgVelocity: avgVelocity,
                    velocityVariance: velocityVariance,
                    timestamp: now
                });
            }
            
            // Limit data size
            if (state.scrollData.scrollEvents.length > 100) {
                state.scrollData.scrollEvents = state.scrollData.scrollEvents.slice(-50);
                state.scrollData.scrollVelocity = state.scrollData.scrollVelocity.slice(-50);
                state.scrollData.scrollPattern = state.scrollData.scrollPattern.slice(-25);
            }
            
            lastScrollTime = now;
            lastScrollY = currentScrollY;
        });
    }
    
    // Collect device and browser information
    function collectDeviceInfo() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 2, 2);
        
        state.deviceInfo = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            screenResolution: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth
            },
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset(),
            touchSupport: 'ontouchstart' in window,
            deviceMemory: navigator.deviceMemory,
            hardwareConcurrency: navigator.hardwareConcurrency,
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            } : null,
            canvasFingerprint: canvas.toDataURL(),
            webglInfo: getWebGLInfo(),
            fonts: getAvailableFonts(),
            plugins: Array.from(navigator.plugins).map(p => ({
                name: p.name,
                filename: p.filename
            }))
        };
    }
    
    // Get WebGL information
    function getWebGLInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return null;
            
            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER),
                version: gl.getParameter(gl.VERSION),
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION)
            };
        } catch (e) {
            return null;
        }
    }
    
    // Detect available fonts
    function getAvailableFonts() {
        const testFonts = [
            'Arial', 'Helvetica', 'Times New Roman', 'Georgia', 'Verdana',
            'Courier New', 'Comic Sans MS', 'Impact', 'Trebuchet MS'
        ];
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const baseFontSize = '50px';
        const testString = 'wwwwwwwwwwwwwwwwwwwwwwwww';
        
        ctx.font = baseFontSize + ' monospace';
        const baseWidth = ctx.measureText(testString).width;
        
        return testFonts.filter(font => {
            ctx.font = baseFontSize + ' ' + font + ', monospace';
            return ctx.measureText(testString).width !== baseWidth;
        });
    }
    
    // Setup timing data collection
    function setupTimingCollection() {
        // Page load timing
        window.addEventListener('load', function() {
            const timing = performance.timing;
            state.timingData.pageLoadTime = timing.loadEventEnd - timing.navigationStart;
            state.timingData.domReadyTime = timing.domContentLoadedEventEnd - timing.navigationStart;
        });
        
        // Update session duration periodically
        setInterval(function() {
            state.timingData.sessionDuration = Date.now() - performance.timing.navigationStart;
        }, 5000);
    }
    
    // Calculate behavioral metrics
    function calculateBehaviorMetrics() {
        // Mouse entropy calculation
        if (state.mouseData.movements.length > 10) {
            const movements = state.mouseData.movements;
            const velocities = movements.map(m => m.velocity);
            const accelerations = movements.map(m => m.acceleration);
            
            state.behaviorMetrics.mouseEntropy = calculateEntropy(velocities) + calculateEntropy(accelerations);
        }
        
        // Keyboard rhythm analysis
        if (state.keyboardData.timingPatterns.length > 5) {
            const patterns = state.keyboardData.timingPatterns;
            const variance = calculateVariance(patterns);
            state.behaviorMetrics.keyboardRhythm = Math.min(variance / 1000, 1); // Normalize
        }
        
        // Scroll consistency
        if (state.scrollData.scrollVelocity.length > 5) {
            const velocities = state.scrollData.scrollVelocity;
            const consistency = 1 - (calculateVariance(velocities) / Math.max(...velocities));
            state.behaviorMetrics.scrollConsistency = Math.max(0, consistency);
        }
        
        // Human likelihood score (composite)
        const mouseScore = Math.min(state.behaviorMetrics.mouseEntropy / 10, 1);
        const keyboardScore = Math.min(state.behaviorMetrics.keyboardRhythm, 1);
        const scrollScore = state.behaviorMetrics.scrollConsistency;
        
        state.behaviorMetrics.humanLikelihood = (mouseScore + keyboardScore + scrollScore) / 3;
    }
    
    // Calculate entropy of a data series
    function calculateEntropy(data) {
        if (data.length === 0) return 0;
        
        const frequency = {};
        data.forEach(value => {
            const bucket = Math.floor(value * 10) / 10; // Round to 1 decimal
            frequency[bucket] = (frequency[bucket] || 0) + 1;
        });
        
        const total = data.length;
        let entropy = 0;
        
        Object.values(frequency).forEach(count => {
            const probability = count / total;
            entropy -= probability * Math.log2(probability);
        });
        
        return entropy;
    }
    
    // Calculate variance
    function calculateVariance(data) {
        if (data.length === 0) return 0;
        
        const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
        const variance = data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length;
        
        return variance;
    }
    
    // Determine if this interaction should be sampled
    function shouldSample() {
        return Math.random() < CONFIG.samplingRate;
    }
    
    // Setup periodic data sending
    function setupDataSending() {
        setInterval(function() {
            if (Date.now() - state.lastSendTime >= CONFIG.sendInterval) {
                sendCollectedData();
            }
        }, CONFIG.sendInterval);
        
        // Send data when page is about to unload
        window.addEventListener('beforeunload', sendCollectedData);
    }
    
    // Activate token with server
    function activateToken() {
        fetch(CONFIG.apiEndpoint + '/api/script/activate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Script-Token': CONFIG.scriptToken
            },
            body: JSON.stringify({
                website_url: CONFIG.websiteUrl,
                session_id: state.sessionId,
                user_agent: navigator.userAgent,
                timestamp: Date.now()
            })
        }).then(response => {
            if (response.ok) {
                log('Token activated successfully');
            } else {
                console.error('Failed to activate token');
            }
        }).catch(error => {
            console.error('Token activation error:', error);
        });
    }
    
    // Send collected data to server
    function sendCollectedData() {
        if (!state.isInitialized) return;
        
        // Calculate current behavioral metrics
        calculateBehaviorMetrics();
        
        const payload = {
            session_id: state.sessionId,
            website_url: CONFIG.websiteUrl,
            timestamp: Date.now(),
            data: {
                mouse: {
                    movementCount: state.mouseData.movements.length,
                    clickCount: state.mouseData.clicks.length,
                    avgVelocity: state.mouseData.velocity.length > 0 ? 
                        state.mouseData.velocity.reduce((a, b) => a + b, 0) / state.mouseData.velocity.length : 0,
                    avgAcceleration: state.mouseData.acceleration.length > 0 ?
                        state.mouseData.acceleration.reduce((a, b) => a + b, 0) / state.mouseData.acceleration.length : 0,
                    entropy: state.behaviorMetrics.mouseEntropy
                },
                keyboard: {
                    keystrokeCount: state.keyboardData.keystrokes.length,
                    avgTypingSpeed: state.keyboardData.typingSpeed.length > 0 ?
                        state.keyboardData.typingSpeed.reduce((a, b) => a + b, 0) / state.keyboardData.typingSpeed.length : 0,
                    rhythm: state.behaviorMetrics.keyboardRhythm
                },
                scroll: {
                    scrollEventCount: state.scrollData.scrollEvents.length,
                    avgVelocity: state.scrollData.scrollVelocity.length > 0 ?
                        state.scrollData.scrollVelocity.reduce((a, b) => a + b, 0) / state.scrollData.scrollVelocity.length : 0,
                    consistency: state.behaviorMetrics.scrollConsistency
                },
                timing: state.timingData,
                device: state.deviceInfo,
                behavioral_metrics: state.behaviorMetrics
            }
        };
        
        // Send data
        fetch(CONFIG.apiEndpoint + '/api/script/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Script-Token': CONFIG.scriptToken
            },
            body: JSON.stringify(payload)
        }).then(response => {
            if (response.ok) {
                log('Data sent successfully');
                state.lastSendTime = Date.now();
                
                // Clear some data to prevent memory buildup
                clearOldData();
            } else {
                console.error('Failed to send data');
            }
        }).catch(error => {
            console.error('Data sending error:', error);
        });
    }
    
    // Clear old data to prevent memory issues
    function clearOldData() {
        // Keep only recent data
        const maxAge = 300000; // 5 minutes
        const cutoff = Date.now() - maxAge;
        
        state.mouseData.movements = state.mouseData.movements.filter(m => m.timestamp > cutoff);
        state.keyboardData.keystrokes = state.keyboardData.keystrokes.filter(k => k.timestamp > cutoff);
        state.scrollData.scrollEvents = state.scrollData.scrollEvents.filter(s => s.timestamp > cutoff);
    }
    
    // Handle visibility change
    function handleVisibilityChange() {
        if (document.hidden) {
            sendCollectedData();
        }
    }
    
    // Handle before unload
    function handleBeforeUnload() {
        sendCollectedData();
    }
    
    // Logging function
    function log(message) {
        if (CONFIG.debugMode) {
            console.log('[Passive CAPTCHA]', message);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose minimal API for external access
    window.PassiveCAPTCHA = {
        getSessionId: function() { return state.sessionId; },
        getMetrics: function() { return state.behaviorMetrics; },
        sendData: sendCollectedData,
        isInitialized: function() { return state.isInitialized; }
    };
    
})();