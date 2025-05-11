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

# [Previous timer and possession functions remain the same...]

# Streamlit UI
st.title("⚽ Football Match Tracker")

# Team configuration and timer - Top section
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

# Current time and possession - Second section
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

# Main action buttons - Using tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["Passing", "Shooting", "Defensive", "Aerial"])

with tab1:
    # Passing buttons
    st.subheader("Passing")
    pass_col1, pass_col2 = st.columns(2)
    with pass_col1:
        st.write(f"{st.session_state.team_a}")
        short_a1, short_a2 = st.columns(2)
        with short_a1:
            if st.button("Short ✓", key="short_pass_a_success", use_container_width=True):
                record_event("Pass", st.session_state.team_a, "", "Successful", "Short")
        with short_a2:
            if st.button("Short ✗", key="short_pass_a_fail", use_container_width=True):
                record_event("Pass", st.session_state.team_a, "", "Failed", "Short")
        long_a1, long_a2 = st.columns(2)
        with long_a1:
            if st.button("Long ✓", key="long_pass_a_success", use_container_width=True):
                record_event("Pass", st.session_state.team_a, "", "Successful", "Long")
        with long_a2:
            if st.button("Long ✗", key="long_pass_a_fail", use_container_width=True):
                record_event("Pass", st.session_state.team_a, "", "Failed", "Long")
    
    with pass_col2:
        st.write(f"{st.session_state.team_b}")
        short_b1, short_b2 = st.columns(2)
        with short_b1:
            if st.button("Short ✓", key="short_pass_b_success", use_container_width=True):
                record_event("Pass", st.session_state.team_b, "", "Successful", "Short")
        with short_b2:
            if st.button("Short ✗", key="short_pass_b_fail", use_container_width=True):
                record_event("Pass", st.session_state.team_b, "", "Failed", "Short")
        long_b1, long_b2 = st.columns(2)
        with long_b1:
            if st.button("Long ✓", key="long_pass_b_success", use_container_width=True):
                record_event("Pass", st.session_state.team_b, "", "Successful", "Long")
        with long_b2:
            if st.button("Long ✗", key="long_pass_b_fail", use_container_width=True):
                record_event("Pass", st.session_state.team_b, "", "Failed", "Long")

with tab2:
    # Shooting buttons
    st.subheader("Shooting")
    shot_col1, shot_col2 = st.columns(2)
    with shot_col1:
        st.write(f"{st.session_state.team_a}")
        shot_a1, shot_a2 = st.columns(2)
        with shot_a1:
            if st.button("On Target", key="shot_on_a", use_container_width=True):
                record_event("Shot", st.session_state.team_a, "", "On Target")
        with shot_a2:
            if st.button("Off Target", key="shot_off_a", use_container_width=True):
                record_event("Shot", st.session_state.team_a, "", "Off Target")
        if st.button("⚽ Goal", key="goal_a", use_container_width=True):
            player = st.text_input("Scorer:", key="scorer_a")
            record_event("Goal", st.session_state.team_a, player)
    
    with shot_col2:
        st.write(f"{st.session_state.team_b}")
        shot_b1, shot_b2 = st.columns(2)
        with shot_b1:
            if st.button("On Target", key="shot_on_b", use_container_width=True):
                record_event("Shot", st.session_state.team_b, "", "On Target")
        with shot_b2:
            if st.button("Off Target", key="shot_off_b", use_container_width=True):
                record_event("Shot", st.session_state.team_b, "", "Off Target")
        if st.button("⚽ Goal", key="goal_b", use_container_width=True):
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
            if st.button("Tackle", key="tackle_a", use_container_width=True):
                record_event("Tackle", st.session_state.team_a)
        with col2:
            if st.button("Intercept", key="interception_a", use_container_width=True):
                record_event("Interception", st.session_state.team_a)
        with col3:
            if st.button("Foul", key="foul_a", use_container_width=True):
                record_event("Foul", st.session_state.team_a)
        
        # Cards for Team A
        card_a1, card_a2 = st.columns(2)
        with card_a1:
            if st.button("Yellow", key="yellow_a", use_container_width=True):
                player = st.text_input("Player (Yellow):", key="yellow_player_a")
                record_event("Card", st.session_state.team_a, player, "Yellow")
        with card_a2:
            if st.button("Red", key="red_a", use_container_width=True):
                player = st.text_input("Player (Red):", key="red_player_a")
                record_event("Card", st.session_state.team_a, player, "Red")
    
    with def_col2:
        st.write(f"{st.session_state.team_b}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Tackle", key="tackle_b", use_container_width=True):
                record_event("Tackle", st.session_state.team_b)
        with col2:
            if st.button("Intercept", key="interception_b", use_container_width=True):
                record_event("Interception", st.session_state.team_b)
        with col3:
            if st.button("Foul", key="foul_b", use_container_width=True):
                record_event("Foul", st.session_state.team_b)
        
        # Cards for Team B
        card_b1, card_b2 = st.columns(2)
        with card_b1:
            if st.button("Yellow", key="yellow_b", use_container_width=True):
                player = st.text_input("Player (Yellow):", key="yellow_player_b")
                record_event("Card", st.session_state.team_b, player, "Yellow")
        with card_b2:
            if st.button("Red", key="red_b", use_container_width=True):
                player = st.text_input("Player (Red):", key="red_player_b")
                record_event("Card", st.session_state.team_b, player, "Red")

with tab4:
    # Aerial duels
    st.subheader("Aerial Duels")
    aerial_col1, aerial_col2 = st.columns(2)
    with aerial_col1:
        st.write(f"{st.session_state.team_a}")
        duel_a1, duel_a2 = st.columns(2)
        with duel_a1:
            if st.button("Won", key="aerial_won_a", use_container_width=True):
                record_event("Aerial Duel", st.session_state.team_a, "", "Won")
        with duel_a2:
            if st.button("Lost", key="aerial_lost_a", use_container_width=True):
                record_event("Aerial Duel", st.session_state.team_a, "", "Lost")
    
    with aerial_col2:
        st.write(f"{st.session_state.team_b}")
        duel_b1, duel_b2 = st.columns(2)
        with duel_b1:
            if st.button("Won", key="aerial_won_b", use_container_width=True):
                record_event("Aerial Duel", st.session_state.team_b, "", "Won")
        with duel_b2:
            if st.button("Lost", key="aerial_lost_b", use_container_width=True):
                record_event("Aerial Duel", st.session_state.team_b, "", "Lost")

# [Rest of the code (data reporting) remains the same...]
