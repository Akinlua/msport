#!/usr/bin/env python3

import time
import os
import glob
import random
# Replace selenium webdriver with undetected-chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class WebsiteOpener:
    """A class to handle opening websites with Selenium using stealth mode."""

    def __init__(self, headless=False, proxy=None):
        """
        Initialize the WebsiteOpener with stealth capabilities.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
            proxy (str): Proxy URL in format "http://host:port" or "http://user:pass@host:port"
        """
        self.temp_user_data_dir = None
        self.setup_driver(headless, proxy)
    
    def setup_driver(self, headless, proxy=None):
        """Set up the Chrome WebDriver using undetected-chromedriver for stealth."""
        # Use undetected-chromedriver options
        options = uc.ChromeOptions()
        
        if headless:
            options.add_argument("--headless=new")
        
        # Enhanced stealth and anti-detection options
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # Remove experimental options that cause issues with undetected-chromedriver
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        
        # Advanced stealth arguments
        # options.add_argument("--disable-web-security")
        # options.add_argument("--allow-running-insecure-content")
        # options.add_argument("--disable-features=VizDisplayCompositor")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-gpu")
        # options.add_argument("--disable-extensions")  # Temporarily disable to avoid conflicts
        # options.add_argument("--disable-plugins")
        # options.add_argument("--disable-images")  # Faster loading
        # options.add_argument("--no-first-run")
        # options.add_argument("--no-default-browser-check")
        # options.add_argument("--disable-background-timer-throttling")
        # options.add_argument("--disable-backgrounding-occluded-windows")
        # options.add_argument("--disable-renderer-backgrounding")
        # options.add_argument("--disable-features=TranslateUI")
        # options.add_argument("--disable-ipc-flooding-protection")
        # options.add_argument("--disable-popup-blocking")
        # options.add_argument("--disable-notifications")
        # options.add_argument("--disable-default-apps")
        
        # Random user agent rotation for better stealth
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ]
        selected_ua = random.choice(user_agents)
        options.add_argument(f"--user-agent={selected_ua}")
        
        # Create temporary user data directory to avoid conflicts
        import tempfile
        self.temp_user_data_dir = tempfile.mkdtemp(prefix="uc-chrome-profile-")
        options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")
        
        print(f"🔧 Using temporary Chrome profile for stealth mode: {self.temp_user_data_dir}")
        print("📂 Profile: Temporary (clean stealth profile)")
        print("🥷 Enhanced stealth mode enabled to avoid bot detection!")
        print(f"🎭 Using random user agent: {selected_ua[:50]}...")
        
        # Add proxy configuration if provided
        if proxy:
            print(f"Configuring proxy: {proxy}")
            if proxy.startswith("http://") or proxy.startswith("https://"):
                proxy_url = proxy
            else:
                proxy_url = f"http://{proxy}"
            
            options.add_argument(f"--proxy-server={proxy_url}")
            print(f"Added proxy argument: --proxy-server={proxy_url}")
        
        print(f"Setting up undetected ChromeDriver with enhanced stealth")
        print(f"Proxy configuration: {proxy}")
        
        try:
            # Use undetected-chromedriver for maximum stealth
            print("🥷 Starting undetected Chrome for enhanced stealth mode...")
            self.driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                driver_executable_path=None,  # Auto-download chromedriver
                # user_data_dir=user_data_dir,
                use_subprocess=True,
                advanced_elements=True,
                headless=headless
            )
            
            # Execute enhanced stealth scripts to further hide automation
            self.apply_stealth_scripts()
            
            print("✅ Undetected Chrome started successfully!")
            print("👀 You should see all your bookmarks, extensions, and saved data!")
            print("🥷 Enhanced bot detection avoidance activated!")
            
        except Exception as e:
            print(f"Undetected Chrome failed: {e}")
            print("🔄 Falling back to regular Chrome with stealth options...")
            
            # Fallback to regular Chrome with maximum stealth options
            try:
                from selenium import webdriver
                chrome_options = Options()
                
                if headless:
                    chrome_options.add_argument("--headless=new")
                
                # Maximum stealth options
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--allow-running-insecure-content")
                chrome_options.add_argument("--disable-features=VizDisplayCompositor")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--remote-debugging-port=0")
                chrome_options.add_argument(f"--user-agent={selected_ua}")
                
                
                # Proxy settings
                if proxy:
                    if proxy.startswith("http://") or proxy.startswith("https://"):
                        proxy_url = proxy
                    else:
                        proxy_url = f"http://{proxy}"
                    chrome_options.add_argument(f"--proxy-server={proxy_url}")
                
                # Use direct path to Chrome on Mac
                if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
                    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                
                self.driver = webdriver.Chrome(options=chrome_options)
                
                # Apply stealth scripts after initialization
                self.apply_stealth_scripts()
                
                print("✅ Regular Chrome started with enhanced stealth mode!")
                
            except Exception as e2:
                print(f"Fallback Chrome also failed: {e2}")
                raise Exception(f"Could not start Chrome in stealth mode. Error: {e2}")
    
    def apply_stealth_scripts(self):
        """Apply advanced stealth scripts to hide automation indicators."""
        try:
            # Enhanced stealth script to hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Override user agent via CDP
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.driver.execute_script("return navigator.userAgent;")
            })
            
            # Comprehensive automation hiding script
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                "source": """
                    // Hide webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Remove automation indicators
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Element;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                    
                    // Override plugins length
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                    );
                    
                    // Hide automation in chrome object
                    if (window.chrome) {
                        delete window.chrome.runtime.onConnect;
                        delete window.chrome.runtime.onMessage;
                    }
                """
            })
            
            # Add random mouse movements and clicks to simulate human behavior
            self.driver.execute_script("""
                // Add subtle random mouse movements
                let mouseX = Math.random() * window.innerWidth;
                let mouseY = Math.random() * window.innerHeight;
                
                function simulateMouseMove() {
                    mouseX += (Math.random() - 0.5) * 10;
                    mouseY += (Math.random() - 0.5) * 10;
                    
                    mouseX = Math.max(0, Math.min(window.innerWidth, mouseX));
                    mouseY = Math.max(0, Math.min(window.innerHeight, mouseY));
                    
                    const event = new MouseEvent('mousemove', {
                        clientX: mouseX,
                        clientY: mouseY
                    });
                    document.dispatchEvent(event);
                }
                
                // Simulate random mouse movements every 2-5 seconds
                setInterval(simulateMouseMove, Math.random() * 3000 + 2000);
            """)
            
            print("🔒 Advanced stealth scripts applied successfully!")
            
        except Exception as e:
            print(f"⚠️  Some stealth scripts failed to apply: {e}")
    
    def human_like_delay(self, min_delay=0.5, max_delay=2.0):
        """Add human-like random delays between actions."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def open_url(self, url):
        """
        Open the specified URL in the browser with human-like behavior.
        
        Args:
            url (str): The URL to open
        """
        try:
            # Add human-like delay before navigation
            self.human_like_delay(0.5, 1.5)
            
            self.driver.get(url)
            
            # Add human-like delay after page load
            self.human_like_delay(1.0, 3.0)
            
            # Simulate human-like scrolling
            self.driver.execute_script("""
                window.scrollTo({
                    top: Math.random() * 300,
                    behavior: 'smooth'
                });
            """)
            
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
                print(f"🧹 Cleaned up temporary uc profile: {self.temp_user_data_dir}")
            except Exception as e:
                print(f"⚠️  Could not clean up uc temp directory: {e}")

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
                print(f"🧹 Cleaned up temporary uc profile: {self.temp_user_data_dir}")
            except Exception as e:
                print(f"⚠️  Could not clean up uc temp directory: {e}")


def main():
    """Main function to demonstrate usage."""
    # Example URL
    url = "https://www.example.com"
    
    # Create an instance of WebsiteOpener with enhanced stealth mode
    opener = WebsiteOpener(headless=False)
    
    # Open the URL
    opener.open_url(url)
    
    # Wait for a few seconds to view the page
    time.sleep(3)
    
    # Close the browser
    opener.close()


if __name__ == "__main__":
    main() 