import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Initialize session state
if 'match_data' not in st.session_state:
    st.session_state.match_data = pd.DataFrame(columns=[
        "Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"
    ])
    st.session_state.team_a = "Team A"
    st.session_state.team_b = "Team B"
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    st.session_state.playback_speed = 1
    st.session_state.current_possession = None
    st.session_state.possession_start = None
    st.session_state.possession_log = []

# ========== FUNCTION DEFINITIONS ==========
def get_current_time():
    if st.session_state.timer_start is None:
        return st.session_state.paused_time * st.session_state.playback_speed
    return (time.time() - st.session_state.timer_start) * st.session_state.playback_speed

def start_timer():
    st.session_state.timer_start = time.time() - st.session_state.paused_time
    if st.session_state.current_possession and not st.session_state.possession_start:
        st.session_state.possession_start = time.time()

def pause_timer():
    if st.session_state.timer_start:
        st.session_state.paused_time = time.time() - st.session_state.timer_start
        st.session_state.timer_start = None
        log_possession_duration()

def reset_timer():
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    st.session_state.possession_log = []
    st.session_state.current_possession = None
    st.session_state.possession_start = None

def log_possession_duration():
    if st.session_state.current_possession and st.session_state.possession_start:
        duration = time.time() - st.session_state.possession_start
        st.session_state.possession_log.append({
            "Team": st.session_state.current_possession,
            "Start": st.session_state.possession_start,
            "Duration": duration
        })
        st.session_state.possession_start = time.time()

def set_possession(team):
    log_possession_duration()
    st.session_state.current_possession = team
    st.session_state.possession_start = time.time()
    st.rerun()

def calculate_possession():
    team_a_time = sum([p["Duration"] for p in st.session_state.possession_log 
                      if p["Team"] == st.session_state.team_a])
    team_b_time = sum([p["Duration"] for p in st.session_state.possession_log 
                      if p["Team"] == st.session_state.team_b])
    
    if st.session_state.possession_start and st.session_state.current_possession:
        current_duration = time.time() - st.session_state.possession_start
        if st.session_state.current_possession == st.session_state.team_a:
            team_a_time += current_duration
        else:
            team_b_time += current_duration
    
    total_time = team_a_time + team_b_time
    if total_time > 0:
        return (team_a_time/total_time)*100, (team_b_time/total_time)*100
    return 0, 0

def record_event(event, team, player="", event_type="", subtype=""):
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)
    
    new_event = {
        "Event": event,
        "Minute": minute,
        "Second": second,
        "Team": team,
        "Player": player,
        "Type": event_type,
        "SubType": subtype,
        "Timestamp": time.time()
    }
    
    st.session_state.match_data = pd.concat(
        [st.session_state.match_data, pd.DataFrame([new_event])],
        ignore_index=True
    )
    st.rerun()

# ========== STREAMLIT UI ==========
st.title("⚽ Football Match Tracker")

# Team configuration and timer
col1, col2, col3 = st.columns([2,2,3])
with col1:
    st.session_state.team_a = st.text_input("Home Team:", "Team A")
with col2:
    st.session_state.team_b = st.text_input("Away Team:", "Team B")
with col3:
    st.session_state.playback_speed = st.radio("Speed:", [1, 2], horizontal=True)
    timer_col1, timer_col2, timer_col3 = st.columns(3)
    with timer_col1:
        if st.button("⏵ Start", use_container_width=True) and st.session_state.timer_start is None:
            start_timer()
    with timer_col2:
        if st.button("⏸ Pause", use_container_width=True) and st.session_state.timer_start is not None:
            pause_timer()
    with timer_col3:
        if st.button("↻ Reset", use_container_width=True):
            reset_timer()

