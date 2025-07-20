#!/usr/bin/env python3

import asyncio
from selenium_driverless import webdriver
import time

async def test_selenium_driverless():
    """Simple test to verify selenium-driverless is working"""
    print("Testing selenium-driverless...")
    
    try:
        # Create Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")  # Run in headless mode for testing
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        print("Creating Chrome driver...")
        driver = await webdriver.Chrome(options=options)
        print("✅ Chrome driver created successfully")
        
        # Test navigation
        print("Testing navigation to example.com...")
        await driver.get("https://www.example.com")
        print("✅ Navigation successful")
        
        # Test finding element
        print("Testing element finding...")
        title_element = await driver.find_element("tag name", "title")
        if title_element:
            print("✅ Element finding successful")
        else:
            print("❌ Element finding failed")
        
        # Test screenshot
        print("Testing screenshot...")
        screenshot_result = await driver.save_screenshot("test_screenshot.png")
        print(f"✅ Screenshot result: {screenshot_result}")
        
        # Close driver
        print("Closing driver...")
        await driver.quit()
        print("✅ Driver closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("=== Selenium-Driverless Test ===")
    
    # Run the async test
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_selenium_driverless())
        
        if result:
            print("\n🎉 All tests passed! selenium-driverless is working correctly.")
        else:
            print("\n💥 Tests failed! There's an issue with selenium-driverless setup.")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 