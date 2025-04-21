import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import os
import json
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NHL Scores Viewer", layout="centered")
st.title("NHL Dashboard - Live from Sportradar")

st_autorefresh(interval=60 * 1000, key="refresh")

selected_date = st.date_input("Select a date", datetime.today())
selected_date_str = selected_date.strftime("%Y-%m-%d")

API_KEY = "YOUR_SPORTRADAR_API_KEY"
BASE_URL = "https://api.sportradar.com/nhl/trial/v7/en"

show_debug = st.sidebar.checkbox("🔧 Show Raw API Response", value=False)

CACHE_DIR = "nhl_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(game_id):
    return os.path.join(CACHE_DIR, f"{game_id}_summary.json")

def get_schedule(date_str):
    url = f"{BASE_URL}/games/{date_str}/schedule.json?api_key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("games", [])
    except:
        return []

def get_game_summary(game_id):
    cache_file = cache_path(game_id)
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    url = f"{BASE_URL}/games/{game_id}/summary.json?api_key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        with open(cache_file, "w") as f:
            json.dump(data, f)
        return data
    except:
        return None

# --- UI Tabs ---
tab1, tab2 = st.tabs(["📅 Games", "🏆 Standings"])

with tab1:
    st.caption(f"⏱ Last updated: {datetime.now().strftime('%I:%M:%S %p')}")
    games = get_schedule(selected_date_str)
    if not games:
        st.info("No NHL Games on this day.")
    else:
        for game in games:
            game_id = game.get("id")
            home = game.get("home", {}).get("name", "Home")
            away = game.get("away", {}).get("name", "Away")
            status = game.get("status")
            scheduled = game.get("scheduled", "")

            with st.expander(f"{away} vs {home} ({status})"):
                st.caption(f"🕒 Scheduled: {scheduled}")
                summary = get_game_summary(game_id)

                if show_debug and summary:
                    st.code(summary, language="json")

                if summary:
                    st.subheader("Goal Scorers")
                    scoring_plays = summary.get("scoring", {}).get("plays", [])
                    if scoring_plays:
                        for play in scoring_plays:
                            scorer = play.get("scoring_player", {}).get("full_name")
                            player_id = play.get("scoring_player", {}).get("id")
                            period = play.get("period")
                            time = play.get("time")
                            desc = f"[{scorer}](https://www.nhl.com/player/{player_id}) scored in Period {period} at {time}"
                            assists = play.get("assists", [])
                            if assists:
                                assist_names = [a.get("full_name") for a in assists]
                                desc += f" (Assists: {', '.join(assist_names)})"
                            st.markdown(f"- {desc}")
                    else:
                        st.caption("⚠️ No goal data available.")

                    st.subheader("Play-by-Play")
                    pbp = summary.get("game", {}).get("pbp", {}).get("events", [])
                    if pbp:
                        for event in pbp[-10:]:
                            time = event.get("clock", {}).get("display_time", "")
                            description = event.get("description", "")
                            st.markdown(f"- {time} | {description}")
                    else:
                        st.caption("⚠️ No play-by-play data found.")
                else:
                    st.caption("❌ Could not fetch game summary.")

                st.divider()

with tab2:
    st.caption("🚧 Standings integration with Sportradar coming soon.")
