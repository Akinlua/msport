#!/usr/bin/env python3
import os
import signal
import sys
import time
import dotenv
import traceback
from bet_engine import BetEngine
from odds_engine import OddsEngine

# Load environment variables
dotenv.load_dotenv()

def main():
    """
    Main entry point for the BetAlert application.
    Initializes the odds engine and bet engine, then starts monitoring for odds alerts.
    """
    print("Starting BetAlert application...")
    
    try:
        # Initialize the bet engine (handles placing bets on Bet9ja)
        print("Initializing bet engine...")
        bet_engine = BetEngine(
            headless=os.getenv("ENVIRONMENT") == "production",
            config_file="config.json"
        )
        
        # Initialize the odds engine (handles monitoring Pinnacle for odds alerts)
        print("Initializing odds engine...")
        odds_engine = OddsEngine(
            bet_engine=bet_engine,
            pinnacle_host=os.getenv("PINNACLE_HOST"),
            pinnacle_api_host=os.getenv("PINNACLE_API_HOST")
        )
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\nShutting down BetAlert application...")
            odds_engine.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start monitoring for odds alerts
        print("Starting to monitor for odds alerts...")
        odds_engine.start_monitoring()
        
        # Keep the main thread running
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error in main application: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
