import json
import streamlit as st
from collections import Counter
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import requests
import matplotlib.pyplot as plt

# -------- Classes ----------
class Pokemon:
    def __init__(self, name, ability, item, teratype, moves):
        self.name = name
        self.ability = ability
        self.item = item
        self.teratype = teratype
        self.moves = moves

class Player:
    def __init__(self, name, placing, wins, losses, decklist):
        self.name = name
        self.placing = placing
        self.wins = wins
        self.losses = losses
        self.decklist = decklist  # list of Pokemon objects
    
    @property
    def record(self):
        return f"{self.wins}W - {self.losses}L"

class RecentlyViewedQueue:
    def __init__(self, max_size=3):
        self.queue = []
        self.max_size = max_size
    
    def enqueue(self, pokemon):
        if pokemon in self.queue:
            self.queue.remove(pokemon)
        self.queue.append(pokemon)
        if len(self.queue) > self.max_size:
            self.queue.pop(0)
    
    def get_recent(self):
        return list(reversed(self.queue))


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
    # Dictionary containing all tournaments. To add a new tournament, simply add a line under here
    tournaments = {
        "Houston 2026": "Data Sets/Houston_2026.json",
        "Curitiba 2026": "Data Sets/Curitiba_2026.json",
        "Seattle 2026": "Data Sets/Seattle_2026.json",
        "EUIC 2026": "Data Sets/EUIC_2026.json",
        "Sydney 2026": "Data Sets/Sydney_2026.json",
        "Birmingham 2026": "Data Sets/Birmingham_2026.json",
        "Merida 2026": "Data Sets/Merida_2026.json",
        "Toronto 2026": "Data Sets/Toronto_2026.json",
    }
    tournament = st.selectbox("Select a tournament", list(tournaments.keys()))
    with open(tournaments[tournament]) as f:
        raw = json.load(f)
    
    players = []
    for p in raw:
        decklist = []
        for mon in p['decklist']:
            decklist.append(Pokemon(
                name=mon['name'],
                ability=mon['ability'],
                item=mon['item'],
                teratype=mon['teratype'],
                moves=mon['badges']
            ))
        players.append(Player(
            name=p['name'],
            placing=p['placing'],
            wins=p['record']['wins'],
            losses=p['record']['losses'],
            decklist=decklist
        ))
    return players
          


# ----------- Tournament Stats -----------
        
# Ensures every player has 6 pokemon, sets them as "unknown" if missing
def get_pokemon_name(decklist, index):
    if index < len(decklist):
        return decklist[index].name
    return "Unknown"

def get_teamsheet(data, selected_name):
    for player in data:
        if player.name == selected_name:
            return player.decklist

def get_player_info(data):
    player_info = []
    for player in data:
        player_info.append({
            "Name": player.name,
            "Placing": str(player.placing),
            "Record": player.record,
            "Pokemon 1": get_pokemon_name(player.decklist, 0),
            "Pokemon 2": get_pokemon_name(player.decklist, 1),
            "Pokemon 3": get_pokemon_name(player.decklist, 2),
            "Pokemon 4": get_pokemon_name(player.decklist, 3),
            "Pokemon 5": get_pokemon_name(player.decklist, 4),
            "Pokemon 6": get_pokemon_name(player.decklist, 5),
        })
    return player_info

def tournament_stats(data):
    query = st.text_input("Search for Player, Placing or Pokemon")
    player_info = get_player_info(data)

    # Filters the table for specific criteria
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
    height = min(760, len(player_info) * row_height + 38)

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
        showdown_text += f"{mon.name} @ {mon.item}\n"
        showdown_text += f"Ability: {mon.ability}\n"
        showdown_text += f"Tera Type: {mon.teratype}\n"
        for move in mon.moves:
            showdown_text += f"- {move}\n"
        showdown_text += "\n"

    st.sidebar.code(showdown_text)
    
# ----------- Usage Stats -------------
# Function that collects day 1/2 usage, % change, record, winrate and appearances
def get_usage_data(data):
    day1_counts = Counter()
    pokemon_wins = Counter()
    pokemon_losses = Counter()
    for player in data:
        for mon in player.decklist:
            day1_counts[mon.name] += 1
            pokemon_wins[mon.name] += player.wins
            pokemon_losses[mon.name] += player.losses

    # Finds players in day 2 by filtering for players with over 5 wins
    day2_players = []
    for i in data:
        if i.wins > 5:
            day2_players.append(i)
    day2_counts = Counter()
    for player in day2_players:
        for mon in player.decklist:
            day2_counts[mon.name] += 1

    usage = []
    for pokemon, count in day1_counts.most_common():
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

    return usage

def get_combinations(names, n, start=0):
    if n == 0:
        return [()]
    combinations = []
    for i in range(start, len(names)):
        for combo in get_combinations(names, n - 1, i + 1):
            combinations.append((names[i],) + combo)
    return combinations

