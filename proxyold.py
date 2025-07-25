import requests
url = 'https://ip.decodo.com/json'
# proxy = "http://brd-customer-hl_1b6b5179-zone-datacenter_proxy1-ip-156.252.228.152:qh13e50d5n6f@brd.superproxy.io:33335"

username = 'sp9jrhuu4a'
password = 'N5uCg8r0lwiupD8Ac+'
proxy = f"http://ng.decodo.com:42001"
result = requests.get(url, proxies = {
    'http': proxy,
    'https': proxy
})
print(result.text)