from selenium_script import *
import os
import dotenv
import json
import urllib.parse
dotenv.load_dotenv()
from time import sleep
import requests
from selenium.webdriver.common.by import By

class BetEngine(WebsiteOpener):
    def __init__(self, headless=os.getenv("ENVIRONMENT")=="production",bet_host=os.getenv("BETNAIJA_HOST"),bet_api_host=os.getenv("BETNAIJA_API_HOST")):
        super().__init__(headless)
        self.__bet_api_host=bet_api_host
        self.__bet_host=bet_host
        self.__cookie_jar=None
        self.__do_login()

    def __do_login(self):
        username=os.getenv("BETNAIJA_USERNAME")
        password=os.getenv("BETNAIJA_PASSWORD")
        self.open_url(f"{self.__bet_host}")
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.XPATH, "//*[@id='header_item']/div/div/div/div[2]/div[3]/div[1]").click()
        self.driver.find_element(By.XPATH, "//*[@id='username']").send_keys(username)
        self.driver.find_element(By.XPATH, "//*[@id='password']").send_keys(password)
        self.driver.find_element(By.XPATH, "//*[@id='header_item']/div/div/div/div[2]/div[3]/div[2]/div[1]/div[3]").click()
        sleep(10)
        self.__cookie_jar = {cookie["name"]: cookie["value"] for cookie in self.driver.get_cookies()}

    def __get_bet_odds(self, shaped_data):
        """Calculate odds based on shaped_data"""
        # This is a placeholder - you'll need to implement the actual odds calculation
        # based on your betting platform's API or requirements
        category_type = shaped_data['category']['type']
        meta = shaped_data['category']['meta']
        
        # Example odds calculation - replace with actual logic
        if category_type == 'spread':
            odds_value = 3.25  # This should be fetched from your odds API
            market_id = "592862875$S_1X2_2"  # This should be fetched from your odds API
            return {
                "odds_value": odds_value,
                "market_id": market_id,
                "stake": 1  # This could be configurable
            }
        return None

    def __place_bet(self, shaped_data):
        """Place bet using the shaped data"""
        # Get odds information
        odds_info = self.__get_bet_odds(shaped_data)
        if not odds_info:
            print("Could not calculate odds for the given bet")
            return

        # Construct the betslip data
        betslip_data = {
            "BETS": [{
                "BSTYPE": 3,
                "TAB": 3,
                "NUMLINES": 1,
                "COMB": 1,
                "TYPE": 1,
                "STAKE": odds_info['stake'],
                "POTWINMIN": odds_info['stake'] * odds_info['odds_value'],
                "POTWINMAX": odds_info['stake'] * odds_info['odds_value'],
                "BONUSMIN": "0",
                "BONUSMAX": "0",
                "ODDMIN": str(odds_info['odds_value']),
                "ODDMAX": str(odds_info['odds_value']),
                "ODDS": {
                    f"{odds_info['market_id']}": str(odds_info['odds_value'])
                },
                "FIXED": {}
            }],
            "IMPERSONIZE": 0
        }

        # Convert betslip to string and properly encode
        betslip_str = json.dumps(betslip_data, separators=(',', ':'))

        # Construct the form data
        form_data = {
            'BETSLIP': betslip_str,
            'BONUS': '0',
            'ACCEPT_ODDS_CHANGES': '1',
            'IS_PASSBET': '0',
            'IS_FIREBETS': '0',
            'IS_CUT1': '0'
        }

        # URL encode the form data
        encoded_data = urllib.parse.urlencode(form_data)

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Cache-Control": "no-cache",
            "Host": "apigw.bet9ja.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.__bet_host,
            "Referer": f"{self.__bet_host}/"
        }

        try:
            print("Sending request with data:", encoded_data)
            
            response = requests.post(
                f"{self.__bet_api_host}/sportsbook/placebet/PlacebetV2?source=desktop&v_cache_version=1.274.3.186",
                data=encoded_data,
                cookies=self.__cookie_jar,
                headers=headers
            )


            if response.status_code == 401:
                print("Session expired, logging in again...")
                self.__do_login()
                return self.__place_bet(shaped_data)

            try:
                response_data = response.json()
                print(f"Bet placement response: {response_data}")
                return response_data
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON response: {e}")
                print(f"Raw response: {response.text}")
                return None

        except Exception as e:
            print(f"Error placing bet: {str(e)}")
            print(f"Full error details: {e.__class__.__name__}")
            return None

    def notify(self, shaped_data):
        """Process the shaped data and place the bet"""
        # Validate shaped data
        required_fields = ['game', 'category', 'match_type']
        if not all(field in shaped_data for field in required_fields):
            print("Invalid shaped data format")
            return

        # Place the bet
        return self.__place_bet(shaped_data)

if __name__ == "__main__":
    """Main Application"""
    bet_engine = BetEngine()
    test_data = {
        "game": {
            "home": "Manchester United",
            "away": "Liverpool"
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
