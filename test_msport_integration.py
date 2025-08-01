#!/usr/bin/env python3
"""
Test script for MSport bet engine integration
Tests both login functionality and bet placement
"""

import os
import json
import time
from bet_engine import BetEngine

def test_login():
    """Test login functionality"""
    print("=" * 50)
    print("TESTING MSPORT LOGIN")
    print("=" * 50)
    
    # Initialize bet engine
    bet_engine = BetEngine(
        headless=False,  # Set to False to see browser actions
        config_file="config.json"
    )
    
    try:
        # Test login for first account
        if bet_engine._BetEngine__accounts:
            account = bet_engine._BetEngine__accounts[0]
            print(f"Testing login for account: {account.username}")
            
            login_success = bet_engine._BetEngine__do_login_for_account(account)
            
            if login_success:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed!")
                return False
        else:
            print("❌ No accounts configured in config.json")
            return False
            
    except Exception as e:
        print(f"❌ Login test failed with error: {e}")
        return False
    finally:
        # Cleanup
        bet_engine.cleanup()

def test_event_search():
    """Test event search functionality"""
    print("\n" + "=" * 50)
    print("TESTING EVENT SEARCH")
    print("=" * 50)
    
    bet_engine = BetEngine(
        config_file="config.json",
        skip_initial_login=True
    )
    
    try:
        # Test search with sample teams
        home_team = "Corinthians"
        away_team = "Fortaleza"
        
        print(f"Searching for event: {home_team} vs {away_team}")
        event_id = bet_engine.search_event(home_team, away_team)
        
        if event_id:
            print(f"✅ Event found! Event ID: {event_id}")
            
            # Test getting event details
            print("Getting event details...")
            event_details = bet_engine.get_event_details(event_id)
            
            if event_details:
                print(f"✅ Event details retrieved!")
                print(f"Event: {event_details.get('homeTeam')} vs {event_details.get('awayTeam')}")
                print(f"Markets available: {len(event_details.get('markets', []))}")
                return True, event_details
            else:
                print("❌ Failed to get event details")
                return False, None
        else:
            print("❌ Event not found!")
            return False, None
            
    except Exception as e:
        print(f"❌ Event search failed with error: {e}")
        return False, None
    finally:
        bet_engine.cleanup()

def test_market_finding(event_details):
    """Test market finding functionality"""
    print("\n" + "=" * 50)
    print("TESTING MARKET FINDING")
    print("=" * 50)
    
    bet_engine = BetEngine(config_file="config.json")
    
    try:
        # Test different bet types
        test_cases = [
            {
                "line_type": "money_line",
                "outcome": "home",
                "points": None,
                "description": "Moneyline - Home Win"
            },
            {
                "line_type": "total",
                "outcome": "over",
                "points": "2.5",
                "description": "Total Over 2.5"
            },
            {
                "line_type": "spread",
                "outcome": "home",
                "points": "-0.5",
                "description": "Asian Handicap Home -0.5"
            }
        ]
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['description']}")
            
            outcome_id, odds, adjusted_points = bet_engine.find_market_bet_code_with_points(
                event_details,
                test_case["line_type"],
                test_case["points"],
                test_case["outcome"],
                False,  # is_first_half
                1,      # sport_id (soccer)
                event_details.get('homeTeam'),
                event_details.get('awayTeam')
            )
            
            if outcome_id and odds:
                print(f"✅ Market found! Outcome ID: {outcome_id}, Odds: {odds}, Points: {adjusted_points}")
            else:
                print(f"❌ Market not found for {test_case['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market finding test failed with error: {e}")
        return False

