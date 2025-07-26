#!/usr/bin/env python3
"""
Simple Selenium script to visit msport.com with proxy support and take a screenshot.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def create_driver_with_proxy(proxy_host=None, proxy_port=None):
    """Create Chrome driver with optional proxy configuration."""
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
    return driver

def visit_and_screenshot(proxy_host=None, proxy_port=None):
    """Visit msport.com and take a screenshot."""
    driver = None
    try:
        # Create driver
        print("Starting Chrome driver...")
        driver = create_driver_with_proxy(proxy_host, proxy_port)
        
        # Visit the website
        print("Visiting msport.com...")
        driver.get("https://msport.com")
        
        # Wait for page to load
        print("Waiting for page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait to ensure full page load
        time.sleep(3)
        
        # Take screenshot
        timestamp = int(time.time())
        screenshot_name = f"msport_screenshot_{timestamp}.png"
        
        print(f"Taking screenshot: {screenshot_name}")
        driver.save_screenshot(screenshot_name)
        
        print(f"Screenshot saved as: {screenshot_name}")
        print(f"Page title: {driver.title}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        if driver:
            driver.quit()
            print("Driver closed.")

if __name__ == "__main__":
    # Example usage:
    # For no proxy:
    visit_and_screenshot()
    
    # For with proxy (uncomment and modify as needed):
    # visit_and_screenshot(proxy_host="127.0.0.1", proxy_port="8080") 