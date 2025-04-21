import streamlit as st
import requests

st.set_page_config(page_title="NHL Scores Viewer", layout="centered")
st.title("NHL Scores - Live from ESPN")

def get_today_games():
    url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
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

# --- Navigation Tabs ---
tab1, tab2 = st.tabs(["📅 Today's Games", "🏆 Standings"])

# --- Tab 1: Today's Games ---
with tab1:
    games = get_today_games()
    if not games:
        st.info("No NHL Games Today")
    else:
        for game in games:
            teams = game['competitions'][0]['competitors']
            status = game['status']['type']['description']

            home = next(t for t in teams if t['homeAway'] == 'home')
            away = next(t for t in teams if t['homeAway'] == 'away')

            home_name = home['team']['displayName']
            away_name = away['team']['displayName']
            home_score = home['score']
            away_score = away['score']
            home_logo = home['team']['logo']
            away_logo = away['team']['logo']

            cols = st.columns([1, 6, 1])
            cols[0].image(away_logo, width=60)
            cols[1].subheader(f"{away_name} vs {home_name}")
            cols[2].image(home_logo, width=60)

            st.write(f"**{away_name}:** {away_score} | **{home_name}:** {home_score}")
            st.caption(f"📍 {status}")
            st.markdown("---")

# --- Tab 2: Standings ---
with tab2:
    standings_data = get_standings()
    if not standings_data:
        st.warning("Could not load standings.")
    else:
        for conference in standings_data:
            st.header(conference['name'])
            rows = []
            for team in conference['standings']['entries']:
                team_name = team['team']['displayName']
                wins = team['stats'][0]['value']
                losses = team['stats'][1]['value']
                points = team['stats'][3]['value']
                streak = team['stats'][8]['displayValue']
                rows.append([team_name, wins, losses, points, streak])
            st.table(rows)
