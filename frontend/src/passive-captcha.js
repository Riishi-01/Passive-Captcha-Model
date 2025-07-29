/**
 * Passive CAPTCHA JavaScript Widget
 * Collects behavioral biometrics and device fingerprinting for human vs bot detection
 * Version: 1.0
 */

(function(window, document) {
    'use strict';

    // Configuration
    const CONFIG = {
        API_URL: 'https://passive-captcha-api.railway.app',
        COLLECTION_DURATION: 15000, // 15 seconds
        MIN_EVENTS_THRESHOLD: 5,
        CONFIDENCE_THRESHOLD: 0.7
    };

    // Data collection storage
    let sessionData = {
        sessionId: generateSessionId(),
        mouseMovements: [],
        keystrokes: [],
        scrollEvents: [],
        sessionStart: Date.now(),
        fingerprint: {}
    };

    let isInitialized = false;
    let isCollecting = false;
    let collectionTimer = null;
    let callbacks = {};

    /**
     * Main PassiveCaptcha object
     */
    const PassiveCaptcha = {
        init: init,
        verify: verify,
        getSessionData: getSessionData,
        reset: reset,
        setConfig: setConfig
    };

    /**
     * Initialize the passive CAPTCHA system
     * @param {Object} options - Configuration options
     */
    function init(options = {}) {
        if (isInitialized) {
            console.warn('PassiveCaptcha already initialized');
            return;
        }

        // Merge options with default config
        Object.assign(CONFIG, options);

        // Set up callbacks
        callbacks = {
            onVerified: options.onVerified || function() {},
            onError: options.onError || function() {},
            onDataCollected: options.onDataCollected || function() {}
        };

        // Start data collection
        startDataCollection();

        // Set up automatic verification
        if (options.element) {
            setupElementVerification(options.element);
        }

        // Collect device fingerprint
        collectDeviceFingerprint();

        isInitialized = true;
        console.log('PassiveCaptcha initialized');
    }

    /**
     * Start collecting behavioral data
     */
    function startDataCollection() {
        if (isCollecting) return;

        isCollecting = true;
        sessionData.sessionStart = Date.now();

        // Mouse movement tracking
        document.addEventListener('mousemove', onMouseMove, { passive: true });

        // Keystroke tracking
        document.addEventListener('keydown', onKeyDown, { passive: true });
        document.addEventListener('keyup', onKeyUp, { passive: true });

        // Scroll tracking
        document.addEventListener('scroll', onScroll, { passive: true });

        // Touch events for mobile
        document.addEventListener('touchstart', onTouchStart, { passive: true });
        document.addEventListener('touchmove', onTouchMove, { passive: true });

        console.log('Data collection started');
    }

    /**
     * Set up verification for a specific element
     * @param {string|Element} element - Element selector or DOM element
     */
    function setupElementVerification(element) {
        const targetElement = typeof element === 'string' 
            ? document.querySelector(element) 
            : element;

        if (!targetElement) {
            console.error('PassiveCaptcha: Target element not found');
            return;
        }

        targetElement.addEventListener('click', function(event) {
            event.preventDefault();
            verify().then(result => {
                if (result.isHuman && result.confidence >= CONFIG.CONFIDENCE_THRESHOLD) {
                    // Allow the action
                    const newEvent = new Event('click', { bubbles: true });
                    targetElement.removeEventListener('click', arguments.callee);
                    targetElement.dispatchEvent(newEvent);
                    targetElement.addEventListener('click', arguments.callee);
                } else {
                    callbacks.onError(result);
                }
            });
        });
    }

    /**
     * Mouse movement event handler
     * @param {MouseEvent} event 
     */
    function onMouseMove(event) {
        sessionData.mouseMovements.push({
            x: event.clientX,
            y: event.clientY,
            timestamp: Date.now()
        });

        // Limit array size to prevent memory issues
        if (sessionData.mouseMovements.length > 1000) {
            sessionData.mouseMovements = sessionData.mouseMovements.slice(-500);
        }
    }

    /**
     * Keystroke event handler
     * @param {KeyboardEvent} event 
     */
    function onKeyDown(event) {
        sessionData.keystrokes.push({
            timestamp: Date.now(),
            keyType: 'down',
            keyCode: event.keyCode,
            key: event.key.length === 1 ? 'char' : 'special'
        });
    }

    function onKeyUp(event) {
        sessionData.keystrokes.push({
            timestamp: Date.now(),
            keyType: 'up',
            keyCode: event.keyCode,
            key: event.key.length === 1 ? 'char' : 'special'
        });

        // Limit array size
        if (sessionData.keystrokes.length > 500) {
            sessionData.keystrokes = sessionData.keystrokes.slice(-250);
        }
    }

    /**
     * Scroll event handler
     * @param {Event} event 
     */
    function onScroll(event) {
        sessionData.scrollEvents.push({
            y: window.pageYOffset,
            timestamp: Date.now()
        });

        // Limit array size
        if (sessionData.scrollEvents.length > 200) {
            sessionData.scrollEvents = sessionData.scrollEvents.slice(-100);
        }
    }

    /**
     * Touch event handlers for mobile devices
     */
    function onTouchStart(event) {
        if (event.touches.length > 0) {
            const touch = event.touches[0];
            sessionData.mouseMovements.push({
                x: touch.clientX,
                y: touch.clientY,
                timestamp: Date.now(),
                type: 'touch'
            });
        }
    }

    function onTouchMove(event) {
        if (event.touches.length > 0) {
            const touch = event.touches[0];
            sessionData.mouseMovements.push({
                x: touch.clientX,
                y: touch.clientY,
                timestamp: Date.now(),
                type: 'touch'
            });
        }
    }

    /**
     * Collect device fingerprint data
     */
    function collectDeviceFingerprint() {
        const fingerprint = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screenWidth: screen.width,
            screenHeight: screen.height,
            screenDepth: screen.colorDepth,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            hardwareConcurrency: navigator.hardwareConcurrency || 0,
            deviceMemory: navigator.deviceMemory || 0,
            webglVendor: getWebGLVendor(),
            canvasFingerprint: getCanvasFingerprint(),
            audioFingerprint: getAudioFingerprint(),
            plugins: getPluginsInfo()
        };

        sessionData.fingerprint = fingerprint;
    }

    /**
     * Get WebGL vendor information
     */
    function getWebGLVendor() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) return '';
            
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            return debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : '';
        } catch (e) {
            return '';
        }
    }

    /**
     * Generate canvas fingerprint
     */
    function getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = 200;
            canvas.height = 50;
            
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillText('PassiveCaptcha fingerprint test 🤖', 2, 2);
            
            ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
            ctx.fillRect(50, 20, 50, 20);
            
            return canvas.toDataURL();
        } catch (e) {
            return '';
        }
    }

    /**
     * Generate audio fingerprint
     */
    function getAudioFingerprint() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const analyser = audioContext.createAnalyser();
            const gainNode = audioContext.createGain();
            
            oscillator.type = 'triangle';
            oscillator.frequency.value = 10000;
            
            gainNode.gain.value = 0;
            
            oscillator.connect(analyser);
            analyser.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.start(0);
            
            const frequencyData = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(frequencyData);
            
            oscillator.stop();
            audioContext.close();
            
            return Array.from(frequencyData.slice(0, 10)).join(',');
        } catch (e) {
            return '';
        }
    }

    /**
     * Get plugins information
     */
    function getPluginsInfo() {
        try {
            const plugins = [];
            for (let i = 0; i < navigator.plugins.length; i++) {
                plugins.push(navigator.plugins[i].name);
            }
            return plugins.slice(0, 10); // Limit to first 10 plugins
        } catch (e) {
            return [];
        }
    }

    /**
     * Verify if the user is human
     * @returns {Promise} Verification result
     */
    async function verify() {
        try {
            // Prepare verification data
            const verificationData = {
                sessionId: sessionData.sessionId,
                mouseMovements: sessionData.mouseMovements,
                keystrokes: sessionData.keystrokes,
                scrollEvents: sessionData.scrollEvents,
                fingerprint: sessionData.fingerprint,
                sessionDuration: Date.now() - sessionData.sessionStart,
                origin: window.location.origin
            };

            // Send to API
            const response = await fetch(`${CONFIG.API_URL}/api/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(verificationData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            // Call callback
            callbacks.onVerified(result);
            
            return result;

        } catch (error) {
            console.error('PassiveCaptcha verification failed:', error);
            const errorResult = {
                isHuman: true, // Fail open for user experience
                confidence: 0.5,
                error: error.message
            };
            
            callbacks.onError(errorResult);
            return errorResult;
        }
    }

    /**
     * Get current session data (for debugging)
     */
    function getSessionData() {
        return {
            ...sessionData,
            sessionDuration: Date.now() - sessionData.sessionStart
        };
    }

    /**
     * Reset session data
     */
    function reset() {
        sessionData = {
            sessionId: generateSessionId(),
            mouseMovements: [],
            keystrokes: [],
            scrollEvents: [],
            sessionStart: Date.now(),
            fingerprint: {}
        };
        
        collectDeviceFingerprint();
    }

    /**
     * Update configuration
     * @param {Object} newConfig 
     */
    function setConfig(newConfig) {
        Object.assign(CONFIG, newConfig);
    }

    /**
     * Generate unique session ID
     */
    function generateSessionId() {
        return 'pc_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Check for bot-like behavior patterns
     */
    function detectSuspiciousBehavior() {
        const patterns = [];
        
        // Check for mechanical mouse movements
        if (sessionData.mouseMovements.length > 10) {
            const velocities = [];
            for (let i = 1; i < sessionData.mouseMovements.length; i++) {
                const prev = sessionData.mouseMovements[i-1];
                const curr = sessionData.mouseMovements[i];
                const dx = curr.x - prev.x;
                const dy = curr.y - prev.y;
                const dt = curr.timestamp - prev.timestamp;
                
                if (dt > 0) {
                    const velocity = Math.sqrt(dx*dx + dy*dy) / dt;
                    velocities.push(velocity);
                }
            }
            
            // Check for suspiciously consistent velocities
            if (velocities.length > 5) {
                const variance = calculateVariance(velocities);
                if (variance < 0.001) {
                    patterns.push('mechanical_movement');
                }
            }
        }

        // Check for suspicious timing patterns in keystrokes
        if (sessionData.keystrokes.length > 10) {
            const intervals = [];
            for (let i = 1; i < sessionData.keystrokes.length; i++) {
                intervals.push(sessionData.keystrokes[i].timestamp - sessionData.keystrokes[i-1].timestamp);
            }
            
            const variance = calculateVariance(intervals);
            if (variance < 100) { // Very consistent timing
                patterns.push('mechanical_typing');
            }
        }

        return patterns;
    }

    /**
     * Calculate variance of an array
     */
    function calculateVariance(values) {
        if (values.length === 0) return 0;
        
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
        const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
        
        return variance;
    }

    // Expose PassiveCaptcha to global scope
    window.PassiveCaptcha = PassiveCaptcha;

    // Auto-initialize if data attributes are present
    document.addEventListener('DOMContentLoaded', function() {
        const autoInit = document.querySelector('[data-passive-captcha]');
        if (autoInit) {
            const options = {
                element: autoInit.getAttribute('data-target') || autoInit,
                onVerified: function(result) {
                    console.log('PassiveCaptcha verification result:', result);
                }
            };
            
            PassiveCaptcha.init(options);
        }
    });

})(window, document); 