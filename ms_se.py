#!/usr/bin/env python3
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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
    
        # Add proxy if provided
        # if proxy_host and proxy_port:
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument(f'--proxy-server=http://ng.decodo.com:42001')
        
        # Additional options for better compatibility
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Create and return driver
        driver = webdriver.Chrome(options=chrome_options)
        print(f"Driver succesful: {driver}")
        self.driver = driver
        return driver
        
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