from selenium_script import WebsiteOpener
import os
import time
import json
import re
import requests
import dotenv
import threading
import queue
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from utils.calculate_no_vig_prices import calculate_no_vig_prices
from utils.calculate_ev import calculate_ev
from scipy.optimize import minimize_scalar
import math
from captcha_solver import CaptchaSolver

dotenv.load_dotenv()

# Set up logging
def setup_logging():
    """Set up structured logging for the betting system"""
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # File handlers for different components
    bet_handler = logging.FileHandler('logs/betting.log')
    bet_handler.setLevel(logging.DEBUG)
    bet_handler.setFormatter(detailed_formatter)
    
    odds_handler = logging.FileHandler('logs/odds.log')
    odds_handler.setLevel(logging.DEBUG)
    odds_handler.setFormatter(detailed_formatter)
    
    auth_handler = logging.FileHandler('logs/auth.log')
    auth_handler.setLevel(logging.DEBUG)
    auth_handler.setFormatter(detailed_formatter)
    
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Create loggers
    bet_logger = logging.getLogger('betting')
    bet_logger.setLevel(logging.DEBUG)
    bet_logger.addHandler(bet_handler)
    bet_logger.addHandler(console_handler)
    
    odds_logger = logging.getLogger('odds')
    odds_logger.setLevel(logging.DEBUG)
    odds_logger.addHandler(odds_handler)
    odds_logger.addHandler(console_handler)
    
    auth_logger = logging.getLogger('auth')
    auth_logger.setLevel(logging.DEBUG)
    auth_logger.addHandler(auth_handler)
    auth_logger.addHandler(console_handler)
    
    error_logger = logging.getLogger('errors')
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(error_handler)
    error_logger.addHandler(console_handler)
    
    return bet_logger, odds_logger, auth_logger, error_logger

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Initialize loggers
bet_logger, odds_logger, auth_logger, error_logger = setup_logging()

class BetAccount:
    """
    Represents a single MSport account with its own login credentials and cookie jar
    """
    def __init__(self, username, password, active=True, max_concurrent_bets=3, min_balance=100, proxy=None):
        self.username = username
        self.password = password
        self.active = active
        self.max_concurrent_bets = max_concurrent_bets
        self.min_balance = min_balance
        self.proxy = proxy  # Format: "http://user:pass@host:port" or "http://host:port"
        self.cookie_jar = None
        self.current_bets = 0
        self.last_login_time = 0
        self.balance = 0
        
    def increment_bets(self):
        self.current_bets += 1
        
    def decrement_bets(self):
        self.current_bets = max(0, self.current_bets - 1)
        
    def can_place_bet(self):
        # auth_logger.debug(f"Account {self.username} can place bet: {self.active} {self.cookie_jar is not None} {self.current_bets < self.max_concurrent_bets} {self.balance >= self.min_balance}")
        # auth_logger.debug(f"current bets: {self.current_bets} max concurrent bets: {self.max_concurrent_bets} balance: {self.balance} min balance: {self.min_balance}")
        return (self.active and 
                self.current_bets < self.max_concurrent_bets)
        
    def set_cookie_jar(self, cookies):
        # Handle both formats: list of cookie dictionaries (from Selenium) or direct dictionary
        if isinstance(cookies, list):
            self.cookie_jar = {cookie["name"]: cookie["value"] for cookie in cookies}
        else:
            # Assume it's already a dictionary
            self.cookie_jar = cookies
        self.last_login_time = time.time()
        
    def needs_login(self, max_session_time=3600):  # 1 hour max session time
        return (self.cookie_jar is None or 
                (time.time() - self.last_login_time) > max_session_time)

    def get_proxies(self):
        """Return proxies dictionary for requests if proxy is configured"""
        if not self.proxy:
            return None
        return {
            'http': self.proxy,
            'https': self.proxy
        }

