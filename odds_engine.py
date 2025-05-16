import dotenv
import os
import time
import requests
import json
import threading
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
    
    def __init__(self, bet_engine=None, pinnacle_host=None, pinnacle_api_host=None):
        self.bet_engine = bet_engine if bet_engine else BetEngine()
        self.__host = pinnacle_host or os.getenv("PINNACLE_HOST")
        self.__user_id = os.getenv("PINNACLE_USER_ID")
        self.__last_processed_timestamp = int(time.time()) * 1000  # Convert to milliseconds
        self.__processed_alerts = set()  # Keep track of processed alert IDs
        self.__processed_event_line_types = set()  # Track event ID + line type combinations
        self.__running = False
        self.__monitor_thread = None
        
        # Validate required environment variables
        if not self.__host or not self.__user_id:
            raise ValueError("Pinnacle host, API host, or user ID not found in environment variables")
    
    def start_monitoring(self, interval=60):
        """
        Start monitoring for new odds alerts in a separate thread
        
        Parameters:
        - interval: Time in seconds between checks for new alerts
        """
        if self.__running:
            print("Monitoring already running")
            return
            
        self.__running = True
        self.__monitor_thread = threading.Thread(
            target=self.__monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.__monitor_thread.start()
        print(f"Started odds monitoring thread with interval of {interval} seconds")
        
    def stop(self):
        """Stop the monitoring thread"""
        if not self.__running:
            print("Monitoring not running")
            return
            
        print("Stopping odds monitoring...")
        self.__running = False
        if self.__monitor_thread and self.__monitor_thread.is_alive():
            self.__monitor_thread.join(timeout=5)
        print("Odds monitoring stopped")
        
    def __monitoring_loop(self, interval):
        """
        Continuous monitoring loop that runs in a separate thread
        
        Parameters:
        - interval: Time in seconds between checks for new alerts
        """
        print(f"Starting odds monitoring with interval of {interval} seconds")
        while self.__running:
            try:
                self.get_odds()
                time.sleep(interval)
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
        # lookback_time = 1747423479000

        print(f"Looking back {lookback_time} milliseconds")
        
        try:
            response = requests.get(
                f"{self.__host}/alerts/{self.__user_id}?dropNotificationsCursor={lookback_time}-0&limitChangeNotificationsCursor={os.getenv('LIMITCHANGENOTIFICATIONCURSOR', lookback_time)}-0&openingLineNotificationsCursor={os.getenv('OPENLINENOTIFICATIONCURSOR', lookback_time)}-1"
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
        line_type = alert.get("lineType", "")
        
        # Create a unique key for this event + line type combination
        event_line_key = f"{alert_id}_{line_type}"
        
        # Skip if we've already processed this event + line type combination
        if event_line_key in self.__processed_event_line_types:
            print(f"Skipping already processed event + line type: {event_line_key}")
            return
            
        # Skip alerts with "(Corners)" in team names
        home_team = alert.get("home", "")
        away_team = alert.get("away", "")
        if "(Corners)" in home_team or "(Corners)" in away_team:
            print(f"Skipping corners market: {home_team} vs {away_team}")
            return
        
        # Skip alerts for matches that have already started (with timezone awareness)
        current_time_ms = int(time.time() * 1000)  # Current time in UTC/GMT
        match_start_time = int(alert.get("starts", 0))  # Pinnacle time is in UTC/GMT
        
        # Add a small buffer (5 minutes) to account for possible delays
        buffer_ms = 5 * 60 * 1000
        
        if match_start_time <= current_time_ms - buffer_ms:
            match_start_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(match_start_time/1000))
            current_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(current_time_ms/1000))
            print(f"Skipping alert for match that already started: {home_team} vs {away_team}")
            print(f"Match start time (GMT): {match_start_datetime}, Current time (GMT): {current_datetime}")
            return
            
        # Shape the data for the bet engine
        shaped_data = self.__shape_alert_data(alert)
        
        # Send to bet engine if valid
        if shaped_data:
            print(f"Sending alert to bet engine: {shaped_data['game']['home']} vs {shaped_data['game']['away']} - {shaped_data['category']['type']}")
            self.__notify_bet_engine(shaped_data)
            
        # Update tracking
        self.__processed_alerts.add(alert_id)
        self.__processed_event_line_types.add(event_line_key)
        self.__last_processed_timestamp = max(self.__last_processed_timestamp, int(alert.get("timestamp", 0)))
        
        # Limit the size of processed alerts set to prevent memory growth
        if len(self.__processed_alerts) > 1000:
            self.__processed_alerts = set(list(self.__processed_alerts)[-1000:])
            
        # Also limit the event + line type combinations set
        if len(self.__processed_event_line_types) > 2000:
            self.__processed_event_line_types = set(list(self.__processed_event_line_types)[-2000:])
    
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
            "eventId": alert.get("eventId"),  # Include the event ID for fetching latest odds
            "starts": alert.get("starts")  # Include the start time for better search matching
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
        Send the shaped alert data to the bet engine
        
        Parameters:
        - shaped_data: The shaped alert data
        """
        try:
            self.bet_engine.notify(shaped_data)
        except Exception as e:
            print(f"Error notifying bet engine: {e}")

if __name__ == "__main__":
    """Test the OddsEngine independently"""
    odds_engine = OddsEngine()
    odds_engine.get_odds()
