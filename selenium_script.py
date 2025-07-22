#!/usr/bin/env python3

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class WebsiteOpener:
    """A class to handle opening websites with Selenium."""

    def __init__(self, headless=False):
        """
        Initialize the WebsiteOpener.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
        """
        self.setup_driver(headless)
    
    def setup_driver(self, headless):
        """Set up the Chrome WebDriver."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Add additional options for stability
        chrome_options.add_argument("--window-size=1920,1080")  # important!
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Use direct path to Chrome on Mac
        if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
            chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print(f"Setting up ChromeDriver with options: {chrome_options}")
        try:
            # Use standard ChromeDriverManager
            print("Installing ChromeDriver")
            driver_path = ChromeDriverManager().install()
            print(f"Driver path: {driver_path}")
            self.driver = webdriver.Chrome(
                service=Service(),
                options=chrome_options
            )
            
        except Exception as e:
            print(f"Error setting up ChromeDriver: {e}")
            # Try alternative setup method if first method fails
            try:
                print("Trying alternative setup method...")
                from selenium.webdriver.chrome.service import Service as ChromeService
                
                self.driver = webdriver.Chrome(
                    service=ChromeService(),
                    options=chrome_options
                )
            except Exception as e2:
                print(f"Alternative setup also failed: {e2}")
                raise
        
    def open_url(self, url):
        """
        Open the specified URL in the browser.
        
        Args:
            url (str): The URL to open
        """
        try:
            self.driver.get(url)
            print(f"Successfully opened: {url}")
            return True
        except Exception as e:
            print(f"Error opening URL: {e}")
            return False
    
    def close(self):
        """Close the browser and clean up resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def close_browser(self):
        """Close the browser if it's open"""
        if hasattr(self, 'driver') and self.driver:
            try:
                print("Closing Selenium WebDriver...")
                self.driver.quit()
                self.driver = None
                print("WebDriver closed successfully")
            except Exception as e:
                print(f"Error closing WebDriver: {e}")


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