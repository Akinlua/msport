#!/usr/bin/env python3

import time
import os
import asyncio
from selenium_driverless import webdriver


class WebsiteOpener:
    """A class to handle opening websites with Selenium Driverless."""

    def __init__(self, headless=False):
        """
        Initialize the WebsiteOpener.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
        """
        self.headless = headless
        self.driver = None
        self.loop = None
        self._setup_complete = False
        # Initialize immediately
        self.setup_driver(headless)
    
    def _ensure_event_loop(self):
        """Ensure we have an event loop running."""
        try:
            self.loop = asyncio.get_event_loop()
            if self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
    
    def _run_async_safely(self, coro):
        """
        Run an async coroutine safely, handling cases where event loop is already running.
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we get here, an event loop is already running
            # We need to schedule the coroutine as a task
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(coro)
        except RuntimeError:
            # No event loop is running, we can use run_until_complete
            self._ensure_event_loop()
            return self.loop.run_until_complete(coro)
        except ImportError:
            # nest_asyncio not available, try alternative approach
            try:
                # Check if we're in a running loop
                asyncio.get_running_loop()
                # If we get here, we're in a running loop but can't use nest_asyncio
                # We'll need to handle this differently
                raise RuntimeError("Event loop already running and nest_asyncio not available. "
                                 "Please install nest_asyncio: pip install nest_asyncio")
            except RuntimeError as e:
                if "no running event loop" in str(e).lower():
                    # No loop running, safe to use run_until_complete
                    self._ensure_event_loop()
                    return self.loop.run_until_complete(coro)
                else:
                    # Re-raise the original error
                    raise
    
    async def _async_setup_driver(self):
        """Set up the Chrome WebDriver asynchronously."""
        print("Starting _async_setup_driver")
        
        try:
            print("Creating ChromeOptions...")
            options = webdriver.ChromeOptions()
            
            if self.headless:
                print("Adding headless argument")
                options.add_argument("--headless=new")
            
            # Add additional options for stability and stealth
            print("Adding Chrome arguments...")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            # Note: add_experimental_option is not supported in selenium-driverless
            # options.add_experimental_option("excludeSwitches", ["enable-automation"])
            # options.add_experimental_option('useAutomationExtension', False)
            
            print(f"Setting up selenium-driverless Chrome with headless: {self.headless}")
            print("About to create webdriver.Chrome...")
            
            self.driver = await webdriver.Chrome(options=options)
            print("webdriver.Chrome created successfully")
            print(f"Driver type: {type(self.driver)}")
            print("selenium-driverless Chrome setup successful")
            return True
        except Exception as e:
            print(f"Error setting up selenium-driverless Chrome: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print("Full async traceback:")
            traceback.print_exc()
            return False
    
    def setup_driver(self, headless):
        """Set up the Chrome WebDriver (sync wrapper)."""
        self.headless = headless
        print(f"self._setup_complete: {self._setup_complete}")
        print(f"self.driver: {self.driver}")
        if not self._setup_complete and self.driver is None:
            try:
                print("Setting up driver")
                print("About to call _async_setup_driver")
                success = self._run_async_safely(self._async_setup_driver())
                print(f"success: {success}")
                if success:
                    self._setup_complete = True
                    print("Driver setup completed successfully")
                else:
                    print("Driver setup failed")
                return success
            except Exception as e:
                print(f"Error in setup_driver: {e}")
                print(f"Error type: {type(e)}")
                import traceback
                print("Full traceback:")
                traceback.print_exc()
                return False
        elif self.driver is not None:
            print("Driver already set up")
            return True
        else:
            print("Driver setup was attempted but failed")
            return False
    
    async def _async_open_url(self, url):
        """Open URL asynchronously."""
        try:
            await self.driver.get(url)
            print(f"Successfully opened: {url}")
            return True
        except Exception as e:
            print(f"Error opening URL: {e}")
            return False
    
    def open_url(self, url):
        """
        Open the specified URL in the browser.
        
        Args:
            url (str): The URL to open
        """
        if not self._setup_complete or self.driver is None:
            print("Driver not ready, setting up...")
            self.setup_driver(self.headless)
        
        if self.driver is None:
            print("Failed to set up driver, cannot open URL")
            return False
        
        return self._run_async_safely(self._async_open_url(url))
    
    async def _async_close(self):
        """Close the browser asynchronously."""
        if self.driver:
            await self.driver.quit()
            self.driver = None
    
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self._run_async_safely(self._async_close())
        self._setup_complete = False

    def close_browser(self):
        """Close the browser if it's open"""
        if self.driver:
            try:
                print("Closing selenium-driverless WebDriver...")
                self._run_async_safely(self._async_close())
                print("WebDriver closed successfully")
                self._setup_complete = False
            except Exception as e:
                print(f"Error closing WebDriver: {e}")

    # Compatibility methods for selenium-driverless
    def get_cookies(self):
        """Get cookies from the browser."""
        if not self.driver:
            print("Driver not available for get_cookies")
            return []
        
        async def _async_get_cookies():
            return await self.driver.get_cookies()
        
        return self._run_async_safely(_async_get_cookies())
    
    def execute_script(self, script, *args):
        """Execute JavaScript in the browser."""
        if not self.driver:
            print("Driver not available for execute_script")
            return None
        
        async def _async_execute():
            return await self.driver.execute_script(script, *args)
        
        return self._run_async_safely(_async_execute())
    
    def save_screenshot(self, filename):
        """Save a screenshot."""
        if not self.driver:
            print("Driver not available for save_screenshot")
            return False
        
        async def _async_screenshot():
            return await self.driver.save_screenshot(filename)
        
        return self._run_async_safely(_async_screenshot())
    
    def find_element(self, by, value):
        """Find an element."""
        if not self.driver:
            print("Driver not available for find_element")
            return None
        
        async def _async_find():
            return await self.driver.find_element(by, value)
        
        return self._run_async_safely(_async_find())
    
    def find_elements(self, by, value):
        """Find multiple elements."""
        if not self.driver:
            print("Driver not available for find_elements")
            return []
        
        async def _async_find():
            return await self.driver.find_elements(by, value)
        
        return self._run_async_safely(_async_find())
    
    def get(self, url):
        """Navigate to URL (compatibility method)."""
        return self.open_url(url)


def main():
    """Main function to demonstrate usage."""
    # Example URL
    url = "https://www.example.com"
    
    # Create an instance of WebsiteOpener
    opener = WebsiteOpener(headless=False)
    
    # Open the URL
    opener.open_url(url)
    
    # Wait for a few seconds to view the page
    time.sleep(3)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 