#!/usr/bin/env python3

import time
import os
import glob
import zipfile
import string
import random
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
        self.proxy_plugin_file = None
        self.temp_user_data_dir = None
        self.setup_driver(headless, proxy)
    
    def create_proxy_auth_extension(self, proxy_host, proxy_port, proxy_user, proxy_pass):
        """Create a Chrome extension for proxy authentication."""
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = f"""
        var config = {{
                mode: "fixed_servers",
                rules: {{
                  singleProxy: {{
                    scheme: "http",
                    host: "{proxy_host}",
                    port: parseInt({proxy_port})
                  }},
                  bypassList: ["localhost"]
                }}
              }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy_user}",
                    password: "{proxy_pass}"
                }}
            }};
        }}
        chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {{urls: ["<all_urls>"]}},
                ['blocking']
        );
        """

        # Generate a random filename to avoid conflicts
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        pluginfile = f'proxy_auth_plugin_{random_string}.zip'

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        
        print(f"✅ Created proxy auth extension: {pluginfile}")
        return pluginfile
    
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
        
        # Force Chrome to NOT use any existing user data directory
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-default-apps")
        
        # Create a unique temporary user data directory to avoid conflicts
        import tempfile
        import time
        
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
        print(f"🔧 Setting up Chrome with clean profile (no user data conflicts)")
        print("📂 Profile: Temporary profile (clean startup)")
        print("✅ This avoids profile lock issues on servers!")
        
        # Add proxy configuration if provided
        if proxy:
            print(f"Configuring proxy: {proxy}")
            
            # Parse proxy URL to extract components
            import urllib.parse
            if proxy.startswith("http://") or proxy.startswith("https://"):
                parsed_proxy = urllib.parse.urlparse(proxy)
                
                if parsed_proxy.username and parsed_proxy.password:
                    # Handle authenticated proxy using Chrome extension
                    print(f"🔐 Detected authenticated proxy")
                    print(f"Host: {parsed_proxy.hostname}:{parsed_proxy.port}")
                    print(f"Username: {parsed_proxy.username}")
                    
                    # Create proxy authentication extension
                    self.proxy_plugin_file = self.create_proxy_auth_extension(
                        proxy_host=parsed_proxy.hostname,
                        proxy_port=parsed_proxy.port,
                        proxy_user=parsed_proxy.username,
                        proxy_pass=parsed_proxy.password
                    )
                    
                    # Add the extension to Chrome
                    chrome_options.add_extension(self.proxy_plugin_file)
                    print(f"✅ Added proxy auth extension to Chrome")
                    
                else:
                    # Simple proxy without authentication
                    proxy_url = proxy
                    chrome_options.add_argument(f"--proxy-server={proxy_url}")
                    print(f"✅ Added simple proxy: {proxy_url}")
            else:
                proxy_url = f"http://{proxy}"
                chrome_options.add_argument(f"--proxy-server={proxy_url}")
                print(f"Added proxy argument: --proxy-server={proxy_url}")
        
        # Use direct path to Chrome on Mac
        if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
            chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print(f"Setting up ChromeDriver with default profile")
        print(f"Proxy configuration: {proxy}")
        
        try:
            # Method 1: Try with system chromedriver first (avoid ChromeDriverManager issues)
            print("🔧 Trying system chromedriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
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
                    # Create completely clean fallback options without any profile settings
                    fallback_options = Options()
                    
                    # Add only basic options, no profile-related settings
                    fallback_options.add_argument("--window-size=1920,1080")
                    fallback_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
                    
                    # Add proxy extension to fallback options if it exists
                    if self.proxy_plugin_file:
                        fallback_options.add_extension(self.proxy_plugin_file)
                        print("✅ Added proxy extension to fallback Chrome")
                    
                    # Use direct path to Chrome on Mac (if applicable)
                    if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
                        fallback_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                    
                    self.driver = webdriver.Chrome(options=fallback_options)
                    print("⚠️  Chrome started without custom profile (using default temporary profile)")
                    print("   Your bookmarks and extensions may not be available")
                    
                except Exception as e3:
                    print(f"All methods failed: {e3}")
                    raise Exception(f"Could not start Chrome. Last error: {e3}")
    
    def test_proxy_ip(self):
        """Test if the proxy is working by checking the IP address."""
        try:
            # Navigate to IP checking service
            self.driver.get("https://ipinfo.io/json")
            
            # Wait for page to load
            time.sleep(3)
            
            # Get the page source and extract IP info
            page_source = self.driver.page_source
            print("🌐 IP Check Result:")
            print(page_source)
            
            # Try to find IP in the page
            if "156.252.228.152" in page_source:
                print("✅ Proxy is working! Using expected IP: 156.252.228.152")
                return True
            else:
                print("❌ Proxy may not be working properly.")
                print("Check the page content above to see the actual IP.")
                return False
                
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
        
        # Clean up proxy plugin file
        if self.proxy_plugin_file and os.path.exists(self.proxy_plugin_file):
            try:
                os.remove(self.proxy_plugin_file)
                print(f"🧹 Cleaned up proxy plugin: {self.proxy_plugin_file}")
            except:
                pass

        # Clean up temporary user data directory
        if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_user_data_dir)
                print(f"🧹 Cleaned up temporary user data dir: {self.temp_user_data_dir}")
            except:
                pass

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
        
        # Clean up proxy plugin file
        if self.proxy_plugin_file and os.path.exists(self.proxy_plugin_file):
            try:
                os.remove(self.proxy_plugin_file)
                print(f"🧹 Cleaned up proxy plugin: {self.proxy_plugin_file}")
            except:
                pass

        # Clean up temporary user data directory
        if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_user_data_dir)
                print(f"🧹 Cleaned up temporary user data dir: {self.temp_user_data_dir}")
            except:
                pass


def main():
    """Main function to demonstrate usage with proxy testing."""
    # Test with your actual proxy
    proxy_url = "http://brd-customer-hl_1b6b5179-zone-datacenter_proxy1-ip-156.252.228.152:qh13e50d5n6f@brd.superproxy.io:33335"
    
    # Create an instance of WebsiteOpener with proxy
    print("🚀 Starting Chrome with authenticated proxy...")
    opener = WebsiteOpener(headless=False, proxy=proxy_url)
    
    # Test the proxy IP
    print("\n🧪 Testing proxy functionality...")
    proxy_working = opener.test_proxy_ip()
    
    if proxy_working:
        print("\n✅ Proxy test successful! Opening MSport...")
        # Open MSport to test actual functionality
        opener.open_url("https://www.msport.com")
    else:
        print("\n⚠️  Continuing anyway...")
        opener.open_url("https://www.example.com")
    
    # Wait for user to see the result
    print("\n⏳ Waiting 10 seconds for you to check the browser...")
    time.sleep(10)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 