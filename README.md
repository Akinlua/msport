# BetAlert

An automated sports betting application that monitors Pinnacle for odds alerts and places value bets on Bet9ja when positive expected value (EV) is detected.

## Overview

BetAlert integrates with Pinnacle's odds API to receive real-time alerts for betting opportunities. When an alert is received, the application:

1. Searches for the corresponding match on Bet9ja
2. Finds the appropriate betting market (spread, moneyline, or total)
3. Calculates the Expected Value (EV) by comparing Bet9ja's odds with Pinnacle's no-vig prices
4. Places a bet automatically if the EV is positive and above the configured threshold

## Requirements

- Python 3.7 or higher
- Chrome browser
- ChromeDriver (compatible with your Chrome version)
- Access to Pinnacle odds API
- Bet9ja account

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/betalert.git
   cd betalert
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file with your credentials and configuration.

## Configuration

The application is configured through environment variables in the `.env` file:

- `ENVIRONMENT`: Set to "development" for visible browser or "production" for headless mode
- `BETNAIJA_HOST` and `BETNAIJA_API_HOST`: Bet9ja website URLs
- `BETNAIJA_USERNAME` and `BETNAIJA_PASSWORD`: Your Bet9ja login credentials
- `PINNACLE_ODDS_HOST`: Pinnacle odds API URL
- `PINNACLE_USER_ID`: Your Pinnacle user ID
- `MIN_EV`: Minimum EV percentage required to place a bet (e.g., 2.0 for 2%)
- `BET_STAKE`: Default amount to stake on each bet
- `ODDS_CHECK_INTERVAL`: Time in seconds between checks for new odds alerts
- `CHROME_DRIVER_PATH`: Optional path to ChromeDriver (auto-detects if not provided)

## Usage

Start the application:

```
python main.py
```

The application will:
1. Log in to your Bet9ja account
2. Start monitoring Pinnacle for odds alerts
3. Process alerts and place bets automatically when positive EV is found
4. Log all activities to the console

Press `Ctrl+C` to stop the application gracefully.

## Components

- `main.py`: Application entry point
- `odds_engine.py`: Handles fetching odds from Pinnacle
- `bet_engine.py`: Manages bet placement on Bet9ja
- `selenium_script.py`: Base class for browser automation
- `utils/`: Helper functions for EV calculations

## Supported Bet Types

The application supports three main bet types:
- **Moneyline**: Home, Away, or Draw
- **Spread**: Home or Away with a point spread
- **Total**: Over or Under with a total points value

## Customization

You can customize the application behavior by:
- Adjusting the minimum EV threshold in the `.env` file
- Modifying the search strategies in `BetEngine.__search_event`
- Changing the bet amount in `BetEngine.__place_bet`
- Adding support for additional bet types

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Sports betting may not be legal in your jurisdiction. Use at your own risk. 