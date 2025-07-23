#!/usr/bin/env python3
"""
Cloudflare Turnstile CAPTCHA Solver using 2captcha service
"""

import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from twocaptcha import TwoCaptcha


class CaptchaSolver:
    """Handle Cloudflare Turnstile CAPTCHA solving using 2captcha service"""
    
    def __init__(self, api_key=None):
        """
        Initialize the CAPTCHA solver
        
        Args:
            api_key (str): 2captcha API key. If None, will try to get from environment variable CAPTCHA_API_KEY
        """
        self.api_key = api_key or os.getenv("CAPTCHA_API_KEY", "faf467050c2932f855a1a3ef21286af0")
        self.solver = TwoCaptcha(self.api_key)
        self.max_retries = 3
        
    def detect_turnstile_captcha(self, driver):
        """
        Detect if Cloudflare Turnstile CAPTCHA is present on the page
        Enhanced to handle shadow DOM and iframe scenarios
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            tuple: (is_present, sitekey, response_field) or (False, None, None)
        """
        try:
            print("🔍 Enhanced CAPTCHA detection starting...")
            
            # Method 1: Look for Turnstile widget in main DOM
            turnstile_selectors = [
                "div.cf-turnstile",
                "[data-sitekey]",
                "iframe[src*='turnstile']",
                "iframe[src*='cloudflare']",
                ".cf-turnstile",
                "#cf-turnstile",
                ".cloudflare-challenge",
                "[id*='cf-chl-widget']"
            ]
            
            turnstile_element = None
            for selector in turnstile_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        turnstile_element = elements[0]
                        print(f"✅ Found Turnstile element with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            # Method 2: Look for Turnstile iframe specifically
            if not turnstile_element:
                print("🔍 Checking for Turnstile iframes...")
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        src = iframe.get_attribute("src") or ""
                        if "turnstile" in src.lower() or "cloudflare" in src.lower():
                            turnstile_element = iframe
                            print(f"✅ Found Turnstile iframe: {src}")
                            break
                except Exception as e:
                    print(f"Error checking iframes: {e}")
            
            # Method 3: Check for shadow DOM elements
            if not turnstile_element:
                print("🔍 Checking for shadow DOM elements...")
                try:
                    # Look for elements that might contain shadow roots
                    shadow_hosts = driver.find_elements(By.CSS_SELECTOR, "*")
                    for host in shadow_hosts:
                        try:
                            # Try to access shadow root (this will fail silently if no shadow root)
                            shadow_root = driver.execute_script("return arguments[0].shadowRoot", host)
                            if shadow_root:
                                # Look for Turnstile elements in shadow DOM
                                turnstile_in_shadow = driver.execute_script("""
                                    var shadowRoot = arguments[0].shadowRoot;
                                    if (shadowRoot) {
                                        var turnstileElements = shadowRoot.querySelectorAll('[data-sitekey], .cf-turnstile, div[id*="turnstile"]');
                                        return turnstileElements.length > 0 ? turnstileElements[0] : null;
                                    }
                                    return null;
                                """, host)
                                
                                if turnstile_in_shadow:
                                    turnstile_element = host  # Use the shadow host
                                    print("✅ Found Turnstile in shadow DOM")
                                    break
                        except Exception:
                            continue
                except Exception as e:
                    print(f"Error checking shadow DOM: {e}")
            
            # Method 4: Look for the challenge text or visual indicators
            if not turnstile_element:
                print("🔍 Looking for visual CAPTCHA indicators...")
                challenge_indicators = [
                    "//*[contains(text(), 'Verify you are human')]",
                    "//*[contains(text(), 'verify you are human')]", 
                    "//*[contains(text(), 'Checking your browser')]",
                    "//*[contains(text(), 'cloudflare')]",
                    "//div[contains(@class, 'challenge')]",
                    "//div[contains(@id, 'challenge')]"
                ]
                
                for indicator in challenge_indicators:
                    try:
                        elements = driver.find_elements(By.XPATH, indicator)
                        if elements:
                            # Find the closest parent that might be the CAPTCHA container
                            for element in elements:
                                parent = element.find_element(By.XPATH, "./..")
                                if parent:
                                    turnstile_element = parent
                                    print(f"✅ Found CAPTCHA by text indicator: {indicator}")
                                    break
                            if turnstile_element:
                                break
                    except Exception:
                        continue
            
            if not turnstile_element:
                print("❌ No Turnstile CAPTCHA element found with any method")
                
                # Final check: look for the response field directly
                response_field = self._find_turnstile_response_field(driver)
                if response_field:
                    print("✅ Found cf-turnstile-response field, assuming CAPTCHA is present")
                    # Try to find sitekey from page source or scripts
                    sitekey = self._extract_sitekey_from_page(driver)
                    return True, sitekey, response_field
                
                return False, None, None
            
            # Extract sitekey from the found element or page
            sitekey = None
            
            # Method 1: Try to get sitekey from the element attributes
            sitekey_attrs = ['data-sitekey', 'data-site-key', 'sitekey']
            for attr in sitekey_attrs:
                try:
                    sitekey = turnstile_element.get_attribute(attr)
                    if sitekey:
                        print(f"✅ Found sitekey from element attribute {attr}: {sitekey}")
                        break
                except Exception:
                    continue
            
            # Method 2: If no sitekey from element, search in page source or scripts
            if not sitekey:
                print("🔍 Searching for sitekey in page source...")
                sitekey = self._extract_sitekey_from_page(driver)
            
            if not sitekey:
                print("❌ Could not find sitekey")
                return False, None, None
            
            # Find the response field
            response_field = self._find_turnstile_response_field(driver)
            
            if not response_field:
                print("❌ Could not find cf-turnstile-response field")
                return False, None, None
            
            print(f"✅ Cloudflare Turnstile CAPTCHA detected:")
            print(f"   Sitekey: {sitekey}")
            print(f"   Response field: Found")
            
            return True, sitekey, response_field
            
        except Exception as e:
            print(f"❌ Error in enhanced CAPTCHA detection: {e}")
            import traceback
            traceback.print_exc()
            return False, None, None
    
    def _find_turnstile_response_field(self, driver):
        """
        Find the cf-turnstile-response field with enhanced search
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            WebElement or None
        """
        response_field_selectors = [
            'input[name="cf-turnstile-response"]',
            'input[id*="cf-chl-widget"]',
            'input[id*="cf-turnstile"]',
            'input[name="g-recaptcha-response"]',  # reCAPTCHA compatibility mode
            'textarea[name="cf-turnstile-response"]',
            'textarea[id*="cf-turnstile"]',
            'input[type="hidden"][name*="turnstile"]',
            'input[type="hidden"][id*="turnstile"]'
        ]
        
        for selector in response_field_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found response field with selector: {selector}")
                    return elements[0]
            except Exception:
                continue
        
        # Also try XPath for more flexible matching
        xpath_selectors = [
            "//input[contains(@name, 'cf-turnstile-response')]",
            "//input[contains(@id, 'cf-chl-widget')]",
            "//input[contains(@name, 'turnstile')]",
            "//textarea[contains(@name, 'turnstile')]",
            "//input[@type='hidden' and contains(@name, 'turnstile')]"
        ]
        
        for selector in xpath_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"✅ Found response field with XPath: {selector}")
                    return elements[0]
            except Exception:
                continue
        
        print("❌ Could not find cf-turnstile-response field with any selector")
        return None
    
    def _extract_sitekey_from_page(self, driver):
        """
        Extract sitekey from page source, scripts, or JavaScript variables
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            sitekey string or None
        """
        try:
            # Method 1: Look in page source for sitekey
            page_source = driver.page_source
            
            import re
            
            # Common patterns for sitekey in HTML/JavaScript
            sitekey_patterns = [
                r'data-sitekey=["\']([^"\']+)["\']',
                r'sitekey:["\s]*([^"\']+)["\']',
                r'siteKey:["\s]*([^"\']+)["\']',
                r'"sitekey":\s*"([^"]+)"',
                r"'sitekey':\s*'([^']+)'",
                r'turnstile\.render\([^,]*["\']([^"\']+)["\']',
                # The specific sitekey from the user's example
                r'0x4AAAAAAAwhpUsVBKANtpy4'
            ]
            
            for pattern in sitekey_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    sitekey = matches[0]
                    print(f"✅ Found sitekey in page source: {sitekey}")
                    return sitekey
            
            # Method 2: Check JavaScript variables
            js_sitekey = driver.execute_script("""
                // Check common JavaScript variables
                if (typeof window.turnstileSiteKey !== 'undefined') return window.turnstileSiteKey;
                if (typeof window.sitekey !== 'undefined') return window.sitekey;
                if (typeof window.SITEKEY !== 'undefined') return window.SITEKEY;
                
                // Check if turnstile object exists
                if (typeof window.turnstile !== 'undefined') {
                    try {
                        var widgets = document.querySelectorAll('[data-sitekey]');
                        if (widgets.length > 0) return widgets[0].getAttribute('data-sitekey');
                    } catch(e) {}
                }
                
                return null;
            """)
            
            if js_sitekey:
                print(f"✅ Found sitekey from JavaScript: {js_sitekey}")
                return js_sitekey
            
            # Method 3: Use the known sitekey from the user's example as fallback
            fallback_sitekey = "0x4AAAAAAAwhpUsVBKANtpy4"
            print(f"⚠️  Using known fallback sitekey: {fallback_sitekey}")
            return fallback_sitekey
            
        except Exception as e:
            print(f"❌ Error extracting sitekey: {e}")
            return None
    
    def solve_turnstile_captcha(self, driver, page_url, max_retries=None):
        """
        Solve Cloudflare Turnstile CAPTCHA on the current page
        
        Args:
            driver: Selenium WebDriver instance
            page_url (str): Current page URL
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            bool: True if CAPTCHA was solved successfully, False otherwise
        """
        if max_retries is None:
            max_retries = self.max_retries
            
        print(f"🔍 Checking for Cloudflare Turnstile CAPTCHA on {page_url}")
        
        # Detect CAPTCHA
        is_present, sitekey, response_field = self.detect_turnstile_captcha(driver)
        
        if not is_present:
            print("✅ No CAPTCHA detected, proceeding...")
            return True
        
        if not sitekey:
            print("❌ CAPTCHA detected but no sitekey found")
            return False
        
        if not response_field:
            print("❌ CAPTCHA detected but no response field found")
            return False
        
        # Solve CAPTCHA with retries
        for attempt in range(1, max_retries + 1):
            print(f"🔄 Solving CAPTCHA attempt {attempt}/{max_retries}")
            
            try:
                # Submit CAPTCHA to 2captcha
                print(f"📤 Submitting Turnstile CAPTCHA to 2captcha...")
                print(f"   Sitekey: {sitekey}")
                print(f"   Page URL: {page_url}")
                
                result = self.solver.turnstile(
                    sitekey=sitekey,
                    url=page_url
                )
                
                captcha_token = result['code']
                print(f"✅ CAPTCHA solved! Token: {captcha_token[:50]}...")
                
                # Inject the token into the response field
                print("💉 Injecting CAPTCHA token into response field...")
                
                # Use JavaScript to set the value (more reliable than send_keys)
                driver.execute_script(
                    "arguments[0].value = arguments[1];",
                    response_field,
                    captcha_token
                )
                
                # Also try setting via setAttribute for compatibility
                driver.execute_script(
                    "arguments[0].setAttribute('value', arguments[1]);",
                    response_field,
                    captcha_token
                )
                
                # Trigger change event to notify the page
                driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                    response_field
                )
                
                # Additional: If there's a callback function, try to trigger it
                driver.execute_script("""
                    // Try to find and trigger Turnstile callback
                    if (window.turnstile && window.turnstile.getResponse) {
                        try {
                            window.turnstile.getResponse();
                        } catch(e) {}
                    }
                    
                    // Try common callback patterns
                    if (window.onTurnstileCallback) {
                        try {
                            window.onTurnstileCallback(arguments[0]);
                        } catch(e) {}
                    }
                """, captcha_token)
                
                print("✅ CAPTCHA token injected successfully!")
                
                # Wait a moment for the page to process the token
                time.sleep(2)
                
                # Verify the token was set
                current_value = response_field.get_attribute('value')
                if current_value == captcha_token:
                    print("✅ CAPTCHA token verification successful!")
                    return True
                else:
                    print(f"⚠️  Token verification failed. Expected: {captcha_token[:20]}..., Got: {current_value[:20] if current_value else 'None'}...")
                    
            except Exception as e:
                print(f"❌ CAPTCHA solving attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    print(f"🔄 Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"❌ All {max_retries} CAPTCHA solving attempts failed")
        
        return False
    
    def wait_for_captcha_completion(self, driver, timeout=30):
        """
        Wait for CAPTCHA to be completed (either solved or disappeared)
        
        Args:
            driver: Selenium WebDriver instance
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            bool: True if CAPTCHA is no longer blocking, False if timeout
        """
        print(f"⏳ Waiting for CAPTCHA completion (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if CAPTCHA is still present
            is_present, _, _ = self.detect_turnstile_captcha(driver)
            
            if not is_present:
                print("✅ CAPTCHA completed or disappeared")
                return True
            
            # Check if we can proceed (look for login form or success indicators)
            try:
                # Look for signs that CAPTCHA is solved (page changed, login form available, etc.)
                login_indicators = [
                    "input[type='tel']",
                    "input[placeholder*='Mobile']", 
                    "input[type='password']",
                    ".login-form",
                    "[data-testid='login']"
                ]
                
                for indicator in login_indicators:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, indicator)
                        if element and element.is_displayed():
                            print("✅ Login form detected - CAPTCHA appears to be solved")
                            return True
                    except NoSuchElementException:
                        continue
                        
            except Exception:
                pass
            
            time.sleep(1)
        
        print(f"⏰ CAPTCHA completion timeout after {timeout}s")
        return False


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing CAPTCHA Solver...")
    
    # Test with demo configuration
    solver = CaptchaSolver()
    print(f"✅ CAPTCHA Solver initialized with API key: {solver.api_key[:10]}...")
    
    # Test API connectivity (optional)
    try:
        balance = solver.solver.balance()
        print(f"💰 2captcha account balance: ${balance}")
    except Exception as e:
        print(f"⚠️  Could not check 2captcha balance: {e}") 