from odds_engine import *
from bet_engine import *
import dotenv
import os
dotenv.load_dotenv()

time_to_sleep=int(os.getenv("TIME_TO_SLEEP"))
if __name__ == "__main__":
    """ Main """
    #make this text green
    print("\033[92m" + "====== Initializing App =====\033[0m")
    counter=0
    bet_engine = BetEngine()
    odds_engine = OddsEngine(betEngine=bet_engine)
    #thread getting odds.
    while True:
        try:
            print( f"\033[92m" + f"[+] Getting odds for the {counter} time" + "\033[0m")
            odds_engine.get_odds()
            counter+=1
            print(f"\033[92m" + f"[!] Sleeping for {time_to_sleep} seconds" + "\033[0m")
            time.sleep(time_to_sleep)
        except Exception as e:
            print(f"\033[91m" + f"[-] Error: {e}" + "\033[0m")
            time.sleep(time_to_sleep)
