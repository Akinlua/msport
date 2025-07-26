# MSport Docker Setup

This directory contains Docker configuration for running the MSport integration tests in a containerized environment.

## Files Created

- `Dockerfile` - Main container definition with Python, Chrome, and dependencies
- `docker-compose.yml` - Service orchestration with optional debugging services
- `entrypoint.sh` - Startup script for Xvfb and application initialization
- `.dockerignore` - Excludes unnecessary files from build context

## Prerequisites

1. Docker and Docker Compose installed
2. `config.json` file with MSport account credentials
3. Optional: Set `CAPTCHA_API_KEY` environment variable for 2captcha integration

## Quick Start

1. **Build and run the main test container:**
   ```bash
   docker-compose up --build msport-test
   ```

2. **Run specific test commands:**
   ```bash
   # Run selenium script directly
   docker-compose run --rm msport-test python selenium_script.py
   
   # Run integration tests
   docker-compose run --rm msport-test python test_msport_integration.py
   
   # Run with interactive shell
   docker-compose run --rm msport-test bash
   ```

## Environment Variables

Set these in a `.env` file or export them:

```bash
# For 2captcha integration
CAPTCHA_API_KEY=your_2captcha_api_key

# For Pinnacle API (if used)
PINNACLE_HOST=your_pinnacle_host
```

## Configuration

### 1. Create config.json

Create a `config.json` file in the project root:

```json
{
    "accounts": [
        {
            "username": "your_msport_username",
            "password": "your_msport_password",
            "active": true,
            "balance": 1000
        }
    ]
}
```

### 2. Create logs directory

```bash
mkdir -p logs
```

## Service Profiles

### Default Profile
- `msport-test` - Main application container

### Debug Profile
Start with VNC access for debugging:

```bash
docker-compose --profile debug up
```

Access VNC at: http://localhost:6080 (password: msport123)

### Selenium Grid Profile
For distributed testing:

```bash
docker-compose --profile selenium-grid up
```

Access Grid UI at: http://localhost:4444

## Docker Commands

### Build and Run
```bash
# Build the image
docker-compose build

# Run the tests
docker-compose up msport-test

# Run in detached mode
docker-compose up -d msport-test

# View logs
docker-compose logs -f msport-test
```

### Development
```bash
# Run with code sync (changes reflected immediately)
docker-compose run --rm -v $(pwd):/app msport-test python test_msport_integration.py

# Interactive shell for debugging
docker-compose run --rm msport-test bash

# Run specific test function
docker-compose run --rm msport-test python -c "from test_msport_integration import test_login; test_login()"
```

### Cleanup
```bash
# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Troubleshooting

### Chrome Issues
If Chrome fails to start:

```bash
# Check Chrome installation in container
docker-compose run --rm msport-test google-chrome --version

# Check ChromeDriver
docker-compose run --rm msport-test chromedriver --version

# Test with headless mode
docker-compose run --rm msport-test python -c "
from selenium_script import WebsiteOpener
opener = WebsiteOpener(headless=True)
opener.open_url('https://www.google.com')
opener.close()
print('Chrome test successful!')
"
```

### Display Issues
If you get display-related errors:

```bash
# Check Xvfb is running
docker-compose run --rm msport-test ps aux | grep Xvfb

# Test display
docker-compose run --rm msport-test echo $DISPLAY
```

### Permission Issues
If you get permission errors:

```bash
# Fix ownership
sudo chown -R $USER:$USER .

# Or run as root (not recommended)
docker-compose run --rm --user root msport-test bash
```

### Network Issues
If the container can't reach MSport:

```bash
# Test network connectivity
docker-compose run --rm msport-test curl -I https://msport.com

# Use host networking (may be needed for some proxy setups)
# Uncomment network_mode: "host" in docker-compose.yml
```

## Performance Optimization

### For faster builds:
- Use multi-stage builds for production
- Pre-built images with dependencies

### For better resource usage:
- Adjust `shm_size` based on your needs
- Limit container resources in docker-compose.yml:

```yaml
services:
  msport-test:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Security Notes

- Never commit `config.json` with real credentials
- Use environment variables for sensitive data
- Consider using Docker secrets for production deployments
- The container runs as non-root user for security

## Production Deployment

For production use:

1. Use environment-specific config files
2. Implement proper logging and monitoring
3. Use health checks
4. Consider using a container orchestrator (Kubernetes, Docker Swarm)
5. Implement proper backup strategies for logs and data 