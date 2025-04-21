import streamlit as st
import requests
from datetime import datetime
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NHL Scores Viewer", layout="centered")
st.title("NHL Dashboard - Live from ESPN")

# Auto-refresh every 60 seconds for live timing
st_autorefresh(interval=60 * 1000, key="refresh")

# --- Helper: Get Today's Games from ESPN ---
def get_today_games():
    url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("events", [])
    except:
        return []

# --- Helper: Get Standings from ESPN ---
def get_standings():
    url = "https://site.web.api.espn.com/apis/v2/sports/hockey/nhl/standings"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("children", [])
    except:
        return []

# --- Helper: Get Play-by-Play ---
def get_play_by_play(game_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event={game_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except:
        return None

# --- Navigation Tabs ---
tab1, tab2 = st.tabs(["📅 Today's Games", "🏆 Standings"])

# --- Tab 1: Today's Games ---
with tab1:
    st.caption(f"⏱ Last updated: {datetime.now().strftime('%I:%M:%S %p')}")
    games = get_today_games()
    if not games:
        st.info("No NHL Games Today")
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

                # Fetch and display play-by-play
                summary = get_play_by_play(game_id)
                if summary:
                    st.subheader("Goal Scorers")
                    goals = summary.get("scoringPlays", [])
                    if goals:
                        for goal in goals:
                            desc = goal.get("text", "")
                            if desc:
                                st.markdown(f"- {desc}")
                    else:
                        st.caption("No goals recorded yet.")

                    st.subheader("Play-by-Play")
                    plays_data = summary.get("plays")
                    if plays_data and "allPlays" in plays_data:
                        all_plays = plays_data["allPlays"]
                        for play in all_plays[-10:]:
                            time = play.get("clock", {}).get("displayValue", "")
                            text = play.get("text", "")
                            st.markdown(f"- {time} | {text}")
                    else:
                        st.caption("No play-by-play data available.")

            st.divider()

# --- Tab 2: Standings ---
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
                points = next((s['value'] for s in team['stats'] if s['name'] == 'points'), 0)
                rows.append({
                    "Team": team_name,
                    "Wins": int(wins),
                    "Losses": int(losses),
                    "Points": int(points)
                })

            df = pd.DataFrame(rows)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )
