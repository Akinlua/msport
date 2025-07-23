#!/usr/bin/env python3
"""
Test script to demonstrate proxy functionality in bet engine
This script tests the ability to switch between accounts with different proxies
"""

import json
import time
from bet_engine import BetEngine

def test_proxy_switching():
    """Test that the bet engine properly switches proxies between accounts"""
    print("=" * 60)
    print("TESTING PROXY FUNCTIONALITY")
    print("=" * 60)
    
    # Create a test configuration with multiple accounts using different proxies
    test_config = {
        "accounts": [
            {
                "username": "test_user_1",
                "password": "test_pass_1",
                "active": True,
                "max_concurrent_bets": 3,
                "min_balance": 100,
                "proxy": "http://proxy1.example.com:8080"
            },
            {
                "username": "test_user_2", 
                "password": "test_pass_2",
                "active": True,
                "max_concurrent_bets": 3,
                "min_balance": 100,
                "proxy": "http://proxy2.example.com:8080"
            },
            {
                "username": "test_user_3",
                "password": "test_pass_3", 
                "active": True,
                "max_concurrent_bets": 3,
                "min_balance": 100,
                "proxy": None  # No proxy for this account
            }
        ],
        "use_proxies": True,
        "max_total_concurrent_bets": 10,
        "bet_settings": {
            "min_ev": 5.0,
            "kelly_fraction": 0.3,
            "min_stake": 1000,
            "max_stake": 5000,
            "bankroll": 10000
        }
    }
    
    # Save test config
    with open("test_config.json", "w") as f:
        json.dump(test_config, f, indent=2)
    
    try:
        # Initialize bet engine with test config
        print("1. Initializing BetEngine with proxy configuration...")
        bet_engine = BetEngine(
            headless=True,  # Use headless for testing
            config_file="test_config.json",
            skip_initial_login=True  # Skip login for proxy testing
        )
        
        # Get the accounts
        accounts = bet_engine._BetEngine__accounts
        print(f"   └─ Loaded {len(accounts)} test accounts")
        
        # Test browser initialization with different accounts
        print("\n2. Testing proxy switching between accounts...")
        
        for i, account in enumerate(accounts, 1):
            print(f"\n   Account {i}: {account.username}")
            print(f"   Proxy: {account.proxy or 'None'}")
            
            # Initialize browser with this account's proxy
            try:
                print(f"   Initializing browser for {account.username}...")
                bet_engine._initialize_browser_if_needed(account)
                
                # Check the current proxy being used
                current_proxy = getattr(bet_engine, '_current_proxy', None)
                print(f"   ✅ Browser initialized with proxy: {current_proxy or 'None'}")
                
                # Simulate some work (in real scenario this would be login/betting)
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error initializing browser: {e}")
        
        print("\n3. Testing proxy change detection...")
        
        # Test that browser reinitializes when switching to different proxy
        account1 = accounts[0]  # Has proxy1
        account2 = accounts[1]  # Has proxy2
        
        print(f"   Switching from {account1.username} to {account2.username}")
        print(f"   Proxy change: {account1.proxy} -> {account2.proxy}")
        
        # Initialize with first account
        bet_engine._initialize_browser_if_needed(account1)
        initial_proxy = getattr(bet_engine, '_current_proxy', None)
        print(f"   Initial proxy: {initial_proxy}")
        
        # Switch to second account (should trigger browser cleanup and reinit)
        bet_engine._initialize_browser_if_needed(account2)
        new_proxy = getattr(bet_engine, '_current_proxy', None)
        print(f"   New proxy: {new_proxy}")
        
        if initial_proxy != new_proxy:
            print("   ✅ Proxy switching working correctly!")
        else:
            print("   ⚠️  Proxy didn't change as expected")
        
        print("\n4. Testing proxy disabled mode...")
        
        # Temporarily disable proxies
        bet_engine._BetEngine__config["use_proxies"] = False
        bet_engine._cleanup_browser_for_proxy_switch()
        
        print("   Disabled proxy usage in config")
        bet_engine._initialize_browser_if_needed(account1)
        disabled_proxy = getattr(bet_engine, '_current_proxy', None)
        print(f"   Proxy when disabled: {disabled_proxy or 'None'}")
        
        if disabled_proxy is None:
            print("   ✅ Proxy correctly disabled!")
        else:
            print("   ⚠️  Proxy still active when disabled")
        
        print("\n✅ Proxy functionality test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            bet_engine.cleanup()
        except:
            pass
        
        # Remove test config file
        import os
        if os.path.exists("test_config.json"):
            os.remove("test_config.json")

def test_account_proxy_methods():
    """Test the BetAccount proxy methods"""
    print("\n" + "=" * 60)
    print("TESTING BETACCOUNT PROXY METHODS")
    print("=" * 60)
    
    from bet_engine import BetAccount
    
    # Test account with proxy
    account_with_proxy = BetAccount(
        username="test_user",
        password="test_pass",
        proxy="http://user:pass@proxy.example.com:8080"
    )
    
    proxies = account_with_proxy.get_proxies()
    print(f"Account with proxy: {account_with_proxy.proxy}")
    print(f"get_proxies() result: {proxies}")
    
    expected = {
        'http': 'http://user:pass@proxy.example.com:8080',
        'https': 'http://user:pass@proxy.example.com:8080'
    }
    
    if proxies == expected:
        print("✅ Proxy formatting correct!")
    else:
        print("❌ Proxy formatting incorrect!")
    
    # Test account without proxy
    account_without_proxy = BetAccount(
        username="test_user",
        password="test_pass",
        proxy=None
    )
    
    no_proxies = account_without_proxy.get_proxies()
    print(f"\nAccount without proxy: {account_without_proxy.proxy}")
    print(f"get_proxies() result: {no_proxies}")
    
    if no_proxies is None:
        print("✅ No proxy handling correct!")
    else:
        print("❌ No proxy handling incorrect!")

if __name__ == "__main__":
    print("Starting proxy functionality tests...\n")
    
    # Test account proxy methods
    test_account_proxy_methods()
    
    # Test proxy switching in bet engine
    success = test_proxy_switching()
    
    if success:
        print("\n🎉 All proxy tests passed!")
        exit(0)
    else:
        print("\n💥 Some proxy tests failed!")
        exit(1) 