from selenium_script import *
import os
import dotenv
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
    def __place_bet(self, shaped_data):
        """ Bet Data Template 
        {
        'BETSLIP': 
        '{
        "BETS":[{"BSTYPE":3,
        "TAB":3,
        "NUMLINES":1,
        "COMB":1,
        "TYPE":1,
        "STAKE":10,
        "POTWINMIN":32.5,
        "POTWINMAX":32.5,
        "BONUSMIN":"0",
        "BONUSMAX":"0",
        "ODDMIN":"3.25",
        "ODDMAX":"3.25",
        "ODDS":{"592862875$S_1X2_2":"3.25"},
        "FIXED":{}}],
        "IMPERSONIZE":0}',
'BONUS': '0',
'ACCEPT_ODDS_CHANGES': '1',
'IS_PASSBET': '0',
'IS_FIREBETS': '0',
'IS_CUT1': '0'}
        """
        bet_data= {
        'BETSLIP': 
        '''{
        "BETS":[{"BSTYPE":3,
        "TAB":3,
        "NUMLINES":1,
        "COMB":1,
        "TYPE":1,
        "STAKE":10,
        "POTWINMIN":32.5,
        "POTWINMAX":32.5,
        "BONUSMIN":"0",
        "BONUSMAX":"0",
        "ODDMIN":"3.25",
        "ODDMAX":"3.25",
        "ODDS":{"592862875$S_1X2_2":"3.25"},
        "FIXED":{}}],
        "IMPERSONIZE":0}''',
'BONUS': '0',
'ACCEPT_ODDS_CHANGES': '1',
'IS_PASSBET': '0',
'IS_FIREBETS': '0',
'IS_CUT1': '0'}
        headers={
                "User-Agent":"Zeus",
                "Accept":"*/*",
                "Cache-Control":"no-cache",
                "Host":"apigw.bet9ja.com",
                "Accept-Encoding":"gzip, deflate, br",
    "Connection":"keep-alive",
        }
        response=requests.post(f"{self.__bet_api_host}/sportsbook/placebet/PlacebetV2?source=desktop&v_cache_version=1.274.3.186",json=bet_data,cookies=self.__cookie_jar,headers=headers)
        if response.status_code==401:
            self.__do_login()
            self.__place_bet(shaped_data)
        print(response.json())

    def notify(self, shaped_data):
        """ Work on the data sent across from the odds engine
        shaped_data template:
                shaped_data={
            "game":{
                "home":"",
                "away":"",
            },
            "category":{
                "type":"",
                "meta":{
                   "value": None,
                   "team": None, 
                   "value_of_under_over": None,
                }   
            },
        "match_type":""
        }
        """
        #do the rest, fam
        #make sure to check that bet doesn't exist
        self.__place_bet(shaped_data)
if __name__ == "__main__":
    """Main Application"""
    bet_engine = BetEngine()
    bet_engine.notify({"game": {"home": "Manchester United", "away": "Liverpool"}, "category": {"type": "spread", "meta": {"value": "1", "team": "home", "value_of_under_over": "+1.5"}}, "match_type": "oddsDrop"})
