#!/usr/bin/env python3

print("=== Testing By Objects ===")

# Test what By objects actually are
try:
    from selenium_driverless.types.by import By
    
    print(f"By.CSS_SELECTOR = {By.CSS_SELECTOR}")
    print(f"Type: {type(By.CSS_SELECTOR)}")
    
    print(f"By.XPATH = {By.XPATH}")
    print(f"Type: {type(By.XPATH)}")
    
    print(f"By.ID = {By.ID}")
    print(f"Type: {type(By.ID)}")
    
    # Test if they're just strings
    if isinstance(By.CSS_SELECTOR, str):
        print("✅ By.CSS_SELECTOR is a string")
    else:
        print("❌ By.CSS_SELECTOR is not a string")
        
    # Test function passing
    def test_function(by_param, value_param):
        print(f"Inside function: by={by_param}, value={value_param}")
        print(f"by type: {type(by_param)}")
        return by_param, value_param
    
    print("\n--- Testing function passing ---")
    result_by, result_value = test_function(By.CSS_SELECTOR, "input[type='tel']")
    
    print(f"Direct: {By.CSS_SELECTOR}")
    print(f"Via function: {result_by}")
    print(f"Are they equal? {By.CSS_SELECTOR == result_by}")
    
    # Test with selenium-driverless if available
    print("\n--- Testing with selenium-driverless ---")
    import asyncio
    from selenium_driverless import webdriver
    
    async def test_selenium_direct_vs_function():
        # Create a simple driver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        
        driver = await webdriver.Chrome(options=options)
        
        try:
            # Navigate to a test page
            await driver.get("https://www.example.com")
            
            # Test 1: Direct usage
            print("Test 1: Direct By usage")
            try:
                element1 = await driver.find_element(By.TAG_NAME, "title", timeout=5)
                print(f"✅ Direct usage worked: {type(element1)}")
            except Exception as e:
                print(f"❌ Direct usage failed: {e}")
            
            # Test 2: Function usage
            def get_by_selector():
                return By.TAG_NAME, "title"
            
            print("Test 2: Function-passed By usage")
            try:
                by_param, value_param = get_by_selector()
                element2 = await driver.find_element(by_param, value_param, timeout=5)
                print(f"✅ Function usage worked: {type(element2)}")
            except Exception as e:
                print(f"❌ Function usage failed: {e}")
                
            # Test 3: Compare results
            try:
                if element1 and element2:
                    print(f"Both elements found successfully")
                    print(f"Element 1 type: {type(element1)}")
                    print(f"Element 2 type: {type(element2)}")
            except:
                pass
                
        finally:
            await driver.quit()
    
    # Run the async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_selenium_direct_vs_function())
    
except Exception as e:
    print(f"Error in test: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===") 