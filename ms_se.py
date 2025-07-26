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
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Add additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

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
            
        print(f"Setting up ChromeDriver with options: {chrome_options}")
        try:
            # Use standard ChromeDriverManager
            print("Installing ChromeDriver")
            self.driver = webdriver.Chrome(
                # service=Service("/usr/local/bin/chromedriver"),
                options=chrome_options
            )
            
        except Exception as e:
            print(f"Error setting up ChromeDriver: {e}")
            # Try alternative setup method if first method fails
            try:
                print("Trying alternative setup method...")
                from selenium.webdriver.chrome.service import Service as ChromeService
                
                self.driver = webdriver.Chrome(
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