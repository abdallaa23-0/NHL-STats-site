import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import os
import json
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NHL Scores Viewer", layout="centered")
st.title("NHL Dashboard - Live from ESPN")

st_autorefresh(interval=60 * 1000, key="refresh")

selected_date = st.date_input("Select a date", datetime.today())
selected_date_str = selected_date.strftime("%Y%m%d")

show_debug = st.sidebar.checkbox("🔧 Show Raw API Response", value=False)

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
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event={game_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except:
        return None

def get_team_roster(team_id):
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/roster"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("athletes", [])
    except:
        return []

# --- UI Tabs ---
tab1, tab2, tab3 = st.tabs(["📅 Games", "🏆 Standings", "📋 Team Rosters"])

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
                    goals = summary.get("scoringPlays")
                    if goals:
                        for goal in goals:
                            scorer = ""
                            assists = []
                            for player in goal.get("players", []):
                                if player.get("playerType") == "Scorer":
                                    scorer = player.get("athlete", {}).get("displayName", "")
                                elif player.get("playerType") == "Assist":
                                    assists.append(player.get("athlete", {}).get("displayName", ""))
                            time = goal.get("clock", "")
                            per = goal.get("period", "")
                            desc = f"{scorer} scored in Period {per} at {time}"
                            if assists:
                                desc += f" (Assists: {', '.join(assists)})"
                            st.markdown(f"- {desc}")
                    else:
                        st.caption("⚠️ No goal data found in API.")

                    st.subheader("Play-by-Play")
                    plays_data = summary.get("plays")
                    if plays_data and "allPlays" in plays_data:
                        all_plays = plays_data["allPlays"]
                        for play in all_plays[-10:]:
                            time = play.get("clock", {}).get("displayValue", "")
                            text = play.get("text", "")
                            st.markdown(f"- {time} | {text}")
                    else:
                        st.caption("⚠️ No play-by-play data found in API.")
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

with tab3:
    def get_all_teams():
        url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams"
        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
            return {team['team']['displayName']: team['team']['id'] for team in data.get("sports", [])[0].get("leagues", [])[0].get("teams", [])}
        except:
            return {}

    teams = get_all_teams()
    team_name = st.selectbox("Select a team:", sorted(teams.keys()))
    team_id = teams.get(team_name)

    if team_id:
        roster = get_team_roster(team_id)
        if roster:
            for group in roster:
                st.subheader(group.get("position", {}).get("abbreviation", "Position"))
                players = group.get("items", [])
                for player in players:
                    name = player.get("fullName", "")
                    photo = player.get("headshot", {}).get("href", "")
                    col1, col2 = st.columns([1, 4])
                    if photo:
                        col1.image(photo, width=60)
                    col2.markdown(f"**{name}**")
        else:
            st.warning("No roster data found.")
