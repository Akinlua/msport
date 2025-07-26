#!/bin/bash

# Start Xvfb for headless operation
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99

# Wait a moment for Xvfb to start
sleep 2

# Check if Chrome is accessible
echo "Checking Chrome installation..."
google-chrome --version

# Check if ChromeDriver is accessible
echo "Checking ChromeDriver installation..."
chromedriver --version

# Run the application
echo "Starting application..."
exec "$@" 