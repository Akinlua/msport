#!/usr/bin/env python3
"""
Test script to demonstrate bet placement modes (immediate vs queued)
"""

import time
from bet_engine import BetEngine

def test_bet_placement_modes():
    """Test both immediate and queued bet placement modes"""
    
    # Initialize bet engine
    bet_engine = BetEngine(
        config_file="config.json",
        skip_initial_login=True  # Skip login for testing
    )
    
    print("=== Testing Bet Placement Modes ===")
    
    # Test 1: Check current mode
    current_mode = bet_engine.get_bet_placement_mode()
    print(f"Current bet placement mode: {current_mode}")
    
    # Test 2: Switch to queued mode
    print("\n--- Switching to queued mode ---")
    bet_engine.set_bet_placement_mode(immediate=False)
    
    # Test 3: Switch back to immediate mode
    print("\n--- Switching to immediate mode ---")
    bet_engine.set_bet_placement_mode(immediate=True)
    
    # Test 4: Check queue size
    queue_size = bet_engine.get_queue_size()
    print(f"Current queue size: {queue_size}")
    
    # Test 5: Clear queue if needed
    if queue_size > 0:
        cleared = bet_engine.clear_bet_queue()
        print(f"Cleared {cleared} bets from queue")
    
    print("\n=== Test completed ===")
    
    # Cleanup
    bet_engine.cleanup()

def show_config_example():
    """Show example configuration for bet placement modes"""
    
    config_example = {
        "accounts": [
            {
                "username": "your_username",
                "password": "your_password",
                "active": True,
                "max_concurrent_bets": 3,
                "min_balance": 100
            }
        ],
        "max_total_concurrent_bets": 5,
        "use_proxies": False,
        "immediate_bet_placement": True,  # Set to False for queued mode
        "bet_settings": {
            "min_ev": 0.02,
            "kelly_fraction": 0.3,
            "min_stake": 10,
            "max_stake": 1000000,
            "max_pinnacle_odds": 3.0,
            "odds_based_stakes": {
                "low_odds": {
                    "max_odds": 1.99,
                    "min_stake": 6000,
                    "max_stake": 12000
                },
                "medium_odds": {
                    "min_odds": 2.0,
                    "max_odds": 3.0,
                    "min_stake": 3000,
                    "max_stake": 7000
                }
            },
            "bankroll": 1000
        }
    }
    
    print("=== Configuration Example ===")
    print("To change bet placement mode, update your config.json:")
    print(f"  'immediate_bet_placement': True   # For immediate placement")
    print(f"  'immediate_bet_placement': False  # For queued placement")
    print("\nOr use the API methods:")
    print(f"  bet_engine.set_bet_placement_mode(immediate=True)   # Immediate")
    print(f"  bet_engine.set_bet_placement_mode(immediate=False)  # Queued")
    print(f"  bet_engine.get_bet_placement_mode()                 # Check current mode")
    print(f"  bet_engine.get_queue_size()                        # Check queue size")
    print(f"  bet_engine.clear_bet_queue()                       # Clear queue")

if __name__ == "__main__":
    show_config_example()
    print("\n" + "="*50 + "\n")
    test_bet_placement_modes() 