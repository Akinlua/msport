#!/usr/bin/env python3
"""
Test script for enhanced Cloudflare Turnstile CAPTCHA detection
This tests the new detection logic for shadow DOM and iframe scenarios
"""

from captcha_solver import CaptchaSolver
from selenium_script import WebsiteOpener
import time

def test_enhanced_captcha_detection():
    """Test the enhanced CAPTCHA detection on MSport using existing browser"""
    print("🧪 Testing Enhanced CAPTCHA Detection with Existing Browser")
    print("=" * 60)
    
    print("📋 Instructions:")
    print("1. Open Chrome browser manually")
    print("2. Navigate to https://www.msport.com/ng/web/welcome")
    print("3. Keep the browser open and run this test")
    print("4. The test will connect to your existing Chrome session")
    print("-" * 60)
    
    input("Press Enter when you have Chrome open with MSport loaded...")
    
    try:
        # Use our enhanced WebsiteOpener with existing browser connection
        website_opener = WebsiteOpener(
            headless=False,
            proxy=None,  # You can enable proxy: "http://154.91.171.203:3129"
            use_existing_browser=True
        )
        
        driver = website_opener.driver
        
        # Initialize CAPTCHA solver
        captcha_solver = CaptchaSolver(api_key="faf467050c2932f855a1a3ef21286af0")
        
        print("🔗 Connected to existing Chrome browser!")
        print(f"📄 Current page: {driver.current_url}")
        
        # Navigate to MSport if not already there
        if "msport.com" not in driver.current_url.lower():
            print("🌐 Navigating to MSport...")
            driver.get("https://www.msport.com/ng/web/welcome")
            time.sleep(5)
        
        print("\n🔍 Testing enhanced CAPTCHA detection...")
        
        # Test the enhanced detection
        is_present, sitekey, response_field = captcha_solver.detect_turnstile_captcha(driver)
        
        if is_present:
            print(f"✅ CAPTCHA Detection SUCCESS!")
            print(f"   Sitekey: {sitekey}")
            print(f"   Response field found: {response_field is not None}")
            
            if response_field:
                field_name = response_field.get_attribute('name')
                field_id = response_field.get_attribute('id')
                field_type = response_field.get_attribute('type')
                print(f"   Response field details:")
                print(f"     - Name: {field_name}")
                print(f"     - ID: {field_id}")
                print(f"     - Type: {field_type}")
            
            # Ask user if they want to test CAPTCHA solving
            solve_captcha = input("\n❓ Do you want to test CAPTCHA solving? (y/n): ").lower().strip()
            
            if solve_captcha in ['y', 'yes']:
                print("\n🔄 Testing CAPTCHA solving...")
                
                try:
                    solved = captcha_solver.solve_turnstile_captcha(
                        driver=driver,
                        page_url=driver.current_url,
                        max_retries=1  # Just one attempt for testing
                    )
                    
                    if solved:
                        print("✅ CAPTCHA solving SUCCESS!")
                        
                        # Check if token was injected
                        if response_field:
                            token_value = response_field.get_attribute('value')
                            if token_value and len(token_value) > 10:
                                print(f"✅ Token successfully injected: {token_value[:50]}...")
                            else:
                                print("⚠️  Token injection may have failed")
                                
                        print("\n🎯 Check your browser - the CAPTCHA should now be solved!")
                        
                    else:
                        print("❌ CAPTCHA solving failed")
                        
                except Exception as e:
                    print(f"❌ CAPTCHA solving error: {e}")
            else:
                print("⏭️  Skipping CAPTCHA solving test")
                
        else:
            print("❌ CAPTCHA Detection FAILED")
            print("   No CAPTCHA found with enhanced detection methods")
            
            # Try manual inspection
            print("\n🔍 Manual inspection of page elements...")
            
            # Check for any iframes
            iframes = driver.find_elements("tag name", "iframe")
            print(f"   Found {len(iframes)} iframes")
            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute("src") or "No src"
                print(f"     Iframe {i+1}: {src[:100]}...")
            
            # Check for common CAPTCHA text
            page_source = driver.page_source
            captcha_indicators = [
                "turnstile", "cloudflare", "verify you are human", 
                "cf-turnstile", "challenge", "captcha"
            ]
            
            found_indicators = []
            for indicator in captcha_indicators:
                if indicator.lower() in page_source.lower():
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"   Found CAPTCHA indicators in page: {found_indicators}")
            else:
                print("   No CAPTCHA indicators found in page source")
        
        # Keep browser session alive
        print(f"\n⏳ Test completed! Your browser session remains open.")
        print("   You can continue using Chrome normally.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def start_chrome_with_debugging():
    """Helper function to start Chrome with remote debugging"""
    print("🚀 Starting Chrome with Remote Debugging")
    print("=" * 50)
    
    import subprocess
    import os
    
    # Chrome path for macOS
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    if not os.path.exists(chrome_path):
        print("❌ Chrome not found at expected path")
        print("Please start Chrome manually with this command:")
        print('"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222')
        return
    
    # Chrome arguments for debugging
    chrome_args = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    
    try:
        print("🚀 Starting Chrome with remote debugging...")
        subprocess.Popen(chrome_args)
        print("✅ Chrome started! You can now run the CAPTCHA test.")
        print("📌 Chrome Debug Port: 9222")
        
    except Exception as e:
        print(f"❌ Failed to start Chrome: {e}")

if __name__ == "__main__":
    print("🚀 Enhanced CAPTCHA Detection with Existing Browser")
    print("\nChoose an option:")
    print("1. Test with existing Chrome browser")
    print("2. Start Chrome with debugging and then test")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        start_chrome_with_debugging()
        input("\nPress Enter after Chrome has started and you've navigated to MSport...")
    
    test_enhanced_captcha_detection()
    print("✅ Test completed!") 