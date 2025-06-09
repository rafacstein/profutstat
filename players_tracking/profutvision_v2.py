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
    st.session_state.selected_player_team_a = None
    st.session_state.selected_player_team_b = None
    # Define players for each team
    st.session_state.players_team_a = {
        "1": "Player 1 (A)", "2": "Player 2 (A)", "3": "Player 3 (A)", 
        "4": "Player 4 (A)", "5": "Player 5 (A)", "6": "Player 6 (A)", 
        "7": "Player 7 (A)", "8": "Player 8 (A)", "9": "Player 9 (A)", 
        "10": "Player 10 (A)", "11": "Player 11 (A)"
    }
    st.session_state.players_team_b = {
        "1": "Player 1 (B)", "2": "Player 2 (B)", "3": "Player 3 (B)", 
        "4": "Player 4 (B)", "5": "Player 5 (B)", "6": "Player 6 (B)", 
        "7": "Player 7 (B)", "8": "Player 8 (B)", "9": "Player 9 (B)", 
        "10": "Player 10 (B)", "11": "Player 11 (B)"
    }

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
    st.session_state.match_data = pd.DataFrame(columns=[ # Reset match data as well
        "Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"
    ])

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

def record_event(event, team, player_key, event_type="", subtype=""):
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)
    
    # Get the actual player name based on team and player_key
    if team == st.session_state.team_a:
        player_name = st.session_state.players_team_a.get(player_key, "")
    else:
        player_name = st.session_state.players_team_b.get(player_key, "")
    
    new_event = {
        "Event": event,
        "Minute": minute,
        "Second": second,
        "Team": team,
        "Player": player_name, # Use the full player name here
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
st.set_page_config(layout="wide") # Use wide layout for more space
st.title("⚽ Football Match Tracker - Player Centric")

# ---
# Top control row - Timer and Teams
control_col1, control_col2, control_col3 = st.columns([2,2,3])
with control_col1:
    st.session_state.team_a = st.text_input("Home Team:", "Team A")
with control_col2:
    st.session_state.team_b = st.text_input("Away Team:", "Team B")
with control_col3:
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

# ---
# Second row - Time and Possession
time_col, poss_col_a, poss_col_b = st.columns([2,1,1])
with time_col:
    current_time = get_current_time()
    display_min = int(current_time // 60)
    display_sec = int(current_time % 60)
    st.metric("Match Time", f"{display_min}:{display_sec:02d}")

team_a_poss, team_b_poss = calculate_possession()
with poss_col_a:
    if st.button(f"🏃 {st.session_state.team_a} Possession", use_container_width=True):
        set_possession(st.session_state.team_a)
    st.metric(f"{st.session_state.team_a} Possession", f"{team_a_poss:.1f}%")
with poss_col_b:
    if st.button(f"🏃 {st.session_state.team_b} Possession", use_container_width=True):
        set_possession(st.session_state.team_b)
    st.metric(f"{st.session_state.team_b} Possession", f"{team_b_poss:.1f}%")

# ---
# Player Selection and Actions
st.header("Player Actions")

player_selection_col1, player_selection_col2 = st.columns(2)

with player_selection_col1:
    st.markdown(f"### {st.session_state.team_a} Player Actions")
    st.session_state.selected_player_team_a = st.selectbox(
        "Select Player (Home Team):", 
        options=list(st.session_state.players_team_a.keys()),
        format_func=lambda x: st.session_state.players_team_a[x],
        key="player_selector_a"
    )
    if st.session_state.selected_player_team_a:
        current_player_a_name = st.session_state.players_team_a[st.session_state.selected_player_team_a]
        st.markdown(f"**Tracking Actions for: {current_player_a_name}**")

        st.markdown("#### Shooting")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Shot On Target", key=f"shot_on_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Shot", st.session_state.team_a, st.session_state.selected_player_team_a, "On Target"))
        with col2:
            st.button("Shot Off Target", key=f"shot_off_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Shot", st.session_state.team_a, st.session_state.selected_player_team_a, "Off Target"))
        with col3:
            st.button("⚽ Goal", key=f"goal_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Goal", st.session_state.team_a, st.session_state.selected_player_team_a))
        
        st.markdown("#### Passing")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Short Pass ✓", key=f"short_pass_a_success_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Pass", st.session_state.team_a, st.session_state.selected_player_team_a, "Successful", "Short"))
        with col2:
            st.button("Short Pass ✗", key=f"short_pass_a_fail_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Pass", st.session_state.team_a, st.session_state.selected_player_team_a, "Failed", "Short"))
        with col3:
            st.button("Long Pass ✓", key=f"long_pass_a_success_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Pass", st.session_state.team_a, st.session_state.selected_player_team_a, "Successful", "Long"))
        with col4:
            st.button("Long Pass ✗", key=f"long_pass_a_fail_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Pass", st.session_state.team_a, st.session_state.selected_player_team_a, "Failed", "Long"))
        
        st.markdown("#### Crossing")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Cross ✓", key=f"cross_a_success_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Cross", st.session_state.team_a, st.session_state.selected_player_team_a, "Successful"))
        with col2:
            st.button("Cross ✗", key=f"cross_a_fail_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Cross", st.session_state.team_a, st.session_state.selected_player_team_a, "Failed"))
        with col3:
            st.button("Corner", key=f"corner_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Corner", st.session_state.team_a, st.session_state.selected_player_team_a))

        st.markdown("#### Defensive / Other Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Clearance", key=f"clearance_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Defensive Action", st.session_state.team_a, st.session_state.selected_player_team_a, "Clearance"))
            st.button("Tackle", key=f"tackle_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Defensive Action", st.session_state.team_a, st.session_state.selected_player_team_a, "Tackle"))
        with col2:
            st.button("Interception", key=f"interception_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Defensive Action", st.session_state.team_a, st.session_state.selected_player_team_a, "Interception"))
            st.button("Foul Committed", key=f"foul_committed_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Foul", st.session_state.team_a, st.session_state.selected_player_team_a, "Committed"))
        with col3:
            st.button("Foul Suffered", key=f"foul_suffered_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Foul", st.session_state.team_a, st.session_state.selected_player_team_a, "Suffered"))
            st.button("Entry Final Third", key=f"entry_final_third_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Attacking Action", st.session_state.team_a, st.session_state.selected_player_team_a, "Entry Final Third"))
        
        st.markdown("#### Aerial Duels")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Aerial Won", key=f"aerial_won_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Aerial Duel", st.session_state.team_a, st.session_state.selected_player_team_a, "Won"))
        with col2:
            st.button("Aerial Lost", key=f"aerial_lost_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Aerial Duel", st.session_state.team_a, st.session_state.selected_player_team_a, "Lost"))
        
        st.markdown("#### Cards")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Yellow Card", key=f"yellow_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Card", st.session_state.team_a, st.session_state.selected_player_team_a, "Yellow"))
        with col2:
            st.button("Red Card", key=f"red_a_{st.session_state.selected_player_team_a}", 
                      on_click=record_event, args=("Card", st.session_state.team_a, st.session_state.selected_player_team_a, "Red"))