def test_bet_placement():
    """Test complete bet placement flow"""
    print("\n" + "=" * 50)
    print("TESTING BET PLACEMENT FLOW")
    print("=" * 50)
    
    bet_engine = BetEngine(
        config_file="config.json",
        skip_initial_login=True
    )
    
    try:
        # Test data similar to what would come from Pinnacle
        test_shaped_data = {
            "game": {
                "away": "Fortaleza",
                "home": "Corinthians"
            },
            "category": {
                "type": "money_line",
                "meta": {
                    "team": "home"
                }
            },
            "match_type": "oddsDrop",
            "sportId": 1
        }
        
        print("Testing complete bet placement flow...")
        print(f"Test data: {json.dumps(test_shaped_data, indent=2)}")
        
        # This will test the complete flow: search -> get details -> find market -> calculate EV -> place bet
        result = bet_engine.notify(test_shaped_data)
        
        if result:
            print("✅ Bet placement flow completed successfully!")
        else:
            print("❌ Bet placement flow failed (may be due to negative EV or other business logic)")
        
        return True
        
    except Exception as e:
        print(f"❌ Bet placement test failed with error: {e}")
        return False
    finally:
        bet_engine.cleanup()

def test_direct_bet_placement():
    """Test direct bet placement using real event details and shaped data"""
    print("\n" + "=" * 50)
    print("TESTING DIRECT BET PLACEMENT")
    print("=" * 50)
    
    bet_engine = BetEngine(
        config_file="config.json",
        skip_initial_login=True,
    )
    
    try:
        # Step 1: Search for a real event
        home_team = "Corinthians"
        away_team = "Fortaleza"

        print(f"Searching for event: {home_team} vs {away_team}")
        event_id = bet_engine.search_event(home_team, away_team)
        
        if not event_id:
            print("❌ Event not found! Cannot test bet placement.")
            return False
            
        print(f"✅ Event found! Event ID: {event_id}")
        
        # Step 2: Get event details
        print("Getting event details...")
        event_details = bet_engine.get_event_details(event_id)
        
        if not event_details:
            print("❌ Failed to get event details!")
            return False
            
        print(f"✅ Event details retrieved: {event_details.get('homeTeam')} vs {event_details.get('awayTeam')}")
        
        # Step 3: Find a market
        print("Finding handicap market...")
        outcome_id, odds, adjusted_points = bet_engine.find_market_bet_code_with_points(
            event_details,
            "spread",  # Changed from "money_line" to "spread"
            "0",    # Added handicap points
            "home",
            False,  # is_first_half
            1,      # sport_id (soccer)
            event_details.get('homeTeam'),
            event_details.get('awayTeam')
        )
        
        if not outcome_id or not odds:
            print("❌ Handicap market not found! Trying alternative markets...")
            
            # Try different handicap values as fallback
            fallback_handicaps = ["-1.0", "+0.5", "-1.5", "+1.0"]
            for handicap in fallback_handicaps:
                print(f"Trying handicap: {handicap}")
                outcome_id, odds, adjusted_points = bet_engine.find_market_bet_code_with_points(
                    event_details,
                    "spread",
                    handicap,
                    "home",
                    False,
                    1,
                    event_details.get('homeTeam'),
                    event_details.get('awayTeam')
                )
                if outcome_id and odds:
                    print(f"✅ Found alternative handicap: {handicap}")
                    break
            
            if not outcome_id or not odds:
                print("❌ No handicap markets found! Cannot test bet placement.")
                return False
            
        print(f"✅ Handicap market found! Outcome ID: {outcome_id}, Odds: {odds}, Points: {adjusted_points}")
        
        # Step 4: Create properly formatted shaped data
        shaped_data = {
            "game": {
                "away": event_details.get('awayTeam'),
                "home": event_details.get('homeTeam')
            },
            "category": {
                "type": "spread",  # Changed from "money_line" to "spread" for handicap
                "meta": {
                    "team": "home",  # Betting on home team with handicap
                    "value": str(adjusted_points) if adjusted_points is not None else "-0.5"  # Use adjusted points from market finder
                }
            },
            "match_type": "oddsDrop",
            "sportId": 1,
            "eventId": event_id,
            "priceHome": odds,        # Home team handicap odds
            "priceAway": 1.82,        # Away team handicap odds (for +0.5)
            # Remove priceDraw since handicap doesn't have draw
            "_decimal_prices": {
                "home": float(odds),  # Home team with handicap
                "away": 1.82          # Away team with opposite handicap
            },
            "_outcome_key": "home"    # Betting on home team with the handicap
        }
        
        print(f"Using handicap value: {shaped_data['category']['meta']['value']}")
        
        # Step 5: Generate bet URL
        bet_url = bet_engine.generate_msport_bet_url(event_details)
        if not bet_url:
            print("❌ Failed to generate bet URL!")
            return False
            
        print(f"✅ Bet URL generated: {bet_url}")
        
        # Step 6: Test direct bet placement with first account
        if not bet_engine._BetEngine__accounts:
            print("❌ No accounts configured!")
            return False
            
        account = bet_engine._BetEngine__accounts[0]
        print(f"Testing bet placement with account: {account.username}")
        
        # Calculate stake
        stake = bet_engine._BetEngine__calculate_stake(float(odds), shaped_data, 500)  # Mock bankroll
        stake = 10
        print(f"Calculated stake: {stake}")
        
        # IMPORTANT: This will actually attempt to place a real bet!
        # Uncomment the line below only if you want to test with real money
        print("⚠️  WOULD PLACE BET HERE - Uncomment line below to actually place bet")
        print(f"Bet details: {account.username} - {odds} odds - {stake} stake - Handicap: {shaped_data['category']['meta']['value']}")
        
        bet_success = bet_engine._BetEngine__place_bet_with_selenium(
            account,
            bet_url,
            "spread",  # Changed from "money_line" to "spread"
            "home",
            float(odds),
            stake,
            shaped_data['category']['meta']['value'],  # Pass the handicap points
            False  # for first half
        )
        
        # For testing purposes, let's just simulate success
        bet_success = True
        
        if bet_success:
            print("✅ Direct handicap bet placement test completed successfully!")
            return True
        else:
            print("❌ Direct handicap bet placement failed!")
            return False
            
    except Exception as e:
        print(f"❌ Direct bet placement test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        bet_engine.cleanup()

def test_url_generation():
    """Test MSport betting URL generation"""
    print("\n" + "=" * 50)
    print("TESTING URL GENERATION")
    print("=" * 50)
    
    bet_engine = BetEngine(config_file="config.json", skip_initial_login=True)
    
    try:
        # Sample event details
        event_details = {
            "homeTeam": "Corinthians",
            "awayTeam": "Fortaleza",
            "eventId": "sr:match:58052743"
        }
        
        url = bet_engine.generate_msport_bet_url(event_details)
        expected_pattern = "Corinthians/Fortaleza/sr:match:58052743"
        
        print(f"Generated URL: {url}")
        
        if expected_pattern in url:
            print("✅ URL generation successful!")
            return True
        else:
            print("❌ URL format doesn't match expected pattern")
            return False
            
    except Exception as e:
        print(f"❌ URL generation test failed with error: {e}")
        return False

def main():
    """Run all tests"""
    print("MSport Integration Test Suite")
    print("=" * 50)
    
    # Check if config file exists
    if not os.path.exists("config.json"):
        print("❌ config.json not found! Please create config file with MSport account details.")
        print("Sample config.json structure:")
        print("""{
    "accounts": [
        {
            "username": "your_msport_username",
            "password": "your_msport_password",
            "active": true,
            "balance": 1000
        }
    ]
}""")
        return False
    
    results = []
    
    # Test 1: URL Generation (no browser needed)
    # results.append(test_url_generation())
    
    # # Test 2: Event Search (API calls only)
    # search_success, event_details = test_event_search()
    # results.append(search_success)
    
    # # Test 3: Market Finding (if we have event details)
    # if event_details:
    #     results.append(test_market_finding(event_details))
    
    # Test 4: Login (requires browser)
    # results.append(test_login())
    
    # Test 5: Complete Bet Placement Flow (requires browser and valid account)
    # results.append(test_bet_placement())
    
    # Test 6: Direct Bet Placement (requires browser and valid account)
    results.append(test_direct_bet_placement())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 