def get_top_groups(data, n):
    group_counts = Counter()
    total = len(data)
    for player in data:
        names = [mon.name for mon in player.decklist]
        for combo in get_combinations(names, n):
            group = tuple(sorted(combo))
            group_counts[group] += 1
    
    result = []
    for group, count in group_counts.most_common(100):
        row = {}
        for i, pokemon in enumerate(group):
            sprite, _ = get_pokemon_details(pokemon)
            row[f"Pokemon {i + 1}"] = sprite
        row["Usage"] = f"{(count / total) * 100:.1f}%"
        result.append(row)
    return result

def usage_stats(data):
    usage_col, pairing_col = st.columns(2)
    with usage_col:
        usage = get_usage_data(data)
        st.subheader("Usage")
        st.dataframe(usage, height=770, hide_index=True)
    with pairing_col:
        st.subheader("Pokemon Groups")
        tabs = st.tabs(["2", "3", "4", "5", "6"])
        for i, tab in enumerate(tabs):
            n = i + 2
            with tab:
                df = pd.DataFrame(get_top_groups(data, n))
                st.dataframe(
                    df,
                    column_config={f"Pokemon {j}": st.column_config.ImageColumn(f"Pokemon {j}") for j in range(1, n + 1)},
                    hide_index=True,
                    row_height=80,
                    height = 710
                )


# ------------ Pokemon Info ----------

# for later use when pulling from pokeapi
STAT_NAMES = {
    "hp": "HP",
    "attack": "Atk",
    "defense": "Def",
    "special-attack": "SpA",
    "special-defense": "SpD",
    "speed": "Spe"
}

def usage_list(data):
    usage = get_usage_data(data)

    dataFrame = pd.DataFrame(usage)[["Pokemon", "Total Usage"]]
    st.dataframe(dataFrame, height = 1717, hide_index=True)

def get_pokemon_list(data):
    usage = get_usage_data(data)
    return [entry["Pokemon"] for entry in usage]

# Cleans the names of specific pokemon in my datasets, so that they can work with PokeAPI
def clean_pokemon_name(name):
    name = name.lower()
    # Removes brackets
    name = name.replace("[", "").replace("]", "")
    # Removes spaces
    name = name.replace(" ", "-")
    
    # Urshifu
    name = name.replace("-rapid-strike-style", "-rapid-strike")
    name = name.replace("-single-strike-style", "-single-strike")
    
    # Genies
    name = name.replace("-incarnate-forme", "-incarnate")
    name = name.replace("-therian-forme", "-therian")
    
    # Ogerpon
    name = name.replace("-teal-mask", "")
    name = name.replace("-wellspring-mask", "-wellspring-mask")
    name = name.replace("-hearthflame-mask", "-hearthflame-mask")
    name = name.replace("-cornerstone-mask", "-cornerstone-mask")
    
    # Regional forms
    name = name.replace("-hisuian-form", "-hisui")
    name = name.replace("-galarian-form", "-galar")
    name = name.replace("-alolan-form", "-alola")
    name = name.replace("-paldean-form", "-paldea")
    
    # Tatsugiri
    name = name.replace("-droopy-form", "-droopy")
    name = name.replace("-stretchy-form", "-stretchy")
    name = name.replace("-curly-form", "-curly")

    # Sinistcha
    name = name.replace("-masterpiece-form", "")
    name = name.replace("-unremarkable-form", "")
    
    name = name.strip("-")
    return name

# streamlit decorator that stores result of the function - this increases speed with large amounts of api calls
@st.cache_data
def get_pokemon_details(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{clean_pokemon_name(name)}"
    response = requests.get(url)
    if response.status_code != 200:
        return None, {}
    data = response.json()
    
    sprite = data['sprites']['other']['official-artwork']['front_default']
    stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}

    return sprite, stats

# helper to create pie charts with specific styling parameters
def make_pie_chart(counts, title, threshold=5):
    total = sum(counts.values())
    grouped = Counter()
    other = 0
    for name, count in counts.items():
        if (count / total) * 100 < threshold:
            other += count
        else:
            grouped[name] = count
    if other > 0:
        grouped['Other'] = other

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        grouped.values(),
        labels=None,
        autopct=lambda p: f'{p:.1f}%' if p >= 5 else '',
        startangle=90,
    )
    ax.legend(grouped.keys(), loc='lower center', bbox_to_anchor=(0.5, -0.2), fontsize=8)
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    plt.setp(ax.texts, color='white')
    st.subheader(title)
    st.pyplot(fig, use_container_width=False)

# creates pie chart with abilities used by each pokemon
def pokemon_abilities(data, pokemon):
    counts = Counter()
    for player in data:
        for mon in player.decklist:
            if mon.name == pokemon:
                counts[mon.ability] += 1
    make_pie_chart(counts, "Abilities")

