#!/usr/bin/env python3

print("=== Basic Selenium-Driverless Import Test ===")

# Test 1: Can we import selenium-driverless?
try:
    print("1. Testing import...")
    import selenium_driverless
    print("✅ selenium_driverless imported successfully")
    print(f"   Version/Location: {selenium_driverless.__file__}")
except Exception as e:
    print(f"❌ Failed to import selenium_driverless: {e}")
    exit(1)

# Test 2: Can we import webdriver?
try:
    print("2. Testing webdriver import...")
    from selenium_driverless import webdriver
    print("✅ webdriver imported successfully")
except Exception as e:
    print(f"❌ Failed to import webdriver: {e}")
    exit(1)

# Test 3: Can we create ChromeOptions?
try:
    print("3. Testing ChromeOptions creation...")
    options = webdriver.ChromeOptions()
    print("✅ ChromeOptions created successfully")
    print(f"   Type: {type(options)}")
except Exception as e:
    print(f"❌ Failed to create ChromeOptions: {e}")
    exit(1)

# Test 4: Can we add arguments to options?
try:
    print("4. Testing adding arguments...")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    print("✅ Arguments added successfully")
except Exception as e:
    print(f"❌ Failed to add arguments: {e}")
    exit(1)

# Test 5: Test async/await basics
try:
    print("5. Testing asyncio basics...")
    import asyncio
    
    async def test_async():
        print("   Inside async function")
        return True
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(test_async())
    print(f"✅ Asyncio working: {result}")
    
except Exception as e:
    print(f"❌ Asyncio test failed: {e}")
    exit(1)

# Test 6: Try to create webdriver (this is where it likely fails)
try:
    print("6. Testing actual webdriver creation...")
    import asyncio
    
    async def create_driver():
        print("   Creating webdriver.Chrome...")
        # Try with minimal options first
        simple_options = webdriver.ChromeOptions()
        simple_options.add_argument("--headless=new")
        simple_options.add_argument("--no-sandbox")
        simple_options.add_argument("--disable-dev-shm-usage")
        # Note: experimental options not supported in selenium-driverless
        
        driver = await webdriver.Chrome(options=simple_options)
        print(f"   Driver created: {type(driver)}")
        
        # Try to close it immediately
        await driver.quit()
        print("   Driver closed successfully")
        return True
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(create_driver())
    print(f"✅ Webdriver creation successful: {result}")
    
except Exception as e:
    print(f"❌ Webdriver creation failed: {e}")
    print(f"   Error type: {type(e)}")
    import traceback
    print("   Full traceback:")
    traceback.print_exc()

print("\n=== Test Complete ===")
print("Run this test to see exactly where the issue occurs.") 