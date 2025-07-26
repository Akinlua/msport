#!/usr/bin/env python3

import time
import os
import tempfile
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class WebsiteOpener:
    """A class to handle opening websites with Selenium."""

    def __init__(self, headless=False, proxy=None):
        """
        Initialize the WebsiteOpener.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
            proxy (str): Proxy URL in format "host:port" or "user:pass@host:port"
        """
        self.proxy = proxy
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
        
        # # Add unique user data directory to prevent conflicts
        # temp_dir = tempfile.gettempdir()
        # unique_id = str(uuid.uuid4())
        # user_data_dir = os.path.join(temp_dir, f"chrome_user_data_{unique_id}")
        # chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # # Additional server-friendly options
        # chrome_options.add_argument("--disable-background-timer-throttling")
        # chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        # chrome_options.add_argument("--disable-renderer-backgrounding")
        # chrome_options.add_argument("--disable-features=TranslateUI")
        # chrome_options.add_argument("--disable-ipc-flooding-protection")
        # chrome_options.add_argument("--single-process")
        # chrome_options.add_argument("--remote-debugging-port=0")  # Use random port
        
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add proxy configuration if provided
        if self.proxy:
            print(f"Configuring proxy: {self.proxy}")
            # Handle different proxy formats
            if self.proxy.startswith("http://") or self.proxy.startswith("https://"):
                proxy_url = self.proxy
            else:
                proxy_url = f"http://{self.proxy}"
            
            chrome_options.add_argument(f"--proxy-server={proxy_url}")
            print(f"Added proxy argument: --proxy-server={proxy_url}")
            
            # Add additional proxy-related arguments for better compatibility
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        
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
                service=Service("/usr/local/bin/chromedriver"),
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
    
    # Example proxy (optional) - format: "host:port" or "user:pass@host:port"
    proxy = None  # Set to your proxy if needed, e.g., "proxy.example.com:8080"
    
    # Create an instance of WebsiteOpener
    opener = WebsiteOpener(headless=False, proxy=proxy)
    
    # Open the URL
    opener.open_url(url)
    
    # Wait for a few seconds to view the page
    time.sleep(3)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 