from selenium_script import WebsiteOpener
import os
import time
import json
import re
import requests
import dotenv
import threading
import queue
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.calculate_no_vig_prices import calculate_no_vig_prices
from utils.calculate_ev import calculate_ev
from scipy.optimize import minimize_scalar
import math

dotenv.load_dotenv()

class BetAccount:
    """
    Represents a single Bet9ja account with its own login credentials and cookie jar
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
        return (self.active and 
                self.cookie_jar is not None and 
                self.current_bets < self.max_concurrent_bets and
                self.balance >= self.min_balance)
        
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
    Handles the bet placement process on Bet9ja, including:
    - Searching for matches
    - Finding the right market
    - Calculating EV
    - Placing bets with positive EV
    """
    
    def __init__(self, headless=os.getenv("ENVIRONMENT")=="production", 
                 bet_host=os.getenv("BETNAIJA_HOST"), 
                 bet_api_host=os.getenv("BETNAIJA_API_HOST"),
                 min_ev=float(os.getenv("MIN_EV", "0")),
                 config_file="config.json"):
        print(f"Initializing BetEngine with min_ev: {min_ev}")
        # Only initialize browser if needed for certain operations
        self.__browser_initialized = False
        self.__browser_open = False
        self.__headless = headless
        print(f"BetEngine initialized with headless: {headless}")
        self.__bet_api_host = bet_api_host
        self.__bet_host = bet_host
        self.__min_ev = min_ev
        self.__accounts = []
        self.__bet_queue = queue.Queue()
        self.__load_config(config_file)
        self.__setup_accounts()
        self.__start_bet_worker()
        
    def _initialize_browser_if_needed(self):
        """Initialize the browser if it hasn't been initialized yet"""
        if not self.__browser_initialized:
            super().__init__(self.__headless)
            self.__browser_initialized = True
            self.__browser_open = True
            print("Browser initialized")
        
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
                
                
            print(f"Loaded configuration from {config_file}")
        except Exception as e:
            print(f"Error loading config file: {e}")
            # Create default config
            self.__config = {
                "accounts": [],
                "max_total_concurrent_bets": 5,
                "use_proxies": False,  # Global flag to enable/disable proxies
                "bet_settings": {
                    "min_ev": self.__min_ev,
                    "kelly_fraction": 0.3,
                    "min_stake": 10,
                    "max_stake": 1000000,
                    "bankroll": 1000
                }
            }
            
    def __setup_accounts(self):
        """Initialize bet accounts from config"""
        # First, set up at least one account from environment variables if available
        env_username = os.getenv("BETNAIJA_USERNAME")
        env_password = os.getenv("BETNAIJA_PASSWORD")
        
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
                print(f"Added account: {account_data.get('username')}")
                
        # Ensure we have at least one account
        if not self.__accounts:
            raise ValueError("No betting accounts configured. Please set BETNAIJA_USERNAME and BETNAIJA_PASSWORD environment variables or configure accounts in config.json")
            
        print(f"Set up {len(self.__accounts)} betting accounts")
        
        # Login to the first account for search functionality
        if self.__accounts:
            self.__do_login_for_account(self.__accounts[0])
            self.__do_login_for_account(self.__accounts[1])

            
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
                print(f"Error in bet worker thread: {e}")
                
            # Small sleep to prevent CPU hogging
            time.sleep(0.1)

    def __do_login(self):
        """Log in to Bet9ja website with the first account (for search functionality)"""
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
                        print(f"✅ Using proxy - Current IP address: {ip_address} {account.username} {account.proxy}")
                    else:
                        print(f"Current IP address (no proxy): {ip_address}")
                    return ip_address
            print("Failed to get IP address")
            return None
        except Exception as e:
            print(f"Error checking IP address: {e}")
            return None
            
    def __do_login_for_account(self, account):
        """Log in to Bet9ja website with a specific account using API"""
        print(f"Logging in to Bet9ja with account: {account.username}")
        
        if not account.username or not account.password:
            raise ValueError("Bet9ja username or password not found for account")
        
        try:
            # Prepare login data as form-data
            login_data = {
                'username': account.username,
                'password': account.password
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Get proxies if configured
            proxies = account.get_proxies()
            if proxies:
                print(f"Using proxy for login: {account.proxy} {account.username}")
                # Check IP with proxy
                self.__check_ip_address(using_proxy=True, proxy_url=proxies, account=account)
            else:
                # Check IP without proxy
                self.__check_ip_address(using_proxy=False, account=account)
            
            # Make the login request
            login_url = f"{self.__bet_host}/desktop/feapi/AuthAjax/Login?v_cache_version=1.276.0.187"
            login_response = requests.post(
                login_url,
                data=login_data,
                headers=headers,
                proxies=proxies
            )
            
            # Check for successful login
            if login_response.status_code != 200:
                print(f"Login failed with status code: {login_response.status_code}")
                raise Exception(f"Login failed with status code: {login_response.status_code}")
            
            # print(f"Login response: {login_response.text}")
            
            # Extract livsid cookie from response headers
            cookies = {}
            if 'set-cookie' in login_response.headers:
                cookie_header = login_response.headers['set-cookie']
                print(f"Set-Cookie header: {cookie_header}")
                livsid_match = re.search(r'livsid=([^;]+)', cookie_header)
                if livsid_match:
                    cookies['livsid'] = livsid_match.group(1)
                    print(f"Extracted livsid cookie: {cookies['livsid']}")
            
            # Store cookies in the account
            account.set_cookie_jar(cookies)
            
            # If this is the first account, also store cookies in the class for search functionality
            if self.__accounts and account == self.__accounts[0]:
                self.__cookie_jar = account.cookie_jar
            
            user_data = login_response.json()
            if user_data.get("R") == "OK" and "D" in user_data and "balance" in user_data["D"]:
                balance_data = user_data["D"]["balance"]
                if "amount" in balance_data:
                    account.balance = float(balance_data["amount"])
                    print(f"Account balance: {account.balance}")
            
            print(f"Login successful for account: {account.username}")
            return True
        except Exception as e:
            print(f"Login failed for account: {account.username}: {e}")
            raise

    def __search_event(self, home_team, away_team, pinnacle_start_time=None):
        """
        Search for an event on Bet9ja using team names and match start time
        
        Parameters:
        - home_team: Home team name
        - away_team: Away team name
        - pinnacle_start_time: Start time from Pinnacle in milliseconds (unix timestamp)
        
        Returns:
        - event ID if found, None otherwise
        """
        print(f"Searching for match: {home_team} vs {away_team}")
        if pinnacle_start_time:
            pinnacle_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(pinnacle_start_time)/1000))
            print(f"Pinnacle start time: {pinnacle_datetime} (GMT)")
        
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
        
        # Get proxy from first account if available
        proxies = None
        if self.__accounts and hasattr(self.__accounts[0], 'get_proxies'):
            proxies = self.__accounts[0].get_proxies()
            if proxies:
                print(f"Using proxy for search: {self.__accounts[0].proxy}")
        
        for search_term in search_strategies:
            print(f"Trying search term: {search_term}")
            
            form_data = {
                'TERM': search_term,
                'START': '0',
                'ROWS': '100000',
                'ISCOMPETITION': '0',
                'ISEVENT': '1',
                'ISTEAM': '0',
                'GROUPBYFIELD': 'sp_id',
                'GROUPBYLIMIT': '11'
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            try:
                # Use the first account's cookie jar for searching
                cookies = self.__cookie_jar
                
                response = requests.post(
                    f"{self.__bet_api_host}/sportsbook/search/SearchV2?source=desktop&v_cache_version=1.274.3.186",
                    data=form_data,
                    cookies=cookies,
                    headers=headers,
                    # proxies=proxies
                )
                
                if response.status_code == 401:
                    print("Session expired, logging in again...")
                    self.__do_login()
                    return self.__search_event(home_team, away_team, pinnacle_start_time)
                
                search_results = response.json()
                
                if search_results["R"] == "OK" and search_results["D"]["numFound"] > 0:
                    # print(f"search results: {search_results}")
                    # Check each sport for events
                    for sport_id, sport_data in search_results["D"]["S"].items():
                        if "E" in sport_data:
                            for event in sport_data["E"]:
                                # Check if home and away team names match (partial match)
                                event_name = event["DS"].lower()
                                
                                # Skip events with variant indicators that don't exist in the original team names
                                should_skip = False
                                for indicator in variant_indicators:
                                    if (indicator in event_name and 
                                        indicator not in home_team.lower() and 
                                        indicator not in away_team.lower()):
                                        # print(f"Skipping variant team: {event['DS']}")
                                        should_skip = True
                                        break
                                
                                if should_skip:
                                    print(f"Skipping variant team: {event['DS']}")
                                    continue
                                
                                # Start with a base match score
                                match_score = 0
                                print(f"event name: {event_name}")
                                
                                # Calculate match score based on word matching
                                home_words = set(word.lower() for word in home_team.lower().split() if len(word) > 2)
                                away_words = set(word.lower() for word in away_team.lower().split() if len(word) > 2)
                                event_words = set(word.lower() for word in event_name.lower().split() if len(word) > 2)
                                
                                home_match_count = len(home_words.intersection(event_words))
                                away_match_count = len(away_words.intersection(event_words))
                                print(f"home match count: {home_match_count}")
                                print(f"away match count: {away_match_count}")
                                
                                # Basic check if both team names are in the event - perfect match
                                if (home_team.lower() in event_name and away_team.lower() in event_name):
                                    # Perfect name match - both exact team names are in the event name
                                    print(f"Found exact name match: {event['DS']} (ID: {event['ID']})")
                                    match_score += 10  # Give a high score for exact match
                                    
                                # At least one word from each team must match
                                if home_match_count > 0 and away_match_count > 0:
                                    match_score += home_match_count + away_match_count
                                else:
                                    # Skip events that don't have at least one word from each team
                                    continue
                                
                                # Check start time if available
                                time_match_score = 0
                                if pinnacle_start_time and "STARTDATE" in event:
                                    bet9ja_start_time = event["STARTDATE"]
                                    try:
                                        # Parse Bet9ja time (assumed to be in GMT as noted)
                                        bet9ja_datetime = time.strptime(bet9ja_start_time, '%Y-%m-%d %H:%M:%S')
                                        bet9ja_timestamp = time.mktime(bet9ja_datetime) * 1000
                                        
                                        # Calculate time difference in hours
                                        time_diff_hours = abs(int(pinnacle_start_time) - bet9ja_timestamp) / (1000 * 60 * 60)
                                        
                                        # print(f"Time difference: {time_diff_hours:.2f} hours")
                                        
                                        # Score based on time difference:
                                        # - Within 30 minutes: +5 points
                                        # - Within 2 hours: +3 points
                                        # - Within 6 hours: +1 point
                                        # - Same day: +0.5 points
                                        # Check if time difference is within 5 minutes (0.0833 hours)
                                        if time_diff_hours <= 1.0833:  # 1 hour and 5 minutes
                                            time_match_score = 10  # High score for very close time match
                                        else:
                                            print(f"Time difference: {time_diff_hours:.2f} hours, not the right game because of difference in time" )
                                            time_match_score = 0  # No score if times don't match closely
                                            
                                        match_score += time_match_score
                                        # print(f"Time match score: +{time_match_score}")
                                    except Exception as e:
                                        print(f"Error parsing time: {e}")
                                
                                # Add to potential matches if score is positive
                                if match_score > 0:
                                    potential_matches.append({
                                        "event_name": event["DS"],
                                        "event_id": event["ID"],
                                        "score": match_score,
                                        "strategy": search_term,
                                        "time_score": time_match_score
                                    })
                                    # print(f"Potential match: {event['DS']} (Score: {match_score})")
            
            except Exception as e:
                print(f"Error searching for event: {e}")
        
        # If we have potential matches, return the one with the highest score
        if potential_matches:
            best_match = max(potential_matches, key=lambda x: x["score"])
            print(f"Best match: {best_match['event_name']} (ID: {best_match['event_id']}, Score: {best_match['score']})")
            return best_match["event_id"]
        
        print("No matching event found on Bet9ja")
        return None

    def __get_event_details(self, event_id):
        """Get detailed information about an event from Bet9ja"""
        print(f"Getting details for event ID: {event_id}")
        
        form_data = {
            'EVENTID': event_id,
            'v_cache_version': '1.274.3.186'
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Get proxy from first account if available
        proxies = None
        if self.__accounts and hasattr(self.__accounts[0], 'get_proxies'):
            proxies = self.__accounts[0].get_proxies()
            if proxies:
                print(f"Using proxy for event details: {self.__accounts[0].proxy}")
        
        try:
            # Use the first account's cookie jar for getting event details
            cookies = self.__cookie_jar
            
            response = requests.get(
                f"{self.__bet_host}/desktop/feapi/PalimpsestAjax/GetEvent?EVENTID={event_id}&v_cache_version=1.274.3.186",
                # data=form_data,
                # cookies=cookies,
                headers=headers,
                # proxies=proxies
            )
            
            if response.status_code == 401:
                print("Session expired, logging in again...")
                self.__do_login()
                return self.__get_event_details(event_id)
            
            event_details = response.json()
            
            if event_details["R"] == "OK":
                return event_details["D"]
            
            print(f"Failed to get event details: {event_details}")
            return None
            
        except Exception as e:
            print(f"Error getting event details: {e}")
            return None

    def __place_bet_with_available_account(self, bet_data):
        """
        Place a bet using an available account
        
        Parameters:
        - bet_data: Dictionary with bet information
        
        Returns:
        - True if bet was placed successfully, False otherwise
        """
        try:
            # Get max concurrent bets from config
            max_total_bets = self.__config.get("max_total_concurrent_bets", 5)
            
            # Count total current bets across all accounts
            total_current_bets = sum(account.current_bets for account in self.__accounts)
            
            # Check if we've reached the global limit
            if total_current_bets >= max_total_bets:
                print(f"Reached global limit of {max_total_bets} concurrent bets. Queuing bet.")
                # Re-add to queue with a delay
                threading.Timer(30.0, lambda: self.__bet_queue.put(bet_data)).start()
                return False
            
            # Find an available account
            print(f"Checking {len(self.__accounts)} accounts")
            for account in self.__accounts:
                print(f"Checking account {account.username}")
                if account.can_place_bet():
                    # Check if login is needed
                    if account.needs_login():
                        try:
                            self.__do_login_for_account(account)
                        except Exception as e:
                            print(f"Failed to login to account {account.username}: {e}")
                            continue  # Try next account
                    
                    # Try to place bet with this account
                    account.increment_bets()
                    success, stake = self.__place_bet_for_account(
                        account=account,
                        bet_code=bet_data["bet_code"],
                        odds=bet_data["odds"],
                        modified_shaped_data=bet_data["modified_shaped_data"],
                        bankroll=account.balance
                    )
                    
                    if success:
                        account.decrement_bets()
                        # dedcue from balance
                        account.balance -= stake
                        print(f"Bet placed successfully with account {account.username}")
                        return True
                    else:
                        # If bet failed, decrement the bet counter
                        account.decrement_bets()
            
            print("No available accounts to place bet. Queuing for retry.")
            # Re-add to queue with a delay
            threading.Timer(60.0, lambda: self.__bet_queue.put(bet_data)).start()
            return False
        except Exception as e:
            print(f"Error in place_bet_with_available_account: {e}")
            # Close browser on error
            self.cleanup()
            raise

    def __place_bet_for_account(self, account, bet_code, odds, modified_shaped_data, bankroll):
        """
        Place a bet on Bet9ja using a specific account
        
        Parameters:
        - account: BetAccount instance
        - bet_code: The bet code from Bet9ja (e.g., "594248648$S_1X2_1")
        - odds: The decimal odds for the bet
        - modified_shaped_data: The modified shaped data for the bet
        - bankroll: The bankroll for the account
        
        Returns:
        - Tuple of (success, stake) where success is True if bet was placed successfully
        """
        print(f"Placing bet with account {account.username}: {bet_code} with odds {odds}")

        # calculate stake
        stake = self.__calculate_stake(odds, modified_shaped_data, bankroll)

        
        # Construct the betslip data
        betslip_data = {
            "BETS": [{
                "BSTYPE": 3,
                "TAB": 3,
                "NUMLINES": 1,
                "COMB": 1,
                "TYPE": 1,
                "STAKE": stake,
                "POTWINMIN": stake * odds,
                "POTWINMAX": stake * odds,
                "BONUSMIN": "0",
                "BONUSMAX": "0",
                "ODDMIN": str(odds),
                "ODDMAX": str(odds),
                "ODDS": {bet_code: str(odds)},
                "FIXED": {}
            }],
            "IMPERSONIZE": 0
        }
        
        # Construct form data
        form_data = {
            'BETSLIP': json.dumps(betslip_data),
            'BONUS': '0',
            'ACCEPT_ODDS_CHANGES': '1',
            'IS_PASSBET': '0',
            'IS_FIREBETS': '0',
            'IS_CUT1': '0'
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Get proxies if configured
        proxies = account.get_proxies()
        if proxies:
            print(f"Using proxy for bet placement: {account.proxy} {account.username}")
            # Check IP with proxy
            self.__check_ip_address(using_proxy=True, proxy_url=proxies, account=account)
        else:
            # Check IP without proxy
            self.__check_ip_address(using_proxy=False, account=account)
        
        try:
            response = requests.post(
                f"{self.__bet_api_host}/sportsbook/placebet/PlacebetV2?source=desktop&v_cache_version=1.274.3.186",
                data=form_data,
                cookies=account.cookie_jar,
                headers=headers,
                proxies=proxies
            )
            print("--------------------------------")
            print(form_data)
            print("--------------------------------")
            
            if response.status_code == 401:
                print(f"Session expired for account {account.username}, logging in again...")
                self.__do_login_for_account(account)
                return self.__place_bet_for_account(account, bet_code, odds, modified_shaped_data, bankroll)
            
            response_data = response.json()
            if response_data.get("status") == -1 or response_data["error"].get("message") == "Invalid session" or response_data["error"].get("code") == 114:
                print(f"Session expired for account {account.username}, logging in again...")
                self.__do_login_for_account(account)
                return self.__place_bet_for_account(account, bet_code, odds, modified_shaped_data, bankroll)
            
            print(f"Bet placement response for account {account.username}: {response_data}")
            
            # Check if the bet was placed successfully
            if response_data.get("status") == 1:
                print(f"Bet placed successfully with account {account.username}!")
                return True, stake
            else:
                print(f"Failed to place bet with account {account.username}: {response_data}")
                return False, stake
                
        except Exception as e:
            print(f"Error placing bet with account {account.username}: {e}")
            return False, stake

    def __place_bet(self, bet_code, odds, modified_shaped_data):
        """
        Queue a bet for placement
        
        Parameters:
        - bet_code: The bet code from Bet9ja (e.g., "594248648$S_1X2_1")
        - odds: The decimal odds for the bet
        - stake: The amount to stake
        
        Returns:
        - True if bet was queued successfully
        """
        print(f"Queueing bet: {bet_code} with odds {odds}")
        
        # Add bet to queue
        bet_data = {
            "bet_code": bet_code,
            "odds": odds,
            "modified_shaped_data": modified_shaped_data,
            "timestamp": time.time()
        }
        
        self.__bet_queue.put(bet_data)
        return True  # Return True as the bet was queued successfully

    def __find_market_bet_code_with_points(self, event_details, line_type, points, outcome, is_first_half=False, sport_id=1, home_team=None, away_team=None):
        """
        Find the appropriate bet code in the Bet9ja event details and return the adjusted points value
        
        Parameters:
        - event_details: The event details from Bet9ja
        - line_type: The type of bet (spread, moneyline, total)
        - points: The points value for the bet
        - outcome: The outcome (home, away, draw, over, under)
        - is_first_half: Whether the bet is for the first half
        - sport_id: The sport ID (1 for soccer, 3 for basketball)
        
        Returns:
        - Tuple of (bet_code, odds, adjusted_points)
        """
        print(f"sport id {sport_id}")
        print(f"Finding market for Game: {home_team} vs {away_team}: {line_type} - {outcome} - {points} - First Half: {is_first_half} - Sport: {'Basketball' if sport_id == 3 or sport_id == "3" else 'Soccer'}")
        
        if "O" not in event_details:
            print("No market odds found in event details")
            return None, None, None
        
        odds_data = event_details["O"]
        
        # Use different market prefixes based on sport
        is_basketball = (sport_id == "3" or sport_id == 3)
        print(f"is basketball: {is_basketball}")
        
        # Handle MONEYLINE bets (1X2 in Bet9ja)
        if line_type.lower() == "money_line":
            # Moneyline doesn't have points, so we'll use None
            adjusted_points = None
            
            if is_basketball:
                # Basketball uses different market codes (B_12 or B_1X21T for first half)
                # Map outcome to Bet9ja format
                outcome_map = {"home": "1", "away": "2"}
                if outcome.lower() not in outcome_map:
                    print(f"Invalid outcome for basketball moneyline: {outcome}")
                    return None, None, adjusted_points
                    
                bet_outcome = outcome_map[outcome.lower()]
                
                # Format: B_1X21T_1HT for first half, B_12_1 for full match
                market_prefix = "B_1X21T_" if is_first_half else "B_12_"
                market_suffix = "HT" if is_first_half else ""
                market_key = f"{market_prefix}{bet_outcome}{market_suffix}"
            else:
                # Soccer uses standard S_1X2 format
                # Map outcome to Bet9ja format
                outcome_map = {"home": "1", "away": "2", "draw": "X"}
                if outcome.lower() not in outcome_map:
                    print(f"Invalid outcome for soccer moneyline: {outcome}")
                    return None, None, adjusted_points
                    
                bet_outcome = outcome_map[outcome.lower()]
                
                # Format: S_1X21T_1 for first half
                market_prefix = "S_1X21T_" if is_first_half else "S_1X2_"
                market_key = f"{market_prefix}{bet_outcome}"
            
            # Look for exact match instead of endswith
            for key, odds in odds_data.items():
                # Check if the key exactly matches our market key
                if key == market_key:
                    print(f"Found moneyline market: {key} with odds {odds}")
                    return key, float(odds), adjusted_points
            
            print(f"No matching moneyline market found for {outcome}")
            return None, None, adjusted_points
            
        # Handle TOTAL bets (Over/Under in Bet9ja)
        elif line_type.lower() == "total":
            # Map outcome to Bet9ja format
            outcome_map = {"over": "O", "under": "U"}
            if outcome.lower() not in outcome_map:
                print(f"Invalid outcome for total: {outcome}")
                return None, None, None
                
            bet_outcome = outcome_map[outcome.lower()]
            
            # First try exact match with original points
            if is_basketball:
                # Basketball format: B_1HOU@82.5_O for first half, B_OUN@164.5_O for full match
                market_prefix = "B_1HOU@" if is_first_half else "B_OUN@"
            else:
                # Soccer format: S_OU1T@0.5_O for first half, S_OU@0.5_O for full match
                market_prefix = "S_OU1T@" if is_first_half else "S_OU@"
                
            exact_key = f"{market_prefix}{points}_{bet_outcome}"
            
            for key, odds in odds_data.items():
                if key == exact_key:  # Exact match instead of endswith
                    print(f"Found exact total market: {key} with odds {odds}")
                    # Use original points since it's an exact match
                    return key, float(odds), points
            
            # Round the original points to nearest .0 or .5
            original_float = float(points)
            
            # Try to find nearest standard points (.0 or .5)
            # Generate a list of standard points to check (nearest .0 and .5 values)
            standard_points = []
            
            # Get the nearest .0 and .5 values above and below
            floor_int = math.floor(original_float)
            ceil_int = math.ceil(original_float)
            
            # Add the standard points in order of proximity
            standard_points.append(floor_int)  # .0 below
            standard_points.append(floor_int + 0.5)  # .5 above floor
            if ceil_int != floor_int:
                standard_points.append(ceil_int)  # .0 above
                standard_points.append(ceil_int - 0.5)  # .5 below ceil
            
            # Sort by distance from original points
            standard_points.sort(key=lambda x: abs(x - original_float))
            
            # Try each standard point
            for std_point in standard_points:
                # Skip negative or zero points for totals
                if std_point <= 0:
                    continue
                    
                std_key = f"{market_prefix}{std_point}_{bet_outcome}"
                
                for key, odds in odds_data.items():
                    if key == std_key:  # Exact match
                        print(f"Found standard total market: {key} with odds {odds}")
                        return key, float(odds), std_point
            
            # If standard points don't match, try incrementing by 0.5 up to +/-2
            for increment in [0.5, 1.0, 1.5, 2.0]:
                for direction in [1, -1]:  # Try both up and down
                    adj_points = original_float + (direction * increment)
                    if adj_points <= 0:
                        continue  # Skip negative or zero points
                        
                    # Round to nearest .0 or .5
                    adj_points_rounded = round(adj_points * 2) / 2
                    
                    adj_key = f"{market_prefix}{adj_points_rounded}_{bet_outcome}"
                    
                    for key, odds in odds_data.items():
                        if key == adj_key:  # Exact match
                            print(f"Found adjusted total market: {key} with odds {odds}")
                            return key, float(odds), adj_points_rounded
            
            print(f"No matching total market found for {points} {outcome}")
            return None, None, None
            
        # Handle SPREAD bets (Handicap in Bet9ja)
        elif line_type.lower() == "spread":
            # Check if points is near zero - if so, use Draw No Bet market instead
            if abs(float(points)) < 0.01:
                print("Handicap is 0, using Draw No Bet (DNB) market")
                # Map outcome to Bet9ja format for DNB
                outcome_map = {"home": "1", "away": "2"}
                if outcome.lower() not in outcome_map:
                    print(f"Invalid outcome for DNB: {outcome}")
                    return None, None, None
                    
                bet_outcome = outcome_map[outcome.lower()]
                
                if is_basketball:
                    # Basketball doesn't typically have DNB market, so try handicap at 0
                    market_prefix = "B_1HH@0_" if is_first_half else "B_H@0_"
                else:
                    # Soccer DNB format: S_DNB1T_1 for first half, S_DNB_1 for full match
                    market_prefix = "S_DNB1T_" if is_first_half else "S_DNB_"
                    
                dnb_key = f"{market_prefix}{bet_outcome}"
                
                # Look for exact match
                for key, odds in odds_data.items():
                    if key == dnb_key:
                        print(f"Found Draw No Bet market: {key} with odds {odds}")
                        return key, float(odds), 0  # Return 0 as the points value
                        
                print(f"No matching Draw No Bet market found for {outcome}")
                return None, None, None
                
            # Adjust the points for away team (Bet9ja uses S_AH@X_Y format)
            handicap_points = points
            # if outcome.lower() == "away":
            #     # Bet9ja represents away handicaps with negative of the original value
            #     handicap_points = -float(points)
            
            # Map outcome to Bet9ja format for Asian Handicap
            outcome_map = {"home": "1", "away": "2"}
            if outcome.lower() not in outcome_map:
                print(f"Invalid outcome for handicap: {outcome}")
                return None, None, None
                
            bet_outcome = outcome_map[outcome.lower()]
            
            if is_basketball:
                # Basketball format: B_1HH@-14.5_1 for first half, B_H@-26.5_1 for full match
                market_prefix = "B_1HH@" if is_first_half else "B_H@"
            else:
                # Soccer format: S_AH1T@X_Y for first half, S_AH@X_Y for full match
                market_prefix = "S_AH1T@" if is_first_half else "S_AH@"
                
            exact_key = f"{market_prefix}{handicap_points}_{bet_outcome}"
            
            # Look for exact match first
            for key, odds in odds_data.items():
                if key == exact_key:  # Exact match instead of endswith
                    print(f"Found exact handicap market: {key} with odds {odds}")
                    # Use original points since it's an exact match
                    return key, float(odds), points
            
            # Round the handicap points to nearest .0 or .5
            handicap_float = float(handicap_points)
            
            # Generate a list of standard handicaps to check (nearest .0 and .5 values)
            standard_handicaps = []
            
            # Get the nearest .0 and .5 values above and below
            floor_int = math.floor(handicap_float)
            ceil_int = math.ceil(handicap_float)
            
            # Add the standard handicaps in order of proximity
            standard_handicaps.append(floor_int)  # .0 below
            standard_handicaps.append(floor_int + 0.5)  # .5 above floor
            if ceil_int != floor_int:
                standard_handicaps.append(ceil_int)  # .0 above
                standard_handicaps.append(ceil_int - 0.5)  # .5 below ceil
            
            # Sort by distance from original handicap
            standard_handicaps.sort(key=lambda x: abs(x - handicap_float))
            
            # Try each standard handicap
            for std_handicap in standard_handicaps:
                std_key = f"{market_prefix}{std_handicap}_{bet_outcome}"
                
                for key, odds in odds_data.items():
                    if key == std_key:  # Exact match
                        print(f"Found standard handicap market: {key} with odds {odds}")
                        # Convert back to original format if needed
                        result_points = std_handicap
                        return key, float(odds), result_points
            
            # If standard handicaps don't match, try incrementing by 0.5 up to +/-3
            for increment in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                for direction in [1, -1]:  # Try both up and down
                    adj_handicap = handicap_float + (direction * increment)
                    
                    # Round to nearest .0 or .5
                    adj_handicap_rounded = round(adj_handicap * 2) / 2
                    
                    adj_key = f"{market_prefix}{adj_handicap_rounded}_{bet_outcome}"
                    
                    for key, odds in odds_data.items():
                        if key == adj_key:  # Exact match
                            print(f"Found adjusted handicap market: {key} with odds {odds}")
                            # Convert back to original format if needed
                            result_points = adj_handicap_rounded
                            return key, float(odds), result_points
            
            print(f"No matching handicap market found for {handicap_points} {outcome}")
            return None, None, None
        
        else:
            print(f"Unsupported line type: {line_type}")
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

    def __calculate_ev(self, bet_odds, shaped_data):
        """
        Calculate the Expected Value (EV) for a bet
        
        Parameters:
        - bet_odds: The decimal odds offered by Bet9ja
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
            print("Using odds from original alert as fallback")
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
            print(f"Using latest Pinnacle odds: {decimal_prices}")
        
        # Store the prices for later use in stake calculation
        shaped_data["_decimal_prices"] = decimal_prices
        
        # Calculate no-vig prices
        if not decimal_prices:
            print("No prices found for calculation")
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
            print(f"No no-vig price found for outcome {outcome_key}")
            return -100  # Negative EV as fallback
            
        # Calculate EV
        ev = calculate_ev(bet_odds, true_price)
        print(f"Bet odds: {bet_odds}, True price: {true_price}, EV: {ev:.2f}%")
        
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
            print("No event ID provided, cannot fetch latest odds")
            return None
            
        pinnacle_api_host = os.getenv("PINNACLE_HOST")
        if not pinnacle_api_host:
            print("Pinnacle Events API host not configured")
            return None
            
        # Get proxy from first account if available
        proxies = None
        if self.__accounts and hasattr(self.__accounts[0], 'get_proxies'):
            proxies = self.__accounts[0].get_proxies()
            if proxies:
                print(f"Using proxy for Pinnacle odds: {self.__accounts[0].proxy}")
            
        try:
            url = f"{pinnacle_api_host}/events/{event_id}"
            print(f"Fetching latest odds from: {url}")
            
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch latest odds: HTTP {response.status_code}")
                return None
                
            event_data = response.json()
            if not event_data or "data" not in event_data or not event_data["data"]:
                print("No data returned from Pinnacle API")
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
            print(f"Error fetching latest odds: {e}")
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
        
    def __calculate_stake(self, bet_odds, shaped_data, bankroll):
        """
        Calculate the stake amount based on Kelly criterion
        
        Parameters:
        - bet_odds: The decimal odds offered by Bet9ja
        - shaped_data: The data with prices and outcome information
        
        Returns:
        - Recommended stake amount
        """
        # Get the stored decimal prices and outcome key
        decimal_prices = shaped_data.get("_decimal_prices", {})
        outcome_key = shaped_data.get("_outcome_key", "")
        
        if not decimal_prices or not outcome_key:
            print("Missing required data for stake calculation")
            return 10  # Default stake if calculation not possible
        
        # Extract values into a list for power method
        odds_values = list(decimal_prices.values())
        if not odds_values:
            return 10  # Default stake
        
        # Calculate fair probabilities using power method
        fair_probs = self.__power_method_devig(odds_values)
        
        # Map the probabilities back to their outcomes
        outcome_probs = {}
        for i, (outcome, _) in enumerate(decimal_prices.items()):
            if i < len(fair_probs):
                outcome_probs[outcome] = fair_probs[i]
        
        # Get the probability for our specific outcome
        if outcome_key not in outcome_probs:
            print(f"Outcome {outcome_key} not found in probabilities")
            return 10  # Default stake
            
        outcome_prob = outcome_probs[outcome_key]
        
        
        # Calculate Kelly stake
        full_kelly = self.__kelly_stake(outcome_prob, bet_odds, bankroll)
        
        # Use 30% of Kelly as a more conservative approach
        fractional_kelly = full_kelly * 0.3
        
        # Apply min/max stake limits
        # min_stake = float(os.getenv("MIN_STAKE", "10"))
        # max_stake = float(os.getenv("MAX_STAKE", "100"))

        min_stake = self.__min_stake
        max_stake = self.__max_stake
        
        stake = max(min_stake, min(fractional_kelly, max_stake))
        
        print(f"Probability: {outcome_prob:.4f}, Full Kelly: {full_kelly:.2f}, "
              f"Fractional Kelly (30%): {fractional_kelly:.2f}, Final Stake: {stake:.2f}")
        
        return stake

    def notify(self, shaped_data):
        """
        Process the alert from Pinnacle and place a bet if EV is positive
        
        Parameters:
        - shaped_data: The data from Pinnacle shaped according to BetEngine requirements
        """
        try:
            print(f"Processing alert: {shaped_data}")
            
            # Validate shaped data
            required_fields = ['game', 'category', 'match_type']
            if not all(field in shaped_data for field in required_fields):
                print("Invalid shaped data format")
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
                print(f"Alert contains start time: {pinnacle_start_time}")
            
            # Determine if this is for first half or full match
            is_first_half = False
            if "periodNumber" in shaped_data and shaped_data["periodNumber"] == "1":
                is_first_half = True
                
            # Step 1: Search for the event on Bet9ja
            print(f"Searching for event: {home_team} vs {away_team}")
            event_id = self.__search_event(home_team, away_team, pinnacle_start_time)
            if not event_id:
                print("Event not found, cannot place bet")
                return
                
            # Step 2: Get event details
            print(f"Getting event details for event: {event_id}")
            event_details = self.__get_event_details(event_id)
            if not event_details:
                print("Could not get event details, cannot place bet")
                return
                
            # Step 3: Find the market for the bet
            print(f"Finding market for bet: {line_type} {outcome} {original_points}")
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
                print("Could not find appropriate market, cannot place bet")
                return
                
            # Create a modified shaped_data with the adjusted points
            modified_shaped_data = shaped_data.copy()
            modified_shaped_data["category"]["meta"]["value"] = adjusted_points
            print(f"Using adjusted points: {adjusted_points} (original was: {original_points})")
            
            # Step 4: Calculate EV with the adjusted points
            print(f"Calculating EV with adjusted points: {adjusted_points}")
            ev = self.__calculate_ev(bet_odds, modified_shaped_data)
            
            # Step 5: Place bet if EV is positive and above threshold
            print(f"EV: {ev:.2f}%")
            if ev > self.__min_ev:
                print(f"Positive EV ({ev:.2f}%), placing bet")
                
                # Calculate optimal stake using Kelly criterion            
                success = self.__place_bet(f"{event_id}${bet_code}", bet_odds, modified_shaped_data)
                
                if success:
                    print(f"Successfully queued bet on {home_team} vs {away_team} - {line_type} {outcome} {adjusted_points}")
                else:
                    print("Failed to queue bet")
            else:
                print(f"Negative or insufficient EV ({ev:.2f}%), not placing bet")
                
            return ev > self.__min_ev
        except Exception as e:
            print(f"Error in notify method: {e}")
            # Close browser on error
            self.cleanup()
            raise

    def __find_market_bet_code(self, event_details, line_type, points, outcome, is_first_half=False, sport_id=1, home_team=None, away_team=None):
        """
        DEPRECATED: Use __find_market_bet_code_with_points instead
        This method is kept for backward compatibility.
        
        Find the appropriate bet code in the Bet9ja event details
        
        Parameters:
        - event_details: The event details from Bet9ja
        - line_type: The type of bet (spread, moneyline, total)
        - points: The points value for the bet
        - outcome: The outcome (home, away, draw, over, under)
        - is_first_half: Whether the bet is for the first half
        - sport_id: The sport ID (1 for soccer, 3 for basketball)
        
        Returns:
        - Tuple of (bet_code, odds)
        """
        # Forward to the new method and discard the adjusted points
        bet_code, odds, _ = self.__find_market_bet_code_with_points(
            event_details, line_type, points, outcome, is_first_half, sport_id, home_team, away_team
        )
        return bet_code, odds

    def cleanup(self):
        """Close browser and clean up resources"""
        if self.__browser_open and self.__browser_initialized:
            try:
                print("Closing browser...")
                self.close_browser()
                self.__browser_open = False
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}")
                
    def __del__(self):
        """Destructor to ensure browser is closed when object is garbage collected"""
        self.cleanup()

if __name__ == "__main__":
    """Main Application"""
    bet_engine = BetEngine(
        headless=os.getenv("ENVIRONMENT") == "production",
        config_file="config.json"
    )
    test_data = {
        "game": {
            "away": "Manchester Utd",
            "home": "Chelsea"
        },
        "category": {
            "type": "spread",
            "meta": {
                "value": "1",
                "team": "home",
                "value_of_under_over": "+1.5"
            }
        },
        "match_type": "oddsDrop"
    }
    bet_engine.notify(test_data)
