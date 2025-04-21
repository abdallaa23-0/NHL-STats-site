import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import json
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NHL Scores Viewer", layout="centered")
st.title("NHL Dashboard - Live from ESPN")

st_autorefresh(interval=60 * 1000, key="refresh")

selected_date = st.date_input("Select a date", datetime.today())
selected_date_str = selected_date.strftime("%Y%m%d")

# Debug toggle
show_debug = st.sidebar.checkbox("🔧 Show Raw API Response", value=False)

# Cache directory setup
CACHE_DIR = "nhl_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(game_id):
    return os.path.join(CACHE_DIR, f"{game_id}_summary.json")

def get_games_for_date(date_str):
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={date_str}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("events", [])
    except:
        return []

def get_standings():
    url = "https://site.web.api.espn.com/apis/v2/sports/hockey/nhl/standings"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("children", [])
    except:
        return []

def get_play_by_play(game_id):
    cache_file = cache_path(game_id)
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
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
    games = get_games_for_date(selected_date_str)
    if not games:
        st.info("No NHL Games on this day.")
    else:
        for game in games:
            game_id = game['id']
            teams = game['competitions'][0]['competitors']
            status = game['status']['type']['description']
            clock = game['status'].get('clock')
            period = game['status'].get('period')

            home = next(t for t in teams if t['homeAway'] == 'home')
            away = next(t for t in teams if t['homeAway'] == 'away')

            home_name = home['team']['displayName']
            away_name = away['team']['displayName']
            home_score = home['score']
            away_score = away['score']
            home_logo = home['team']['logo']
            away_logo = away['team']['logo']

            with st.expander(f"{away_name} {away_score} - {home_score} {home_name}"):
                cols = st.columns([1, 6, 1])
                cols[0].image(away_logo, width=60)
                cols[1].markdown(f"### {away_name} vs {home_name}")
                cols[2].image(home_logo, width=60)

                if status.lower() == "in progress" and clock and period:
                    try:
                        minutes = int(clock) // 60
                        seconds = int(clock) % 60
                        time_display = f"{minutes}:{seconds:02d}"
                        st.caption(f"⏱ Period {period} - {time_display} remaining")
                    except:
                        st.caption(f"⏱ Period {period} - {clock} remaining")
                else:
                    st.caption(f"📍 {status}")

                summary = get_play_by_play(game_id)

                if show_debug and summary:
                    st.code(summary, language="json")

                if summary:
                    st.subheader("Goal Scorers")
                    goals = [play for play in summary.get("liveData", {}).get("plays", {}).get("allPlays", []) if play.get("result", {}).get("event") == "Goal"]
                    if goals:
                        for goal in goals:
                            period = goal.get("about", {}).get("period")
                            time = goal.get("about", {}).get("periodTime")
                            players = goal.get("players", [])
                            scorer = next((p for p in players if p["playerType"] == "Scorer"), None)
                            assists = [p for p in players if p["playerType"] == "Assist"]

                            if scorer:
                                name = scorer['player']['fullName']
                                pid = scorer['player']['id']
                                link = f"https://www.nhl.com/player/{pid}"
                                desc = f"[{name}]({link}) scored in Period {period} at {time}"
                            else:
                                desc = f"Goal in Period {period} at {time}"

                            if assists:
                                assist_names = [a['player']['fullName'] for a in assists]
                                desc += f" (Assists: {', '.join(assist_names)})"

                            st.markdown(f"- {desc}")
                    else:
                        st.caption("⚠️ No goal data found in API or cache.")

                    st.subheader("Play-by-Play")
                    all_plays = summary.get("liveData", {}).get("plays", {}).get("allPlays", [])
                    if all_plays:
                        for play in all_plays[-10:]:
                            time = play.get("about", {}).get("periodTime")
                            desc = play.get("result", {}).get("description")
                            st.markdown(f"- {time} | {desc}")
                    else:
                        st.caption("⚠️ No play-by-play data found in API or cache.")
                else:
                    st.caption("❌ Could not fetch game summary.")

                st.divider()

with tab2:
    standings_data = get_standings()
    if not standings_data:
        st.warning("Could not load standings.")
    else:
        for conference in standings_data:
            st.subheader(conference['name'])
            rows = []
            for team in conference['standings']['entries']:
                team_name = team['team']['displayName']
                wins = next((s['value'] for s in team['stats'] if s['name'] == 'wins'), 0)
                losses = next((s['value'] for s in team['stats'] if s['name'] == 'losses'), 0)
                otl = next((s['value'] for s in team['stats'] if s['name'] == 'otLosses'), 0)
                points = next((s['value'] for s in team['stats'] if s['name'] == 'points'), 0)
                rows.append({
                    "Team": team_name,
                    "Wins": int(wins),
                    "Losses": int(losses),
                    "OTL": int(otl),
                    "Points": int(points)
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)