with player_selection_col2:
    st.markdown(f"### {st.session_state.team_b} Player Actions")
    st.session_state.selected_player_team_b = st.selectbox(
        "Select Player (Away Team):", 
        options=list(st.session_state.players_team_b.keys()),
        format_func=lambda x: st.session_state.players_team_b[x],
        key="player_selector_b"
    )
    if st.session_state.selected_player_team_b:
        current_player_b_name = st.session_state.players_team_b[st.session_state.selected_player_team_b]
        st.markdown(f"**Tracking Actions for: {current_player_b_name}**")

        st.markdown("#### Shooting")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Shot On Target", key=f"shot_on_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Shot", st.session_state.team_b, st.session_state.selected_player_team_b, "On Target"))
        with col2:
            st.button("Shot Off Target", key=f"shot_off_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Shot", st.session_state.team_b, st.session_state.selected_player_team_b, "Off Target"))
        with col3:
            st.button("⚽ Goal", key=f"goal_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Goal", st.session_state.team_b, st.session_state.selected_player_team_b))
        
        st.markdown("#### Passing")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Short Pass ✓", key=f"short_pass_b_success_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Pass", st.session_state.team_b, st.session_state.selected_player_team_b, "Successful", "Short"))
        with col2:
            st.button("Short Pass ✗", key=f"short_pass_b_fail_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Pass", st.session_state.team_b, st.session_state.selected_player_team_b, "Failed", "Short"))
        with col3:
            st.button("Long Pass ✓", key=f"long_pass_b_success_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Pass", st.session_state.team_b, st.session_state.selected_player_team_b, "Successful", "Long"))
        with col4:
            st.button("Long Pass ✗", key=f"long_pass_b_fail_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Pass", st.session_state.team_b, st.session_state.selected_player_team_b, "Failed", "Long"))
        
        st.markdown("#### Crossing")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Cross ✓", key=f"cross_b_success_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Cross", st.session_state.team_b, st.session_state.selected_player_team_b, "Successful"))
        with col2:
            st.button("Cross ✗", key=f"cross_b_fail_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Cross", st.session_state.team_b, st.session_state.selected_player_team_b, "Failed"))
        with col3:
            st.button("Corner", key=f"corner_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Corner", st.session_state.team_b, st.session_state.selected_player_team_b))

        st.markdown("#### Defensive / Other Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Clearance", key=f"clearance_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Defensive Action", st.session_state.team_b, st.session_state.selected_player_team_b, "Clearance"))
            st.button("Tackle", key=f"tackle_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Defensive Action", st.session_state.team_b, st.session_state.selected_player_team_b, "Tackle"))
        with col2:
            st.button("Interception", key=f"interception_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Defensive Action", st.session_state.team_b, st.session_state.selected_player_team_b, "Interception"))
            st.button("Foul Committed", key=f"foul_committed_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Foul", st.session_state.team_b, st.session_state.selected_player_team_b, "Committed"))
        with col3:
            st.button("Foul Suffered", key=f"foul_suffered_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Foul", st.session_state.team_b, st.session_state.selected_player_team_b, "Suffered"))
            st.button("Entry Final Third", key=f"entry_final_third_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Attacking Action", st.session_state.team_b, st.session_state.selected_player_team_b, "Entry Final Third"))
        
        st.markdown("#### Aerial Duels")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Aerial Won", key=f"aerial_won_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Aerial Duel", st.session_state.team_b, st.session_state.selected_player_team_b, "Won"))
        with col2:
            st.button("Aerial Lost", key=f"aerial_lost_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Aerial Duel", st.session_state.team_b, st.session_state.selected_player_team_b, "Lost"))
        
        st.markdown("#### Cards")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Yellow Card", key=f"yellow_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Card", st.session_state.team_b, st.session_state.selected_player_team_b, "Yellow"))
        with col2:
            st.button("Red Card", key=f"red_b_{st.session_state.selected_player_team_b}", 
                      on_click=record_event, args=("Card", st.session_state.team_b, st.session_state.selected_player_team_b, "Red"))

# ---
# Data reporting at bottom
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
else:
    st.info("No events recorded yet. Start tracking!")

# Auto-refresh to update timer
if st.session_state.timer_start:
    time.sleep(1)
    st.rerun()
