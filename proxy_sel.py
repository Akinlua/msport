from selenium import webdriver

proxy_host = "brd.superproxy.io"
proxy_port = "22225"
proxy_user = "brd-customer-myaccount-zone-residential"
proxy_pass = "myPass123"

proxy_auth = f"{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--proxy-server=http://brd-customer-hl_1b6b5179-zone-datacenter_proxy1-ip-156.252.228.152:qh13e50d5n6f@brd.superproxy.io:33335")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://ipinfo.io/json")  # test IP



import undetected_chromedriver as uc

# Your proxy details (Bright Data residential example)
proxy_user = "brd-customer-youruser-zone-residential"
proxy_pass = "yourpassword"
proxy_host = "brd.superproxy.io"
proxy_port = "22225"

proxy_string = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

options = uc.ChromeOptions()
options.add_argument("--start-maximized")

options.add_argument(f"--proxy-server={proxy_string}")

driver = uc.Chrome(options=options)
driver.get("https://ipinfo.io/json")  # This should now show your proxy IP
