from selenium_script import *
import os
import dotenv
dotenv.load_dotenv()
import requests

class BetEngine(WebsiteOpener):
    def __init__(self, headless=os.getenv("ENVIRONMENT")=="production",bet_host=os.getenv("BETNAIJA_HOST"),bet_api_host=os.getenv("BETNAIJA_API_HOST")):
        super().__init__(headless)
        self.__bet_api_host=bet_api_host
        self.__bet_host=bet_host
        super().open_url(self.__bet_host)

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
        print(shaped_data)
if __name__ == "__main__":
    """Main Application"""
    bet_engine = BetEngine()
    bet_engine.notify({"game": {"home": "Manchester United", "away": "Liverpool"}, "category": {"type": "spread", "meta": {"value": "1", "team": "home", "value_of_under_over": "+1.5"}}, "match_type": "oddsDrop"})
