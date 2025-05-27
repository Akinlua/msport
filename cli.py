#!/usr/bin/env python3
"""
CLI tool for managing betalert configuration
"""
import json
import argparse
import sys
from typing import Dict, Any, Optional

CONFIG_FILE = "config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {CONFIG_FILE}")
        sys.exit(1)

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to config.json"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving configuration: {e}")
        sys.exit(1)

def add_account(username: str, password: str) -> None:
    """Add a new account with default settings"""
    config = load_config()
    
    # Check if username already exists
    for account in config['accounts']:
        if account['username'] == username:
            print(f"Error: Account with username '{username}' already exists")
            return
    
    new_account = {
        "username": username,
        "password": password,
        "active": True,
        "max_concurrent_bets": 3,
        "min_balance": 100,
        "proxy": None
    }
    
    config['accounts'].append(new_account)
    save_config(config)
    print(f"Account '{username}' added successfully")

def remove_account(username: str) -> None:
    """Remove an account by username"""
    config = load_config()
    
    original_count = len(config['accounts'])
    config['accounts'] = [acc for acc in config['accounts'] if acc['username'] != username]
    
    if len(config['accounts']) == original_count:
        print(f"Error: Account with username '{username}' not found")
        return
    
    save_config(config)
    print(f"Account '{username}' removed successfully")

def list_accounts() -> None:
    """List all accounts"""
    config = load_config()
    
    if not config['accounts']:
        print("No accounts found")
        return
    
    print("\nAccounts:")
    print("-" * 80)
    print(f"{'Username':<15} {'Active':<8} {'Max Bets':<10} {'Min Balance':<12} {'Proxy':<20}")
    print("-" * 80)
    
    for account in config['accounts']:
        proxy_display = account['proxy'] if account['proxy'] else "None"
        print(f"{account['username']:<15} {str(account['active']):<8} {account['max_concurrent_bets']:<10} {account['min_balance']:<12} {proxy_display:<20}")

def set_use_proxies(use_proxies: bool) -> None:
    """Set the global use_proxies setting"""
    config = load_config()
    config['use_proxies'] = use_proxies
    save_config(config)
    print(f"use_proxies set to {use_proxies}")

def add_proxy_to_account(username: str, proxy: str) -> None:
    """Add or update proxy for a specific account"""
    config = load_config()
    
    account_found = False
    for account in config['accounts']:
        if account['username'] == username:
            account['proxy'] = proxy
            account_found = True
            break
    
    if not account_found:
        print(f"Error: Account with username '{username}' not found")
        return
    
    save_config(config)
    print(f"Proxy '{proxy}' added to account '{username}'")

def remove_proxy_from_account(username: str) -> None:
    """Remove proxy from a specific account"""
    config = load_config()
    
    account_found = False
    for account in config['accounts']:
        if account['username'] == username:
            account['proxy'] = None
            account_found = True
            break
    
    if not account_found:
        print(f"Error: Account with username '{username}' not found")
        return
    
    save_config(config)
    print(f"Proxy removed from account '{username}'")

def edit_bet_settings(min_ev: Optional[float] = None, kelly_fraction: Optional[float] = None,
                     min_stake: Optional[int] = None, max_stake: Optional[int] = None,
                     bankroll: Optional[int] = None) -> None:
    """Edit bet settings"""
    config = load_config()
    
    if min_ev is not None:
        config['bet_settings']['min_ev'] = min_ev
    if kelly_fraction is not None:
        config['bet_settings']['kelly_fraction'] = kelly_fraction
    if min_stake is not None:
        config['bet_settings']['min_stake'] = min_stake
    if max_stake is not None:
        config['bet_settings']['max_stake'] = max_stake
    if bankroll is not None:
        config['bet_settings']['bankroll'] = bankroll
    
    save_config(config)
    print("Bet settings updated successfully")

def show_bet_settings() -> None:
    """Show current bet settings"""
    config = load_config()
    settings = config['bet_settings']
    
    print("\nCurrent Bet Settings:")
    print("-" * 30)
    print(f"Min EV: {settings['min_ev']}")
    print(f"Kelly Fraction: {settings['kelly_fraction']}")
    print(f"Min Stake: {settings['min_stake']}")
    print(f"Max Stake: {settings['max_stake']}")
    print(f"Bankroll: {settings['bankroll']}")

def show_config() -> None:
    """Show full configuration"""
    config = load_config()
    print("\nFull Configuration:")
    print("=" * 50)
    print(json.dumps(config, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Betalert Configuration CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add account command
    add_parser = subparsers.add_parser('add-account', help='Add a new account')
    add_parser.add_argument('username', help='Username for the account')
    add_parser.add_argument('password', help='Password for the account')
    
    # Remove account command
    remove_parser = subparsers.add_parser('remove-account', help='Remove an account')
    remove_parser.add_argument('username', help='Username of the account to remove')
    
    # List accounts command
    subparsers.add_parser('list-accounts', help='List all accounts')
    
    # Set use proxies command
    proxy_parser = subparsers.add_parser('set-use-proxies', help='Set global proxy usage')
    proxy_parser.add_argument('value', choices=['true', 'false'], help='Enable or disable proxy usage')
    
    # Add proxy to account command
    add_proxy_parser = subparsers.add_parser('add-proxy', help='Add proxy to an account')
    add_proxy_parser.add_argument('username', help='Username of the account')
    add_proxy_parser.add_argument('proxy', help='Proxy address (e.g., http://proxy:port)')
    
    # Remove proxy from account command
    remove_proxy_parser = subparsers.add_parser('remove-proxy', help='Remove proxy from an account')
    remove_proxy_parser.add_argument('username', help='Username of the account')
    
    # Edit bet settings command
    bet_parser = subparsers.add_parser('edit-bet-settings', help='Edit bet settings')
    bet_parser.add_argument('--min-ev', type=float, help='Minimum expected value')
    bet_parser.add_argument('--kelly-fraction', type=float, help='Kelly fraction')
    bet_parser.add_argument('--min-stake', type=int, help='Minimum stake')
    bet_parser.add_argument('--max-stake', type=int, help='Maximum stake')
    bet_parser.add_argument('--bankroll', type=int, help='Bankroll amount')
    
    # Show bet settings command
    subparsers.add_parser('show-bet-settings', help='Show current bet settings')
    
    # Show full config command
    subparsers.add_parser('show-config', help='Show full configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    if args.command == 'add-account':
        add_account(args.username, args.password)
    elif args.command == 'remove-account':
        remove_account(args.username)
    elif args.command == 'list-accounts':
        list_accounts()
    elif args.command == 'set-use-proxies':
        set_use_proxies(args.value == 'true')
    elif args.command == 'add-proxy':
        add_proxy_to_account(args.username, args.proxy)
    elif args.command == 'remove-proxy':
        remove_proxy_from_account(args.username)
    elif args.command == 'edit-bet-settings':
        if not any([args.min_ev, args.kelly_fraction, args.min_stake, args.max_stake, args.bankroll]):
            print("Error: At least one bet setting must be provided")
            return
        edit_bet_settings(args.min_ev, args.kelly_fraction, args.min_stake, args.max_stake, args.bankroll)
    elif args.command == 'show-bet-settings':
        show_bet_settings()
    elif args.command == 'show-config':
        show_config()

if __name__ == '__main__':
    main() 