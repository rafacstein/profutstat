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

# Timer functions
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

def get_current_time():
    if st.session_state.timer_start is None:
        return st.session_state.paused_time * st.session_state.playback_speed
    return (time.time() - st.session_state.timer_start) * st.session_state.playback_speed

# Possession tracking
def log_possession_duration():
    if st.session_state.current_possession and st.session_state.possession_start:
        duration = time.time() - st.session_state.possession_start
        st.session_state.possession_log.append({
            "Team": st.session_state.current_possession,
            "Start": st.session_state.possession_start,
            "Duration": duration
        })
        st.session_state.possession_start = time.time()

def calculate_possession():
    team_a_time = sum([p["Duration"] for p in st.session_state.possession_log 
                      if p["Team"] == st.session_state.team_a])
    team_b_time = sum([p["Duration"] for p in st.session_state.possession_log 
                      if p["Team"] == st.session_state.team_b])
    
    # Add current possession if active
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

# Event recording
def record_event(event, team, player="", event_type="", subtype=""):
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)
    
    # Handle possession changes
    if event == "Possession":
        if st.session_state.current_possession != team:
            log_possession_duration()
            st.session_state.current_possession = team
            st.session_state.possession_start = time.time()
    
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

# Streamlit UI
st.title("⚽ Advanced Football Analytics")

# Team configuration
col1, col2 = st.columns(2)
with col1:
    st.session_state.team_a = st.text_input("Home Team:", "Team A")
with col2:
    st.session_state.team_b = st.text_input("Away Team:", "Team B")

# Match timer controls
st.header("Match Clock")
timer_col1, timer_col2 = st.columns([1, 2])
with timer_col1:
    st.session_state.playback_speed = st.radio("Speed:", [1, 2], index=0)
with timer_col2:
    if st.button("⏵ Start") and st.session_state.timer_start is None:
        start_timer()
    if st.button("⏸ Pause") and st.session_state.timer_start is not None:
        pause_timer()
    if st.button("↻ Reset"):
        reset_timer()

# Display current time
current_time = get_current_time()
display_min = int(current_time // 60)
display_sec = int(current_time % 60)
st.metric("Match Time", f"{display_min}:{display_sec:02d}")

# Possession stats
st.header("Possession")
team_a_poss, team_b_poss = calculate_possession()
poss_col1, poss_col2 = st.columns(2)
with poss_col1:
    st.metric(f"{st.session_state.team_a} Possession", f"{team_a_poss:.1f}%")
with poss_col2:
    st.metric(f"{st.session_state.team_b} Possession", f"{team_b_poss:.1f}%")
st.progress(int(team_a_poss))

# Action buttons
def create_action_buttons():
    st.header("Match Actions")
    
    # Possession controls
    st.subheader("Possession")
    poss_col1, poss_col2 = st.columns(2)
    with poss_col1:
        if st.button(f"🏃 {st.session_state.team_a} Possession"):
            record_event("Possession", st.session_state.team_a)
    with poss_col2:
        if st.button(f"🏃 {st.session_state.team_b} Possession"):
            record_event("Possession", st.session_state.team_b)
    
    # Pass types
    st.subheader("Passing")
    pass_col1, pass_col2 = st.columns(2)
    with pass_col1:
        st.write(f"{st.session_state.team_a} Passes")
        if st.button("Short Pass ✓", key="short_pass_a_success"):
            record_event("Pass", st.session_state.team_a, "", "Successful", "Short")
        if st.button("Short Pass ✗", key="short_pass_a_fail"):
            record_event("Pass", st.session_state.team_a, "", "Failed", "Short")
        if st.button("Long Pass ✓", key="long_pass_a_success"):
            record_event("Pass", st.session_state.team_a, "", "Successful", "Long")
        if st.button("Long Pass ✗", key="long_pass_a_fail"):
            record_event("Pass", st.session_state.team_a, "", "Failed", "Long")
    
    with pass_col2:
        st.write(f"{st.session_state.team_b} Passes")
        if st.button("Short Pass ✓", key="short_pass_b_success"):
            record_event("Pass", st.session_state.team_b, "", "Successful", "Short")
        if st.button("Short Pass ✗", key="short_pass_b_fail"):
            record_event("Pass", st.session_state.team_b, "", "Failed", "Short")
        if st.button("Long Pass ✓", key="long_pass_b_success"):
            record_event("Pass", st.session_state.team_b, "", "Successful", "Long")
        if st.button("Long Pass ✗", key="long_pass_b_fail"):
            record_event("Pass", st.session_state.team_b, "", "Failed", "Long")
    
    # [Additional action buttons...]

create_action_buttons()

# Data reporting
st.header("Match Report")
if not st.session_state.match_data.empty:
    st.dataframe(st.session_state.match_data.sort_values(["Minute", "Second"]))
    
    # Export data
    if st.button("Export to CSV"):
        csv = st.session_state.match_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="football_analysis.csv",
            mime="text/csv"
        )
