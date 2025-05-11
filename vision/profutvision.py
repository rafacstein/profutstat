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
# [Keep all your existing functions exactly the same...]

# ========== STREAMLIT UI ==========
st.set_page_config(layout="wide")  # Force landscape mode

st.title("⚽ Football Match Tracker - Landscape View")

# Top control row - Timer and Teams
control_col1, control_col2, control_col3, control_col4 = st.columns([2,2,3,2])
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
with control_col4:
    st.write("")  # Spacer
    if st.button("Export to CSV", use_container_width=True):
        csv = st.session_state.match_data.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="match_analysis.csv",
            mime="text/csv",
            use_container_width=True
        )

# Second row - Time and Possession
time_col, poss_col_a, poss_col_b, data_col = st.columns([2,1,1,2])
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
with data_col:
    st.write("")  # Spacer for alignment

# Main action buttons - Horizontal layout
st.header("Match Actions")

# Row 1: Passing and Crossing
pass_cross_col1, pass_cross_col2 = st.columns(2)
with pass_cross_col1:
    # Passing
    st.subheader("Passing")
    pass_col1, pass_col2 = st.columns(2)
    with pass_col1:
        st.markdown(f"**{st.session_state.team_a}**")
        st.button("Short ✓", key="short_pass_a_success", on_click=record_event, 
                args=("Pass", st.session_state.team_a, "", "Successful", "Short"))
        st.button("Short ✗", key="short_pass_a_fail", on_click=record_event, 
                args=("Pass", st.session_state.team_a, "", "Failed", "Short"))
        st.button("Long ✓", key="long_pass_a_success", on_click=record_event, 
                args=("Pass", st.session_state.team_a, "", "Successful", "Long"))
        st.button("Long ✗", key="long_pass_a_fail", on_click=record_event, 
                args=("Pass", st.session_state.team_a, "", "Failed", "Long"))
    
    with pass_col2:
        st.markdown(f"**{st.session_state.team_b}**")
        st.button("Short ✓", key="short_pass_b_success", on_click=record_event, 
                args=("Pass", st.session_state.team_b, "", "Successful", "Short"))
        st.button("Short ✗", key="short_pass_b_fail", on_click=record_event, 
                args=("Pass", st.session_state.team_b, "", "Failed", "Short"))
        st.button("Long ✓", key="long_pass_b_success", on_click=record_event, 
                args=("Pass", st.session_state.team_b, "", "Successful", "Long"))
        st.button("Long ✗", key="long_pass_b_fail", on_click=record_event, 
                args=("Pass", st.session_state.team_b, "", "Failed", "Long"))

with pass_cross_col2:
    # Crossing
    st.subheader("Crossing")
    cross_col1, cross_col2 = st.columns(2)
    with cross_col1:
        st.markdown(f"**{st.session_state.team_a}**")
        st.button("Cross ✓", key="cross_a_success", on_click=record_event, 
                args=("Cross", st.session_state.team_a, "", "Successful"))
        st.button("Cross ✗", key="cross_a_fail", on_click=record_event, 
                args=("Cross", st.session_state.team_a, "", "Failed"))
        st.button("Corner", key="corner_a", on_click=record_event, 
                args=("Corner", st.session_state.team_a))
    
    with cross_col2:
        st.markdown(f"**{st.session_state.team_b}**")
        st.button("Cross ✓", key="cross_b_success", on_click=record_event, 
                args=("Cross", st.session_state.team_b, "", "Successful"))
        st.button("Cross ✗", key="cross_b_fail", on_click=record_event, 
                args=("Cross", st.session_state.team_b, "", "Failed"))
        st.button("Corner", key="corner_b", on_click=record_event, 
                args=("Corner", st.session_state.team_b))

