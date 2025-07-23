#!/usr/bin/env python3
"""
Simple script to start Chrome with remote debugging enabled
This allows Selenium to connect to your existing Chrome browser
"""

import subprocess
import os
import sys

def start_chrome_with_debugging():
    """Start Chrome with remote debugging on port 9222"""
    
    print("🚀 Starting Chrome with Remote Debugging")
    print("=" * 50)
    
    # Chrome executable path for macOS
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    debug_port = 9222
    
    # Check if Chrome exists
    if not os.path.exists(chrome_path):
        print("❌ Chrome not found at expected path!")
        print(f"   Expected: {chrome_path}")
        print("\n💡 Please start Chrome manually with this command:")
        print(f'   "{chrome_path}" --remote-debugging-port={debug_port}')
        return False
    
    # Chrome arguments
    chrome_args = [
        chrome_path,
        f"--remote-debugging-port={debug_port}",
        # Use default profile instead of temporary one
        # "--user-data-dir=/tmp/chrome-selenium",  # Separate profile
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-default-apps",
        "https://www.msport.com/ng/web/welcome"  # Open MSport directly
    ]
    
    try:
        print(f"🌐 Starting Chrome with:")
        print(f"   Debug Port: {debug_port}")
        print(f"   Opening: https://www.msport.com/ng/web/welcome")
        print("   You can now use Selenium to connect to this Chrome instance!")
        
        # Start Chrome
        process = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"✅ Chrome started successfully!")
        print(f"📌 Process ID: {process.pid}")
        print(f"🔗 Debug URL: http://localhost:{debug_port}")
        
        print("\n📋 What to do next:")
        print("1. Chrome should open with MSport loaded")
        print("2. You can now run your Selenium scripts")
        print("3. They will connect to this Chrome instance")
        print("4. Close this terminal when you're done (Chrome will keep running)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Chrome: {e}")
        return False

def check_chrome_debug_status():
    """Check if Chrome is already running with debugging"""
    import psutil
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and '--remote-debugging-port=' in ' '.join(cmdline):
                        for part in cmdline:
                            if part.startswith('--remote-debugging-port='):
                                port = part.split('=')[1]
                                print(f"✅ Chrome already running with debug port: {port}")
                                print(f"🔗 Debug URL: http://localhost:{port}")
                                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("❌ No Chrome with remote debugging found")
        return False
        
    except Exception as e:
        print(f"❌ Error checking Chrome status: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Chrome Remote Debug Starter")
    print("=" * 40)
    
    # Check if Chrome is already running with debugging
    if check_chrome_debug_status():
        print("\n💡 Chrome is already running with remote debugging!")
        print("   You can use your existing Chrome session.")
        choice = input("\n❓ Start a new Chrome instance anyway? (y/n): ").lower().strip()
        if choice not in ['y', 'yes']:
            print("✅ Using existing Chrome instance")
            sys.exit(0)
    
    # Start Chrome with debugging
    if start_chrome_with_debugging():
        print("\n🎉 Setup complete!")
        print("   You can now run test_captcha_detection.py")
    else:
        print("\n💥 Setup failed!")
        sys.exit(1) 