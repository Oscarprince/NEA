import json
import streamlit as st
from collections import Counter
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd


# --------- Page Settings --------
st.set_page_config(layout="wide", page_title="VGC Analyser", page_icon="https://www.serebii.net/itemdex/sprites/sv/pokeball.png")
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 460px !important;
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("VGC Tournament Analyser")

# ------- Tournament Picker -----------
def load_tournament():
    # Dictionary containing all tournaments, to add one simply add a line under here
    tournaments = {
        "EUIC 2026": "Data Sets/EUIC_2026.json",
        "Sydney 2026": "Data Sets/Sydney_2026.json",
        "Birmingham 2026": "Data Sets/Birmingham_2026.json",
        "Merida 2026": "Data Sets/Merida_2026.json",
        "Toronto 2026": "Data Sets/Toronto_2026.json",
    }

    tournament = st.selectbox("Select a tournament", list(tournaments.keys()))
    # with statement automatically closes file when it is not needed
    with open(tournaments[tournament]) as f: 
        return json.load(f)
          


# ----------- Tournament Stats -----------
        
# Ensures every player has 6 pokemon, sets them as "unknown" if missing
def get_pokemon_name(decklist, index):
    if index < len(decklist):
        return decklist[index]['name']
    return "Unknown"


def get_teamsheet(data, selected_name):
    # first find the player in data
    player = None
    for i in data:
        if i['name'] == selected_name:
            player = i
            break
    teamsheet = []
    for mon in player['decklist']:
        teamsheet.append({
            "Name": mon['name'],
            "Item": mon['item'],
            "Ability": mon['ability'],
            "Tera Type": mon['teratype'],
            "Moves": mon['badges'],
        })
    return teamsheet

def tournament_stats(data):
    query = st.text_input("Search for Player, Placing or Pokemon")
    player_info = []
    for player in data:
        player_info.append({
            "Name": player['name'],
            "Placing": str(player['placing']),
            "Record": f"{player['record']['wins']}W - {player['record']['losses']}L",
            "Pokemon 1": get_pokemon_name(player['decklist'], 0),
            "Pokemon 2": get_pokemon_name(player['decklist'], 1),
            "Pokemon 3": get_pokemon_name(player['decklist'], 2),
            "Pokemon 4": get_pokemon_name(player['decklist'], 3),
            "Pokemon 5": get_pokemon_name(player['decklist'], 4),
            "Pokemon 6": get_pokemon_name(player['decklist'], 5),
        })

    if query:
        filtered = []
        for p in player_info:
            if query.lower() in p['Name'].lower():
                filtered.append(p)
            elif query.isdigit() and int(query) == p['Placing']:
                filtered.append(p)
            elif any(query.lower() in p[f'Pokemon {i}'].lower() for i in range(1, 7)):
                filtered.append(p)
        player_info = filtered
        st.write(f"Results: {len(player_info)}")
    
    row_height = 35
    dataFrame = pd.DataFrame(player_info)
    height = min(700, len(player_info) * row_height + 38)

    gb = GridOptionsBuilder.from_dataframe(dataFrame)
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    # changing the placing and record columns to be smaller as data is short
    gb.configure_column("Placing", width=80)
    gb.configure_column("Record", width=100)
    grid_options = gb.build()

    selected = AgGrid(dataFrame, gridOptions=grid_options, height=height, update_mode=GridUpdateMode.SELECTION_CHANGED, reload_data=True)

    if selected.selected_rows is not None :
        selected_name = selected.selected_rows.iloc[0]['Name']
        display_teamsheet(data, selected_name)

def display_teamsheet(data, selected_name):
    teamsheet = get_teamsheet(data, selected_name)
    st.sidebar.header(f"Teamsheet: {selected_name.split(' [')[0]}")
    
    showdown_text = ""
    for mon in teamsheet:
        showdown_text += f"{mon['Name']} @ {mon['Item']}\n"
        showdown_text += f"Ability: {mon['Ability']}\n"
        showdown_text += f"Tera Type: {mon['Tera Type']}\n"
        for move in mon['Moves']:
            showdown_text += f"- {move}\n"
        showdown_text += "\n"

    st.sidebar.code(showdown_text)
    

# ----------- Usage Stats -------------
def usage_stats(data):
    day1_counts = Counter()
    pokemon_wins = Counter()
    pokemon_losses = Counter()
    for player in data:
        for mon in player['decklist']:
            day1_counts[mon['name']] += 1
            pokemon_wins[mon['name']] += player['record']['wins']
            pokemon_losses[mon['name']] += player['record']['losses']

    # Finds day 2 players by filtering for more than 5 wins
            
    day2_players = []
    for i in data:
        if i['record']['wins'] > 5:
            day2_players.append(i)
    day2_counts = Counter()
    for player in day2_players:
        for mon in player['decklist']:
            day2_counts[mon['name']] += 1


    usage = []
    for pokemon, count in day1_counts.most_common(30):
        day1_percentage = (count / len(data)) * 100
        day2_count = day2_counts[pokemon]
        day2_percentage = (day2_count / len(day2_players)) * 100
        winrate = pokemon_wins[pokemon] / (pokemon_wins[pokemon] + pokemon_losses[pokemon]) * 100
        
        usage.append({
            "Pokemon": pokemon,
            "Total Usage": f"{day1_percentage:.1f}%",
            "Day 2 Usage": f"{day2_percentage:.1f}%",
            "% Change": f"{day2_percentage - day1_percentage:.1f}%",
            "Record": f"{pokemon_wins[pokemon]} - {pokemon_losses[pokemon]}",
            "Winrate": f"{winrate:.2f}%",    
            "Appearances": str(count),
        })


    st.subheader("Usage")
    st.dataframe(usage, height=700)


data = load_tournament()

tab1, tab2, tab3 = st.tabs(["Tournament Stats", "Usage Stats", "Pokemon"])
with tab1:
    tournament_stats(data)
with tab2:
    usage_stats(data)

