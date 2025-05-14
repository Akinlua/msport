from selenium_script import WebsiteOpener
import os
import time
import json
import re
import requests
import dotenv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.calculate_no_vig_prices import calculate_no_vig_prices
from utils.calculate_ev import calculate_ev

dotenv.load_dotenv()

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
                 min_ev=float(os.getenv("MIN_EV", "0"))):
        super().__init__(headless)
        self.__bet_api_host = bet_api_host
        self.__bet_host = bet_host
        self.__cookie_jar = None
        self.__min_ev = min_ev  # Minimum EV threshold for placing bets
        self.__do_login()
        
    def __do_login(self):
        """Log in to Bet9ja website"""
        print("Logging in to Bet9ja...")
        username = os.getenv("BETNAIJA_USERNAME")
        password = os.getenv("BETNAIJA_PASSWORD")
        
        if not username or not password:
            raise ValueError("Bet9ja username or password not found in environment variables")
            
        self.open_url(f"{self.__bet_host}")
        self.driver.implicitly_wait(10)
        
        try:
            self.driver.find_element(By.XPATH, "//*[@id='header_item']/div/div/div/div[2]/div[3]/div[1]").click()
            self.driver.find_element(By.XPATH, "//*[@id='username']").send_keys(username)
            self.driver.find_element(By.XPATH, "//*[@id='password']").send_keys(password)
            self.driver.find_element(By.XPATH, "//*[@id='header_item']/div/div/div/div[2]/div[3]/div[2]/div[1]/div[3]").click()
            time.sleep(5)
            self.__cookie_jar = {cookie["name"]: cookie["value"] for cookie in self.driver.get_cookies()}
            print("Login successful")
        except Exception as e:
            print(f"Login failed: {e}")
            raise

    def __search_event(self, home_team, away_team):
        """
        Search for an event on Bet9ja using team names
        Returns the event ID if found, None otherwise
        """
        print(f"Searching for match: {home_team} vs {away_team}")
        
        # Try different search strategies
        search_strategies = [
            f"{home_team} {away_team}",  # Full match name
            home_team,                   # Home team only
            away_team,                   # Away team only
        ]
        
        # Add individual words from team names as search strategies
        for team in [home_team, away_team]:
            words = team.split()
            for word in words:
                if len(word) > 3 and word not in search_strategies:  # Only use words longer than 3 chars
                    search_strategies.append(word)
        
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
                response = requests.post(
                    f"{self.__bet_api_host}/sportsbook/search/SearchV2?source=desktop&v_cache_version=1.274.3.186",
                    data=form_data,
                    cookies=self.__cookie_jar,
                    headers=headers
                )
                
                if response.status_code == 401:
                    print("Session expired, logging in again...")
                    self.__do_login()
                    return self.__search_event(home_team, away_team)
                
                search_results = response.json()
                
                if search_results["R"] == "OK" and search_results["D"]["numFound"] > 0:
                    # Check each sport for events
                    for sport_id, sport_data in search_results["D"]["S"].items():
                        if "E" in sport_data:
                            for event in sport_data["E"]:
                                # Check if home and away team names match (partial match)
                                event_name = event["DS"].lower()
                                if (home_team.lower() in event_name and away_team.lower() in event_name):
                                    print(f"Found match: {event['DS']} (ID: {event['ID']})")
                                    return event["ID"]
            
            except Exception as e:
                print(f"Error searching for event: {e}")
        
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
        
        try:
            response = requests.post(
                f"{self.__bet_api_host}/sportsbook/PalimpsestAjax/GetEvent?EVENTID={event_id}&v_cache_version=1.274.3.186",
                data=form_data,
                cookies=self.__cookie_jar,
                headers=headers
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

    def __find_market_bet_code(self, event_details, line_type, points, outcome, is_first_half=False):
        """
        Find the appropriate bet code in the Bet9ja event details
        
        Parameters:
        - event_details: The event details from Bet9ja
        - line_type: The type of bet (spread, moneyline, total)
        - points: The points value for the bet
        - outcome: The outcome (home, away, draw, over, under)
        - is_first_half: Whether the bet is for the first half
        
        Returns:
        - Tuple of (bet_code, odds)
        """
        print(f"Finding market for: {line_type} - {outcome} - {points} - First Half: {is_first_half}")
        
        if "O" not in event_details:
            print("No market odds found in event details")
            return None, None
        
        odds_data = event_details["O"]
        
        # Handle MONEYLINE bets (1X2 in Bet9ja)
        if line_type.lower() == "moneyline":
            # Map outcome to Bet9ja format
            outcome_map = {"home": "1", "away": "2", "draw": "X"}
            if outcome.lower() not in outcome_map:
                print(f"Invalid outcome for moneyline: {outcome}")
                return None, None
                
            bet_outcome = outcome_map[outcome.lower()]
            
            # Format: S_1X2_1 for main match, S_1X21T_1 for first half
            market_prefix = "S_1X21T_" if is_first_half else "S_1X2_"
            market_key = f"{market_prefix}{bet_outcome}"
            
            # Look for exact match
            for key, odds in odds_data.items():
                if key.endswith(market_key):
                    print(f"Found moneyline market: {key} with odds {odds}")
                    return key, float(odds)
            
            print(f"No matching moneyline market found for {outcome}")
            return None, None
            
        # Handle TOTAL bets (Over/Under in Bet9ja)
        elif line_type.lower() == "total":
            # Map outcome to Bet9ja format
            outcome_map = {"over": "O", "under": "U"}
            if outcome.lower() not in outcome_map:
                print(f"Invalid outcome for total: {outcome}")
                return None, None
                
            bet_outcome = outcome_map[outcome.lower()]
            
            # Normalize points value to Bet9ja format (typically .0 or .5)
            # First try exact match
            market_prefix = "S_OU1T@" if is_first_half else "S_OU@"
            exact_key = f"{market_prefix}{points}_{bet_outcome}"
            
            # Look for exact match first
            for key, odds in odds_data.items():
                if key.endswith(exact_key):
                    print(f"Found exact total market: {key} with odds {odds}")
                    return key, float(odds)
            
            # Try to find nearest points
            closest_point = None
            closest_key = None
            closest_odds = None
            
            # First try higher values (up to +1.5 from original)
            for increment in [0.5, 1.0, 1.5]:
                adj_points = float(points) + increment
                adj_key = f"{market_prefix}{adj_points}_{bet_outcome}"
                adj_key_alt = f"{market_prefix}{adj_points:.1f}_{bet_outcome}"  # Try with .0 format
                
                for key, odds in odds_data.items():
                    if key.endswith(adj_key) or key.endswith(adj_key_alt):
                        print(f"Found higher total market: {key} with odds {odds}")
                        return key, float(odds)
            
            # Then try lower values (down to -1.5 from original)
            for decrement in [0.5, 1.0, 1.5]:
                if float(points) - decrement <= 0:
                    continue  # Skip if points would be negative or zero
                    
                adj_points = float(points) - decrement
                adj_key = f"{market_prefix}{adj_points}_{bet_outcome}"
                adj_key_alt = f"{market_prefix}{adj_points:.1f}_{bet_outcome}"  # Try with .0 format
                
                for key, odds in odds_data.items():
                    if key.endswith(adj_key) or key.endswith(adj_key_alt):
                        print(f"Found lower total market: {key} with odds {odds}")
                        return key, float(odds)
            
            print(f"No matching total market found for {points} {outcome}")
            return None, None
            
        # Handle SPREAD bets (Handicap in Bet9ja)
        elif line_type.lower() == "spread":
            # Adjust the points for away team (Bet9ja uses 1X2HND@X_YH format)
            handicap_points = points
            if outcome.lower() == "away":
                # Bet9ja represents away handicaps with negative of the original value
                handicap_points = -float(points)
            
            # Map outcome to Bet9ja format
            outcome_map = {"home": "1H", "away": "2H", "draw": "XH"}
            if outcome.lower() not in outcome_map:
                print(f"Invalid outcome for spread: {outcome}")
                return None, None
                
            bet_outcome = outcome_map[outcome.lower()]
            
            # Format: S_1X2HND@2_1H for main match, S_1X2HND1T@2_1H for first half
            market_prefix = "S_1X2HND1T@" if is_first_half else "S_1X2HND@"
            exact_key = f"{market_prefix}{handicap_points}_{bet_outcome}"
            
            # Look for exact match first
            for key, odds in odds_data.items():
                if key.endswith(exact_key):
                    print(f"Found exact spread market: {key} with odds {odds}")
                    return key, float(odds)
            
            # Try to find nearest points (typically in whole numbers for handicap)
            # First try higher values (up to +3 from original)
            for increment in [1, 2, 3]:
                adj_points = float(handicap_points) + increment
                adj_key = f"{market_prefix}{adj_points}_{bet_outcome}"
                
                for key, odds in odds_data.items():
                    if key.endswith(adj_key):
                        print(f"Found higher spread market: {key} with odds {odds}")
                        return key, float(odds)
            
            # Then try lower values (down to -3 from original)
            for decrement in [1, 2, 3]:
                adj_points = float(handicap_points) - decrement
                adj_key = f"{market_prefix}{adj_points}_{bet_outcome}"
                
                for key, odds in odds_data.items():
                    if key.endswith(adj_key):
                        print(f"Found lower spread market: {key} with odds {odds}")
                        return key, float(odds)
            
            print(f"No matching spread market found for {handicap_points} {outcome}")
            return None, None
        
        else:
            print(f"Unsupported line type: {line_type}")
            return None, None

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
        
        # Get prices from shaped_data based on line type
        if line_type == "moneyline":
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
            if "priceDraw" in shaped_data:
                decimal_prices["draw"] = float(shaped_data["priceDraw"])
        
        # Calculate no-vig prices
        if not decimal_prices:
            print("No prices found in shaped data")
            return -100  # Negative EV as fallback
            
        no_vig_prices = calculate_no_vig_prices(decimal_prices)
        
        # Map outcome to the corresponding key in no_vig_prices
        if line_type == "total":
            # Map over/under to home/away
            outcome_map = {"over": "home", "under": "away"}
            outcome_key = outcome_map.get(outcome.lower(), outcome.lower())
        else:
            outcome_key = outcome.lower()
        
        # Get the true price using the power method (or choose another method if preferred)
        true_price = no_vig_prices["power"].get(outcome_key)
        
        if not true_price:
            print(f"No no-vig price found for outcome {outcome_key}")
            return -100  # Negative EV as fallback
            
        # Calculate EV
        ev = calculate_ev(bet_odds, true_price)
        print(f"Bet odds: {bet_odds}, True price: {true_price}, EV: {ev:.2f}%")
        
        return ev

    def __place_bet(self, bet_code, odds, stake=10):
        """
        Place a bet on Bet9ja
        
        Parameters:
        - bet_code: The bet code from Bet9ja (e.g., "594248648$S_1X2_1")
        - odds: The decimal odds for the bet
        - stake: The amount to stake
        
        Returns:
        - True if bet was placed successfully, False otherwise
        """
        print(f"Placing bet: {bet_code} with odds {odds} and stake {stake}")
        
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
        
        try:
            response = requests.post(
                f"{self.__bet_api_host}/sportsbook/placebet/PlacebetV2?source=desktop&v_cache_version=1.274.3.186",
                data=form_data,
                cookies=self.__cookie_jar,
                headers=headers
            )
            
            if response.status_code == 401:
                print("Session expired, logging in again...")
                self.__do_login()
                return self.__place_bet(bet_code, odds, stake)
            
            response_data = response.json()
            print(f"Bet placement response: {response_data}")
            
            # Check if the bet was placed successfully
            if response_data.get("R") == "OK":
                print("Bet placed successfully!")
                return True
            else:
                print(f"Failed to place bet: {response_data}")
                return False
                
        except Exception as e:
            print(f"Error placing bet: {e}")
            return False

    def notify(self, shaped_data):
        """
        Process the alert from Pinnacle and place a bet if EV is positive
        
        Parameters:
        - shaped_data: The data from Pinnacle shaped according to BetEngine requirements
        """
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
        points = shaped_data["category"]["meta"].get("value")
        
        # Determine if this is for first half or full match
        is_first_half = False
        if "periodNumber" in shaped_data and shaped_data["periodNumber"] == "1":
            is_first_half = True
            
        # Step 1: Search for the event on Bet9ja
        event_id = self.__search_event(home_team, away_team)
        if not event_id:
            print("Event not found, cannot place bet")
            return
            
        # Step 2: Get event details
        event_details = self.__get_event_details(event_id)
        if not event_details:
            print("Could not get event details, cannot place bet")
            return
            
        # Step 3: Find the market for the bet
        bet_code, bet_odds = self.__find_market_bet_code(
            event_details, 
            line_type, 
            points, 
            outcome, 
            is_first_half
        )
        
        if not bet_code or not bet_odds:
            print("Could not find appropriate market, cannot place bet")
            return
            
        # Step 4: Calculate EV
        ev = self.__calculate_ev(bet_odds, shaped_data)
        
        # Step 5: Place bet if EV is positive and above threshold
        if ev > self.__min_ev:
            print(f"Positive EV ({ev:.2f}%), placing bet")
            success = self.__place_bet(f"{event_id}${bet_code}", bet_odds)
            
            if success:
                print(f"Successfully placed bet on {home_team} vs {away_team} - {line_type} {outcome} {points}")
            else:
                print("Failed to place bet")
        else:
            print(f"Negative or insufficient EV ({ev:.2f}%), not placing bet")
            
        return ev > self.__min_ev

if __name__ == "__main__":
    """Main Application"""
    bet_engine = BetEngine()
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
