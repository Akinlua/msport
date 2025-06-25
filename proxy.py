import requests
url = 'https://ip.decodo.com/json'
proxy = "http://156.233.88.27:3129"

result = requests.get(url, proxies = {
    'http': proxy,
    'https': proxy
})
print(result.text)