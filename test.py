import requests

print("test")
url = "https://apigw.bet9ja.com/sportsbook/placebet/PlacebetV2?source=desktop&v_cache_version=1.274.3.186"

payload = {'BETSLIP': '{"BETS":[{"BSTYPE":3,"TAB":3,"NUMLINES":1,"COMB":1,"TYPE":1,"STAKE":10,"POTWINMIN":32.5,"POTWINMAX":32.5,"BONUSMIN":"0","BONUSMAX":"0","ODDMIN":"3.25","ODDMAX":"3.25","ODDS":{"592862875$S_1X2_2":"3.25"},"FIXED":{}}],"IMPERSONIZE":0}',
'BONUS': '0',
'ACCEPT_ODDS_CHANGES': '1',
'IS_PASSBET': '0',
'IS_FIREBETS': '0',
'IS_CUT1': '0'}
files=[

]
headers = {
  'Cookie': 'livlang=en; _gcl_au=1.1.2044421124.1744315943; _tgpc=cc36af2c-f8f9-549f-ad72-ca17d2e4e27e; _ga=GA1.1.1332312323.1744315949; landingRedirection=true; MgidSensorNVis=1; MgidSensorHref=https://www.bet9ja.com/; _fbp=fb.1.1744719395106.299929522819854705; regQueryString=s=new&btag=a_144010b_1c_10184705288&s1={source_id}&promocode=&t2=&utm_source=affiliates&utm_medium=144010&utm_campaign1&referrer=https://ad.trck.media/; _hjSessionUser_95609=eyJpZCI6IjIxZjQ4NGU5LTg0NzUtNTc4ZC1iYWM3LWQ3MDRhYWEwZjRhNiIsImNyZWF0ZWQiOjE3NDQ3MTkzOTA0MDcsImV4aXN0aW5nIjp0cnVlfQ==; promocode=570; ftv=1; btag=a_570b_2c_10540647311; affiliateExtraData=btag%3Da_570b_2c_10540647311%26promocode%3D%26s1%3DCABAVHVJQMDABNG%26t2%3D%26utm_source%3Daffiliates%26utm_medium%3D570%26utm_campaign1%3D%26referrer%3Dhttps%253A%252F%252Flp.cleverwebserver.com%252F; _sp_srt_id.55ca=85508513-5b9b-4522-9739-724420e5fac7.1744719391.11.1746908343.1746836680.4dabbb2c-0c14-4267-bf21-fb747489f227.854ffeaf-92c8-4638-9bc9-68b7e39a2229...0; _tglksd=eyJzIjoiMDdlNDdiNmItNDJkNi01YTc3LWJkOTAtYzc2YjllZDM4ZGM1Iiwic3QiOjE3NDY5MTMwMTM1MTEsInNvZCI6IihkaXJlY3QpIiwic29kdCI6MTc0NjkwODMyNzg5NSwic29kcyI6Im8iLCJzb2RzdCI6MTc0NjkwODMyNzg5NX0=; ak_bmsc=F726E939BA2B184285AD62F43DCB942F~000000000000000000000000000000~YAAQQgkfuDIR/bWWAQAACbyDvxtfVNJRhFN5fh9gXHKxR7r7gj2vtnr/CBNbQmV/NNhuT6Ep73nnA7ueKV43uYGWJCObXWOQv4GN3kbpgoUmMZEVexXO6uM8+AvKrZT7oZAMWtP4oa1esZehygvog1zaQN+gm0myYV2noERMI0Ry+dz1rUAmS310kXj9D86wdMynP5VkdFjCBvOqDVskzIk/dwMSSsUdatqAWYZtMFC+/sf7JqVhki5bmuNB3yxzonOfnwRvX0IhhOyczhVXjsdmeeUzlUquNh/5Up/3JAtAEIXBV3Bc/QZQ93SHVtZp0y4WGjiNj03KgmZQtU+UWJ0n+gwTNJDq9QOMDPMu5wa+HWs2ZE0fb7Sb7a/u998ky/H2CPhEzd4lkfE=; livsid=e4deda39-3976-887e-541f-e3e9af7e5a40; _ga_YYQNLHMCQS=GS2.1.s1746970048$o23$g1$t1746973519$j60$l0$h0; bm_sv=1372871CF8D496C05E657F84F4D922D8~YAAQkzEUAtBwQbKWAQAAsna8vxuOgGBlVy376wMoGmPqw7temnNg4qeGxXbTThm63kSLKmTcicmv3TJFmsQOnEARcuY779Ux9uLXkLqklNVKGK35JkIIz4tX9to+7PvVgAid3L22hFJBAmyQr28moq5E4Kuriri9NDYmavWJLJuXumcWOekT28NjpU4ZMavl51abj1denW7G7EYtuqI7pnIjTN43trcl528XjhVTd27hxYdDcxRC8cj4H4zXaHkOMw==~1'
}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
