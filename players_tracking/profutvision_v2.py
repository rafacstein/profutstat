import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Initialize session state
# Ensure ALL session state variables are initialized here
if 'match_data' not in st.session_state:
    st.session_state.match_data = pd.DataFrame(columns=[
        "Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"
    ])
    st.session_state.team_a = "Time A"
    st.session_state.team_b = "Time B"
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    st.session_state.playback_speed = 1
    st.session_state.current_possession = None
    st.session_state.possession_start = None
    st.session_state.possession_log = []

    # --- Crucial: Initialize these DataFrames inside the 'if not in' block ---
    # This guarantees they are set up when the session starts or resets
    st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"])
    st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"])
    # ---

    st.session_state.selected_player_team_a_num = None
    st.session_state.selected_player_team_b_num = None

# ... rest of your code ...
