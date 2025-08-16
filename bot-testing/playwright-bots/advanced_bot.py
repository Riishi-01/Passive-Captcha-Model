#!/usr/bin/env python3
"""
Advanced Playwright Bot - Human Simulation
This bot attempts to mimic human behavior to test sophisticated detection
"""

import sys
import os
import time
import json
import random
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_URL, UIDAI_URL, ADMIN_URL, USER_AGENTS, RESULTS_DIR, DELAY_RANGE

class AdvancedPlaywrightBot:
    def __init__(self, headless=True):
        self.browser = None
        self.page = None
        self.headless = headless
        self.ua = UserAgent()
        self.results = {
            'bot_type': 'playwright_advanced',
            'start_time': datetime.now().isoformat(),
            'actions': [],
            'detections': [],
            'errors': [],
            'human_simulation': True
        }
        
    def log_action(self, action, details=None):
        """Log action with timestamp"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {}
        }
        self.results['actions'].append(log_entry)
        print(f"[ADVANCED BOT] {action}: {details}")
        
    async def human_delay(self, min_delay=None, max_delay=None):
        """Simulate human-like delays"""
        min_d = min_delay or DELAY_RANGE[0]
        max_d = max_delay or DELAY_RANGE[1]
        delay = random.uniform(min_d, max_d)
        await asyncio.sleep(delay)
        return delay
        
    async def human_type(self, element, text, typing_speed_range=(50, 150)):
        """Type text with human-like timing"""
        for char in text:
            await element.type(char)
            # Human typing speed: 50-150ms between characters
            delay = random.uniform(typing_speed_range[0], typing_speed_range[1]) / 1000
            await asyncio.sleep(delay)
            
    async def human_mouse_movement(self):
        """Simulate natural mouse movements"""
        viewport = await self.page.viewport_size()
        if not viewport:
            return
            
        # Random mouse movements
        for _ in range(random.randint(3, 8)):
            x = random.randint(0, viewport['width'])
            y = random.randint(0, viewport['height'])
            
            # Move in steps for natural movement
            await self.page.mouse.move(x, y, steps=random.randint(10, 30))
            await self.human_delay(0.1, 0.5)
            
    async def human_scroll_behavior(self):
        """Simulate human scrolling patterns"""
        # Get page height
        page_height = await self.page.evaluate("document.body.scrollHeight")
        
        # Human-like scrolling - gradual, with pauses
        scroll_positions = []
        current_pos = 0
        
        while current_pos < page_height:
            # Random scroll amount (human-like)
            scroll_amount = random.randint(100, 400)
            current_pos += scroll_amount
            scroll_positions.append(min(current_pos, page_height))
            
        for pos in scroll_positions:
            await self.page.evaluate(f"window.scrollTo(0, {pos})")
            await self.human_delay(0.5, 2.0)  # Human reading time
            
    async def setup_browser(self):
        """Setup Playwright browser with human-like settings"""
        playwright = await async_playwright().start()
        
        # Use random but realistic user agent
        user_agent = self.ua.random
        
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with human-like settings
        context = await self.browser.new_context(
            viewport={'width': 1366, 'height': 768},  # Common resolution
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'longitude': -74.0060, 'latitude': 40.7128},  # NYC
            permissions=['geolocation']
        )
        
        # Add realistic headers
        await context.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.page = await context.new_page()
        
        # Stealth modifications
        await self.page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock chrome property
            window.chrome = {
                runtime: {},
            };
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
    async def test_uidai_portal(self):
        """Test UIDAI portal with human-like behavior"""
        print(f"\n=== Testing UIDAI Portal: {UIDAI_URL} ===")
        
        try:
            # Navigate with human-like timing
            self.log_action('navigate', {'url': UIDAI_URL})
            await self.page.goto(UIDAI_URL, wait_until='domcontentloaded')
            
            # Human-like initial pause (reading page)
            await self.human_delay(2, 5)
            
            # Get page title
            title = await self.page.title()
            self.log_action('get_title', {'title': title})
            
            # Natural mouse movements
            await self.human_mouse_movement()
            
            # Human-like reading behavior - scroll and pause
            await self.human_scroll_behavior()
            
            # Look for interesting content to interact with
            await self.human_delay(1, 3)
            
            # Find clickable elements and interact naturally
            clickable_elements = await self.page.query_selector_all('a, button')
            if clickable_elements:
                # Human behavior: not clicking everything, being selective
                selected_elements = random.sample(
                    clickable_elements, 
                    min(3, len(clickable_elements))
                )
                
                for element in selected_elements:
                    try:
                        # Check if element is visible and clickable
                        if await element.is_visible():
                            # Human-like hover before click
                            await element.hover()
                            await self.human_delay(0.5, 1.5)
                            
                            # Natural click with random timing
                            await element.click()
                            self.log_action('click', {'element': await element.get_attribute('class')})
                            
                            # Human reaction time after click
                            await self.human_delay(1, 3)
                            
                    except Exception as e:
                        self.log_action('click_error', {'error': str(e)})
            
            # Look for forms and interact naturally
            forms = await self.page.query_selector_all('form')
            for form in forms[:1]:  # Only interact with first form
                inputs = await form.query_selector_all('input, textarea')
                for inp in inputs[:2]:  # Limit inputs
                    try:
                        input_type = await inp.get_attribute('type')
                        if input_type not in ['submit', 'button', 'hidden']:
                            await inp.click()
                            await self.human_delay(0.5, 1.0)
                            
                            # Human-like typing
                            await self.human_type(inp, "test user input")
                            self.log_action('form_input', {'type': input_type})
                            
                            await self.human_delay(1, 2)
                    except:
                        pass
                        
        except Exception as e:
            self.log_action('error', {'message': str(e)})
            self.results['errors'].append(str(e))
            
    async def test_admin_panel(self):
        """Test admin panel with sophisticated evasion"""
        print(f"\n=== Testing Admin Panel: {ADMIN_URL} ===")
        
        try:
            self.log_action('navigate', {'url': ADMIN_URL})
            await self.page.goto(ADMIN_URL, wait_until='domcontentloaded')
            
            # Human-like pause to observe the page
            await self.human_delay(3, 6)
            
            # Natural mouse exploration
            await self.human_mouse_movement()
            
            # Look for login form
            try:
                # Find login elements with human-like search pattern
                await self.human_delay(1, 2)
                
                username_field = await self.page.query_selector('input[type="text"], input[type="email"], input[name*="user"], input[id*="user"]')
                password_field = await self.page.query_selector('input[type="password"]')
                
                if username_field and password_field:
                    # Human-like form interaction
                    await username_field.click()
                    await self.human_delay(0.5, 1.0)
                    
                    # Clear field naturally
                    await username_field.select_text()
                    await self.human_type(username_field, "admin")
                    
                    await self.human_delay(0.5, 1.5)
                    
                    # Move to password field
                    await password_field.click()
                    await self.human_delay(0.3, 0.8)
                    
                    await password_field.select_text()
                    await self.human_type(password_field, "admin123")
                    
                    self.log_action('login_attempt', {'username': 'admin'})
                    
                    # Human pause before submitting
                    await self.human_delay(1, 3)
                    
                    # Find and click submit button
                    submit_btn = await self.page.query_selector('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in")')
                    if submit_btn:
                        await submit_btn.click()
                        
                        # Wait for response
                        await self.human_delay(2, 4)
                        
            except Exception as e:
                self.log_action('login_error', {'error': str(e)})
                
        except Exception as e:
            self.log_action('error', {'message': str(e)})
            self.results['errors'].append(str(e))
            
    async def run_test(self):
        """Run complete bot test"""
        print("🎭 Starting Advanced Playwright Bot Test")
        print("This bot attempts to mimic human behavior patterns")
        
        try:
            await self.setup_browser()
            
            # Test UIDAI portal
            await self.test_uidai_portal()
            
            # Human-like break between tests
            await self.human_delay(5, 10)
            
            # Test admin panel
            await self.test_admin_panel()
            
            # Final human-like delay
            await self.human_delay(3, 6)
            
        except Exception as e:
            print(f"Test failed: {e}")
            self.results['errors'].append(str(e))
        finally:
            if self.browser:
                await self.browser.close()
                
        self.results['end_time'] = datetime.now().isoformat()
        return self.results
        
    def save_results(self):
        """Save test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{RESULTS_DIR}/advanced_playwright_{timestamp}.json"
        
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to: {filename}")

async def main():
    bot = AdvancedPlaywrightBot(headless=True)
    results = await bot.run_test()
    bot.save_results()
    
    print(f"\n=== Test Summary ===")
    print(f"Actions performed: {len(results['actions'])}")
    print(f"Errors encountered: {len(results['errors'])}")
    print(f"Test duration: {results['end_time']} - {results['start_time']}")
    
    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(main())