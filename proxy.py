import requests
url = 'https://ip.decodo.com/json'
proxy = "http://156.228.104.89:3129"

result = requests.get(url, proxies = {
    'http': proxy,
    'https': proxy
})
print(result.text)