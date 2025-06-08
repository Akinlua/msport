import requests

url = "https://sports.bet9ja.com/desktop/feapi/AuthAjax/Login?v_cache_version=1.276.0.187"

payload = {
    'username': 'Suleybawa',
    'password': 'Spotify1'
}
headers = {
    # ":authority": "sports.bet9ja.com",
    # ":method": "POST", 
    # ":path": "/desktop/feapi/AuthAjax/Login?v_cache_version=1.279.0.197",
    # ":scheme": "https",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "content-length": "36",
    "content-type": "application/x-www-form-urlencoded",
    # "cookie": "MgidSensorNVis=2; MgidSensorHref=https://sports.bet9ja.com/mobile/login; livlang=en; _gcl_au=1.1.1685039516.1747492669; _ga=GA1.1.1119100165.1747492671; _tgpc=8e05409b-5108-551e-aebd-010bc067197d; _fbp=fb.1.1747492671467.463674449363430150; __adm_tid=tid-40ef3922d.467e01bbe; promocode=303356; btag=a_303356b_112c_10699825318; ftv=1; livsid=34f208b0-5504-54b9-f36d-fc6ba75d66e5; bm_mi=190A533D9C7BD16B4B7D4083D7F23E2D~YAAQUvkTAumohTuXAQAAzzXZTxw0y0MbnOX3OtFvOon3asfXdjpy4K1/xxZ7oOrxKpefuajBkWYG5e1xj7hMVZSuBOQPIiKi8rCcGFzVQk5hMy55opY3qVJ5V3vCpwn0KqEAO5PGaVWg2G6ASTWGDV5IRjaBXiiTefya8Gqot/dB3b8nTG4ZqrjClwDWzV0UvgSdpbWLEnUliI9ZiHA/K1AoZpaGphWMtrnCtEZzCONBX2+6NkVwPxKTIFwxChQ7mW2Xcfij20Po8RrBRFnm3rwQH2ONRqdn7HEWZUdfNi/yNTJs6TMuGoP54SAv~1; ak_bmsc=53E6ABF1A7EAEC3735E179BE4281ACC2~000000000000000000000000000000~YAAQUvkTAm+phTuXAQAAuD/ZTxwHPFX0nmQlgJ8Co0k/54ITzjPSQ2ADURaRGpvD5MEuCFfLw26Am0zfNS9edxqu80ov2TsAgRNl1x1PRuTAw+RHQWZx6wx1A8m3rl927UuLgS7niX9amBdGg3FQBwqxTms34tB53qG2i8vIBsmQNS+OTQ0E7uwGpeWpD3EXEttyqHg/upOneEulZSCU9tBVoi/751UGFFAuomkqpBi0FXnKwCJDvca+l8gcZPCwyBw9KyXsTov1SiR0S1rxflMFAXV1CRtHr0V4eMxP/DfZruQ8e0wmPF8Z1LCg8RPrsjgjFIiIqF2AUKtm9iXTyZNeq9wAFbeVSs2VvsgbSrBl8pe7wDpKYWyLukFLIYF7V0VnY8X3KFvJYPi0h0uAItsgQjN36PdpjwV1KqqlQSfQ4Nu/rz64U8NsWS/TuJUMhrGXoH902H1/7/n3w0y2olE9aW0TszMT5CdbzJqf; _ga_YYQNLHMCQS=GS2.1.s1749391324$o29$g1$t1749391329$j55$l0$h0; _tguatd=eyJzYyI6InNwb3J0cy5iZXQ5amEuY29tIiwiZnRzIjoic3BvcnRzLmJldDlqYS5jb20ifQ==; _tgidts=eyJzaCI6ImQ0MWQ4Y2Q5OGYwMGIyMDRlOTgwMDk5OGVjZjg0MjdlIiwiY2kiOiJkMmZmZDA4My03MzMwLTVlMDgtODk1My1mYTM3ZjQ4OTkxMzgiLCJzaSI6IjhlYWNkMGQ1LTU3NjUtNThlNy05MDAyLTNhZWI0NTc5MGRmOSJ9; _tglksd=eyJzIjoiOGVhY2QwZDUtNTc2NS01OGU3LTkwMDItM2FlYjQ1NzkwZGY5Iiwic3QiOjE3NDkzOTEzMjk5NjAsInNvZCI6InNwb3J0cy5iZXQ5amEuY29tIiwic29kdCI6MTc0OTM5MTMyOTk2MCwic29kcyI6InIiLCJzb2RzdCI6MTc0OTM5MTMyOTk2MH0=; bm_sv=1ECD8B087220576449039007BFD84EA9~YAAQU/kTAh04bkaXAQAAv1zZTxzzM4V4SjIW8OEaYSsEiwDR5I37K6A7CB0luiuPTIwOkUFx5DTd1N8D91DbBZyJv7bAmmhTUC7nVeGy5RNOxIII77Q3y/dAKUCyVsWg+G/z948koBRvV9G0VN+N2ahMsFl3y/i8jIXCM8UuhG3ppEHEp5NocRz+NgSXdSay2fHFHy3SAc4evUav7KuYperWIn8e80qtbzVjdgAdRgpnmb1RBmiY7XPTRby6UgZS1g==~1; _sp_srt_ses.55ca=*; _sp_srt_id.55ca=28e4d0c6-e94d-4cc1-acd2-89299c65f14d.1747492672.16.1749391337.1749385004.58b84b0d-54df-4942-876e-44deda694411.8f1eaee4-480b-4ed3-ba85-23d0e2901c10...0; _tgsid=eyJscGQiOiJ7XCJscHVcIjpcImh0dHBzOi8vc3BvcnRzLmJldDlqYS5jb20lMkZcIixcImxwdFwiOlwiQmV0OWphJTIwTmlnZXJpYSUyMFNwb3J0JTIwQmV0dGluZyUyQyUyMFByZW1pZXIlMjBMZWFndWUlMjBPZGRzJTJDJTIwQ2FzaW5vJTJDJTIwQmV0XCIsXCJscHJcIjpcImh0dHBzOi8vc3BvcnRzLmJldDlqYS5jb21cIn0iLCJwcyI6IjNmOTUwMjgxLThlMjMtNGI4ZC04NmUzLWJmNTFhN2E0ZjNmNyIsInB2YyI6IjEiLCJzYyI6IjhlYWNkMGQ1LTU3NjUtNThlNy05MDAyLTNhZWI0NTc5MGRmOTotMSIsInRpbSI6IjhlYWNkMGQ1LTU3NjUtNThlNy05MDAyLTNhZWI0NTc5MGRmOToxNzQ5MzkxMzMzMDQ3Oi0xIn0=",
    "origin": "https://sports.bet9ja.com",
    "priority": "u=1, i",
    "referer": "https://sports.bet9ja.com/",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors", 
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}

response = requests.post(url, headers=headers, data=payload)

print("Status code:", response.status_code)
print("Response body:", response.text)
