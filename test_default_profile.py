#!/usr/bin/env python3
"""
Simple test to verify that Selenium uses your default Chrome profile
This should open Chrome with all your bookmarks, extensions, saved passwords, etc.
"""

from selenium_script import WebsiteOpener
import time

def test_default_profile():
    """Test that Chrome opens with default profile"""
    print("🧪 Testing Default Chrome Profile")
    print("=" * 40)
    
    print("🚨 CRITICAL: You MUST close ALL Chrome windows first!")
    print("   📋 Steps:")
    print("   1. Close ALL Chrome browser windows")
    print("   2. Make sure Chrome is completely closed (check Activity Monitor)")
    print("   3. Then run this test")
    print("   ")
    print("   ⚠️  If Chrome is still running, you'll get profile lock errors!")
    
    choice = input("\n❓ Have you completely closed ALL Chrome windows and processes? (y/n): ").lower().strip()
    if choice not in ['y', 'yes']:
        print("❌ Please close ALL Chrome windows/processes first, then run again.")
        print("💡 Tip: Check Activity Monitor to make sure Chrome is not running")
        return False
    
    print("\n📋 This test will:")
    print("1. Open Chrome with your default profile")
    print("2. Navigate to MSport")
    print("3. Check if your extensions/bookmarks are visible")
    print("4. Test CAPTCHA detection")
    
    try:
        # Create WebsiteOpener - this should use your default profile
        print("\n🚀 Starting Chrome with default profile...")
        opener = WebsiteOpener(
            headless=False,
            proxy="http://154.91.171.203:3129"  # Your proxy
        )
        
        driver = opener.driver
        
        print("✅ Chrome started!")
        print("👀 Check your Chrome window - you should see:")
        print("   - Your bookmarks bar")
        print("   - Your extensions")
        print("   - Your saved passwords available")
        
        # Navigate to MSport
        print("\n🌐 Navigating to MSport...")
        driver.get("https://www.msport.com/ng/web/welcome")
        time.sleep(5)
        
        print(f"📄 Current URL: {driver.current_url}")
        
        # Test CAPTCHA detection
        print("\n🔍 Testing CAPTCHA detection...")
        from captcha_solver import CaptchaSolver
        
        captcha_solver = CaptchaSolver(api_key="faf467050c2932f855a1a3ef21286af0")
        is_present, sitekey, response_field = captcha_solver.detect_turnstile_captcha(driver)
        
        if is_present:
            print("✅ CAPTCHA detected successfully!")
            print(f"   Sitekey: {sitekey}")
            print(f"   Response field: {'Found' if response_field else 'Not found'}")
        else:
            print("❌ No CAPTCHA detected")
        
        print("\n✅ Test completed successfully!")
        print("📋 Verify in your Chrome window:")
        print("   - Are your bookmarks visible?")
        print("   - Are your extensions loaded?")
        print("   - Is MSport loaded correctly?")
        
        input("\nPress Enter to close Chrome...")
        
        # Close browser
        driver.quit()
        print("🔒 Chrome closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Default Chrome Profile Test")
    print("=" * 35)
    
    success = test_default_profile()
    
    if success:
        print("\n🎉 Default profile test completed!")
    else:
        print("\n💥 Test failed!") 