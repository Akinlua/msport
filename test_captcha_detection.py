#!/usr/bin/env python3
"""
Test script for enhanced Cloudflare Turnstile CAPTCHA detection
This tests the new detection logic for shadow DOM and iframe scenarios
"""

from captcha_solver import CaptchaSolver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_enhanced_captcha_detection():
    """Test the enhanced CAPTCHA detection on MSport"""
    print("🧪 Testing Enhanced CAPTCHA Detection")
    print("=" * 50)
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Add proxy if needed (you can enable this)
    # chrome_options.add_argument("--proxy-server=http://154.91.171.203:3129")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Initialize CAPTCHA solver
        captcha_solver = CaptchaSolver(api_key="faf467050c2932f855a1a3ef21286af0")
        
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
            
            # Test actual CAPTCHA solving
            print("\n🔄 Testing CAPTCHA solving...")
            
            try:
                solved = captcha_solver.solve_turnstile_captcha(
                    driver=driver,
                    page_url="https://www.msport.com/ng/web/welcome",
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
                else:
                    print("❌ CAPTCHA solving failed")
                    
            except Exception as e:
                print(f"❌ CAPTCHA solving error: {e}")
                
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
        
        # Wait a bit to see the result
        print(f"\n⏳ Keeping browser open for 10 seconds for manual inspection...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            driver.quit()
            print("🔒 Browser closed")
        except:
            pass

if __name__ == "__main__":
    print("🚀 Starting Enhanced CAPTCHA Detection Test")
    test_enhanced_captcha_detection()
    print("✅ Test completed!") 