# creates pie chart with teras used by each pokemon
def pokemon_teras(data, pokemon):
    counts = Counter()
    for player in data:
        for mon in player.decklist:
            if mon.name == pokemon:
                counts[mon.teratype] += 1
    make_pie_chart(counts, "Tera Types")

# creates pie chart with items used by each pokemon
def pokemon_items(data, pokemon):
    counts = Counter()
    for player in data:
        for mon in player.decklist:
            if mon.name == pokemon:
                counts[mon.item] += 1
    make_pie_chart(counts, "Items")

# finds the top performing teams with the selected pokemon
def get_top_teams(data, pokemon, n=8):
    player_info = get_player_info(data)
    filtered = []
    for p in player_info:
        for i in range(1, 7):
            if p[f'Pokemon {i}'] == pokemon:
                filtered.append(p)
                break
    filtered.sort(key=lambda x: int(x['Placing']))
    return filtered[:n]

# find the most common partners for a pokemon
def get_top_partners(data, pokemon):
    partner_counts = Counter()
    total = 0
    for player in data:
        names = [mon.name for mon in player.decklist]
        if pokemon in names:
            total += 1
            for name in names:
                if name != pokemon:
                    partner_counts[name] += 1
    
    partners = []
    for name, count in partner_counts.most_common():
        partners.append({
            "Pokemon": name,
            "Usage": f"{(count / total) * 100:.1f}%"
        })
    return partners

def get_top_moves(data, pokemon):
    move_counts = Counter()
    total = 0
    for player in data:
        for mon in player.decklist:
            if mon.name == pokemon:
                total += 1
                for move in mon.moves:
                    move_counts[move] += 1
    
    moves = []
    for move, count in move_counts.most_common():
        moves.append({
            "Move": move,
            "Usage": f"{(count / total) * 100:.1f}%"
        })
    return moves

# displays the pokemon info 
def pokemon_info(data):
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.session_state.recently_viewed.get_recent():
            st.subheader("Recently Viewed")
            for pokemon in st.session_state.recently_viewed.get_recent():
                sprite, _ = get_pokemon_details(pokemon)
                st.image(sprite, width=60)
                if st.button(pokemon):
                    st.session_state.pokemon_select = pokemon
        st.subheader("Usage")
        usage_list(data)
    with col2:
        selected_pokemon = st.selectbox(
            "Select a Pokemon", 
            get_pokemon_list(data), 
            index=None, 
            placeholder="Enter a Pokemon...",
            key="pokemon_select"
        )
        if selected_pokemon:
            st.session_state.recently_viewed.enqueue(selected_pokemon)
            sprite, stats = get_pokemon_details(selected_pokemon)
            img_col, details_col = st.columns([1, 4])
            with img_col:
                st.image(sprite, width=250)
            with details_col:
                if max(stats.values()) >= 200:
                    max_stat = 256
                elif max(stats.values()) >= 170:
                    max_stat = 200                     
                elif max(stats.values()) >= 140:
                    max_stat = 170                   
                else:
                    max_stat = 150
                for stat, value in stats.items():
                    stat_name_col, stat_value_col, bar_col = st.columns([2, 1, 20])
                    with stat_name_col:
                        st.write(f"**{STAT_NAMES.get(stat, stat)}**")
                    with stat_value_col:
                        st.write(str(value))
                    with bar_col:
                        st.progress(value / max_stat)
            abilities_col, teras_col, items_col = st.columns([1,1,1])
            with abilities_col:
                pokemon_abilities(data, selected_pokemon)
            with teras_col:
                pokemon_teras(data, selected_pokemon)
            with items_col:
                pokemon_items(data, selected_pokemon)
            
            # displays top 8 placing teams with the selected pokemon
            st.subheader(f"Top teams with {selected_pokemon}")
            top_teams = get_top_teams(data, selected_pokemon)
            dataFrame = pd.DataFrame(top_teams)
            st.dataframe(dataFrame, height=318, hide_index=True)

            top_partners, top_moves = st.columns([1, 1])
            with top_partners:
                st.subheader(f"Top partners with {selected_pokemon}")
                top_partners = get_top_partners(data, selected_pokemon)
                dataFrame = pd.DataFrame(top_partners)
                st.dataframe(dataFrame, height = 318, hide_index=True)
            with top_moves:
                st.subheader(f"Top moves used by {selected_pokemon}")
                top_moves = get_top_moves(data, selected_pokemon)
                dataFrame = pd.DataFrame(top_moves)
                st.dataframe(dataFrame, height = 318, hide_index=True)               

# --------- Main ------------

data = load_tournament()

if "recently_viewed" not in st.session_state:
    st.session_state.recently_viewed = RecentlyViewedQueue()

tab1, tab2, tab3 = st.tabs(
    ["Tournament Stats", "Usage Stats", "Pokemon"], 
    key="main_tabs"
)
with tab1:
    tournament_stats(data)
with tab2:
    usage_stats(data)
with tab3:
    pokemon_info(data)