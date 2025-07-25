#!/usr/bin/env python3

import time
import os
import tempfile
import subprocess
import shutil
import signal
import psutil
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
        self.driver = None
        self.setup_driver(headless, proxy)
    
    def kill_existing_chrome_processes(self):
        """Kill any existing Chrome processes that might be using our temp directory."""
        try:
            print("🧹 Checking for existing Chrome processes...")
            killed_count = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        # Kill Chrome processes that might be using our temp directory
                        if 'chrome-profile-' in cmdline or '--user-data-dir=' in cmdline:
                            print(f"🔪 Killing Chrome process: PID {proc.info['pid']}")
                            proc.kill()
                            killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if killed_count > 0:
                print(f"✅ Killed {killed_count} Chrome processes")
                time.sleep(2)  # Wait for processes to die
            else:
                print("✅ No conflicting Chrome processes found")
                
        except Exception as e:
            print(f"⚠️ Error checking Chrome processes: {e}")
    
    def create_unique_temp_dir(self):
        """Create a unique temporary directory with timestamp to avoid conflicts."""
        import uuid
        import datetime
        
        # Create a unique temp dir with timestamp and UUID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        temp_base = tempfile.gettempdir()
        temp_dir_name = f"chrome-profile-{timestamp}-{unique_id}"
        temp_dir_path = os.path.join(temp_base, temp_dir_name)
        
        # Ensure the directory doesn't exist
        counter = 0
        while os.path.exists(temp_dir_path):
            counter += 1
            temp_dir_path = os.path.join(temp_base, f"{temp_dir_name}-{counter}")
        
        os.makedirs(temp_dir_path, exist_ok=False)
        return temp_dir_path
    
    def cleanup_old_temp_dirs(self):
        """Clean up old Chrome profile temp directories."""
        try:
            temp_base = tempfile.gettempdir()
            print("🧹 Cleaning up old Chrome profile directories...")
            
            cleaned_count = 0
            for item in os.listdir(temp_base):
                if item.startswith('chrome-profile-'):
                    old_dir = os.path.join(temp_base, item)
                    try:
                        shutil.rmtree(old_dir)
                        cleaned_count += 1
                        print(f"🗑️ Removed old profile: {item}")
                    except Exception as e:
                        print(f"⚠️ Could not remove {item}: {e}")
            
            if cleaned_count > 0:
                print(f"✅ Cleaned up {cleaned_count} old profile directories")
            else:
                print("✅ No old profile directories to clean")
                
        except Exception as e:
            print(f"⚠️ Error cleaning old temp dirs: {e}")
    
    def setup_driver(self, headless, proxy=None):
        """Set up the Chrome WebDriver with enhanced conflict resolution."""
        
        # Kill any existing Chrome processes first
        self.kill_existing_chrome_processes()
        
        # Clean up old temp directories
        self.cleanup_old_temp_dirs()
        
        chrome_options = Options()
         
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Create unique temporary user data directory
        self.temp_user_data_dir = self.create_unique_temp_dir()
        chrome_options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")
        print(f"✅ Using unique temporary profile: {self.temp_user_data_dir}")
        
        # Enhanced options for server stability
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--single-process")  # Helps on servers
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
                # service=Service("/usr/local/bin/chromedriver"),
                service=Service(r"C:\Users\Administrator\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"),

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
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                print("✅ WebDriver closed successfully")
            except Exception as e:
                print(f"⚠️ Error closing WebDriver: {e}")
        
        # Clean up temporary user data directory
        if self.temp_user_data_dir and os.path.exists(self.temp_user_data_dir):
            try:
                shutil.rmtree(self.temp_user_data_dir)
                print(f"🧹 Cleaned up temporary profile: {self.temp_user_data_dir}")
            except Exception as e:
                print(f"⚠️ Could not clean up temp directory: {e}")

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
                shutil.rmtree(self.temp_user_data_dir)
                print(f"🧹 Cleaned up temporary profile: {self.temp_user_data_dir}")
            except Exception as e:
                print(f"⚠️ Could not clean up temp directory: {e}")


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
        print("\n⚠️ Continuing anyway...")
        opener.open_url("https://www.example.com")
    
    # Wait for user to see the result
    print("\n⏳ Waiting 15 seconds for you to check the browser...")
    time.sleep(15)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 