#!/usr/bin/env python3

import time
import os
import tempfile
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
            proxy (str): Proxy URL in format "http://host:port"
        """
        self.temp_user_data_dir = None
        self.setup_driver(headless, proxy)
    
    def setup_driver(self, headless, proxy=None):
        """Set up the Chrome WebDriver with simple configuration."""
        chrome_options = Options()
         
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Create temporary user data directory to avoid conflicts
        self.temp_user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
        chrome_options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")
        print(f"✅ Using temporary profile: {self.temp_user_data_dir}")
        
        # Basic options
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        
        # Simple proxy configuration
        if proxy:
            print(f"Configuring proxy: {proxy}")
            chrome_options.add_argument(f"--proxy-server={proxy}")
            print(f"✅ Added proxy: {proxy}")
        
        print(f"Setting up ChromeDriver...")
        
        try:
            # Try with ChromeDriverManager
            self.driver = webdriver.Chrome(
                # service=Service(ChromeDriverManager().install()),
                service=Service("/usr/local/bin/chromedriver"),
                options=chrome_options
            )
            print("✅ Chrome started successfully!")
            
        except Exception as e:
            print(f"ChromeDriverManager failed: {e}")
            try:
                # Try system chromedriver
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✅ Chrome started with system chromedriver!")
                
            except Exception as e2:
                print(f"System chromedriver also failed: {e2}")
                raise Exception(f"Could not start Chrome: {e2}")
    
    def test_proxy_ip(self):
        """Test if the proxy is working by checking the IP address."""
        try:
            print("🧪 Testing proxy functionality...")
            
            # Navigate to IP checking service
            print("🌐 Checking IP address...")
            self.driver.get("https://ipinfo.io/json")
            
            # Wait for page to load
            time.sleep(3)
            
            # Get the page source and extract IP info
            page_source = self.driver.page_source
            print("🌐 IP Check Result:")
            print(page_source)
            
            return True
                
        except Exception as e:
            print(f"❌ Error testing proxy: {e}")
            return False
        
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
        
        # Clean up temporary user data directory
        if self.temp_user_data_dir and os.path.exists(self.temp_user_data_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_user_data_dir)
                print(f"🧹 Cleaned up temporary profile: {self.temp_user_data_dir}")
            except Exception as e:
                print(f"⚠️  Could not clean up temp directory: {e}")

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
        
        # Clean up temporary user data directory
        if self.temp_user_data_dir and os.path.exists(self.temp_user_data_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_user_data_dir)
                print(f"🧹 Cleaned up temporary profile: {self.temp_user_data_dir}")
            except Exception as e:
                print(f"⚠️  Could not clean up temp directory: {e}")


def main():
    """Main function to demonstrate usage with proxy testing."""
    # Simple proxy configuration
    proxy_url = "http://ng.decodo.com:42001"
    
    # Create an instance of WebsiteOpener with proxy
    print("🚀 Starting Chrome with proxy...")
    opener = WebsiteOpener(headless=False, proxy=proxy_url)
    
    # Test the proxy IP
    print("\n🧪 Testing proxy functionality...")
    proxy_working = opener.test_proxy_ip()
    
    if proxy_working:
        print("\n✅ Proxy test successful! Opening MSport...")
        opener.open_url("https://www.msport.com")
    else:
        print("\n⚠️  Continuing anyway...")
        opener.open_url("https://www.example.com")
    
    # Wait for user to see the result
    print("\n⏳ Waiting 15 seconds for you to check the browser...")
    time.sleep(15)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 