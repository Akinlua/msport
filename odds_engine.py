import dotenv
import os
import time
import requests
import json
dotenv.load_dotenv()

class BetEngine:
    def __init__(self,):
        pass

    def notify(self, shaped_data):
        print(shaped_data)

class OddsEngine:
    """
    Handles fetching odds from Pinnacle and sending alerts to the BetEngine when
    there are potential value betting opportunities.
    """
    
    def __init__(self, bet_engine=None, host=os.getenv("PINNACLE_ODDS_HOST"), 
                 user_id=os.getenv("PINNACLE_USER_ID")):
        self.bet_engine = bet_engine if bet_engine else BetEngine()
        self.__host = host
        self.__user_id = user_id
        self.__last_processed_timestamp = int(time.time()) * 1000  # Convert to milliseconds
        self.__processed_alerts = set()  # Keep track of processed alert IDs
        
        # Validate required environment variables
        if not host or not user_id:
            raise ValueError("Pinnacle odds host or user ID not found in environment variables")
    
    def start_monitoring(self, interval=60):
        """
        Start monitoring for new odds alerts continuously
        
        Parameters:
        - interval: Time in seconds between checks for new alerts
        """
        print(f"Starting odds monitoring with interval of {interval} seconds")
        while True:
            try:
                self.get_odds()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("Odds monitoring stopped by user")
                break
            except Exception as e:
                print(f"Error in odds monitoring: {e}")
                time.sleep(interval)  # Still wait before retrying
                
    def get_odds(self):
        """
        Fetch new odds alerts from Pinnacle and process them
        """
        current_time = int(time.time() * 1000)
        # Look back 10 minutes for alerts
        lookback_time = current_time - (60 * 10 * 1000)
        
        # TODO: Add support for dropNotificationsCursor and openingLineNotificationsCursor
        try:
            response = requests.get(
                f"{self.__host}/alerts/{self.__user_id}?dropNotificationsCursor={lookback_time}-0"
            )
            
            if response.status_code != 200:
                print(f"Error fetching odds: HTTP {response.status_code}")
                return
                
            data = response.json()
            
            if "data" not in data or not data["data"]:
                print("No new alerts")
                return
                
            print(f"Retrieved {len(data['data'])} alerts")
            
            # Process each alert
            for alert in data["data"]:
                self.__process_alert(alert)
                
        except Exception as e:
            print(f"Error fetching odds: {e}")
    
    def __process_alert(self, alert):
        """
        Process a single alert from Pinnacle
        
        Parameters:
        - alert: The alert data from Pinnacle
        """
        # Skip if we've already processed this alert
        alert_id = alert.get("eventId", "")
        if alert_id in self.__processed_alerts:
            return
            
        # Skip alerts for matches that have already started
        current_time_ms = int(time.time() * 1000)
        match_start_time = int(alert.get("starts", 0))
        if match_start_time <= current_time_ms:
            print(f"Skipping alert for match that already started: {alert.get('home', '')} vs {alert.get('away', '')}")
            return
            
        # Shape the data for the bet engine
        shaped_data = self.__shape_alert_data(alert)
        
        # Send to bet engine if valid
        if shaped_data:
            print(f"Sending alert to bet engine: {shaped_data['game']['home']} vs {shaped_data['game']['away']} - {shaped_data['category']['type']}")
            self.__notify_bet_engine(shaped_data)
            
        # Update tracking
        self.__processed_alerts.add(alert_id)
        self.__last_processed_timestamp = max(self.__last_processed_timestamp, int(alert.get("timestamp", 0)))
        
        # Limit the size of processed alerts set to prevent memory growth
        if len(self.__processed_alerts) > 1000:
            self.__processed_alerts = set(list(self.__processed_alerts)[-1000:])
    
    def __shape_alert_data(self, alert):
        """
        Transform the alert data from Pinnacle format to BetEngine format
        
        Parameters:
        - alert: The raw alert data from Pinnacle
        
        Returns:
        - Dictionary with shaped data for BetEngine or None if invalid
        """
        # Check for required fields
        required_fields = ["home", "away", "lineType", "outcome"]
        if not all(field in alert for field in required_fields):
            print(f"Alert missing required fields: {alert}")
            return None
            
        shaped_data = {
            "game": {
                "home": alert.get("home", ""),
                "away": alert.get("away", ""),
            },
            "category": {
                "type": alert.get("lineType", ""),
                "meta": {
                   "value": alert.get("points"),
                   "team": alert.get("outcome"), 
                   "value_of_under_over": None,
                }   
            },
            "match_type": alert.get("type", ""),
            "periodNumber": alert.get("periodNumber", "0"),  # Default to main match
        }
        
        # Add the appropriate prices based on line type
        if shaped_data["category"]["type"].lower() == "moneyline":
            if "priceHome" in alert:
                shaped_data["priceHome"] = alert["priceHome"]
            if "priceAway" in alert:
                shaped_data["priceAway"] = alert["priceAway"]
            if "priceDraw" in alert:
                shaped_data["priceDraw"] = alert["priceDraw"]
                
        elif shaped_data["category"]["type"].lower() == "total":
            if "priceOver" in alert:
                shaped_data["priceOver"] = alert["priceOver"]
            if "priceUnder" in alert:
                shaped_data["priceUnder"] = alert["priceUnder"]
                
        elif shaped_data["category"]["type"].lower() == "spread":
            if "priceHome" in alert:
                shaped_data["priceHome"] = alert["priceHome"]
            if "priceAway" in alert:
                shaped_data["priceAway"] = alert["priceAway"]
            if "priceDraw" in alert:
                shaped_data["priceDraw"] = alert["priceDraw"]
        
        # Try to add value_of_under_over for UI display
        try:
            if "priceHome" in alert and float(alert["priceHome"]) > 0:
                shaped_data["category"]["meta"]["value_of_under_over"] = f"+{alert['priceHome']}"
            elif "priceHome" in alert:
                shaped_data["category"]["meta"]["value_of_under_over"] = str(alert["priceHome"])
            elif "priceAway" in alert and float(alert["priceAway"]) > 0:
                shaped_data["category"]["meta"]["value_of_under_over"] = f"+{alert['priceAway']}"
            elif "priceAway" in alert:
                shaped_data["category"]["meta"]["value_of_under_over"] = str(alert["priceAway"])
        except (ValueError, TypeError):
            # If conversion fails, leave it as None
            pass
            
        return shaped_data
    
    def __notify_bet_engine(self, shaped_data):
        """
        Send the shaped data to the bet engine
        
        Parameters:
        - shaped_data: The shaped alert data
        """
        try:
            # Send a copy to avoid reference issues
            result = self.bet_engine.notify(shaped_data.copy())
            return result
        except Exception as e:
            print(f"Error notifying bet engine: {e}")
            return False

if __name__ == "__main__":
    """Test the OddsEngine independently"""
    odds_engine = OddsEngine()
    odds_engine.get_odds()
