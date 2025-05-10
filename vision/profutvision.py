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

# Manual possession control
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
st.title("⚽ Football Match Analyzer")

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

# Manual possession control
st.header("Possession Control")
poss_col1, poss_col2 = st.columns(2)
with poss_col1:
    if st.button(f"🏃 {st.session_state.team_a} Possession"):
        set_possession(st.session_state.team_a)
with poss_col2:
    if st.button(f"🏃 {st.session_state.team_b} Possession"):
        set_possession(st.session_state.team_b)

# Possession stats
team_a_poss, team_b_poss = calculate_possession()
st.subheader("Possession Stats")
st.metric("Current Possession", st.session_state.current_possession or "None")
col_a, col_b = st.columns(2)
with col_a:
    st.metric(f"{st.session_state.team_a} Possession", f"{team_a_poss:.1f}%")
with col_b:
    st.metric(f"{st.session_state.team_b} Possession", f"{team_b_poss:.1f}%")
st.progress(int(team_a_poss))

# Action buttons
def create_action_buttons():
    st.header("Match Actions")
    
    # Passing
    st.subheader("Passing")
    pass_col1, pass_col2 = st.columns(2)
    with pass_col1:
        st.write(f"{st.session_state.team_a}")
        if st.button("Short Pass ✓", key="short_pass_a_success"):
            record_event("Pass", st.session_state.team_a, "", "Successful", "Short")
        if st.button("Short Pass ✗", key="short_pass_a_fail"):
            record_event("Pass", st.session_state.team_a, "", "Failed", "Short")
        if st.button("Long Pass ✓", key="long_pass_a_success"):
            record_event("Pass", st.session_state.team_a, "", "Successful", "Long")
        if st.button("Long Pass ✗", key="long_pass_a_fail"):
            record_event("Pass", st.session_state.team_a, "", "Failed", "Long")
    
    with pass_col2:
        st.write(f"{st.session_state.team_b}")
        if st.button("Short Pass ✓", key="short_pass_b_success"):
            record_event("Pass", st.session_state.team_b, "", "Successful", "Short")
        if st.button("Short Pass ✗", key="short_pass_b_fail"):
            record_event("Pass", st.session_state.team_b, "", "Failed", "Short")
        if st.button("Long Pass ✓", key="long_pass_b_success"):
            record_event("Pass", st.session_state.team_b, "", "Successful", "Long")
        if st.button("Long Pass ✗", key="long_pass_b_fail"):
            record_event("Pass", st.session_state.team_b, "", "Failed", "Long")
    
    # Shooting
    st.subheader("Shooting")
    shot_col1, shot_col2 = st.columns(2)
    with shot_col1:
        st.write(f"{st.session_state.team_a}")
        if st.button("Shot On Target", key="shot_on_a"):
            record_event("Shot", st.session_state.team_a, "", "On Target")
        if st.button("Shot Off Target", key="shot_off_a"):
            record_event("Shot", st.session_state.team_a, "", "Off Target")
        if st.button("⚽ Goal", key="goal_a"):
            player = st.text_input("Scorer:", key="scorer_a")
            record_event("Goal", st.session_state.team_a, player)
    
    with shot_col2:
        st.write(f"{st.session_state.team_b}")
        if st.button("Shot On Target", key="shot_on_b"):
            record_event("Shot", st.session_state.team_b, "", "On Target")
        if st.button("Shot Off Target", key="shot_off_b"):
            record_event("Shot", st.session_state.team_b, "", "Off Target")
        if st.button("⚽ Goal", key="goal_b"):
            player = st.text_input("Scorer:", key="scorer_b")
            record_event("Goal", st.session_state.team_b, player)
    
    # Defensive actions
    st.subheader("Defensive Actions")
    def_col1, def_col2 = st.columns(2)
    with def_col1:
        st.write(f"{st.session_state.team_a}")
        if st.button("Tackle", key="tackle_a"):
            record_event("Tackle", st.session_state.team_a)
        if st.button("Interception", key="interception_a"):
            record_event("Interception", st.session_state.team_a)
    
    with def_col2:
        st.write(f"{st.session_state.team_b}")
        if st.button("Tackle", key="tackle_b"):
            record_event("Tackle", st.session_state.team_b)
        if st.button("Interception", key="interception_b"):
            record_event("Interception", st.session_state.team_b)
    
    # Cards
    st.subheader("Disciplinary")
    card_col1, card_col2 = st.columns(2)
    with card_col1:
        st.write(f"{st.session_state.team_a}")
        if st.button("Yellow Card", key="yellow_a"):
            player = st.text_input("Player (Yellow):", key="yellow_player_a")
            record_event("Card", st.session_state.team_a, player, "Yellow")
        if st.button("Red Card", key="red_a"):
            player = st.text_input("Player (Red):", key="red_player_a")
            record_event("Card", st.session_state.team_a, player, "Red")
    
    with card_col2:
        st.write(f"{st.session_state.team_b}")
        if st.button("Yellow Card", key="yellow_b"):
            player = st.text_input("Player (Yellow):", key="yellow_player_b")
            record_event("Card", st.session_state.team_b, player, "Yellow")
        if st.button("Red Card", key="red_b"):
            player = st.text_input("Player (Red):", key="red_player_b")
            record_event("Card", st.session_state.team_b, player, "Red")
    
    # Other actions
    st.subheader("Other Actions")
    other_col1, other_col2 = st.columns(2)
    with other_col1:
        st.write(f"{st.session_state.team_a}")
        if st.button("Corner", key="corner_a"):
            record_event("Corner", st.session_state.team_a)
        if st.button("Foul", key="foul_a"):
            record_event("Foul", st.session_state.team_a)
    
    with other_col2:
        st.write(f"{st.session_state.team_b}")
        if st.button("Corner", key="corner_b"):
            record_event("Corner", st.session_state.team_b)
        if st.button("Foul", key="foul_b"):
            record_event("Foul", st.session_state.team_b)

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
            file_name="match_analysis.csv",
            mime="text/csv"
        )

    # Possession timeline
    st.subheader("Possession Timeline")
    possession_df = pd.DataFrame(st.session_state.possession_log)
    if not possession_df.empty:
        possession_df["StartTime"] = possession_df["Start"].apply(
            lambda x: datetime.fromtimestamp(x).strftime('%M:%S'))
        st.bar_chart(possession_df.groupby("Team")["Duration"].sum())
