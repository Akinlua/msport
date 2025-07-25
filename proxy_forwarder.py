import os
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def create_proxy_extension(proxy_host, proxy_port, proxy_username, proxy_password):
    """Create Chrome extension for proxy authentication"""
    
    manifest_json = """
    {
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
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (proxy_host, proxy_port, proxy_username, proxy_password)

    # Create extension directory
    extension_dir = "proxy_auth_extension"
    if not os.path.exists(extension_dir):
        os.makedirs(extension_dir)
    
    # Write files
    with open(f"{extension_dir}/manifest.json", "w") as f:
        f.write(manifest_json)
    
    with open(f"{extension_dir}/background.js", "w") as f:
        f.write(background_js)
    
    return extension_dir

def setup_selenium_with_auth_proxy(proxy_host, proxy_port, proxy_username, proxy_password):
    """Setup Selenium with authenticated proxy"""
    
    # Create proxy extension
    extension_dir = create_proxy_extension(proxy_host, proxy_port, proxy_username, proxy_password)
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f"--load-extension={extension_dir}")
    chrome_options.add_argument("--disable-extensions-except=" + extension_dir)
    chrome_options.add_argument("--disable-extensions-file-access-check")
    
    # Optional: Run headless
    # chrome_options.add_argument("--headless")
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    return driver

# Example usage
if __name__ == "__main__":
    # Your residential proxy details
    PROXY_HOST = "brd.superproxy.io"
    PROXY_PORT = "33335"
    PROXY_USERNAME = "brd-customer-hl_1b6b5179-zone-datacenter_proxy1-ip-156.252.228.152"
    PROXY_PASSWORD = "qh13e50d5n6f"
    
    # Create driver with authenticated proxy
    driver = setup_selenium_with_auth_proxy(
        PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD
    )
    
    try:
        # Test the proxy
        driver.get("https://httpbin.org/ip")
        print("Page loaded successfully with proxy")
        
        # Your automation code here
        driver.get("https://example.com")
        
    finally:
        driver.quit()