#!/usr/bin/env python3
import os
import signal
import sys
import time
import dotenv
from bet_engine import BetEngine
from odds_engine import OddsEngine

# Load environment variables
dotenv.load_dotenv()

def handle_interrupt(signum, frame):
    """Handle keyboard interrupts gracefully"""
    print("\nShutting down application...")
    sys.exit(0)

def main():
    """
    Main application entry point
    
    Initializes the bet engine and odds engine,
    then starts monitoring for odds alerts
    """
    print("Starting BetAlert application...")
    
    try:
        # Initialize bet engine
        print("Initializing bet engine...")
        bet_engine = BetEngine(
            headless=os.getenv("ENVIRONMENT") == "production",
            bet_host=os.getenv("BETNAIJA_HOST"),
            bet_api_host=os.getenv("BETNAIJA_API_HOST"),
            min_ev=float(os.getenv("MIN_EV", "0"))
        )
        
        # Initialize odds engine with the bet engine
        print("Initializing odds engine...")
        odds_engine = OddsEngine(
            bet_engine=bet_engine,
            host=os.getenv("PINNACLE_ODDS_HOST"),
            user_id=os.getenv("PINNACLE_USER_ID")
        )
        
        # Register interrupt handler for clean shutdown
        signal.signal(signal.SIGINT, handle_interrupt)
        
        # Start monitoring for odds alerts
        odds_check_interval = int(os.getenv("ODDS_CHECK_INTERVAL", "60"))
        print(f"Starting odds monitoring with {odds_check_interval} second intervals...")
        odds_engine.start_monitoring(interval=odds_check_interval)
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
