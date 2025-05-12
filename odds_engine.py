import dotenv
import os
import time
import requests
dotenv.load_dotenv()

class BetEngine:
    def __init__(self,):
        pass

    def notify(self, shaped_data):
        print(shaped_data)

class OddsEngine:
    def __init__(self,betEngine=BetEngine(),host=os.getenv("PINNACLE_ODDS_HOST"),user_id=os.getenv("PINNACLE_USER_ID")):
        self.betEngine = betEngine
        self.__host = host
        self.__user_id = user_id
        self.__last_processed_timestamp = int(time.time()) * 1000  # Convert to milliseconds
        self.__processed_alerts = set()  # Keep track of processed alert IDs

    def get_odds(self):
        current_time = int(time.time()*1000)
        response = requests.get(
            f"{self.__host}/alerts/{self.__user_id}?dropNotificationsCursor={current_time-60*10*1000}-0"
        )
        data = response.json()
        shaped_data = {
            "game": {
                "home": "",
                "away": "",
            },
            "category": {
                "type": "",
                "meta": {
                   "value": None,
                   "team": None, 
                   "value_of_under_over": None,
                }   
            },
            "match_type": ""
        }

        for alert in data["data"]:
            # Skip if we've already processed this alert or if it's older than our last processed timestamp
            alert_timestamp = int(alert["timestamp"])
            alert_id = alert["eventId"]
            if (alert_id in self.__processed_alerts):
                print("here")
                continue

            # Skip alerts for matches that have already started
            current_time_ms = int(time.time() * 1000)
            match_start_time = int(alert["starts"])
            if match_start_time <= current_time_ms:
                continue

            shaped_data["game"]["home"] = alert["home"]
            shaped_data["game"]["away"] = alert["away"]
            shaped_data["category"]["type"] = alert["lineType"]
            shaped_data["category"]["meta"]["value"] = alert["points"]
            shaped_data["category"]["meta"]["team"] = alert["outcome"]
            
            try:
                if float(alert["priceHome"]) > 0:
                    shaped_data["category"]["meta"]["value_of_under_over"] = f"+{alert['priceHome']}"
                else:
                    shaped_data["category"]["meta"]["value_of_under_over"] = str(alert["priceHome"])
            except:
                try:
                    if float(alert["priceAway"]) > 0:
                        shaped_data["category"]["meta"]["value_of_under_over"] = f"+{alert['priceAway']}"
                    else:
                        shaped_data["category"]["meta"]["value_of_under_over"] = str(alert["priceAway"])
                except:
                    shaped_data["category"]["meta"]["value_of_under_over"] = None
            
            shaped_data["match_type"] = alert["type"]
            
            # Process the alert
            self.__notify_betengine(shaped_data.copy())  # Send a copy to avoid reference issues
            
            # Update tracking
            self.__processed_alerts.add(alert_id)
            self.__last_processed_timestamp = max(self.__last_processed_timestamp, alert_timestamp)

            # Limit the size of processed alerts set to prevent memory growth
            if len(self.__processed_alerts) > 1000:
                self.__processed_alerts = set(list(self.__processed_alerts)[-1000:])

    def __notify_betengine(self, shaped_data):
        self.betEngine.notify(shaped_data)

if __name__=="__main__":
    """ Tester"""
    oddsEngine = OddsEngine()
    oddsEngine.get_odds()
