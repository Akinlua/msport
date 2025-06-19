import requests
url = 'https://ip.decodo.com/json'
proxy = "http://156.242.43.44:3129"

result = requests.get(url, proxies = {
    'http': proxy,
    'https': proxy
})
print(result.text)