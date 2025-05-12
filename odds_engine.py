import dotenv
import os
import time
import requests
dotenv.load_dotenv()

class BetEngine:
    def __init__(self,):
        pass

class OddsEngine:
    def __init__(self,betEngine=BetEngine(),host=os.getenv("PINNACLE_ODDS_HOST"),user_id=os.getenv("PINNACLE_USER_ID")):
        self.betEngine = betEngine
        self.__host = host
        self.__user_id = user_id

    def get_odds(self):
        response = requests.get(f"{self.__host}/alerts/{self.__user_id}?dropNotificationsCursor={int(time.time())}&limitChangeNotificationsCursor={int(time.time())}&openingLineNotificationsCursor={int(time.time())}")
        data=response.json()
        sample_data=        {
            "id": "1746985490673-0",
            "sportId": "1",
            "minDropPercent": "15",
            "timeIntervalMs": "210000",
            "maxTimeToMatchStartMs": "21600000",
            "lowerBoundOdds": "1.5",
            "upperBoundOdds": "2.4",
            "nickname": "Soccer(<2.4)",
            "includeMoneyline": "1",
            "includeSpreads": "1",
            "includeTotals": "1",
            "percentageChange": "15.505500261917234",
            "changeFrom": "1.909",
            "changeTo": "1.613",
            "eventId": "1609349687",
            "periodNumber": "0",
            "lineType": "spread",
            "points": "-1",
            "outcome": "home",
            "timestamp": "1746985490523",
            "leagueName": "Argentina - Torneo Federal A",
            "home": "Club Villa Mitre",
            "away": "Kimberley Mar del Plata",
            "noVigPrice": "",
            "starts": "1746988200000",
            "type": "oddsDrop",
            "alertingCriteriaId": "alertingCriteria:ug8i4f3wxkkhq5vvmzgx936m",
            "userId": "user_2VqFOsEjFG0YgEAhZDvFe4QE6yf",
            "lowerBoundLimit": "150",
            "upperBoundLimit": "1000000",
            "includeOrExcludeCompetitions": "include",
            "enabled": "1",
            "changeDirection": "increase",
            "includePeriod0": "1",
            "includePeriod1": "1",
            "priceHome": "1.613",
            "priceAway": "2.18"
        }
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
        for alert in data["data"]:
            shaped_data["game"]["home"]=alert["home"]
            shaped_data["game"]["away"]=alert["away"]
            shaped_data["category"]["type"]=alert["lineType"]
            shaped_data["category"]["meta"]["value"]=alert["points"]
            shaped_data["category"]["meta"]["team"]=alert["outcome"]
            try:
                shaped_data["category"]["meta"]["value_of_under_over"]=f"+{alert["priceHome"]}"
            except:
                try:
                    shaped_data["category"]["meta"]["value_of_under_over"]=f"-{alert["priceAway"]}"
                except:
                    shaped_data["category"]["meta"]["value_of_under_over"]=None
            shaped_data["match_type"]=alert["type"]
            self.__notify_betengine(shaped_data)

    def __notify_betengine(self, shaped_data):
        self.betEngine.notify(shaped_data)



if __name__=="__main__":
    """ Tester"""
    oddsEngine = OddsEngine()
    print(oddsEngine.get_odds())