# Row 2: Shooting and Defensive
shot_def_col1, shot_def_col2 = st.columns(2)
with shot_def_col1:
    # Shooting
    st.subheader("Shooting")
    shot_col1, shot_col2 = st.columns(2)
    with shot_col1:
        st.markdown(f"**{st.session_state.team_a}**")
        st.button("On Target", key="shot_on_a", on_click=record_event, 
                args=("Shot", st.session_state.team_a, "", "On Target"))
        st.button("Off Target", key="shot_off_a", on_click=record_event, 
                args=("Shot", st.session_state.team_a, "", "Off Target"))
        player_a = st.text_input("Scorer:", key="scorer_a")
        st.button("⚽ Goal", key="goal_a", on_click=record_event, 
                args=("Goal", st.session_state.team_a, player_a))
    
    with shot_col2:
        st.markdown(f"**{st.session_state.team_b}**")
        st.button("On Target", key="shot_on_b", on_click=record_event, 
                args=("Shot", st.session_state.team_b, "", "On Target"))
        st.button("Off Target", key="shot_off_b", on_click=record_event, 
                args=("Shot", st.session_state.team_b, "", "Off Target"))
        player_b = st.text_input("Scorer:", key="scorer_b")
        st.button("⚽ Goal", key="goal_b", on_click=record_event, 
                args=("Goal", st.session_state.team_b, player_b))

with shot_def_col2:
    # Defensive
    st.subheader("Defensive Actions")
    def_col1, def_col2 = st.columns(2)
    with def_col1:
        st.markdown(f"**{st.session_state.team_a}**")
        st.button("Tackle", key="tackle_a", on_click=record_event, 
                args=("Tackle", st.session_state.team_a))
        st.button("Intercept", key="interception_a", on_click=record_event, 
                args=("Interception", st.session_state.team_a))
        st.button("Foul", key="foul_a", on_click=record_event, 
                args=("Foul", st.session_state.team_a))
        yellow_player_a = st.text_input("Player (Yellow):", key="yellow_player_a")
        st.button("Yellow", key="yellow_a", on_click=record_event, 
                args=("Card", st.session_state.team_a, yellow_player_a, "Yellow"))
        red_player_a = st.text_input("Player (Red):", key="red_player_a")
        st.button("Red", key="red_a", on_click=record_event, 
                args=("Card", st.session_state.team_a, red_player_a, "Red"))
    
    with def_col2:
        st.markdown(f"**{st.session_state.team_b}**")
        st.button("Tackle", key="tackle_b", on_click=record_event, 
                args=("Tackle", st.session_state.team_b))
        st.button("Intercept", key="interception_b", on_click=record_event, 
                args=("Interception", st.session_state.team_b))
        st.button("Foul", key="foul_b", on_click=record_event, 
                args=("Foul", st.session_state.team_b))
        yellow_player_b = st.text_input("Player (Yellow):", key="yellow_player_b")
        st.button("Yellow", key="yellow_b", on_click=record_event, 
                args=("Card", st.session_state.team_b, yellow_player_b, "Yellow"))
        red_player_b = st.text_input("Player (Red):", key="red_player_b")
        st.button("Red", key="red_b", on_click=record_event, 
                args=("Card", st.session_state.team_b, red_player_b, "Red"))

# Row 3: Aerial Duels and Live Data
aerial_data_col1, aerial_data_col2 = st.columns([1,2])
with aerial_data_col1:
    # Aerial Duels
    st.subheader("Aerial Duels")
    aerial_col1, aerial_col2 = st.columns(2)
    with aerial_col1:
        st.markdown(f"**{st.session_state.team_a}**")
        st.button("Won", key="aerial_won_a", on_click=record_event, 
                args=("Aerial Duel", st.session_state.team_a, "", "Won"))
        st.button("Lost", key="aerial_lost_a", on_click=record_event, 
                args=("Aerial Duel", st.session_state.team_a, "", "Lost"))
    
    with aerial_col2:
        st.markdown(f"**{st.session_state.team_b}**")
        st.button("Won", key="aerial_won_b", on_click=record_event, 
                args=("Aerial Duel", st.session_state.team_b, "", "Won"))
        st.button("Lost", key="aerial_lost_b", on_click=record_event, 
                args=("Aerial Duel", st.session_state.team_b, "", "Lost"))

with aerial_data_col2:
    # Live Data Feed
    st.subheader("Live Match Data")
    if not st.session_state.match_data.empty:
        st.dataframe(st.session_state.match_data.sort_values(["Minute", "Second"], ascending=False),
                    height=200, use_container_width=True)
    else:
        st.info("No match data recorded yet")

# Custom CSS to maximize space
st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            padding: 0.25rem;
        }
        .stTextInput input {
            padding: 0.25rem;
        }
        section.main > div {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)
