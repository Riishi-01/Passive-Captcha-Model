"""
Bot Testing Configuration
"""

# Target URLs - Railway deployment
BASE_URL = "https://captcha-prototype-production.up.railway.app"
UIDAI_URL = f"{BASE_URL}/"
ADMIN_URL = f"{BASE_URL}/admin"
HEALTH_URL = f"{BASE_URL}/health"

# Admin credentials for testing
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Test configuration
TEST_DURATION = 30  # seconds
TEST_ITERATIONS = 5
DELAY_RANGE = (0.1, 2.0)  # min, max delay between actions

# User agents for different bot types
USER_AGENTS = {
    'human': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'bot_obvious': 'Python/3.11 requests/2.31.0',
    'bot_selenium': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0.0.0 Safari/537.36',
    'bot_sneaky': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Results directory
RESULTS_DIR = "results"