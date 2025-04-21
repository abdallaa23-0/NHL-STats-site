import streamlit as st
import requests
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="NHL Scores Viewer", layout="centered")
st.title("NHL Dashboard - Powered by SportsData.io")

API_KEY = "YOUR_SPORTSDATAIO_API_KEY"  # Replace with your actual SportsData.io API key
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# --- Helper: Get Today's Games ---
def get_today_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{today}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except:
        return []

# --- Helper: Get All Players ---
def get_player(name):
    url = "https://api.sportsdata.io/v3/nhl/scores/json/Players"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        players = response.json()
        for player in players:
            if name.lower() in player["Name"].lower():
                return player
        return None
    except:
        return None

# --- Helper: Get Player Stats ---
def get_player_stats(player_id):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerSeasonStatsByPlayer/2024/{player_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except:
        return None

# --- Helper: Get Standings ---
def get_standings():
    url = "https://api.sportsdata.io/v3/nhl/scores/json/Standings/2024"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except:
        return []

# --- Navigation Tabs ---
tab1, tab2, tab3 = st.tabs(["📅 Today's Games", "👤 Player Stats", "🏆 Standings"])

# --- Tab 1: Today's Games ---
with tab1:
    games = get_today_games()
    if not games:
        st.info("No NHL Games Today")
    else:
        for game in games:
            home = game['HomeTeam']
            away = game['AwayTeam']
            home_score = game.get('HomeTeamScore', '-')
            away_score = game.get('AwayTeamScore', '-')
            status = game.get('Status', 'Scheduled')
            st.subheader(f"{away} vs {home}")
            st.write(f"**{away}:** {away_score} | **{home}:** {home_score}")
            st.caption(f"📍 {status}")
            st.markdown("---")

# --- Tab 2: Player Stats ---
with tab2:
    player_name = st.text_input("Enter player name:", placeholder="Connor McDavid")
    if player_name:
        player = get_player(player_name)
        if not player:
            st.error("Player not found.")
        else:
            stats = get_player_stats(player["PlayerID"])
            if not stats:
                st.warning("No stats available.")
            else:
                st.subheader(f"Stats for {player['Name']}")
                if player.get("PhotoUrl"):
                    st.image(player["PhotoUrl"], width=100)
                cols = st.columns(2)
                for i, (key, value) in enumerate(stats.items()):
                    cols[i % 2].markdown(f"**{key.replace('_', ' ').title()}:** {value}")

# --- Tab 3: Standings ---
with tab3:
    standings = get_standings()
    if not standings:
        st.warning("Could not load standings.")
    else:
        st.subheader("🏒 NHL Standings Table")
        df = pd.DataFrame([
            {
                "Team": team["Name"],
                "Wins": team["Wins"],
                "Losses": team["Losses"],
                "OT Losses": team["OvertimeLosses"],
                "Points": team["Points"],
                "Streak": team["Streak"]
            } for team in standings
        ])
        st.dataframe(df.style.set_properties(**{
            'text-align': 'left',
            'background-color': '#f9f9f9',
            'border-color': '#ddd',
            'border-style': 'solid',
            'border-width': '1px'
        }).set_table_styles([
            {"selector": "th", "props": [
                ("font-weight", "bold"),
                ("background-color", "#f0f2f6")
            ]}
        ]), use_container_width=True)