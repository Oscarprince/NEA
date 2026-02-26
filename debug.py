import json
f = open('Data Sets/Sydney_2026.json')
data = json.load(f)

for player in data:
    if len(player['decklist']) < 6:
        print(player['name'], len(player['decklist']))