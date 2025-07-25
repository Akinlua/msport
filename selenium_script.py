#!/usr/bin/env python3

import time
import os
import glob
import zipfile
import string
import random
import json # Added for json.dumps
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
        
        manifest_json = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy Auth",
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
                "scripts": ["background.js"],
                "persistent": True
            },
            "minimum_chrome_version": "22.0.0"
        }

        background_js = f"""
console.log("Proxy extension starting...");

// Set proxy configuration
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy_host}",
            port: parseInt({proxy_port})
        }},
        bypassList: ["localhost", "127.0.0.1"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
    console.log("Proxy configured:", config);
    if (chrome.runtime.lastError) {{
        console.error("Proxy setup error:", chrome.runtime.lastError);
    }} else {{
        console.log("Proxy setup successful");
    }}
}});

// Handle authentication
function callbackFn(details) {{
    console.log("Auth required for:", details.url);
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

console.log("Proxy extension loaded successfully");
"""

        # Generate a random filename to avoid conflicts
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        pluginfile = f'proxy_auth_plugin_{random_string}.zip'

        # Create the zip file with proper structure
        with zipfile.ZipFile(pluginfile, 'w', zipfile.ZIP_DEFLATED) as zp:
            zp.writestr("manifest.json", json.dumps(manifest_json, indent=2))
            zp.writestr("background.js", background_js)
        
        print(f"✅ Created proxy auth extension: {pluginfile}")
        
        # Verify the zip file was created correctly
        try:
            with zipfile.ZipFile(pluginfile, 'r') as zp:
                files = zp.namelist()
                print(f"📦 Extension files: {files}")
        except Exception as e:
            print(f"❌ Error verifying extension zip: {e}")
        
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
        
        # Enable extension support and logging
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")  # Enable all logs
        chrome_options.add_argument("--disable-web-security")  # Allow extension to work
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        # DON'T disable extensions - they need to be enabled for proxy to work
        # chrome_options.add_argument("--disable-extensions")  # COMMENTED OUT
        
        # Create a unique temporary user data directory - REQUIRED for proxy extensions to work
        import tempfile
        import time
        temp_user_data_dir = tempfile.mkdtemp(prefix=f"chrome_proxy_{int(time.time())}_")
        chrome_options.add_argument(f"--user-data-dir={temp_user_data_dir}")
        print(f"🔧 Created temporary profile for proxy: {temp_user_data_dir}")
        
        # Store for cleanup later
        self.temp_user_data_dir = temp_user_data_dir
        
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
    
    def debug_proxy_extension(self):
        """Debug the proxy extension to see if it's working properly."""
        try:
            print("🔍 Debugging proxy extension...")
            
            # Check Chrome console logs for extension errors
            try:
                logs = self.driver.get_log('browser')
                if logs:
                    print("📋 Chrome browser logs:")
                    for log in logs[-10:]:  # Show last 10 logs
                        print(f"  {log['level']}: {log['message']}")
                else:
                    print("📋 No browser logs found")
            except Exception as e:
                print(f"⚠️  Could not retrieve browser logs: {e}")
            
            # First, let's check if the extension is loaded
            print("📋 Checking Chrome extensions...")
            try:
                # Go to chrome://extensions to check if our proxy extension is loaded
                self.driver.get("chrome://extensions/")
                time.sleep(2)
                page_source = self.driver.page_source.lower()
                if "chrome proxy" in page_source or "proxy auth" in page_source:
                    print("✅ Proxy extension appears to be loaded")
                else:
                    print("❌ Proxy extension NOT found in extensions page")
                    print("🔍 Available extensions on page:")
                    # Try to find what extensions are actually loaded
                    if "extensions" in page_source:
                        print("   Extensions page loaded, but proxy extension not visible")
                    else:
                        print("   Could not access extensions page properly")
            except Exception as e:
                print(f"⚠️  Could not check extension status: {e}")
            
            # Execute JavaScript to check if proxy is set
            print("🔍 Checking proxy configuration via JavaScript...")
            proxy_check_script = """
            var result = {};
            try {
                if (typeof chrome !== 'undefined' && chrome.proxy) {
                    result.chromeProxy = 'Available';
                    // Try to get proxy settings
                    chrome.proxy.settings.get({}, function(config) {
                        console.log('Proxy config:', config);
                    });
                } else {
                    result.chromeProxy = 'Not available';
                }
                if (typeof chrome !== 'undefined' && chrome.runtime) {
                    result.chromeRuntime = 'Available';
                } else {
                    result.chromeRuntime = 'Not available';
                }
            } catch (e) {
                result.error = e.toString();
            }
            return JSON.stringify(result);
            """
            
            try:
                result = self.driver.execute_script(proxy_check_script)
                print(f"📋 JavaScript proxy check: {result}")
            except Exception as e:
                print(f"⚠️  Could not execute proxy check script: {e}")
            
            # Check if we can access chrome://net-internals/#proxy
            try:
                print("🔍 Checking Chrome network internals...")
                self.driver.get("chrome://net-internals/#proxy")
                time.sleep(2)
                print("✅ Accessed Chrome network internals page")
                # Try to get proxy info from the page
                page_text = self.driver.page_source
                if "brd.superproxy.io" in page_text:
                    print("✅ Found proxy server in network internals!")
                else:
                    print("❌ Proxy server not found in network internals")
            except Exception as e:
                print(f"⚠️  Could not access Chrome network internals: {e}")
                
        except Exception as e:
            print(f"❌ Error debugging proxy extension: {e}")
    
    def test_proxy_ip(self):
        """Test if the proxy is working by checking the IP address."""
        try:
            print("🧪 Testing proxy functionality...")
            
            # First, let's check if the extension is loaded
            print("📋 Checking Chrome extensions...")
            try:
                # Go to chrome://extensions to check if our proxy extension is loaded
                self.driver.get("chrome://extensions/")
                time.sleep(2)
                page_source = self.driver.page_source.lower()
                if "chrome proxy" in page_source or "proxy auth" in page_source:
                    print("✅ Proxy extension appears to be loaded")
                else:
                    print("⚠️  Proxy extension may not be loaded properly")
            except:
                print("⚠️  Could not check extension status")
            
            # Navigate to IP checking service
            print("🌐 Checking IP address...")
            self.driver.get("https://ipinfo.io/json")
            
            # Wait for page to load
            time.sleep(3)
            
            # Get the page source and extract IP info
            page_source = self.driver.page_source
            print("🌐 IP Check Result:")
            print(page_source)
            
            # Try to find the expected proxy IP
            if "156.252.228.152" in page_source:
                print("✅ SUCCESS! Proxy is working! Using expected IP: 156.252.228.152")
                return True
            else:
                print("❌ PROXY NOT WORKING! Using local IP instead of proxy.")
                
                # Let's also try a different IP checking service
                print("🔄 Trying alternative IP check...")
                self.driver.get("https://httpbin.org/ip")
                time.sleep(2)
                alt_result = self.driver.page_source
                print("Alternative IP check result:")
                print(alt_result)
                
                if "156.252.228.152" in alt_result:
                    print("✅ Proxy working on alternative service!")
                    return True
                else:
                    print("❌ Proxy still not working on alternative service")
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
    
    # Debug the proxy extension first
    print("\n🔍 Debugging proxy setup...")
    opener.debug_proxy_extension()
    
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
    print("\n⏳ Waiting 15 seconds for you to check the browser and proxy...")
    time.sleep(15)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 