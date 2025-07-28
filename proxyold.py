# import requests
# url = 'https://ip.decodo.com/json'
# # proxy = "http://brd-customer-hl_1b6b5179-zone-datacenter_proxy1-ip-156.252.228.152:qh13e50d5n6f@brd.superproxy.io:33335"

# username = 'sp9jrhuu4a'
# password = 'N5uCg8r0lwiupD8Ac+'
# proxy = f"http://ng.decodo.com:42001"
# result = requests.get(url, proxies = {
#     'http': proxy,
#     'https': proxy
# })
# print(result.text)

import requests
url = 'https://ip.decodo.com/json'
proxy = f"http://brd-customer-hl_3fa1037b-zone-datacenter_proxy1-country-ng:be0682squyj3@brd.superproxy.io:33335"
result = requests.get(url, proxies = {
    'http': proxy,
    'https': proxy
})
print(result.text)


# import urllib.request
# import ssl

# proxy = 'http://brd-customer-hl_3fa1037b-zone-datacenter_proxy1-country-ng:be0682squyj3@brd.superproxy.io:33335'
# url = 'https://geo.brdtest.com/welcome.txt?product=dc&method=native'

# opener = urllib.request.build_opener(
#     urllib.request.ProxyHandler({'https': proxy, 'http': proxy})
# )

# try:
#     print(opener.open(url).read().decode())
# except Exception as e:
#     print(f"Error: {e}")