class BetEngine(WebsiteOpener):
    """
    Handles the bet placement process on MSport, including:
    - Searching for matches
    - Finding the right market
    - Calculating EV
    - Placing bets with positive EV using selenium
    """
    
    def __init__(self, headless=os.getenv("ENVIRONMENT")=="production", 
                 bet_host=os.getenv("MSPORT_HOST", "https://www.msport.com"), 
                 bet_api_host=os.getenv("MSPORT_API_HOST", "https://www.msport.com/api/ng/facts-center/query/frontend"),
                 min_ev=float(os.getenv("MIN_EV", "0")),
                 config_file="config.json",
                 skip_initial_login=False):
        bet_logger.info(f"Initializing BetEngine with min_ev: {min_ev}")
        # Only initialize browser if needed for certain operations
        self.__browser_initialized = False
        self.__browser_open = False
        self.__headless = headless
        self.__skip_initial_login = skip_initial_login
        # bet_logger.debug(f"BetEngine initialized with headless: {headless}, skip_initial_login: {skip_initial_login}")
        self.__bet_api_host = bet_api_host
        self.__bet_host = bet_host
        self.__min_ev = min_ev
        self.__accounts = []
        self.__bet_queue = queue.Queue()
        self.__load_config(config_file)
        self.__setup_accounts()
        self.__start_bet_worker()
        
    def _initialize_browser_if_needed(self, account=None):
        """Initialize the browser if it hasn't been initialized yet
        
        Parameters:
        - account: Specific BetAccount to use for proxy configuration. If None, uses first available proxy.
        """
        # Check if we need to reinitialize browser for a different proxy
        current_proxy = getattr(self, '_current_proxy', None)
        target_proxy = None
        
        if self.__config.get("use_proxies", False):
            if account and account.proxy:
                target_proxy = account.proxy
            else:
                # Fallback to first available proxy
                for acc in self.__accounts:
                    if acc.proxy:
                        target_proxy = acc.proxy
                        break
        
        # If browser is initialized but we need a different proxy, clean up first
        bet_logger.debug(f"self.__browser_initialized: {self.__browser_initialized}")
        bet_logger.debug(f"current_proxy: {current_proxy} target_proxy: {target_proxy}")
        if (self.__browser_initialized and 
            current_proxy != target_proxy and 
            self.__config.get("use_proxies", False)):
            # bet_logger.debug(f"Proxy change detected: {current_proxy} -> {target_proxy}")
            # bet_logger.debug("Cleaning up browser to switch proxy...")
            self._cleanup_browser_for_proxy_switch()
        
        if not self.__browser_initialized:
            bet_logger.info("Initializing browser...")
            
            # Get proxy from the specified account or first available account if configured
            proxy = target_proxy
            if proxy:
                bet_logger.info(f"Using proxy: {proxy}")
                if account:
                    bet_logger.debug(f"  └─ From account: {account.username}")
                else:
                    bet_logger.debug(f"  └─ From fallback account")
            else:
                if self.__config.get("use_proxies", False):
                    bet_logger.warning("Proxy usage enabled but no proxy found in accounts")
                else:
                    bet_logger.debug("Proxy usage disabled in config")
            
            super().__init__(self.__headless, proxy)
            self.__browser_initialized = True
            self.__browser_open = True
            self._current_proxy = proxy  # Store current proxy for future comparison
            bet_logger.info("Browser initialized")
            
            # Check IP address if using proxy
            if proxy:
                proxy_dict = {'http': proxy, 'https': proxy}
                self.__check_ip_address(using_proxy=True, proxy_url=proxy_dict, account=account)
            else:
                self.__check_ip_address(using_proxy=False)
    
    def _cleanup_browser_for_proxy_switch(self):
        """Clean up the current browser instance to allow for proxy switching"""
        try:
            if hasattr(self, 'driver') and self.driver:
                bet_logger.info("Closing current browser for proxy switch...")
                self.driver.quit()
                self.driver = None
            
            self.__browser_initialized = False
            self.__browser_open = False
            self._current_proxy = None
            bet_logger.info("Browser cleanup completed")
            
        except Exception as e:
            error_logger.error(f"Error during browser cleanup: {e}")
            # Force reset the flags even if cleanup failed
            self.__browser_initialized = False
            self.__browser_open = False
            self._current_proxy = None
        
    def __load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                self.__config = json.load(f)
                
            # Update min_ev from config if available
            if "bet_settings" in self.__config and "min_ev" in self.__config["bet_settings"]:
                self.__min_ev = float(self.__config["bet_settings"]["min_ev"])
                
            if "bet_settings" in self.__config and "min_stake" in self.__config["bet_settings"]:
                self.__min_stake = float(self.__config["bet_settings"]["min_stake"])
                
            if "bet_settings" in self.__config and "max_stake" in self.__config["bet_settings"]:
                self.__max_stake = float(self.__config["bet_settings"]["max_stake"])
                
            if "bet_settings" in self.__config and "max_pinnacle_odds" in self.__config["bet_settings"]:
                self.__max_pinnacle_odds = float(self.__config["bet_settings"]["max_pinnacle_odds"])
            else:
                self.__max_pinnacle_odds = 3.0  # Default value
                
            # Load odds-based stake ranges
            if "bet_settings" in self.__config and "odds_based_stakes" in self.__config["bet_settings"]:
                self.__odds_based_stakes = self.__config["bet_settings"]["odds_based_stakes"]
            else:
                # Default odds-based stake ranges
                self.__odds_based_stakes = {
                    "low_odds": {
                        "max_odds": 1.99,
                        "min_stake": 6000,
                        "max_stake": 12000
                    },
                    "medium_odds": {
                        "min_odds": 2.0,
                        "max_odds": 3.0,
                        "min_stake": 3000,
                        "max_stake": 7000
                    }
                }
                
                
            bet_logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            error_logger.error(f"Error loading config file: {e}")
            # Create default config
            self.__config = {
                "accounts": [],
                "max_total_concurrent_bets": 5,
                "use_proxies": False,  # Global flag to enable/disable proxies
                "immediate_bet_placement": True,  # Place bets immediately instead of queuing
                "bet_settings": {
                    "min_ev": self.__min_ev,
                    "kelly_fraction": 0.3,
                    "min_stake": 10,
                    "max_stake": 1000000,
                    "max_pinnacle_odds": 3.0,
                    "odds_based_stakes": {
                        "low_odds": {
                            "max_odds": 1.99,
                            "min_stake": 6000,
                            "max_stake": 12000
                        },
                        "medium_odds": {
                            "min_odds": 2.0,
                            "max_odds": 3.0,
                            "min_stake": 3000,
                            "max_stake": 7000
                        }
                    },
                    "bankroll": 1000
                }
            }
            
    def __setup_accounts(self):
        """Initialize bet accounts from config"""
        # First, set up at least one account from environment variables if available
        env_username = os.getenv("MSPORT_USERNAME")
        env_password = os.getenv("MSPORT_PASSWORD")
        
        if env_username and env_password:
            self.__accounts.append(BetAccount(env_username, env_password))
            
        # Then add accounts from config
        if "accounts" in self.__config:
            for account_data in self.__config["accounts"]:
                # Skip if username/password is missing or account already exists
                if not account_data.get("username") or not account_data.get("password"):
                    continue
                    
                # Check if this account is already added from env vars
                if (env_username and env_password and 
                    account_data.get("username") == env_username and 
                    account_data.get("password") == env_password):
                    continue
                    
                self.__accounts.append(BetAccount(
                    username=account_data.get("username"),
                    password=account_data.get("password"),
                    active=account_data.get("active", True),
                    max_concurrent_bets=account_data.get("max_concurrent_bets", 3),
                    min_balance=account_data.get("min_balance", 100),
                    proxy=account_data.get("proxy")
                ))
                auth_logger.info(f"Added account: {account_data.get('username')}")
                
        # Ensure we have at least one account
        if not self.__accounts:
            raise ValueError("No betting accounts configured. Please set MSPORT_USERNAME and MSPORT_PASSWORD environment variables or configure accounts in config.json")
            
        bet_logger.info(f"Set up {len(self.__accounts)} betting accounts")
        
        # Try to login to accounts for initial setup, but don't fail if login fails
        if self.__accounts and not self.__skip_initial_login:
            auth_logger.info("Attempting initial login for all accounts...")
            try:
                for account in self.__accounts:
                    try:
                        self.__do_login_for_account(account)
                        auth_logger.info(f"Successfully logged in account: {account.username}")
                    except Exception as e:
                        error_logger.error(f"Failed to login account {account.username} during setup: {e}")
                        auth_logger.warning("Account will be available for retry later")
                        # Continue with other accounts instead of crashing
                        continue
            finally:
                # Close browser after all login attempts are complete
                if self.__browser_initialized:
                    bet_logger.info("Closing browser after account setup...")
                    self.cleanup()
        elif self.__skip_initial_login:
            auth_logger.info("Skipping initial login as requested")
        else:
            auth_logger.warning("No accounts configured for initial login")

            
    def __start_bet_worker(self):
        """Start a worker thread to process bet queue"""
        self.__worker_thread = threading.Thread(target=self.__process_bet_queue, daemon=True)
        self.__worker_thread.start()
        
    def __process_bet_queue(self):
        """Process bets from the queue"""
        while True:
            try:
                # Get bet data from queue
                bet_data = self.__bet_queue.get()
                
                # Place bet with available accounts
                self.__place_bet_with_available_account(bet_data)
                
                # Mark task as done
                self.__bet_queue.task_done()
                
            except Exception as e:
                error_logger.error(f"Error in bet worker thread: {e}")
                
            # Small sleep to prevent CPU hogging
            time.sleep(0.1)

    def __do_login(self):
        """Log in to MSport website with the first account (for search functionality)"""
        if self.__accounts:
            self.__do_login_for_account(self.__accounts[0])
        else:
            raise ValueError("No betting accounts configured")
            
    def __check_ip_address(self, using_proxy=False, proxy_url=None, account=None ):
        """Check and log the current IP address being used"""
        try:
            # Use a service that returns the client's IP address
            ip_check_url = "https://api.ipify.org?format=json"
            response = requests.get(ip_check_url, proxies=proxy_url)
            if response.status_code == 200:
                ip_data = response.json()
                if "ip" in ip_data:
                    ip_address = ip_data["ip"]
                    if using_proxy:
                        auth_logger.info(f"✅ Using proxy - Current IP address: {ip_address} {account.username} {account.proxy}")
                    else:
                        auth_logger.info(f"Current IP address (no proxy): {ip_address}")
                    return ip_address
            auth_logger.warning("Failed to get IP address")
            return None
        except Exception as e:
            error_logger.error(f"Error checking IP address: {e}")
            return None
            
    def __fetch_account_balance(self, account):
        """
        Fetch account balance from MSport API after login
        
        Parameters:
        - account: BetAccount instance with valid cookies
        
        Returns:
        - Balance amount as float, or 0 if failed
        """
        try:
            if not account.cookie_jar:
                auth_logger.warning(f"No cookies available for account {account.username}, cannot fetch balance")
                return 0
                
            balance_url = f"{self.__bet_host}/api/ng/pocket/financialAccounts/balance"
            
            # Convert cookie jar to requests format
            cookies = {}
            if isinstance(account.cookie_jar, dict):
                cookies = account.cookie_jar
            elif isinstance(account.cookie_jar, list):
                cookies = {cookie["name"]: cookie["value"] for cookie in account.cookie_jar}
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.msport.com/",
            }
            
            response = requests.get(balance_url, headers=headers, cookies=cookies, proxies=account.get_proxies())
            
            if response.status_code == 200:
                balance_data = response.json()
                
                if balance_data.get("bizCode") == 10000 and "data" in balance_data:
                    avl_bal = balance_data["data"].get("avlBal", 0)
                    biz_code = balance_data.get("bizCode", 10000)
                    
                    # Calculate real balance as avlBal / bizCode
                    real_balance = avl_bal / biz_code
                    auth_logger.info(f"Account {account.username} balance: {real_balance:.2f} (avlBal: {avl_bal}, bizCode: {biz_code})")
                    
                    return real_balance
                else:
                    auth_logger.warning(f"Invalid balance response for account {account.username}: {balance_data}")
                    return 0
            else:
                auth_logger.error(f"Failed to fetch balance for account {account.username}: HTTP {response.status_code}")
                return 0
                
        except Exception as e:
            error_logger.error(f"Error fetching balance for account {account.username}: {e}")
            return 0

    def __do_login_for_account(self, account, _retry=False):
        """Log in to MSport website with a specific account using selenium"""
        auth_logger.info(f"Logging in to MSport with account: {account.username}")
        
        if not account.username or not account.password:
            raise ValueError("MSport username or password not found for account")
        
        try:
            # Initialize browser with account-specific proxy
            self._initialize_browser_if_needed(account)
            
            # Initialize CAPTCHA solver
            # captcha_config = self.__config.get("captcha", {})
            # if captcha_config.get("enabled", True):
            #     captcha_solver = CaptchaSolver(api_key=captcha_config.get("api_key"))
            #     captcha_solver.max_retries = captcha_config.get("max_retries", 3)
            # else:
            #     print("⚠️  CAPTCHA solving is disabled in configuration")
            #     captcha_solver = None

            # Check if already logged in first
            try:
                # Look for account balance element which indicates successful login
                balance_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".account--balance.account-item.tw-text-yellow"))
                )
                auth_logger.info(f"Already logged in for account: {account.username}")
                
                # Get cookies from selenium
                selenium_cookies = self.driver.get_cookies()
                account.set_cookie_jar(selenium_cookies)
                
                # Fetch account balance after successful login
                balance = self.__fetch_account_balance(account)
                account.balance = balance
                auth_logger.info(f"Updated account balance: {balance:.2f}")
            
                # If this is the first account, also store cookies in the class for search functionality
                if self.__accounts and account == self.__accounts[0]:
                    self.__cookie_jar = account.cookie_jar
                
                return True
                
            except TimeoutException:
                auth_logger.info(f"Not logged in, proceeding with login process for account: {account.username}")
                # Continue with login process
            except Exception as e:
                auth_logger.warning(f"Error checking login status: {e}")
                # Continue with login process
            
            # Navigate to MSport login page
            login_url = f"{self.__bet_host}"
            self.driver.get(login_url)
            # time.sleep(3)  # Give page time to load
            auth_logger.info(f"Navigated to login page: {login_url}")
            # Find phone number input (based on the images provided)
            # print("🔍 Looking for login form elements...")
            phone_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel'], input[placeholder*='Mobile']"))
            )
            phone_input.clear()
            phone_input.send_keys(account.username)
            auth_logger.info(f"📱 Entered phone number: {account.username}")
            
            # Find password input
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input.clear()
            password_input.send_keys(account.password)
            auth_logger.info(f"🔑 Entered password")
            
            # Find and click login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], .v-button.btn.login.popper-input-button"))
            )
            login_button.click()
            auth_logger.info(f"🚀 Clicked login button")
            
            # Take screenshot for debugging
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"login_status_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                # print(f"📸 Login status screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                error_logger.error(f"Failed to take screenshot: {screenshot_error}")

            # time.sleep(5000)
            
            
            # Check if login was successful by looking for user profile or betting interface
            try:
                # Look for elements that indicate successful login
                WebDriverWait(self.driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".account--balance.account-item.tw-text-yellow")),
                        EC.url_contains("home"),
                        EC.url_contains("sports")
                    )
                )
                auth_logger.info(f"Login successful for account: {account.username}")
                
                # Get cookies from selenium
                selenium_cookies = self.driver.get_cookies()
                account.set_cookie_jar(selenium_cookies)
                
                # Fetch account balance after successful login
                balance = self.__fetch_account_balance(account)
                account.balance = balance
                auth_logger.info(f"Updated account balance: {balance:.2f}")
            
                # If this is the first account, also store cookies in the class for search functionality
                if self.__accounts and account == self.__accounts[0]:
                    self.__cookie_jar = account.cookie_jar
                
                return True
                    
            except TimeoutException:
                auth_logger.warning(f"Login may have failed for account: {account.username}")
                raise Exception("Login verification timeout")
                
        except Exception as e:
            # Take screenshot of error state
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"login_error_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                auth_logger.info(f"Login error screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                error_logger.error(f"Failed to take error screenshot: {screenshot_error}")
            error_logger.error(f"❌ Login failed for account: {account.username}: {e}")
            # Minimal recovery for Selenium tab crashes
            msg = str(e).lower()
            if ("tab crashed" in msg or "chrome not reachable" in msg or "disconnected" in msg) and not _retry:
                error_logger.error("Detected browser/tab crash during login. Restarting browser and retrying once...")
                self.__restart_browser(account)
                return self.__do_login_for_account(account, _retry=True)
            
            error_logger.error(f"❌ Login failed for account: {account.username}: {e}")
            raise

    def __search_event(self, home_team, away_team, pinnacle_start_time=None):
        """
        Search for an event on MSport using team names and match start time
        
        Parameters:
        - home_team: Home team name
        - away_team: Away team name
        - pinnacle_start_time: Start time from Pinnacle in milliseconds (unix timestamp)
        
        Returns:
        - event ID if found, None otherwise
        """
        odds_logger.info(f"Searching for match: {home_team} vs {away_team}")
        if pinnacle_start_time:
            pinnacle_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(pinnacle_start_time)/1000))
            odds_logger.debug(f"Pinnacle start time: {pinnacle_datetime} (GMT)")
        
        # Try different search strategies
        search_strategies = [
            f"{home_team.lower()} {away_team.lower()}",  # Full match name
            home_team.lower(),                   # Home team only
            away_team.lower(),                   # Away team only
        ]
        
        # Add individual words from team names as search strategies
        for team in [home_team, away_team]:
            words = team.split()
            for word in words:
                if len(word) > 3 and word not in search_strategies:  # Only use words longer than 3 chars
                    search_strategies.append(word)
        
        # Store potential matches with scores for later evaluation
        potential_matches = []
        
        # List of terms that indicate the wrong team variant
        variant_indicators = ["ladies", "women", "u21", "u-21", "u23", "u-23", "youth", "junior", "reserve", "b team"]
        
        for search_term in search_strategies:
            odds_logger.debug(f"Trying search term: {search_term}")
            
            try:
                # MSport search endpoint
                search_url = f"{self.__bet_api_host}/search/event/page/v2"
                params = {
                    'keyword': search_term,
                    'size': 20,
                    'sportId': 'sr:sport:1'  # Soccer sport ID
                }
            
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Referer": "https://www.msport.com/",
                    "Operid": "2"
                }
                
                odds_logger.debug(f"Searching with URL: {search_url} and params: {params}")
                response = requests.get(search_url, params=params, headers=headers)
                
                odds_logger.debug(f"Response status: {response.status_code}")
                # print(f"Response content: {response.text[:500]}...")
                if response.status_code == 200:
                    try:
                        search_results = response.json()
                        # print(f"Search response: {search_results}")
                    except ValueError as e:
                        error_logger.error(f"Failed to parse JSON response: {e}")
                        odds_logger.debug(f"Response content: {response.text[:500]}...")
                        continue
                
                    # Updated to handle the correct API response structure
                    if "data" in search_results and search_results["data"] and "events" in search_results["data"]:
                        events = search_results["data"]["events"]
                        for event in events:
                            # Extract team names and event details
                            home_team_name = event.get("homeTeam", "").lower()
                            away_team_name = event.get("awayTeam", "").lower()
                            event_id = event.get("eventId")
                            
                            if not event_id:
                                continue
                                
                            # Skip events with variant indicators that don't exist in the original team names
                            event_name = f"{home_team_name} vs {away_team_name}"
                            should_skip = False
                            for indicator in variant_indicators:
                                if (indicator in event_name and 
                                    indicator not in home_team.lower() and 
                                    indicator not in away_team.lower()):
                                    should_skip = True
                                    break
                                
                            if should_skip:
                                odds_logger.debug(f"Skipping variant team: {event_name}")
                                continue
                                
                            # Calculate match score based on word matching
                            match_score = 0
                            home_words = set(word.lower() for word in home_team.lower().split() if len(word) > 1)
                            away_words = set(word.lower() for word in away_team.lower().split() if len(word) > 1)
                            event_home_words = set(word.lower() for word in home_team_name.split() if len(word) > 1)
                            event_away_words = set(word.lower() for word in away_team_name.split() if len(word) > 1)
                            
                            home_match_count = len(home_words.intersection(event_home_words))
                            away_match_count = len(away_words.intersection(event_away_words))
                            
                            # Perfect match check
                            if (home_team.lower() in home_team_name and away_team.lower() in away_team_name):
                                match_score += 10
                                    
                            # At least one word from each team must match
                            if home_match_count > 0 and away_match_count > 0:
                                match_score += home_match_count + away_match_count
                            else:
                                continue
                            
                                
                            # Check start time if available
                            time_match_score = 0
                            if pinnacle_start_time and "startTime" in event:
                                msport_start_time = event["startTime"]
                                try:
                                    # MSport time is likely in milliseconds
                                    time_diff_hours = abs(int(pinnacle_start_time) - msport_start_time) / (1000 * 60 * 60)
                                    
                                    if time_diff_hours <= 1.0833:  # Within 1 hour and 5 minutes
                                        time_match_score = 10
                                        match_score += time_match_score
                                    else:
                                        odds_logger.debug(f"Time difference: {time_diff_hours:.2f} hours, not the right game")
                                            
                                except Exception as e:
                                    error_logger.error(f"Error parsing time: {e}")
                                
                            # Add to potential matches if score is positive
                            if match_score > 0:
                                potential_matches.append({
                                "event_name": f"{event.get('homeTeam')} vs {event.get('awayTeam')}",
                                "event_id": event_id,
                                "score": match_score,
                                "strategy": search_term,
                                "home_team": event.get('homeTeam'),
                                "away_team": event.get('awayTeam')
                            })
                            odds_logger.debug(f"Potential match: {event_name} (Score: {match_score})")
                    else:
                        odds_logger.debug(f"No data found in search response for term: {search_term}")
                else:
                    odds_logger.warning(f"Search request failed with status: {response.status_code}")
                    # print(f"Response content: {response.text[:500]}...")
            
            except Exception as e:
                error_logger.error(f"Error searching for event with term '{search_term}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # If we have potential matches, return the one with the highest score
        if potential_matches:
            best_match = max(potential_matches, key=lambda x: x["score"])
            odds_logger.info(f"Best match: {best_match['event_name']} (ID: {best_match['event_id']}, Score: {best_match['score']})")
            return best_match["event_id"]
        
        odds_logger.warning("No matching event found on MSport")
        return None

    def __get_event_details(self, event_id):
        """Get detailed information about an event from MSport"""
        odds_logger.info(f"Getting details for event ID: {event_id}")
        
        try:
            # MSport event details endpoint
            details_url = f"{self.__bet_api_host}/match/detail"
            params = {
                'eventId': event_id
            }
        
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.msport.com/",
                "Operid": "2"
            }
            
            odds_logger.debug(f"Getting event details with URL: {details_url} and params: {params}")
            response = requests.get(details_url, params=params, headers=headers)
            
            odds_logger.debug(f"Event details response status: {response.status_code}")
            if response.status_code == 200:
                try:
                    event_details = response.json()
                    # print(f"Event details response: {event_details}")
                except ValueError as e:
                    error_logger.error(f"Failed to parse JSON response for event details: {e}")
                    odds_logger.debug(f"Response content: {response.text[:500]}...")
                    return None
                
                if "data" in event_details:
                    return event_details["data"]
                else:
                    odds_logger.warning(f"No 'data' field in event details response")
                    return None
            else:
                odds_logger.error(f"Failed to get event details: HTTP {response.status_code}")
                odds_logger.debug(f"Response content: {response.text[:500]}...")
                return None
            
        except Exception as e:
            error_logger.error(f"Error getting event details: {e}")
            import traceback
            traceback.print_exc()
            return None

    def __generate_msport_bet_url(self, event_details):
        """
        Generate MSport betting URL based on event details
        Format: https://www.msport.com/ng/web/sports/Soccer/HomeTeam/AwayTeam/eventId
        """
        try:
            home_team = event_details.get("homeTeam", "")
            away_team = event_details.get("awayTeam", "")
            event_id = event_details.get("eventId", "")
            
            # Replace spaces with underscores
            home_team_formatted = home_team.replace(" ", "_")
            away_team_formatted = away_team.replace(" ", "_")
            
            bet_url = f"{self.__bet_host}/ng/web/sports/Soccer/{home_team_formatted}/{away_team_formatted}/{event_id}"
            bet_logger.info(f"Generated MSport bet URL: {bet_url}")
            return bet_url
            
        except Exception as e:
            error_logger.error(f"Error generating MSport bet URL: {e}")
            return None

    def __wait_for_market_content(self, timeout_seconds: int = 15) -> None:
        """
        Explicitly wait for MSport market content to render.
        Waits until at least one of the known market containers is present.
        """
        try:
            # Ensure document is at least interactive/complete first
            WebDriverWait(self.driver, timeout_seconds).until(
                lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
            )
        except Exception:
            # Continue to element-based checks even if readyState wait fails
            pass
        
        target_selectors = [
            ".m-market-item",
            ".m-market-row.m-market-row--3",
            ".m-market-row.m-market-row",
        ]
        
        WebDriverWait(self.driver, timeout_seconds, poll_frequency=0.5).until(
            lambda d: any(len(d.find_elements(By.CSS_SELECTOR, sel)) > 0 for sel in target_selectors)
        )

    def __place_bet_with_selenium(self, account, bet_url, market_type, outcome, odds, stake, points=None, is_first_half=False, _retry=False):
        """
        Place a bet on MSport using Selenium
        
        Parameters:
        - account: BetAccount instance
        - bet_url: MSport betting URL for the event
        - market_type: Type of bet (moneyline, total, spread)
        - outcome: Outcome to bet on
        - odds: Expected odds
        - stake: Amount to stake
        - points: Points value for total/spread bets
        - is_first_half: Whether this is a first half bet
        
        Returns:
        - True if bet was placed successfully, False otherwise
        """
        try:
            # Always login before placing bet (this will also initialize browser if needed)
            bet_logger.info("Logging in before placing bet...")
            login_success = self.__do_login_for_account(account)
            if not login_success:
                bet_logger.error("Login failed, cannot place bet")
                return False
            
            bet_logger.info(f"Navigating to betting page: {bet_url}")
            self.open_url(bet_url)
            # Wait for the market content to render instead of using sleep
            try:
                self.__wait_for_market_content(timeout_seconds=15)
            except Exception as e:
                bet_logger.warning(f"Market content not detected within wait window: {e}")
            
            # Find and click the market/outcome
            market_element = self.__get_market_selector(market_type, outcome, points, is_first_half)
            # bet_logger.debug(f"Market element: {market_element}")
            if not market_element:
                bet_logger.error("Could not find market element")
                return False
            
            try:
                bet_logger.info(f"Found market element for: {market_type} - {outcome} - {points}")
                
                # # Verify odds before placing bet
                # try:
                #     # Use more specific selector to find odds within the correct div structure
                #     odds_element = market_element.find_element(By.CSS_SELECTOR, ".has-desc.m-outcome.multiple .odds")
                #     odds_text = odds_element.text.strip()
                #     import re
                #     odds_match = re.search(r'(\d+\.?\d*)', odds_text)
                #     if odds_match:
                #         actual_odds = float(odds_match.group(1))
                #         odds_diff = abs(actual_odds - odds)
                        
                #         if odds_diff > 0.1:  # Allow 0.1 difference
                #             bet_logger.error(f"⚠️ Odds mismatch! Expected: {odds}, Actual: {actual_odds}")
                #             bet_logger.error("Bet cancelled due to odds change")
                #             return False
                #         else:
                #             bet_logger.info(f"✅ Odds verified: {actual_odds} (expected: {odds})")
                # except Exception as e:
                #     bet_logger.error(f"Could not verify odds: {e}")
                
                # Simple direct clicking approach - no scrolling
                try:
                    # Wait for element to be clickable
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(market_element)
                    )
                    
                    # Direct click on the element
                    market_element.click()
                    bet_logger.info(f"Clicked on market: {market_type} - {outcome} - {points}")
                    # time.sleep(2)
                    
                except Exception as click_error:
                    bet_logger.error(f"Direct click failed, trying JavaScript click: {click_error}")
                    
                    # Fallback to JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", market_element)
                        bet_logger.info(f"JavaScript clicked on market: {market_type} - {outcome} - {points}")
                        # time.sleep(2)
                    except Exception as js_error:
                        bet_logger.error(f"JavaScript click also failed: {js_error}")
                        
                        # Last resort: try ActionChains
                        try:
                            actions = ActionChains(self.driver)
                            actions.move_to_element(market_element).click().perform()
                            bet_logger.info(f"ActionChains clicked on market: {market_type} - {outcome} - {points}")
                            # time.sleep(2)
                        except Exception as action_error:
                            bet_logger.error(f"All click methods failed: {action_error}")
                            raise Exception("All click methods failed")
                
            except Exception as e:
                    bet_logger.error(f"Could not click market element: {e}")
                    return False
            
            # Enter stake amount
            try:
                # Use JavaScript to properly handle the stake input
                stake_js_script = """
                const wrapper = document.querySelector('.m-edit-wrap.tw-flex.tw-items-center.tw-justify-end');

                if (wrapper) {
                  // get all input elements and filter by classList instead of using invalid selectors
                  const inputs = wrapper.querySelectorAll('input');
                  const input = Array.from(inputs).find(el => 
                    el.classList.contains('v-input--inner') &&
                    el.classList.contains('tw-box-border') &&
                    el.classList.contains('tw-flex-1')
                  );

                  if (input) {
                    input.value = ''; // clear
                    input.value = arguments[0]; // set new value

                    // dispatch input event to notify frameworks
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    console.log('✅ Input cleared and updated.');
                    return true;
                  } else {
                    console.warn('⚠️ Input not found inside wrapper.');
                    return false;
                  }
                } else {
                  console.warn('⚠️ Wrapper div not found.');
                  return false;
                }
                """
                
                # Execute the JavaScript with the stake value
                result = self.driver.execute_script(stake_js_script, str(10))
                
                if result:
                    bet_logger.info(f"✅ Successfully entered stake: 10 using JavaScript")
                    # time.sleep(1)
                else:
                    bet_logger.error("❌ JavaScript stake input failed, trying fallback methods")
                    
                    # Fallback to Selenium methods if JavaScript fails
                    stake_input = None
                    fallback_selectors = [
                        ".m-edit-wrap input",
                        ".v-input--inner",
                        "input[type='number']",
                        "input[class*='v-input']"
                    ]
                    
                    for selector in fallback_selectors:
                        try:
                            stake_input = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            bet_logger.info(f"Found stake input using fallback selector: {selector}")
                            break
                        except TimeoutException:
                            continue
                    
                    if not stake_input:
                        bet_logger.error("Could not find stake input field")
                        return False
                    
                    # Clear and enter stake with Selenium
                    stake_input.clear()
                    # time.sleep(0.5)
                    stake_input.send_keys(str(10))
                    bet_logger.info(f"Entered stake using Selenium fallback: 10")
                    # time.sleep(1)
                
            except Exception as e:
                bet_logger.error(f"Error entering stake: {e}")
                return False
            
            # Place the bet
            try:
                # Use the specific CSS selector for bet button
                place_bet_button = None
                
                try:
                    place_bet_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.v-button.m-place-btn"))
                    )
                    bet_logger.info("Found place bet button using specific CSS class")
                    
                except Exception as e:
                    bet_logger.error(f"Could not find bet button with specific class: {e}")
                    
                    # Fallback selectors
                    fallback_button_selectors = [
                        ".v-button",
                        ".m-place-btn", 
                        "button[class*='place']",
                        "button[class*='bet']",
                        "//button[@type='submit']",
                        "//button[contains(@class, 'place-bet')]",
                        "//button[contains(@class, 'bet-submit')]",
                        "//button[contains(text(), 'Place Bet')]",
                        "//button[contains(text(), 'Bet')]"
                    ]
                    
                    for selector in fallback_button_selectors:
                        try:
                            if selector.startswith("//"):
                                place_bet_button = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                            else:
                                place_bet_button = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                            bet_logger.info(f"Found bet button using fallback selector: {selector}")
                            break
                        except TimeoutException:
                            continue
                
                if not place_bet_button:
                    bet_logger.error("Could not find place bet button")
                    return False
                
                # Improved scrolling and clicking approach for bet button (same as market selector)
                try:
                    # First, scroll the button into view with some offset to avoid other elements
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var elementRect = element.getBoundingClientRect();
                        var absoluteElementTop = elementRect.top + window.pageYOffset;
                        var middle = absoluteElementTop - (window.innerHeight / 2) + 150;
                        window.scrollTo(0, middle);
                    """, place_bet_button)
                    # time.sleep(1)
                    
                    # Wait for button to be clickable
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(place_bet_button)
                    )
                    
                    # Try JavaScript click if regular click fails
                    try:
                        self.driver.execute_script("arguments[0].click();", place_bet_button)
                        bet_logger.info("JavaScript clicked place bet button")
                        # place_bet_button.click()
                        # bet_logger.info("Clicked place bet button")
                    except Exception as click_error:
                        bet_logger.error(f"Regular click failed, trying JavaScript click: {click_error}")
                        self.driver.execute_script("arguments[0].click();", place_bet_button)
                        bet_logger.info("JavaScript clicked place bet button")
                    
                    # time.sleep(3)
                    
                except Exception as scroll_click_error:
                    bet_logger.error(f"Failed to scroll and click bet button: {scroll_click_error}")
                    
                    # Last resort: try moving to element and clicking
                    try:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(place_bet_button).click().perform()
                        bet_logger.info("ActionChains clicked place bet button")
                        # time.sleep(3)
                    except Exception as action_error:
                        bet_logger.error(f"ActionChains also failed for bet button: {action_error}")
                        raise Exception("All click methods failed for bet button")
                
                # Check for success confirmation
                try:
                    success_selectors = [
                        # "//div[contains(@class, 'bet-success')]",
                        # "//div[contains(@class, 'success-message')]",
                        # "//div[contains(@class, 'success')]",
                        # "//div[contains(text(), 'successful')]",
                        "//div[contains(text(), 'Success')]"
                    ]
                    
                    success_found = False
                    for selector in success_selectors:
                        try:
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            success_found = True
                            break
                        except TimeoutException:
                            continue
                    
                    if success_found:
                        bet_logger.info("✅ Bet placed successfully!")
                        return True
                    else:
                        # Take screenshot of failed bet state
                        try:
                            timestamp = time.strftime("%Y%m%d-%H%M%S")
                            screenshot_path = f"failed_bet_screenshot_{timestamp}.png"
                            self.driver.save_screenshot(screenshot_path)
                            bet_logger.info(f"Failed bet screenshot saved to {screenshot_path}")
                        except Exception as screenshot_error:
                            bet_logger.error(f"Failed to take failed bet screenshot: {screenshot_error}")
                        bet_logger.warning("⚠️ No success confirmation found, bet may have failed")
                        return False
                
                except Exception as e:
                    bet_logger.error(f"Error checking for success confirmation: {e}")
                    return False
                    
            except Exception as e:
                bet_logger.error(f"Error clicking place bet button: {e}")
                return False
                
        except Exception as e:
            # Minimal recovery for Selenium tab crashes
            msg = str(e).lower()
            if ("tab crashed" in msg or "chrome not reachable" in msg or "disconnected" in msg):
                bet_logger.error("Detected browser/tab crash during bet placement. Restarting browser and retrying once...")
                self.__restart_browser(account)
                return self.__place_bet_with_selenium(account, bet_url, market_type, outcome, odds, stake, points, is_first_half, _retry=True)
            
            bet_logger.error(f"Error placing bet with Selenium: {e}")
            # Take screenshot of error state
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshot_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                bet_logger.info(f"Error screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                bet_logger.error(f"Failed to take error screenshot: {screenshot_error}")
            import traceback
            traceback.print_exc()
            return False

    def __get_market_selector(self, market_type, outcome, points=None, is_first_half=False):
        """
        Get the CSS selector for a specific market and outcome on MSport
        
        Parameters:
        - market_type: Type of bet (moneyline, total, spread)
        - outcome: Outcome to bet on
        - points: Points value for total/spread bets
        - is_first_half: Whether this is a first half bet
        
        Returns:
        - Element or None if not found
        """
        market_type_lower = market_type.lower()
        outcome_lower = outcome.lower()
        
        # Handle first half navigation
        if is_first_half:
            # Click halftime button first
            try:
                # Wait for the first half button to be present and clickable
                halftime_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.snap-nav.tw-relative.tw-flex.tw-select-none.tw-whitespace-nowrap li.m-sub-nav-item.snap-nav-item:nth-child(5)"))
                )
                
                # Try regular click first
                try:
                    halftime_button.click()
                    # print("Clicked first half tab")
                except Exception as click_error:
                    bet_logger.error(f"Regular click failed, trying JavaScript click: {click_error}")
                    # Use JavaScript click as fallback
                    self.driver.execute_script("arguments[0].click();", halftime_button)
                    bet_logger.info("JavaScript clicked first half tab")
                
                time.sleep(2)
            except Exception as e:
                bet_logger.error(f"Could not click first half tab: {e}")
                return None
        
        # Get all market rows
        try:
            # Take screenshot before searching for market rows
            try:
                screenshot_path = f"market_search_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                bet_logger.info(f"Market search screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                bet_logger.error(f"Failed to take market search screenshot: {screenshot_error}")
            market_rows = self.driver.find_elements(By.CSS_SELECTOR, ".m-market-row.m-market-row--3")
            if not market_rows:
                bet_logger.warning("No market rows found")
                return None
        except Exception as e:
            bet_logger.error(f"Error finding market rows: {e}")
            return None
        
        # 1X2 (Moneyline) - First div from the list
        if market_type_lower == "moneyline" or market_type_lower == "money_line":
            return self.__find_1x2_outcome(market_rows[0] if market_rows else None, outcome_lower)
        
        # Over/Under
        elif market_type_lower == "total":
            if not points:
                return None
            return self.__find_total_outcome(points, outcome_lower)
        
        # Asian Handicap
        elif market_type_lower == "spread":
            if not points:
                return None
            
            # Check if handicap is 0 - if so, use DNB (Draw No Bet) market instead
            if abs(float(points)) < 0.01:  # Using small threshold for floating point comparison
                bet_logger.warning(f"Handicap is 0, looking for DNB (Draw No Bet) market instead of Asian Handicap")
                return self.__find_dnb_outcome(outcome_lower, is_first_half)
            
            return self.__find_handicap_outcome(points, outcome_lower)
        
        return None
    
    def __find_1x2_outcome(self, market_row, outcome):
        """
        Find the 1X2 outcome element
        
        Parameters:
        - market_row: The market row element for 1X2
        - outcome: 'home', 'draw', or 'away'
        
        Returns:
        - Element or None if not found
        """
        if not market_row:
            bet_logger.warning("No 1X2 market row provided")
            return None
            
        try:
            # Get all outcome divs with class "has-desc m-outcome multiple"
            outcome_divs = market_row.find_elements(By.CSS_SELECTOR, ".has-desc.m-outcome.multiple")
            
            if len(outcome_divs) < 3:
                bet_logger.warning(f"Expected 3 outcomes for 1X2, found {len(outcome_divs)}")
                return None
            
            # Map outcome to index: first=home, second=draw, third=away
            outcome_index = {"home": 0, "draw": 1, "away": 2}
            
            if outcome not in outcome_index:
                bet_logger.error(f"Invalid 1X2 outcome: {outcome}")
                return None
            
            target_div = outcome_divs[outcome_index[outcome]]
            
            # Verify odds by checking inner "odds" class
            try:
                odds_element = target_div.find_element(By.CSS_SELECTOR, ".odds")
                odds_text = odds_element.text.strip()
                bet_logger.info(f"Found 1X2 {outcome} with odds: {odds_text}")
                return target_div
            except Exception as e:
                bet_logger.error(f"Could not find odds in 1X2 outcome: {e}")
                return None
                
        except Exception as e:
            bet_logger.error(f"Error finding 1X2 outcome: {e}")
            return None
    
    def __find_total_outcome(self, target_points, outcome):
        """
        Find the over/under outcome element
        
        Parameters:
        - target_points: Points value to look for
        - outcome: 'over' or 'under'
        
        Returns:
        - Element or None if not found
        """
        try:
            # Get all market specifier divs
            specifier_divs = self.driver.find_elements(By.CSS_SELECTOR, ".m-market-specifier")
            
            if not specifier_divs:
                bet_logger.warning("No market specifier divs found for totals")
                return None
            
            # Use the first one for over/under
            ou_specifier = specifier_divs[0]
            
            # Get all market rows within this specifier
            ou_rows = ou_specifier.find_elements(By.CSS_SELECTOR, ".m-market-row.m-market-row")
            
            for row in ou_rows:
                try:
                    # Check if this row has the target points
                    desc_element = row.find_element(By.CSS_SELECTOR, ".m-outcome.m-outcome-desc span")
                    points_text = desc_element.text.strip()
                    
                    # Extract points value
                    import re
                    match = re.search(r'(\d+\.?\d*)', points_text)
                    if match:
                        row_points = float(match.group(1))
                        
                        # Check if this matches our target points
                        if abs(row_points - float(target_points)) < 0.01:
                            # Found the right row, now get over (first) or under (second) outcome
                            outcome_divs = row.find_elements(By.CSS_SELECTOR, ".m-outcome")
                            
                            # Filter to get only the betting outcomes (not the description one)
                            betting_outcomes = [div for div in outcome_divs if div.find_elements(By.CSS_SELECTOR, ".odds")]
                            
                            if len(betting_outcomes) < 2:
                                bet_logger.warning(f"Expected 2 betting outcomes for totals, found {len(betting_outcomes)}")
                                continue
                            
                            # First is over, second is under
                            target_div = betting_outcomes[0] if outcome == "over" else betting_outcomes[1]
                            
                            # Verify odds
                            try:
                                odds_element = target_div.find_element(By.CSS_SELECTOR, ".odds")
                                odds_text = odds_element.text.strip()
                                bet_logger.info(f"Found total {outcome} {target_points} with odds: {odds_text}")
                                return target_div
                            except Exception as e:
                                bet_logger.error(f"Could not find odds in total outcome: {e}")
                                continue
                                
                except Exception as e:
                    # Row doesn't match, continue to next
                    continue
                    
            bet_logger.warning(f"Could not find total market for {target_points} {outcome}")
            return None
            
        except Exception as e:
            bet_logger.error(f"Error finding total outcome: {e}")
            return None
    
    def __find_handicap_outcome(self, target_points, outcome):
        """
        Find the Asian handicap outcome element
        
        Parameters:
        - target_points: Points value to look for
        - outcome: 'home' or 'away'
        
        Returns:
        - Element or None if not found
        """
        try:
            # Get the handicap market div
            handicap_divs = self.driver.find_elements(By.CSS_SELECTOR, ".m-market-handicap")
            
            if not handicap_divs:
                bet_logger.warning("No handicap market divs found")
                return None
            
            # Use the first (or only) handicap div
            handicap_div = handicap_divs[0]
            
            # Get all market rows within this handicap div
            handicap_rows = handicap_div.find_elements(By.CSS_SELECTOR, ".m-market-row.m-market-row")
            
            for row in handicap_rows:
                try:
                    # Get both home and away outcome divs
                    outcome_divs = row.find_elements(By.CSS_SELECTOR, ".has-desc.m-outcome.multiple")
                    
                    if len(outcome_divs) < 2:
                        bet_logger.warning(f"Expected 2 outcomes for handicap, found {len(outcome_divs)}")
                        continue
                    
                    # First div is home, second is away
                    target_div = outcome_divs[0] if outcome == "home" else outcome_divs[1]
                    
                    # Check the desc to see if it matches our target points
                    try:
                        desc_element = target_div.find_element(By.CSS_SELECTOR, ".desc")
                        desc_text = desc_element.text.strip()
                        
                        # Extract points value from description
                        import re
                        match = re.search(r'([+-]?\d+\.?\d*)', desc_text)
                        if match:
                            row_points = float(match.group(1))
                            
                            # Check if this matches our target points
                            if abs(row_points - float(target_points)) < 0.01:
                                # Verify odds
                                try:
                                    odds_element = target_div.find_element(By.CSS_SELECTOR, ".odds")
                                    odds_text = odds_element.text.strip()
                                    bet_logger.info(f"Found handicap {outcome} {target_points} with odds: {odds_text}")
                                    return target_div
                                except Exception as e:
                                    bet_logger.error(f"Could not find odds in handicap outcome: {e}")
                                    continue
                                    
                    except Exception as e:
                        # Desc doesn't match, continue
                        continue
                        
                except Exception as e:
                    # Row doesn't match, continue to next
                    continue
            
            bet_logger.warning(f"Could not find handicap market for {target_points} {outcome}")
            return None
            
        except Exception as e:
            bet_logger.error(f"Error finding handicap outcome: {e}")
            return None

    def __find_dnb_outcome(self, outcome, is_first_half=False):
        """
        Find the DNB (Draw No Bet) outcome element
        
        Parameters:
        - outcome: 'home' or 'away'
        - is_first_half: Whether this is a first half bet
        
        Returns:
        - Element or None if not found
        """
        try:
            # First, find all market items
            market_items = self.driver.find_elements(By.CSS_SELECTOR, ".m-market-item")
            
            if not market_items:
                bet_logger.warning("No market items found")
                return None
            
            # Look for DNB market item
            dnb_market_item = None
            for market_item in market_items:
                try:
                    # Check the h1 element with the correct class structure
                    h1_element = market_item.find_element(By.CSS_SELECTOR, "h1.m-market-item--name a.tw-flex.tw-items-center span.tw-line-clamp-2")
                    market_name = h1_element.text.strip().lower()
                    
                    # Check if this is DNB market
                    if "dnb" in market_name:
                        # For first half, ensure "1st half" is also present
                        if is_first_half:
                            if "1st half" in market_name:
                                dnb_market_item = market_item
                                bet_logger.info(f"Found first half DNB market: {market_name}")
                                break
                        else:
                            # For normal matches, ensure "1st half" is NOT present
                            if "1st half" not in market_name:
                                dnb_market_item = market_item
                                bet_logger.info(f"Found normal DNB market: {market_name}")
                                break
                except Exception as e:
                    # This market item doesn't have the expected structure, continue to next
                    continue
            
            if not dnb_market_item:
                bet_logger.warning("No DNB market item found")
                return None
            
            # Now get the content div within this market item
            content_div = dnb_market_item.find_element(By.CSS_SELECTOR, ".m-market-item--content")
            
            # Get all outcome divs within this content div
            outcome_divs = content_div.find_elements(By.CSS_SELECTOR, ".has-desc.m-outcome.multiple")
            
            if len(outcome_divs) < 2:
                bet_logger.warning(f"Expected 2 outcomes for DNB, found {len(outcome_divs)}")
                return None
            
            # First div is home, second is away
            target_div = outcome_divs[0] if outcome == "home" else outcome_divs[1]
            
            # Verify odds
            try:
                odds_element = target_div.find_element(By.CSS_SELECTOR, ".odds")
                odds_text = odds_element.text.strip()
                bet_logger.info(f"Found DNB {outcome} with odds: {odds_text}")
                return target_div
            except Exception as e:
                bet_logger.error(f"Could not find odds in DNB outcome: {e}")
                return None
            
        except Exception as e:
            bet_logger.error(f"Error finding DNB outcome: {e}")
            return None

    def __place_bet_with_available_account(self, bet_data):
        """
        Place a bet using all available accounts
        
        Parameters:
        - bet_data: Dictionary with bet information
        
        Returns:
        - True if at least one bet was placed successfully, False otherwise
        """
        try:
            # Get max concurrent bets from config
            max_total_bets = self.__config.get("max_total_concurrent_bets", 5)
            
            # Count total current bets across all accounts
            total_current_bets = sum(account.current_bets for account in self.__accounts)
            
            # Check if we've reached the global limit
            if total_current_bets >= max_total_bets:
                bet_logger.warning(f"Reached global limit of {max_total_bets} concurrent bets. Queuing bet.")
                # Re-add to queue with a delay
                threading.Timer(30.0, lambda: self.__bet_queue.put(bet_data)).start()
                return False
            
            # Track if at least one bet was placed successfully
            any_bet_placed = False
            
            # Find all available accounts and place bets with each
            bet_logger.info(f"Checking {len(self.__accounts)} accounts")
            bet_logger.debug(f"account names: {[account.username for account in self.__accounts]}")

            for account in self.__accounts:
                bet_logger.debug(f"just checking account {account.username}")
            for account in self.__accounts:
                bet_logger.debug(f"Checking account {account.username}")
                if account.can_place_bet():
                    bet_logger.info(f"Account {account.username} can place bet")
                    # Check if login is needed
                    # if account.needs_login():
                    #     try:
                    #         self.__do_login_for_account(account)
                    #     except Exception as e:
                    #         print(f"Failed to login to account {account.username}: {e}")
                    #         continue  # Try next account
                    
                    # Try to place bet with this account
                    account.increment_bets()
                    success = self.__place_bet_with_selenium(
                        account,
                        self.__generate_msport_bet_url(bet_data["event_details"]),
                        bet_data["market_type"],
                        bet_data["outcome"],
                        bet_data["odds"],
                        self.__calculate_stake(bet_data["odds"], bet_data["shaped_data"], account.balance),
                        bet_data["shaped_data"]["category"]["meta"].get("value")
                    )
                    
                    if success:
                        account.decrement_bets()
                        bet_logger.info(f"Bet placed successfully with account {account.username}")
                        any_bet_placed = True
                    else:
                        # If bet failed, decrement the bet counter
                        account.decrement_bets()
                else:
                    bet_logger.debug(f"Account {account.username} cannot place bet")
            
            if not any_bet_placed:
                bet_logger.warning("No available accounts to place bet. Queuing for retry.")
                # Re-add to queue with a delay
                threading.Timer(60.0, lambda: self.__bet_queue.put(bet_data)).start()
                return False
            
            return any_bet_placed
        except Exception as e:
            error_logger.error(f"Error in place_bet_with_available_account: {e}")
            # Close browser on error
            self.cleanup()
            raise

    def __calculate_ev(self, bet_odds, shaped_data):
        """
        Calculate the Expected Value (EV) for a bet
        
        Parameters:
        - bet_odds: The decimal odds offered by MSport
        - shaped_data: The data from Pinnacle with prices
        
        Returns:
        - EV percentage
        """
        line_type = shaped_data["category"]["type"].lower()
        outcome = shaped_data["category"]["meta"]["team"]
        points = shaped_data["category"]["meta"].get("value")
        
        # Determine if this is for first half or full match
        is_first_half = False
        period_key = "num_0"  # Default to full match
        if "periodNumber" in shaped_data and shaped_data["periodNumber"] == "1":
            is_first_half = True
            period_key = "num_1"
            
        # Get the event ID to fetch latest odds from Pinnacle
        event_id = shaped_data.get("eventId")
        
        # Fetch latest odds from Pinnacle API if event ID is available
        latest_prices = self.__fetch_latest_pinnacle_odds(event_id, line_type, points, outcome, period_key)
        
        # If we couldn't get latest odds, fall back to the ones in shaped_data
        if not latest_prices:
            bet_logger.debug("Using odds from original alert as fallback")
            # Get prices from shaped_data based on line type
            if line_type == "money_line":
                # For moneyline, we use home, away, and draw prices
                decimal_prices = {}
                if "priceHome" in shaped_data:
                    decimal_prices["home"] = float(shaped_data["priceHome"])
                if "priceAway" in shaped_data:
                    decimal_prices["away"] = float(shaped_data["priceAway"])
                if "priceDraw" in shaped_data:
                    decimal_prices["draw"] = float(shaped_data["priceDraw"])
                    
            elif line_type == "total":
                # For totals, we map over/under to home/away
                decimal_prices = {}
                if "priceOver" in shaped_data:
                    decimal_prices["home"] = float(shaped_data["priceOver"])  # Over as home
                if "priceUnder" in shaped_data:
                    decimal_prices["away"] = float(shaped_data["priceUnder"])  # Under as away
                    
            elif line_type == "spread":
                # For spread, we use home and away prices
                decimal_prices = {}
                if "priceHome" in shaped_data:
                    decimal_prices["home"] = float(shaped_data["priceHome"])
                if "priceAway" in shaped_data:
                    decimal_prices["away"] = float(shaped_data["priceAway"])
        else:
            # Use the latest prices we fetched
            decimal_prices = latest_prices
            bet_logger.debug(f"Using latest Pinnacle odds: {decimal_prices}")
        
        # Store the prices for later use in stake calculation
        shaped_data["_decimal_prices"] = decimal_prices
        
        # Calculate no-vig prices
        if not decimal_prices:
            bet_logger.debug("No prices found for calculation")
            return -100  # Negative EV as fallback
            
        no_vig_prices = calculate_no_vig_prices(decimal_prices)
        
        # Map outcome to the corresponding key in no_vig_prices
        if line_type == "total":
            # Map over/under to home/away
            outcome_map = {"over": "home", "under": "away"}
            outcome_key = outcome_map.get(outcome.lower(), outcome.lower())
        else:
            outcome_key = outcome.lower()
        
        # Store the outcome key for later use in stake calculation
        shaped_data["_outcome_key"] = outcome_key
        
        # Get the true price using the power method (or choose another method if preferred)
        true_price = no_vig_prices["power"].get(outcome_key)
        
        if not true_price:
            bet_logger.debug(f"No no-vig price found for outcome {outcome_key}")
            return -100  # Negative EV as fallback
            
        # Calculate EV
        ev = calculate_ev(bet_odds, true_price)
        bet_logger.debug(f"Bet odds: {bet_odds}, True price: {true_price}, EV: {ev:.2f}%")
        
        return ev
        
    def __fetch_latest_pinnacle_odds(self, event_id, line_type, points, outcome, period_key):
        """
        Fetch the latest odds from Pinnacle API for a specific event
        
        Parameters:
        - event_id: The Pinnacle event ID
        - line_type: The type of bet (spread, moneyline, total)
        - points: The points value for the bet
        - outcome: The outcome (home, away, draw, over, under)
        - period_key: The period key (num_0 for full match, num_1 for first half)
        
        Returns:
        - Dictionary with the latest decimal prices or None if not found
        """
        if not event_id:
            bet_logger.debug("No event ID provided, cannot fetch latest odds")
            return None
            
        pinnacle_api_host = os.getenv("PINNACLE_HOST")
        if not pinnacle_api_host:
            bet_logger.debug("Pinnacle Events API host not configured")
            return None
            
        # Get proxy from first account if available
        proxies = None
        if self.__accounts and hasattr(self.__accounts[0], 'get_proxies'):
            proxies = self.__accounts[0].get_proxies()
            if proxies:
                bet_logger.debug(f"Using proxy for Pinnacle odds: {self.__accounts[0].proxy}")
            
        try:
            url = f"{pinnacle_api_host}/events/{event_id}"
            bet_logger.debug(f"Fetching latest odds from: {url}")
            
            response = requests.get(url)
            if response.status_code != 200:
                bet_logger.debug(f"Failed to fetch latest odds: HTTP {response.status_code}")
                return None
                
            event_data = response.json()
            if not event_data or "data" not in event_data or not event_data["data"]:
                bet_logger.debug("No data returned from Pinnacle API")
                return None
                
            if event_data["data"] == None or event_data["data"] == "null":
                return None
            
            # Extract the period data
            periods = event_data["data"].get("periods", {})
            period = periods.get(period_key, {})
            
            # Extract the appropriate odds based on line type
            decimal_prices = {}
            
            if line_type == "money_line":
                money_line = period.get("money_line", {})
                if "home" in money_line:
                    decimal_prices["home"] = float(money_line["home"])
                if "away" in money_line:
                    decimal_prices["away"] = float(money_line["away"])
                if "draw" in money_line:
                    decimal_prices["draw"] = float(money_line["draw"])
                    
            elif line_type == "spread":
                spreads = period.get("spreads", {})
                # Find the closest spread to the points value
                closest_spread = None
                min_diff = float('inf')
                
                for spread_key, spread_data in spreads.items():
                    try:
                        spread_points = float(spread_data.get("hdp", 0))
                        diff = abs(float(points) - spread_points)
                        
                        if diff < min_diff:
                            min_diff = diff
                            closest_spread = spread_data
                    except (ValueError, TypeError):
                        continue
                
                if closest_spread:
                    if "home" in closest_spread:
                        decimal_prices["home"] = float(closest_spread["home"])
                    if "away" in closest_spread:
                        decimal_prices["away"] = float(closest_spread["away"])
                    
            elif line_type == "total":
                totals = period.get("totals", {})
                # Find the closest total to the points value
                closest_total = None
                min_diff = float('inf')
                
                for total_key, total_data in totals.items():
                    try:
                        total_points = float(total_data.get("points", 0))
                        diff = abs(float(points) - total_points)
                        
                        if diff < min_diff:
                            min_diff = diff
                            closest_total = total_data
                    except (ValueError, TypeError):
                        continue
                
                if closest_total:
                    if "over" in closest_total:
                        decimal_prices["home"] = float(closest_total["over"])  # Over as home
                    if "under" in closest_total:
                        decimal_prices["away"] = float(closest_total["under"])  # Under as away
            
            return decimal_prices if decimal_prices else None
            
        except Exception as e:
            bet_logger.error(f"Error fetching latest odds: {e}")
            return None

    def __power_method_devig(self, odds_list, max_iter=100, tol=1e-10):
        """
        Devigs a list of decimal odds using the power method.
        Returns the fair probabilities (without the bookmaker's margin).
        
        Parameters:
        - odds_list: List of decimal odds values
        - max_iter: Maximum number of iterations for optimization
        - tol: Tolerance for convergence
        
        Returns:
        - List of fair probabilities
        """
        def implied_probs(power):
            return [o**-power for o in odds_list]

        def objective(power):
            return abs(sum(implied_probs(power)) - 1)

        res = minimize_scalar(objective, bounds=(0.001, 10), method='bounded')
        power = res.x
        probs = implied_probs(power)
        total = sum(probs)
        return [p / total for p in probs]  # normalized
        
    def __kelly_stake(self, prob, odds, bankroll):
        """
        Calculate the optimal stake using the Kelly Criterion
        
        Parameters:
        - prob: Probability of winning
        - odds: Decimal odds
        - bankroll: Available bankroll
        
        Returns:
        - Recommended stake amount (0 if no bet recommended)
        """
        b = odds - 1
        q = 1 - prob
        numerator = (b * prob - q)
        if numerator <= 0:
            return 0  # no bet
        return bankroll * numerator / b
        
    def __round_stake_humanlike(self, stake):
        """
        Round stake to more human-like amounts to avoid detection
        
        Parameters:
        - stake: The calculated stake amount
        
        Returns:
        - Rounded stake that looks more natural
        """
        if stake < 50:
            # For small amounts, round to nearest 5 or 10
            if stake < 20:
                return round(stake / 5) * 5  # Round to nearest 5
            else:
                return round(stake / 10) * 10  # Round to nearest 10
        
        elif stake < 200:
            # For medium amounts (50-200), round to nearest 10 or 25
            if stake < 100:
                return round(stake / 10) * 10  # Round to nearest 10
            else:
                return round(stake / 25) * 25  # Round to nearest 25
        
        elif stake < 1000:
            # For larger amounts (200-1000), round to nearest 50
            return round(stake / 50) * 50
        
        elif stake < 5000:
            # For large amounts (1000-5000), round to nearest 100
            # Examples: 1506 -> 1500, 2453 -> 2500
            return round(stake / 100) * 100
        
        elif stake < 10000:
            # For very large amounts (5000-10000), round to nearest 250
            return round(stake / 250) * 250
        
        else:
            # For extremely large amounts (10000+), round to nearest 500
            return round(stake / 500) * 500

    def __get_stake_limits_for_odds(self, odds):
        """
        Get the appropriate min and max stake limits based on odds
        
        Parameters:
        - odds: The decimal odds for the bet
        
        Returns:
        - Tuple of (min_stake, max_stake)
        """
        # Check if odds fall into any defined range
        for range_name, range_config in self.__odds_based_stakes.items():
            min_odds = range_config.get("min_odds", 0)
            max_odds = range_config.get("max_odds", float('inf'))
            
            # Check if odds fall within this range
            if min_odds <= odds <= max_odds:
                min_stake = range_config.get("min_stake", self.__min_stake)
                max_stake = range_config.get("max_stake", self.__max_stake)
                bet_logger.debug(f"Using {range_name} stake limits for odds {odds:.2f}: min={min_stake}, max={max_stake}")
                return min_stake, max_stake
        
        # If no range matches, use default limits
        bet_logger.debug(f"Using default stake limits for odds {odds:.2f}: min={self.__min_stake}, max={self.__max_stake}")
        return self.__min_stake, self.__max_stake

    def __calculate_stake(self, bet_odds, shaped_data, bankroll):
        """
        Calculate the stake amount based on Kelly criterion
        
        Parameters:
        - bet_odds: The decimal odds offered by MSport
        - shaped_data: The data with prices and outcome information
        
        Returns:
        - Recommended stake amount (rounded to human-like values)
        """
        # Get the stored decimal prices and outcome key
        decimal_prices = shaped_data.get("_decimal_prices", {})
        outcome_key = shaped_data.get("_outcome_key", "")
        
        if not decimal_prices or not outcome_key:
            bet_logger.debug("Missing required data for stake calculation")
            return self.__round_stake_humanlike(10)  # Default stake if calculation not possible
        
        # Extract values into a list for power method
        odds_values = list(decimal_prices.values())
        if not odds_values:
            return self.__round_stake_humanlike(10)  # Default stake
        
        # Calculate fair probabilities using power method
        fair_probs = self.__power_method_devig(odds_values)
        
        # Map the probabilities back to their outcomes
        outcome_probs = {}
        for i, (outcome, _) in enumerate(decimal_prices.items()):
            if i < len(fair_probs):
                outcome_probs[outcome] = fair_probs[i]
        
        # Get the probability for our specific outcome
        if outcome_key not in outcome_probs:
            bet_logger.debug(f"Outcome {outcome_key} not found in probabilities")
            return self.__round_stake_humanlike(10)  # Default stake
            
        outcome_prob = outcome_probs[outcome_key]
        
        
        # Calculate Kelly stake
        full_kelly = self.__kelly_stake(outcome_prob, bet_odds, bankroll)
        
        # Use 30% of Kelly as a more conservative approach
        fractional_kelly = full_kelly * 0.3
        
        # Get odds-based stake limits
        min_stake, max_stake = self.__get_stake_limits_for_odds(bet_odds)
        
        stake = max(min_stake, min(fractional_kelly, max_stake))
        
        # Round to human-like amounts
        rounded_stake = self.__round_stake_humanlike(stake)
        
        bet_logger.debug(f"Probability: {outcome_prob:.4f}, Full Kelly: {full_kelly:.2f}, "
              f"Fractional Kelly (30%): {fractional_kelly:.2f}, Calculated Stake: {stake:.2f}, "
              f"Rounded Stake: {rounded_stake:.2f}")
        
        return rounded_stake

    def notify(self, shaped_data):
        """
        Process the alert from Pinnacle and place a bet if EV is positive
        
        Parameters:
        - shaped_data: The data from Pinnacle shaped according to BetEngine requirements
        """
        try:
            bet_logger.debug(f"Processing alert: {shaped_data}")
            
            # Validate shaped data
            required_fields = ['game', 'category', 'match_type']
            if not all(field in shaped_data for field in required_fields):
                bet_logger.debug("Invalid shaped data format")
                return
                
            # Get necessary information from shaped data
            home_team = shaped_data["game"]["home"]
            away_team = shaped_data["game"]["away"]
            line_type = shaped_data["category"]["type"]
            outcome = shaped_data["category"]["meta"]["team"]
            original_points = shaped_data["category"]["meta"].get("value")
            
            # Get sport ID (1 for soccer, 3 for basketball)
            sport_id = shaped_data.get("sportId", 0)  # Default to soccer if not specified
            
            # Get start time if available
            pinnacle_start_time = shaped_data.get("starts")
            if pinnacle_start_time:
                bet_logger.debug(f"Alert contains start time: {pinnacle_start_time}")
            
            # Determine if this is for first half or full match
            is_first_half = False
            if "periodNumber" in shaped_data and shaped_data["periodNumber"] == "1":
                is_first_half = True
                
            # Step 1: Search for the event on MSport
            bet_logger.debug(f"Searching for event: {home_team} vs {away_team}")
            event_id = self.__search_event(home_team, away_team, pinnacle_start_time)
            if not event_id:
                bet_logger.debug("Event not found, cannot place bet")
                return
                
            # Step 2: Get event details
            bet_logger.debug(f"Getting event details for event: {event_id}")
            event_details = self.__get_event_details(event_id)
            if not event_details:
                bet_logger.debug("Could not get event details, cannot place bet")
                return
                
            # Step 3: Find the market for the bet
            bet_logger.debug(f"Finding market for bet: {line_type} {outcome} {original_points}")
            bet_code, bet_odds, adjusted_points = self.__find_market_bet_code_with_points(
                event_details, 
                line_type, 
                original_points, 
                outcome, 
                is_first_half,
                sport_id,
                home_team,
                away_team
            )
            
            if not bet_code or not bet_odds:
                bet_logger.debug("Could not find appropriate market, cannot place bet")
                return
                
            # Create a modified shaped_data with the adjusted points
            modified_shaped_data = shaped_data.copy()
            modified_shaped_data["category"]["meta"]["value"] = adjusted_points
            bet_logger.debug(f"Using adjusted points: {adjusted_points} (original was: {original_points})")
            
            # Step 4: Calculate EV with the adjusted points
            bet_logger.debug(f"Calculating EV with adjusted points: {adjusted_points}")
            ev = self.__calculate_ev(bet_odds, modified_shaped_data)
            
            # Log the current bet placement mode
            placement_mode = self.get_bet_placement_mode()
            bet_logger.info(f"Processing bet with {placement_mode} placement mode - EV: {ev:.2%}")
            
            # Check if EV meets minimum threshold
            if ev < self.__min_ev:
                bet_logger.info(f"EV {ev} below minimum threshold {self.__min_ev}, skipping bet")
                return False
            
            # Check Pinnacle odds for the specific outcome before placing bet
            decimal_prices = modified_shaped_data.get("_decimal_prices", {})
            outcome_key = modified_shaped_data.get("_outcome_key", "")
            if bet_odds > self.__max_pinnacle_odds:
                bet_logger.debug(f"Pinnacle odds ({bet_odds:.2f}) are above {self.__max_pinnacle_odds} threshold, not placing bet")
                return False
            else: 
                bet_logger.debug(f"Pinnacle odds check passed: {bet_odds:.2f} <= {self.__max_pinnacle_odds}")
            
            # Step 5: Place bet if EV is positive and above threshold
            bet_logger.debug(f"EV: {ev:.2f}%")
            if ev > self.__min_ev:
                bet_logger.debug(f"Positive EV ({ev:.2f}%), placing bet")
                
                # Queue the bet for placement
                success = self.__place_bet(
                    event_details, 
                    line_type, 
                    outcome, 
                    bet_odds, 
                    modified_shaped_data
                )
                
                if success:
                    bet_logger.debug(f"Successfully queued bet on {home_team} vs {away_team} - {line_type} {outcome} {adjusted_points}")
                else:
                    bet_logger.debug("Failed to queue bet")
            else:
                bet_logger.debug(f"Negative or insufficient EV ({ev:.2f}%), not placing bet")
                
            return ev > self.__min_ev
        except Exception as e:
            bet_logger.error(f"Error in notify method: {e}")
            # Close browser on error
            self.cleanup()
            raise

    def __find_market_bet_code_with_points(self, event_details, line_type, points, outcome, is_first_half=False, sport_id=1, home_team=None, away_team=None):
        """
        Find the appropriate bet code in the MSport event details and return the adjusted points value
        
        Parameters:
        - event_details: The event details from MSport
        - line_type: The type of bet (spread, moneyline, total)
        - points: The points value for the bet
        - outcome: The outcome (home, away, draw, over, under)
        - is_first_half: Whether the bet is for the first half
        - sport_id: The sport ID (1 for soccer, 3 for basketball)
        
        Returns:
        - Tuple of (bet_code, odds, adjusted_points)
        """
        bet_logger.debug(f"sport id {sport_id}")
        bet_logger.debug(f"Finding market for Game: {home_team} vs {away_team}: {line_type} - {outcome} - {points} - First Half: {is_first_half} - Sport: {'Basketball' if sport_id == 3 or sport_id == "3" else 'Soccer'}")
        
        if "markets" not in event_details:
            bet_logger.debug("No markets found in event details")
            return None, None, None

        markets = event_details["markets"]
        
        # Use different market names based on sport
        is_basketball = (sport_id == "3" or sport_id == 3)
        bet_logger.debug(f"is basketball: {is_basketball}")
        
        # Determine the correct market descriptions based on is_first_half
        if is_first_half:
            # First half market descriptions
            moneyline_market = "1st half - 1x2"
            total_market = "1st half - o/u"
            spread_market = "1st half - asian handicap"
            dnb_market = "1st half - dnb"
        else:
            # Full match market descriptions
            moneyline_market = "1x2"
            total_market = "over/under"
            spread_market = "asian handicap"
            dnb_market = "dnb"
        
        odds_logger.info(f"Looking for markets: moneyline='{moneyline_market}', total='{total_market}', spread='{spread_market}', dnb='{dnb_market}'")

        # Handle MONEYLINE bets (1X2 in MSport)
        if line_type.lower() == "money_line":
            # Find 1x2 market
            for market in markets:
                market_desc = market.get("description", "").lower()
                # print(f"Checking market: '{market_desc}' against target: '{moneyline_market.lower()}'")
                
                if market_desc == moneyline_market.lower():
                    # Map outcome to MSport format
                    outcome_map = {"home": "1", "away": "3", "draw": "2"}
                    if outcome.lower() not in outcome_map:
                        bet_logger.debug(f"Invalid outcome for moneyline: {outcome}")
                        continue
                        
                    target_outcome_id = outcome_map[outcome.lower()]
                    
                    # Find matching outcome
                    for market_outcome in market.get("outcomes", []):
                        if market_outcome.get("id") == target_outcome_id:
                            bet_logger.debug(f"Found moneyline market: {market['description']} outcome {target_outcome_id} with odds {market_outcome['odds']}")
                            return market_outcome["id"], float(market_outcome["odds"]), None
            
            bet_logger.debug(f"No matching moneyline market found for {outcome}")
            return None, None, None
            
        # Handle TOTAL bets (Over/Under in MSport)
        elif line_type.lower() == "total":
            # Map outcome to MSport format
            outcome_map = {"over": "12", "under": "13"}
            if outcome.lower() not in outcome_map:
                bet_logger.debug(f"Invalid outcome for total: {outcome}")
                return None, None, None
                
            target_outcome_id = outcome_map[outcome.lower()]
            original_points = float(points)
            
            # Round to nearest 0.5 increment first (e.g., 1.25 -> 1.5, 1.3 -> 1.5, 1.7 -> 1.5)
            rounded_points = round(original_points * 2) / 2
            bet_logger.debug(f"Original points: {original_points}, Rounded to nearest 0.5: {rounded_points}")
            
            # Generate alternate lines to search for (4 steps up and down with 0.5 increments)
            alternate_points = []
            
            # Add rounded target first
            alternate_points.append(rounded_points)
            
            # Add 4 steps upward (0.5, 1.0, 1.5, 2.0 higher)
            for i in range(1, 5):
                alternate_points.append(rounded_points + (i * 0.5))
            
            # Add 4 steps downward (0.5, 1.0, 1.5, 2.0 lower), but not below 0
            for i in range(1, 5):
                lower_point = rounded_points - (i * 0.5)
                if lower_point >= 0:  # Don't go below 0
                    alternate_points.append(lower_point)
            
            bet_logger.debug(f"Searching for total points in order: {alternate_points}")
            
            # Find Over/Under markets and look for the closest points from our alternate list
            best_match = None
            best_diff = float('inf')
            
            for market in markets:
                market_desc = market.get("description", "").lower()
                # print(f"Checking market: '{market_desc}' against target: '{total_market.lower()}'")
                
                if market_desc == total_market.lower():
                    for market_outcome in market.get("outcomes", []):
                        outcome_desc = market_outcome.get("description", "")
                        outcome_id = market_outcome.get("id")
                        
                        # Check if this outcome matches our target (over/under)
                        if outcome_id == target_outcome_id:
                            # Extract points from description (e.g., "Over 2.5" -> 2.5)
                            try:
                                if "over" in outcome_desc.lower():
                                    market_points = float(outcome_desc.lower().replace("over", "").strip())
                                elif "under" in outcome_desc.lower():
                                    market_points = float(outcome_desc.lower().replace("under", "").strip())
                                else:
                                    continue
                                
                                # Check if this market point is in our alternate points list
                                for alt_point in alternate_points:
                                    diff = abs(market_points - alt_point)
                                    if diff < 0.01:  # Match found (allowing for floating point precision)
                                        # Calculate priority based on distance from original target
                                        priority_diff = abs(market_points - original_points)
                                        
                                        if priority_diff < best_diff:
                                            best_diff = priority_diff
                                            best_match = {
                                                "id": outcome_id,
                                                "odds": float(market_outcome["odds"]),
                                                "points": market_points,
                                                "description": outcome_desc
                                            }
                                        break  # Found match in alternate points, move to next outcome
                                    
                            except (ValueError, AttributeError):
                                continue
            
            if best_match:
                if best_match["points"] != original_points:
                    bet_logger.debug(f"Exact total {original_points} not found, using closest: {best_match['points']}")
                bet_logger.debug(f"Found total market: {best_match['description']} with odds {best_match['odds']}")
                return best_match["id"], best_match["odds"], best_match["points"]
            
            bet_logger.debug(f"No matching total market found for {points} {outcome} or alternate lines")
            return None, None, None
            
        # Handle SPREAD bets (Asian Handicap in MSport)
        elif line_type.lower() == "spread":
            original_points = float(points)
            
            # Check if handicap is 0 - if so, use DNB (Draw No Bet) market instead
            if abs(original_points) < 0.01:  # Using small threshold for floating point comparison
                bet_logger.debug(f"Handicap is 0, looking for DNB (Draw No Bet) market instead of Asian Handicap")
                
                # Map outcome to MSport format for DNB (based on actual API structure)
                outcome_map = {"home": "4", "away": "5"}
                if outcome.lower() not in outcome_map:
                    bet_logger.debug(f"Invalid outcome for DNB: {outcome}")
                    return None, None, None
                    
                target_outcome_id = outcome_map[outcome.lower()]
                
                # Look for DNB market
                dnb_market_name = dnb_market
                
                for market in markets:
                    market_desc = market.get("description", "").lower()
                    # print(f"Checking market: '{market_desc}' against target: '{dnb_market_name}'")
                    
                    if market_desc == dnb_market_name:
                        # Find matching outcome
                        for market_outcome in market.get("outcomes", []):
                            if market_outcome.get("id") == target_outcome_id:
                                bet_logger.debug(f"Found DNB market: {market['description']} outcome {target_outcome_id} with odds {market_outcome['odds']}")
                                return market_outcome["id"], float(market_outcome["odds"]), 0.0  # Return 0.0 as adjusted points
                
                bet_logger.debug(f"No matching DNB market found for {outcome}")
                return None, None, None
            
            # Original Asian Handicap logic for non-zero handicaps
            # Map outcome to MSport format for Asian Handicap
            outcome_map = {"home": "1714", "away": "1715"}
            if outcome.lower() not in outcome_map:
                bet_logger.debug(f"Invalid outcome for handicap: {outcome}")
                return None, None, None
                
            target_outcome_id = outcome_map[outcome.lower()]
            
            # Round to nearest 0.5 increment first (e.g., -0.25 -> -0.5, +1.3 -> +1.5, -1.7 -> -1.5)
            rounded_points = round(original_points * 2) / 2
            bet_logger.debug(f"Original handicap: {original_points}, Rounded to nearest 0.5: {rounded_points}")
            
            # Generate alternate handicap lines to search for (4 steps in each direction with 0.5 increments)
            alternate_points = []
            
            # Add rounded target first
            alternate_points.append(rounded_points)
            
            # Add 4 steps in positive direction (towards 0 if negative, away from 0 if positive)
            if rounded_points < 0:
                # For negative handicaps, go towards 0 (less negative)
                for i in range(1, 5):
                    new_point = rounded_points + (i * 0.5)
                    if new_point <= 0:  # Don't cross zero for negative handicaps
                        alternate_points.append(new_point)
            else:
                # For positive handicaps, go away from 0 (more positive)
                for i in range(1, 5):
                    alternate_points.append(rounded_points + (i * 0.5))
            
            # Add 4 steps in negative direction (away from 0 if negative, towards 0 if positive)
            if rounded_points < 0:
                # For negative handicaps, go away from 0 (more negative)
                for i in range(1, 5):
                    alternate_points.append(rounded_points - (i * 0.5))
            else:
                # For positive handicaps, go towards 0 (less positive)
                for i in range(1, 5):
                    new_point = rounded_points - (i * 0.5)
                    if new_point >= 0:  # Don't cross zero for positive handicaps
                        alternate_points.append(new_point)
            
            bet_logger.debug(f"Searching for handicap points in order: {alternate_points}")
            
            # Find Asian Handicap markets and look for the closest points from our alternate list
            best_match = None
            best_diff = float('inf')
            
            for market in markets:
                market_desc = market.get("description", "").lower()
                # print(f"Checking market: '{market_desc}' against target: '{spread_market.lower()}'")
                
                if market_desc == spread_market.lower():
                    for market_outcome in market.get("outcomes", []):
                        outcome_desc = market_outcome.get("description", "")
                        outcome_id = market_outcome.get("id")
                        
                        # Check if this outcome matches our target (home/away)
                        if outcome_id == target_outcome_id:
                            # Extract points from description (e.g., "Home (-0.5)" -> -0.5, "Away (+1.5)" -> 1.5)
                            try:
                                import re
                                match = re.search(r'[(\[]([+-]?\d+\.?\d*)[)\]]', outcome_desc)
                                if match:
                                    market_points = float(match.group(1))
                                    display_points = market_points
                                    
                                    # Check if this market point is in our alternate points list
                                    for alt_point in alternate_points:
                                        diff = abs(display_points - alt_point)
                                        if diff < 0.01:  # Match found (allowing for floating point precision)
                                            # Calculate priority based on distance from original target
                                            priority_diff = abs(display_points - original_points)
                                            
                                            if priority_diff < best_diff:
                                                best_diff = priority_diff
                                                best_match = {
                                                    "id": outcome_id,
                                                    "odds": float(market_outcome["odds"]),
                                                    "points": display_points,
                                                    "description": outcome_desc
                                                }
                                            break  # Found match in alternate points, move to next outcome
                                        
                            except (ValueError, AttributeError):
                                continue
            
            if best_match:
                if best_match["points"] != original_points:
                    bet_logger.debug(f"Exact handicap {original_points} not found, using closest: {best_match['points']}")
                bet_logger.debug(f"Found handicap market: {best_match['description']} with odds {best_match['odds']}")
                return best_match["id"], best_match["odds"], best_match["points"]
            
            bet_logger.debug(f"No matching handicap market found for {points} {outcome} or alternate lines")
            return None, None, None
        
        else:
            bet_logger.debug(f"Unsupported line type: {line_type}")
            return None, None, None
            
    def __extract_points_from_key(self, key):
        """Extract points value from a bet key"""
        try:
            # For totals: S_OU@2.5_O or S_OU1T@2.5_O
            # For spreads: S_1X2HND@2_1H or S_1X2HND1T@2_1H
            parts = key.split('@')
            if len(parts) < 2:
                return None
                
            # The points should be between '@' and '_'
            points_part = parts[1].split('_')[0]
            return float(points_part)
        except (ValueError, IndexError):
            return None

    def cleanup(self):
        """Close browser and clean up resources"""
        if self.__browser_open and self.__browser_initialized:
            try:
                bet_logger.debug("Closing browser...")
                self.close_browser()
                self.__browser_open = False
                bet_logger.debug("Browser closed successfully")
            except Exception as e:
                bet_logger.error(f"Error closing browser: {e}")
        
        # Reset browser state so it can be reinitialized when needed
        self.__browser_initialized = False
        self.__browser_open = False
                
    def __del__(self):
        """Destructor to ensure browser is closed when object is garbage collected"""
        self.cleanup()

    def __place_bet(self, event_details, line_type, outcome, odds, modified_shaped_data):
        """
        Place a bet on MSport
        
        Parameters:
        - event_details: Event details from MSport
        - line_type: Type of bet (money_line, total, spread)
        - outcome: Outcome to bet on
        - odds: The decimal odds for the bet
        - modified_shaped_data: The modified shaped data for the bet
        
        Returns:
        - True if bet was placed/queued successfully
        """
        # Check if immediate bet placement is enabled
        immediate_placement = self.__config.get("immediate_bet_placement", True)
        
        if immediate_placement:
            bet_logger.info(f"Placing MSport bet immediately: {line_type} - {outcome} with odds {odds}")
            
            # Create bet data
            bet_data = {
                "event_details": event_details,
                "market_type": line_type,
                "outcome": outcome,
                "odds": odds,
                "shaped_data": modified_shaped_data,
                "timestamp": time.time()
            }
            
            # Place bet immediately
            try:
                result = self.__place_bet_with_available_account(bet_data)
                if result:
                    bet_logger.info("Bet placed successfully")
                else:
                    bet_logger.warning("Bet placement failed")
                return result
            except Exception as e:
                error_logger.error(f"Error placing bet immediately: {e}")
                return False
        else:
            bet_logger.info(f"Queueing MSport bet: {line_type} - {outcome} with odds {odds}")
            
            # Add bet to queue
            bet_data = {
                "event_details": event_details,
                "market_type": line_type,
                "outcome": outcome,
                "odds": odds,
                "shaped_data": modified_shaped_data,
                "timestamp": time.time()
            }
            
            self.__bet_queue.put(bet_data)
            return True  # Return True as the bet was queued successfully

    def __find_market_bet_code(self, event_details, line_type, points, outcome, is_first_half=False, sport_id=1, home_team=None, away_team=None):
        """
        DEPRECATED: Use __find_market_bet_code_with_points instead
        This method is kept for backward compatibility.
        
        Find the appropriate bet code in the MSport event details
        
        Parameters:
        - event_details: The event details from MSport
        - line_type: The type of bet (spread, moneyline, total)
        - points: The points value for the bet
        - outcome: The outcome (home, away, draw, over, under)
        - is_first_half: Whether the bet is for the first half
        - sport_id: The sport ID (1 for soccer, 3 for basketball)
        - home_team: Home team name (for logging)
        - away_team: Away team name (for logging)
        
        Returns:
        - Tuple of (bet_code, odds)
        """
        # Forward to the new method and discard the adjusted points
        bet_code, odds, _ = self.__find_market_bet_code_with_points(
            event_details, line_type, points, outcome, is_first_half, sport_id, home_team, away_team
        )
        return bet_code, odds

    def refresh_account_balances(self):
        """
        Refresh account balances for all accounts that have valid cookies
        
        Returns:
        - Dictionary with account usernames and their updated balances
        """
        balance_updates = {}
        
        for account in self.__accounts:
            if account.cookie_jar:
                try:
                    old_balance = account.balance
                    new_balance = self.__fetch_account_balance(account)
                    account.balance = new_balance
                    balance_updates[account.username] = {
                        "old_balance": old_balance,
                        "new_balance": new_balance,
                        "change": new_balance - old_balance
                    }
                    bet_logger.debug(f"Balance updated for {account.username}: {old_balance:.2f} -> {new_balance:.2f} (change: {new_balance - old_balance:+.2f})")
                except Exception as e:
                    bet_logger.error(f"Failed to refresh balance for {account.username}: {e}")
                    balance_updates[account.username] = {
                        "error": str(e)
                    }
            else:
                bet_logger.debug(f"No valid cookies for {account.username}, skipping balance refresh")
                
        return balance_updates

    def search_event(self, home_team, away_team, pinnacle_start_time=None):
        """
        Public method to search for an event on MSport
        
        Parameters:
        - home_team: Home team name
        - away_team: Away team name
        - pinnacle_start_time: Start time from Pinnacle in milliseconds (unix timestamp)
        
        Returns:
        - event ID if found, None otherwise
        """
        return self.__search_event(home_team, away_team, pinnacle_start_time)
    
    def get_event_details(self, event_id):
        """
        Public method to get detailed information about an event from MSport
        
        Parameters:
        - event_id: The event ID to get details for
        
        Returns:
        - Event details dictionary or None if not found
        """
        return self.__get_event_details(event_id)
    
    def generate_msport_bet_url(self, event_details):
        """
        Public method to generate MSport betting URL based on event details
        
        Parameters:
        - event_details: Event details dictionary
        
        Returns:
        - Betting URL string or None if generation fails
        """
        return self.__generate_msport_bet_url(event_details)
    
    def find_market_bet_code_with_points(self, event_details, line_type, points, outcome, is_first_half=False, sport_id=1, home_team=None, away_team=None):
        """
        Public method to find the appropriate bet code in the MSport event details
        
        Parameters:
        - event_details: The event details from MSport
        - line_type: The type of bet (spread, moneyline, total)
        - points: The points value for the bet
        - outcome: The outcome (home, away, draw, over, under)
        - is_first_half: Whether the bet is for the first half
        - sport_id: The sport ID (1 for soccer, 3 for basketball)
        - home_team: Home team name (for logging)
        - away_team: Away team name (for logging)
        
        Returns:
        - Tuple of (bet_code, odds, adjusted_points)
        """
        return self.__find_market_bet_code_with_points(event_details, line_type, points, outcome, is_first_half, sport_id, home_team, away_team)

    def test_direct_bet_placement(self):
        """
        Test function to directly test bet placement with real event data
        This bypasses the normal alert flow and tests the CSS selector system
        
        NEW: Now supports DNB (Draw No Bet) market when handicap is 0
        """
        bet_logger.debug("=== Testing Direct Bet Placement ===")
        
        # Example test data - modify these values as needed
        test_data = {
            "game": {
                "home": "Chelsea",  # Changed to more common teams
                "away": "Arsenal"
            },
            "category": {
            "type": "spread",  # Changed from "moneyline" to "spread" for handicap
            "meta": {
                    "team": "home",  # for handicap: "home" or "away"
                    "value": "-0.5"  # handicap value (e.g., "-0.5", "+1.5", "-1.0")
                }
            },
            "match_type": "test",
            "sportId": 1,  # 1 for soccer, 3 for basketball
            "starts": None  # can add start time in milliseconds if needed
        }
        
        bet_logger.debug(f"Testing DNB market with handicap 0: {test_data['category']['meta']['value']}")
        
        try:
            # Step 1: Search for the event
            bet_logger.debug(f"\n1. Searching for event: {test_data['game']['home']} vs {test_data['game']['away']}")
            event_id = self.search_event(
                test_data["game"]["home"], 
                test_data["game"]["away"], 
                test_data.get("starts")
            )
            
            if not event_id:
                bet_logger.debug("❌ Event not found")
                return False
            
            bet_logger.debug(f"✅ Found event ID: {event_id}")
            
            # Step 2: Get event details
            bet_logger.debug(f"\n2. Getting event details...")
            event_details = self.get_event_details(event_id)
            
            if not event_details:
                print("❌ Could not get event details")
                return False
                
            print(f"✅ Got event details for: {event_details.get('homeTeam')} vs {event_details.get('awayTeam')}")
            
            # Step 3: Generate betting URL
            print(f"\n3. Generating betting URL...")
            bet_url = self.generate_msport_bet_url(event_details)
            
            if not bet_url:
                print("❌ Could not generate betting URL")
                return False
                
            print(f"✅ Generated URL: {bet_url}")
            
            # Step 4: Find market (this tests the new CSS selector system)
            print(f"\n4. Testing market finder...")
            line_type = test_data["category"]["type"]
            outcome = test_data["category"]["meta"]["team"]
            points = test_data["category"]["meta"].get("value")
            sport_id = test_data.get("sportId", 1)
            
            bet_code, odds, adjusted_points = self.find_market_bet_code_with_points(
                event_details,
                line_type,
                points,
                outcome,
                is_first_half=False,
                sport_id=sport_id,
                home_team=test_data["game"]["home"],
                away_team=test_data["game"]["away"]
            )
            
            if not bet_code or not odds:
                print("❌ Could not find market")
                return False
                
            print(f"✅ Found market: {bet_code} with odds {odds}")
            if adjusted_points is not None:
                print(f"   Adjusted points: {adjusted_points}")
            
            # Step 5: Test CSS selector system (without actually placing bet)
            print(f"\n5. Testing CSS selector system...")
            
            # Navigate to the betting page first
            self._initialize_browser_if_needed(test_data["accounts"][0])
            print(f"Navigating to: {bet_url}")
            self.open_url(bet_url)
            time.sleep(5)
            
            # Test the new selector system
            market_element = self.__get_market_selector(line_type, outcome, points, is_first_half=False)
            
            if market_element:
                print("✅ CSS selector system found market element!")
                
                # Try to get odds from the element to verify it's working
                try:
                    odds_element = market_element.find_element(By.CSS_SELECTOR, ".odds")
                    odds_text = odds_element.text.strip()
                    print(f"   Element odds: {odds_text}")
                    
                    # Test scrolling and element positioning (but don't click)
                    print("   Testing element positioning...")
                    
                    # Use the same improved scrolling logic
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var elementRect = element.getBoundingClientRect();
                        var absoluteElementTop = elementRect.top + window.pageYOffset;
                        var middle = absoluteElementTop - (window.innerHeight / 2) + 100;
                        window.scrollTo(0, middle);
                    """, market_element)
                    # time.sleep(2)
                    
                    # Check if element is now in viewport and clickable
                    element_rect = self.driver.execute_script("""
                        var element = arguments[0];
                        var rect = element.getBoundingClientRect();
                        return {
                            top: rect.top,
                            bottom: rect.bottom,
                            left: rect.left,
                            right: rect.right,
                            visible: rect.top >= 0 && rect.bottom <= window.innerHeight
                        };
                    """, market_element)
                    
                    print(f"   Element position: top={element_rect['top']:.1f}, visible={element_rect['visible']}")
                    
                    if element_rect['visible'] and element_rect['top'] > 50:  # Ensure it's not covered by header
                        print("✅ Element is properly positioned and clickable!")
                    else:
                        print("⚠️  Element positioning may have issues")
                    
                    print("✅ Successfully tested CSS selector system!")
                    print("⚠️  Test completed without placing actual bet (safety measure)")
                    
                except Exception as e:
                    print(f"⚠️  Found element but couldn't extract odds: {e}")
                    
            else:
                print("❌ CSS selector system could not find market element")
                return False
            
            print(f"\n=== Test Summary ===")
            print(f"Event: {test_data['game']['home']} vs {test_data['game']['away']}")
            print(f"Market: {line_type} - {outcome}")
            if points:
                print(f"Points: {points}")
            print(f"Status: CSS selectors working ✅")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            self.cleanup()

    def get_bet_placement_mode(self):
        """
        Get the current bet placement mode
        
        Returns:
        - 'immediate' if bets are placed immediately
        - 'queued' if bets are queued for later placement
        """
        immediate_placement = self.__config.get("immediate_bet_placement", True)
        return "immediate" if immediate_placement else "queued"
    
    def set_bet_placement_mode(self, immediate=True):
        """
        Set the bet placement mode
        
        Parameters:
        - immediate: True for immediate placement, False for queued placement
        """
        self.__config["immediate_bet_placement"] = immediate
        mode = "immediate" if immediate else "queued"
        bet_logger.info(f"Bet placement mode changed to: {mode}")
        
        # Save config to file if it exists
        try:
            with open("config.json", "w") as f:
                json.dump(self.__config, f, indent=4)
            bet_logger.info("Configuration saved to config.json")
        except Exception as e:
            error_logger.error(f"Failed to save configuration: {e}")
    
    def get_queue_size(self):
        """
        Get the current size of the bet queue
        
        Returns:
        - Number of bets in the queue
        """
        return self.__bet_queue.qsize()
    
    def clear_bet_queue(self):
        """
        Clear all bets from the queue
        
        Returns:
        - Number of bets that were cleared
        """
        cleared_count = 0
        while not self.__bet_queue.empty():
            try:
                self.__bet_queue.get_nowait()
                self.__bet_queue.task_done()
                cleared_count += 1
            except queue.Empty:
                break
        
        bet_logger.info(f"Cleared {cleared_count} bets from queue")
        return cleared_count

if __name__ == "__main__":
    """Main Application
    
    NEW FEATURE: Now supports DNB (Draw No Bet) market when handicap is 0
    - When handicap points is 0, the system will look for DNB market instead of Asian Handicap
    - DNB market has only 2 outcomes: Home and Away (no Draw)
    - This provides better odds for matches where a draw is unlikely
    """
    bet_engine = BetEngine(
        headless=os.getenv("ENVIRONMENT") == "production",
        config_file="config.json"
    )
    
    # Run the test function instead of the old test
    bet_engine.test_direct_bet_placement()