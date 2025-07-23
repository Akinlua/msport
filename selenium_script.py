#!/usr/bin/env python3

import time
import os
import glob
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
            proxy (str): Proxy URL in format "http://host:port" or "http://user:pass@host:port"
        """
        self.setup_driver(headless, proxy)
    
    def setup_driver(self, headless, proxy=None):
        """Set up the Chrome WebDriver using default profile."""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Add additional options for stability
        chrome_options.add_argument("--window-size=1920,1080")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option('useAutomationExtension', False)
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Additional arguments to fix DevToolsActivePort issues
        # chrome_options.add_argument("--remote-debugging-port=0")  # Use random available port
        # # chrome_options.add_argument("--disable-extensions")  # Allow extensions to work
        # chrome_options.add_argument("--disable-plugins")
        # chrome_options.add_argument("--disable-background-timer-throttling")
        # chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        # chrome_options.add_argument("--disable-renderer-backgrounding")
        # chrome_options.add_argument("--disable-features=TranslateUI")
        # chrome_options.add_argument("--disable-ipc-flooding-protection")
        # chrome_options.add_argument("--no-first-run")
        # chrome_options.add_argument("--no-default-browser-check")
        
        # Use your actual default Chrome profile directly
        import os
        
        home_dir = os.path.expanduser("~")
        user_data_dir = os.path.join(home_dir, "Library", "Application Support", "Google", "Chrome")
        
        # Use your actual Chrome user data directory and default profile
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")
        
        print(f"🔧 Using your actual Chrome profile: {user_data_dir}")
        print("📂 Profile: Default (your main Chrome profile)")
        print("✅ This will load all your bookmarks, extensions, and saved data!")
        
        # Add proxy configuration if provided
        if proxy:
            print(f"Configuring proxy: {proxy}")
            if proxy.startswith("http://") or proxy.startswith("https://"):
                proxy_url = proxy
            else:
                proxy_url = f"http://{proxy}"
            
            chrome_options.add_argument(f"--proxy-server={proxy_url}")
            print(f"Added proxy argument: --proxy-server={proxy_url}")
            
            # Add arguments to handle proxy authentication
            # chrome_options.add_argument("--disable-web-security")
            # chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            # chrome_options.add_argument("--proxy-bypass-list=localhost,127.0.0.1")
            # chrome_options.add_argument("--disable-popup-blocking")
            # chrome_options.add_argument("--disable-extensions-http-throttling")
        
        # Use direct path to Chrome on Mac
        if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
            chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print(f"Setting up ChromeDriver with default profile")
        print(f"Proxy configuration: {proxy}")
        
        try:
            # Method 1: Try with system chromedriver first (avoid ChromeDriverManager issues)
            print("🔧 Trying system chromedriver...")
            self.driver = webdriver.Chrome(options=chrome_options, service=Service(r'C:\Users\Administrator\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'))
            print("✅ Chrome started with system chromedriver!")
            print("👀 You should see all your bookmarks, extensions, and saved data!")
            
        except Exception as e1:
            print(f"System chromedriver failed: {e1}")
            try:
                # Method 2: Try with ChromeDriverManager but fix the path
                print("🔧 Trying ChromeDriverManager...")
                driver_path = ChromeDriverManager().install()
                
                # Fix the ChromeDriverManager path issue
                if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
                    import glob
                    driver_dir = os.path.dirname(driver_path)
                    
                    # Look for the actual chromedriver executable
                    possible_paths = [
                        os.path.join(driver_dir, 'chromedriver'),
                        os.path.join(driver_dir, '**', 'chromedriver'),
                    ]
                    
                    chromedriver_path = None
                    for pattern in possible_paths:
                        matches = glob.glob(pattern, recursive=True)
                        for match in matches:
                            if os.path.isfile(match) and os.access(match, os.X_OK) and 'THIRD_PARTY' not in match:
                                chromedriver_path = match
                                break
                        if chromedriver_path:
                            break
                    
                    if chromedriver_path:
                        driver_path = chromedriver_path
                        print(f"✅ Found correct chromedriver: {driver_path}")
                    else:
                        raise Exception("Could not find valid chromedriver executable")
                
                self.driver = webdriver.Chrome(
                    service=Service(driver_path),
                    options=chrome_options
                )
                print("✅ Chrome started with ChromeDriverManager!")
                print("👀 You should see all your bookmarks, extensions, and saved data!")
                
            except Exception as e2:
                print(f"ChromeDriverManager also failed: {e2}")
                
                # Method 3: Try without specifying service path at all
                try:
                    print("🔧 Trying default Chrome service...")
                    # Remove user-data-dir temporarily to avoid profile conflicts
                    fallback_options = Options()
                    for arg in chrome_options.arguments:
                        if not arg.startswith('--user-data-dir') and not arg.startswith('--profile-directory'):
                            fallback_options.add_argument(arg)
                    
                    # Copy experimental options
                    for key, value in chrome_options.experimental_options.items():
                        fallback_options.add_experimental_option(key, value)
                    
                    if chrome_options.binary_location:
                        fallback_options.binary_location = chrome_options.binary_location
                    
                    self.driver = webdriver.Chrome(options=fallback_options)
                    print("⚠️  Chrome started without custom profile (using default temporary profile)")
                    print("   Your bookmarks and extensions may not be available")
                    
                except Exception as e3:
                    print(f"All methods failed: {e3}")
                    raise Exception(f"Could not start Chrome. Last error: {e3}")
        
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
    
    # Create an instance of WebsiteOpener with default profile
    opener = WebsiteOpener(headless=False)
    
    # Open the URL
    opener.open_url(url)
    
    # Wait for a few seconds to view the page
    time.sleep(3)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 