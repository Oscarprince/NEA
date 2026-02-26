import json
from collections import Counter

def load_tournament():
    print("What tournament do you want to analyse?")
    print("  - (1) Sydney_2026")
    print("  - (2) EUIC_2026")
    query = input("> ")

    match query:
        case "Sydney_2026" | "1":
            f = open('Data Sets/Sydney_2026.json')
            return json.load(f)
        case "EUIC_2026" | "2":
            f = open('Data Sets/EUIC_2026.json')
            return json.load(f)
        case _:
            print("Tournament not found")
            return None

# --------------------- Player Lookup -----------------------
        
# Gets stats from one specific player - cmd+/ to uncomment lol
def player_lookup(data):
    query = input("What player/placing do you want to look at? ")

    player = None
    for i in data:
        if query.isdigit():
            if i['placing'] == int(query):
                player = i
                break
        else:
            if query.lower() in i['name'].lower():
                player = i
                break

    if player is None:
        print("No player found with that placing.")
    else:
        print(f"Name: {player['name']}")
        print(f"Placing: {player['placing']}")
        print(f"Record: {player['record']['wins']}W - {player['record']['losses']}L")
        for mon in player['decklist']:
            print(f"  - {mon['name']} @ {mon['item']}")


# --------------------- Usage Stats ----------------------------
 
# loops through all mons per player, adding the mon's name to pokemon_counts. 
def usage_stats(data):
    day1_counts = Counter()
    for player in data:
        for mon in player['decklist']:
            day1_counts[mon['name']] += 1

    # Finds day 2 players by filtering for more than 5 wins
            
    day2_players = []
    for i in data:
        if i['record']['wins'] > 5:
            day2_players.append(i)
    day2_counts = Counter()
    for player in day2_players:
        for mon in player['decklist']:
            day2_counts[mon['name']] += 1

    print("Day 1 Usage:")
    rank = 1
    for pokemon, count in day1_counts.most_common(15):
        percentage = (count / len(data)) * 100
        print(f"{rank}. {pokemon}: {count} ({percentage:.1f}%)")
        rank += 1

    print("\nDay 2 Usage:")
    rank = 1
    for pokemon, count in day2_counts.most_common(15):
        percentage = (count / len(day2_players)) * 100
        print(f"{rank}. {pokemon}: {count} ({percentage:.1f}%)")
        rank += 1


# ---------- Program ----------

running = True
while running:
    data = load_tournament()
    while running:
        print("What do you want to look at?")
        print("  - (1) Usage Stats ")
        print("  - (2) Player Info ")
        print("  - (3) Tournament Select")
        print("  - (4) Exit")
        query = input("> ")

        match query:
            case "Usage Stats" | "1":
                usage_stats(data)
            case "Player Info" | "2":
                player_lookup(data)
            case "Tournament Select" | "3":
                break
            case "Exit" | "4":
                running = False          
            case _:
                print("Invalid Answer ")