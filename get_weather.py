import urllib.request, json
resp = urllib.request.urlopen('https://wttr.in/Seoul?format=j1&days=3')
d = json.load(resp)
for w in d['weather']:
    print(f"{w['date']}: {w['mintempC']}~{w['maxtempC']}C")
