import pandas as pd  # Import pandas for data analysis and manipulation
import json          # Import json to read JSON files

# Load the JSON file containing tournament data
# 'with open' ensures the file is properly closed after reading
with open("TournamentData/BeloHorizonte.json", "r") as file:
    data = json.load(file)  # Load the JSON into a Python object (list of dictionaries)

# Convert the top-level JSON list into a pandas DataFrame
# Each dictionary in the list becomes a row, keys become column names
df = pd.DataFrame(data)

# Create an empty list to hold a flattened version of the data
# This will allow one row per Pokémon rather than one row per player
rows = []

# Loop over each player in the data
for player in data:
    # Each player has a "decklist" which is a list of Pokémon dictionaries
    for p in player["decklist"]:
        # For each Pokémon, create a new dictionary with relevant details
        rows.append({
            "player": player["name"],       # Name of the player
            "placing": player["placing"],   # Final ranking of the player
            "pokemon": p["name"],           # Pokémon name
            "teratype": p["teratype"],      # Pokémon type
            "ability": p["ability"],        # Pokémon ability
            "item": p["item"]               # Pokémon held item
        })

# Convert the flattened list of dictionaries into a pandas DataFrame
# Now each row corresponds to a single Pokémon, with player info included
pokemon_df = pd.DataFrame(rows)

# Preview the first 5 rows of the flattened DataFrame to check everything looks correct
print(pokemon_df.head())

