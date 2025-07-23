#!/usr/bin/env python3
"""
Connect to your default Chrome browser session
This script will connect Selenium to your regular Chrome browser with all your profiles, extensions, etc.
"""

import os
import subprocess
import time
from selenium_script import WebsiteOpener

def get_default_chrome_profile_path():
    """Get the path to the default Chrome profile on macOS"""
    home_dir = os.path.expanduser("~")
    chrome_profile_path = os.path.join(home_dir, "Library", "Application Support", "Google", "Chrome")
    return chrome_profile_path

def start_chrome_with_default_profile():
    """Start Chrome with remote debugging using the default profile"""
    
    print("🚀 Starting Chrome with Default Profile")
    print("=" * 50)
    
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    debug_port = 9222
    
    if not os.path.exists(chrome_path):
        print("❌ Chrome not found!")
        return False
    
    # Use your default Chrome profile
    default_profile = get_default_chrome_profile_path()
    
    chrome_args = [
        chrome_path,
        f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={default_profile}",  # Use your default profile
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.msport.com/ng/web/welcome"
    ]
    
    try:
        print(f"🌐 Starting Chrome with your default profile:")
        print(f"   Profile Path: {default_profile}")
        print(f"   Debug Port: {debug_port}")
        print(f"   Opening: MSport")
        
        # Start Chrome with your default profile
        process = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print("✅ Chrome started with your default profile!")
        print("   You should see all your bookmarks, extensions, saved passwords, etc.")
        
        # Wait a moment for Chrome to start
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Chrome: {e}")
        return False

def test_connection():
    """Test connecting to Chrome with default profile"""
    
    print("\n🔗 Testing Selenium Connection")
    print("=" * 40)
    
    try:
        # Connect to Chrome using your default profile
        website_opener = WebsiteOpener(
            headless=False,
            proxy=None,  # You can add proxy here if needed
            use_existing_browser=True
        )
        
        driver = website_opener.driver
        
        print("✅ Successfully connected to your default Chrome!")
        print(f"📄 Current URL: {driver.current_url}")
        
        # Check if we're on MSport
        if "msport" in driver.current_url.lower():
            print("✅ Already on MSport!")
        else:
            print("🌐 Navigating to MSport...")
            driver.get("https://www.msport.com/ng/web/welcome")
            time.sleep(3)
            print("✅ Navigated to MSport!")
        
        print("\n🎉 Success! Your Selenium script is now connected to your default Chrome browser")
        print("   All your extensions, saved passwords, and settings are available!")
        
        # Keep the connection alive
        input("\nPress Enter to close the connection...")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Connect to Default Chrome Profile")
    print("=" * 45)
    
    print("\n📋 This script will:")
    print("1. Start Chrome with your default profile (all your data)")
    print("2. Enable remote debugging")
    print("3. Connect Selenium to your Chrome session")
    print("4. Navigate to MSport")
    
    choice = input("\n❓ Continue? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        if start_chrome_with_default_profile():
            test_connection()
        else:
            print("💥 Failed to start Chrome")
    else:
        print("✋ Cancelled by user") 