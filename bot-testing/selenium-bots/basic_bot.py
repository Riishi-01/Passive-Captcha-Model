#!/usr/bin/env python3
"""
Basic Selenium Bot - No Human Simulation
This bot performs mechanical actions that should be easily detected
"""

import sys
import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_URL, UIDAI_URL, ADMIN_URL, USER_AGENTS, RESULTS_DIR

class BasicSeleniumBot:
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.results = {
            'bot_type': 'selenium_basic',
            'start_time': datetime.now().isoformat(),
            'actions': [],
            'detections': [],
            'errors': []
        }
        
    def setup_driver(self):
        """Setup Chrome driver with bot-like settings"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Bot-like settings (easily detectable)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')  # This will break the CAPTCHA, but shows bot behavior
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--user-agent=' + USER_AGENTS['bot_selenium'])
        
        # Bot detection flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def log_action(self, action, details=None):
        """Log action with timestamp"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {}
        }
        self.results['actions'].append(log_entry)
        print(f"[BASIC BOT] {action}: {details}")
        
    def test_uidai_portal(self):
        """Test basic interactions with UIDAI portal"""
        print(f"\n=== Testing UIDAI Portal: {UIDAI_URL} ===")
        
        try:
            # Navigate to UIDAI portal
            self.log_action('navigate', {'url': UIDAI_URL})
            self.driver.get(UIDAI_URL)
            
            # Wait a very short time (bot-like)
            time.sleep(0.1)
            
            # Get page title
            title = self.driver.title
            self.log_action('get_title', {'title': title})
            
            # Mechanical clicking - find all clickable elements and click rapidly
            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a, button, input[type="button"], input[type="submit"]')
            self.log_action('found_clickable', {'count': len(clickable_elements)})
            
            for i, element in enumerate(clickable_elements[:5]):  # Click first 5 elements
                try:
                    # Very fast clicking (bot-like)
                    element.click()
                    self.log_action('click', {'element_index': i, 'tag': element.tag_name})
                    time.sleep(0.05)  # Extremely fast - obviously bot
                except Exception as e:
                    self.log_action('click_error', {'element_index': i, 'error': str(e)})
            
            # Mechanical scrolling
            for scroll_pos in [100, 300, 500, 800, 1000]:
                self.driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                time.sleep(0.01)  # Very fast scrolling
                self.log_action('scroll', {'position': scroll_pos})
            
            # Rapid form interactions if any forms exist
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            for form in forms:
                inputs = form.find_elements(By.CSS_SELECTOR, 'input, textarea')
                for inp in inputs:
                    try:
                        # Type at impossible speed
                        inp.clear()
                        inp.send_keys("bot_test_input")
                        time.sleep(0.01)
                        self.log_action('form_input', {'type': inp.get_attribute('type')})
                    except:
                        pass
                        
        except Exception as e:
            self.log_action('error', {'message': str(e)})
            self.results['errors'].append(str(e))
            
    def test_admin_panel(self):
        """Test admin panel access"""
        print(f"\n=== Testing Admin Panel: {ADMIN_URL} ===")
        
        try:
            self.log_action('navigate', {'url': ADMIN_URL})
            self.driver.get(ADMIN_URL)
            
            # Very short wait
            time.sleep(0.1)
            
            # Look for login form
            try:
                # Find login elements rapidly
                username_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="text"], input[type="email"], input[name*="user"], input[name*="login"]')
                password_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                
                # Instant typing (bot-like)
                username_field.clear()
                username_field.send_keys("admin")
                password_field.clear()  
                password_field.send_keys("admin123")
                
                self.log_action('login_attempt', {'username': 'admin'})
                
                # Find and click submit button instantly
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
                submit_btn.click()
                
                time.sleep(0.1)
                
            except Exception as e:
                self.log_action('login_error', {'error': str(e)})
                
        except Exception as e:
            self.log_action('error', {'message': str(e)})
            self.results['errors'].append(str(e))
            
    def run_test(self):
        """Run complete bot test"""
        print("🤖 Starting Basic Selenium Bot Test")
        print("This bot uses obvious automation patterns that should be easily detected")
        
        try:
            self.setup_driver()
            
            # Test UIDAI portal
            self.test_uidai_portal()
            
            # Test admin panel
            self.test_admin_panel()
            
            # Final wait
            time.sleep(1)
            
        except Exception as e:
            print(f"Test failed: {e}")
            self.results['errors'].append(str(e))
        finally:
            if self.driver:
                self.driver.quit()
                
        self.results['end_time'] = datetime.now().isoformat()
        return self.results
        
    def save_results(self):
        """Save test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{RESULTS_DIR}/basic_selenium_{timestamp}.json"
        
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to: {filename}")

if __name__ == "__main__":
    bot = BasicSeleniumBot(headless=True)
    results = bot.run_test()
    bot.save_results()
    
    print(f"\n=== Test Summary ===")
    print(f"Actions performed: {len(results['actions'])}")
    print(f"Errors encountered: {len(results['errors'])}")
    print(f"Test duration: {results['end_time']} - {results['start_time']}")
    
    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")