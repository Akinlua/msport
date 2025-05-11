from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import asyncio
import dotenv
import datetime
import glob
import shutil
import json
from bson.objectid import ObjectId
from selenium.webdriver.common.action_chains import ActionChains
import requests
dotenv.load_dotenv()

async def setup_driver():
    """Setup and return a driverless Chrome instance"""
    # Create the download directory if it doesn't exist
    # Create and return the webdriver
    options = webdriver.ChromeOptions()
    if(os.getenv("ENVIRONMENT") == "production"):
        #make chrome headless
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
    download_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads"))
    os.makedirs(download_dir, exist_ok=True)
    print(f"Downloads will be saved to: {download_dir}")
    
    # Create a profile directory for Chrome to make settings persistent
    profile_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile"))
    os.makedirs(profile_dir, exist_ok=True)
    print(f"Using Chrome profile at: {profile_dir}")
    
    # Add logging preferences
    options.add_argument("--log-level=3")  # Minimal logging
    
    # Use the custom profile directory
    #options.add_argument(f"--user-data-dir={profile_dir}")
    
    # Set download preferences with absolute path - more reliable
    prefs = {
        "download.default_directory": download_dir.replace("\\", "/"),  # Use forward slashes
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,  # Disable safe browsing which can block downloads
        "plugins.always_open_pdf_externally": True,  # Auto-download PDFs
        "browser.download.folderList": 2,  # 2 means custom location
        "browser.helperApps.neverAsk.saveToDisk": "application/pdf,application/x-pdf,application/octet-stream,text/plain,text/html",
        "browser.download.manager.showWhenStarting": False
    }
    options.add_experimental_option("prefs", prefs)
    
    # Additional settings for downloads
    download_dir_escaped = download_dir.replace('\\', '/')
    options.add_argument(f"--download.default_directory={download_dir_escaped}")
    
    # Create the driver
    driver = await webdriver.Chrome(options=options)
    
    # Execute JS to modify download behavior directly in the page context
    await driver.execute_script("""
        window.addEventListener('load', function() {
            // Try to set browser to auto-download files
            Object.defineProperty(HTMLAnchorElement.prototype, 'download', {
                get: function() { return true; }
            });
        });
    """)
    
    return driver

async def login(driver, credentials=1):
    await driver.get("https://www.pinnacleoddsdropper.com/terminal", wait_load=True)



async def main():
    # Initialize the driver
    driver = await setup_driver()
    
    try:
        await login(driver)
        await driver.sleep(10)
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Always close the drivers
        await driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