# Current time and possession
time_col, poss_col_a, poss_col_b = st.columns([2,1,1])
with time_col:
    current_time = get_current_time()
    display_min = int(current_time // 60)
    display_sec = int(current_time % 60)
    st.metric("Match Time", f"{display_min}:{display_sec:02d}")

team_a_poss, team_b_poss = calculate_possession()
with poss_col_a:
    if st.button(f"🏃 {st.session_state.team_a}", use_container_width=True):
        set_possession(st.session_state.team_a)
    st.metric("Possession", f"{team_a_poss:.1f}%")
with poss_col_b:
    if st.button(f"🏃 {st.session_state.team_b}", use_container_width=True):
        set_possession(st.session_state.team_b)
    st.metric("Possession", f"{team_b_poss:.1f}%")

# Main action tabs
tab1, tab2, tab3, tab4 = st.tabs(["Passing", "Shooting", "Defensive", "Aerial"])

with tab1:
    # Passing buttons
    st.subheader("Passing")
    pass_col1, pass_col2 = st.columns(2)
    with pass_col1:
        st.write(f"{st.session_state.team_a}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Short ✓", key="short_pass_a_success"):
                record_event("Pass", st.session_state.team_a, "", "Successful", "Short")
        with col2:
            if st.button("Short ✗", key="short_pass_a_fail"):
                record_event("Pass", st.session_state.team_a, "", "Failed", "Short")
        col3, col4 = st.columns(2)
        with col3:
            if st.button("Long ✓", key="long_pass_a_success"):
                record_event("Pass", st.session_state.team_a, "", "Successful", "Long")
        with col4:
            if st.button("Long ✗", key="long_pass_a_fail"):
                record_event("Pass", st.session_state.team_a, "", "Failed", "Long")
    
    with pass_col2:
        st.write(f"{st.session_state.team_b}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Short ✓", key="short_pass_b_success"):
                record_event("Pass", st.session_state.team_b, "", "Successful", "Short")
        with col2:
            if st.button("Short ✗", key="short_pass_b_fail"):
                record_event("Pass", st.session_state.team_b, "", "Failed", "Short")
        col3, col4 = st.columns(2)
        with col3:
            if st.button("Long ✓", key="long_pass_b_success"):
                record_event("Pass", st.session_state.team_b, "", "Successful", "Long")
        with col4:
            if st.button("Long ✗", key="long_pass_b_fail"):
                record_event("Pass", st.session_state.team_b, "", "Failed", "Long")

with tab2:
    # Shooting buttons
    st.subheader("Shooting")
    shot_col1, shot_col2 = st.columns(2)
    with shot_col1:
        st.write(f"{st.session_state.team_a}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("On Target", key="shot_on_a"):
                record_event("Shot", st.session_state.team_a, "", "On Target")
        with col2:
            if st.button("Off Target", key="shot_off_a"):
                record_event("Shot", st.session_state.team_a, "", "Off Target")
        if st.button("⚽ Goal", key="goal_a"):
            player = st.text_input("Scorer:", key="scorer_a")
            record_event("Goal", st.session_state.team_a, player)
    
    with shot_col2:
        st.write(f"{st.session_state.team_b}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("On Target", key="shot_on_b"):
                record_event("Shot", st.session_state.team_b, "", "On Target")
        with col2:
            if st.button("Off Target", key="shot_off_b"):
                record_event("Shot", st.session_state.team_b, "", "Off Target")
        if st.button("⚽ Goal", key="goal_b"):
            player = st.text_input("Scorer:", key="scorer_b")
            record_event("Goal", st.session_state.team_b, player)

with tab3:
    # Defensive actions
    st.subheader("Defensive Actions")
    def_col1, def_col2 = st.columns(2)
    with def_col1:
        st.write(f"{st.session_state.team_a}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Tackle", key="tackle_a"):
                record_event("Tackle", st.session_state.team_a)
        with col2:
            if st.button("Intercept", key="interception_a"):
                record_event("Interception", st.session_state.team_a)
        with col3:
            if st.button("Foul", key="foul_a"):
                record_event("Foul", st.session_state.team_a)
        
        # Cards for Team A
        card_a1, card_a2 = st.columns(2)
        with card_a1:
            if st.button("Yellow", key="yellow_a"):
                player = st.text_input("Player (Yellow):", key="yellow_player_a")
                record_event("Card", st.session_state.team_a, player, "Yellow")
        with card_a2:
            if st.button("Red", key="red_a"):
                player = st.text_input("Player (Red):", key="red_player_a")
                record_event("Card", st.session_state.team_a, player, "Red")
    
    with def_col2:
        st.write(f"{st.session_state.team_b}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Tackle", key="tackle_b"):
                record_event("Tackle", st.session_state.team_b)
        with col2:
            if st.button("Intercept", key="interception_b"):
                record_event("Interception", st.session_state.team_b)
        with col3:
            if st.button("Foul", key="foul_b"):
                record_event("Foul", st.session_state.team_b)
        
        # Cards for Team B
        card_b1, card_b2 = st.columns(2)
        with card_b1:
            if st.button("Yellow", key="yellow_b"):
                player = st.text_input("Player (Yellow):", key="yellow_player_b")
                record_event("Card", st.session_state.team_b, player, "Yellow")
        with card_b2:
            if st.button("Red", key="red_b"):
                player = st.text_input("Player (Red):", key="red_player_b")
                record_event("Card", st.session_state.team_b, player, "Red")

with tab4:
    # Aerial duels
    st.subheader("Aerial Duels")
    aerial_col1, aerial_col2 = st.columns(2)
    with aerial_col1:
        st.write(f"{st.session_state.team_a}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Won", key="aerial_won_a"):
                record_event("Aerial Duel", st.session_state.team_a, "", "Won")
        with col2:
            if st.button("Lost", key="aerial_lost_a"):
                record_event("Aerial Duel", st.session_state.team_a, "", "Lost")
    
    with aerial_col2:
        st.write(f"{st.session_state.team_b}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Won", key="aerial_won_b"):
                record_event("Aerial Duel", st.session_state.team_b, "", "Won")
        with col2:
            if st.button("Lost", key="aerial_lost_b"):
                record_event("Aerial Duel", st.session_state.team_b, "", "Lost")

# Data reporting
st.header("Match Report")
if not st.session_state.match_data.empty:
    st.dataframe(st.session_state.match_data.sort_values(["Minute", "Second"]))
    
    if st.button("Export to CSV"):
        csv = st.session_state.match_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="match_analysis.csv",
            mime="text/csv"
        )
