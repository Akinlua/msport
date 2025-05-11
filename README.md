# Selenium Website Opener

A simple, well-structured Selenium script to open a website URL.

## Requirements

- Python 3.6+
- Chrome browser installed

## Installation

1. Clone this repository or download the files
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with:

```bash
python selenium_script.py
```

### Customizing

To open a different URL, modify the `url` variable in the `main()` function:

```python
# Example URL
url = "https://your-website-url.com"
```

To run in headless mode (without visible browser window):

```python
opener = WebsiteOpener(headless=True)
```

## Structure

- `WebsiteOpener` class: Handles all Selenium operations
- `setup_driver()`: Configures the Chrome WebDriver
- `open_url()`: Opens the specified URL
- `close()`: Cleans up resources

## License

MIT 