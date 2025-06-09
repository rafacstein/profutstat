import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Initialize session state
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

    # --- Novos para Cadastro de Jogadores ---
    st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"])
    st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"])
    # ---

    st.session_state.selected_player_team_a_num = None # Armazena apenas o número do jogador selecionado
    st.session_state.selected_player_team_b_num = None # Armazena apenas o número do jogador selecionado

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
    st.session_state.match_data = pd.DataFrame(columns=[
        "Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"
    ])
    # Não resetar jogadores cadastrados ao resetar o timer da partida
    # st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"])
    # st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"])

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

def record_event(event, team, player_number, event_type="", subtype=""):
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)
    
    player_name = ""
    if team == st.session_state.team_a:
        # Busca o nome do jogador pelo número no DataFrame de jogadores cadastrados
        player_row = st.session_state.registered_players_a[st.session_state.registered_players_a["Number"] == player_number]
        if not player_row.empty:
            player_name = player_row["Name"].iloc[0]
    else:
        player_row = st.session_state.registered_players_b[st.session_state.registered_players_b["Number"] == player_number]
        if not player_row.empty:
            player_name = player_row["Name"].iloc[0]
            
    # Adiciona o número do jogador ao nome para melhor identificação
    full_player_display = f"#{player_number} {player_name}" if player_name else f"#{player_number} (Nome não encontrado)"

    new_event = {
        "Event": event,
        "Minute": minute,
        "Second": second,
        "Team": team,
        "Player": full_player_display, # Usa o nome completo formatado
        "Type": event_type,
        "SubType": subtype,
        "Timestamp": time.time()
    }
    
    st.session_state.match_data = pd.concat(
        [st.session_state.match_data, pd.DataFrame([new_event])],
        ignore_index=True
    )
    st.rerun()

# ========== UI: CADASTRO DE JOGADORES ==========
def player_registration_section():
    st.header("📋 Cadastro de Jogadores")
    registration_col1, registration_col2 = st.columns(2)

    with registration_col1:
        st.subheader(f"{st.session_state.team_a} - Cadastro")
        player_num_a = st.text_input("Número do Jogador (Time A):", key="player_num_a")
        player_name_a = st.text_input("Nome do Jogador (Time A):", key="player_name_a")
        if st.button(f"Adicionar Jogador ao {st.session_state.team_a}"):
            if player_num_a and player_name_a:
                if player_num_a in st.session_state.registered_players_a["Number"].values:
                    st.warning(f"Jogador com número {player_num_a} já existe no {st.session_state.team_a}.")
                else:
                    new_player = pd.DataFrame([{"Number": player_num_a, "Name": player_name_a}])
                    st.session_state.registered_players_a = pd.concat(
                        [st.session_state.registered_players_a, new_player], ignore_index=True
                    )
                    st.success(f"Jogador #{player_num_a} {player_name_a} adicionado ao {st.session_state.team_a}!")
            else:
                st.error("Por favor, preencha o número e o nome do jogador.")
        
        st.markdown("---")
        st.subheader(f"Jogadores de {st.session_state.team_a} Cadastrados:")
        if not st.session_state.registered_players_a.empty:
            st.dataframe(st.session_state.registered_players_a, use_container_width=True)
            if st.button(f"Limpar Jogadores de {st.session_state.team_a}", key="clear_players_a"):
                st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"])
                st.rerun()
        else:
            st.info("Nenhum jogador cadastrado para o Time A.")


    with registration_col2:
        st.subheader(f"{st.session_state.team_b} - Cadastro")
        player_num_b = st.text_input("Número do Jogador (Time B):", key="player_num_b")
        player_name_b = st.text_input("Nome do Jogador (Time B):", key="player_name_b")
        if st.button(f"Adicionar Jogador ao {st.session_state.team_b}"):
            if player_num_b and player_name_b:
                if player_num_b in st.session_state.registered_players_b["Number"].values:
                    st.warning(f"Jogador com número {player_num_b} já existe no {st.session_state.team_b}.")
                else:
                    new_player = pd.DataFrame([{"Number": player_num_b, "Name": player_name_b}])
                    st.session_state.registered_players_b = pd.concat(
                        [st.session_state.registered_players_b, new_player], ignore_index=True
                    )
                    st.success(f"Jogador #{player_num_b} {player_name_b} adicionado ao {st.session_state.team_b}!")
            else:
                st.error("Por favor, preencha o número e o nome do jogador.")

        st.markdown("---")
        st.subheader(f"Jogadores de {st.session_state.team_b} Cadastrados:")
        if not st.session_state.registered_players_b.empty:
            st.dataframe(st.session_state.registered_players_b, use_container_width=True)
            if st.button(f"Limpar Jogadores de {st.session_state.team_b}", key="clear_players_b"):
                st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"])
                st.rerun()
        else:
            st.info("Nenhum jogador cadastrado para o Time B.")
    
    st.markdown("---") # Separador visual

# ========== STREAMLIT UI ==========
st.set_page_config(layout="wide")
st.title("⚽ Football Match Tracker")

# Exibe a seção de cadastro de jogadores primeiro
player_registration_section()

# Top control row - Timer and Teams
st.header("⚙️ Controles da Partida")
control_col1, control_col2, control_col3 = st.columns([2,2,3])
with control_col1:
    st.session_state.team_a = st.text_input("Nome do Time da Casa:", st.session_state.team_a)
with control_col2:
    st.session_state.team_b = st.text_input("Nome do Time Visitante:", st.session_state.team_b)
with control_col3:
    st.session_state.playback_speed = st.radio("Velocidade do Timer:", [1, 2], horizontal=True, index=0)
    timer_col1, timer_col2, timer_col3 = st.columns(3)
    with timer_col1:
        if st.button("⏵ Iniciar", use_container_width=True) and st.session_state.timer_start is None:
            start_timer()
    with timer_col2:
        if st.button("⏸ Pausar", use_container_width=True) and st.session_state.timer_start is not None:
            pause_timer()
    with timer_col3:
        if st.button("↻ Resetar Tudo", use_container_width=True):
            reset_timer()
            st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"]) # Resetar jogadores cadastrados
            st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"]) # Resetar jogadores cadastrados
            st.rerun()

# Second row - Time and Possession
time_col, poss_col_a, poss_col_b = st.columns([2,1,1])
with time_col:
    current_time = get_current_time()
    display_min = int(current_time // 60)
    display_sec = int(current_time % 60)
    st.metric("Tempo de Jogo", f"{display_min}:{display_sec:02d}")

team_a_poss, team_b_poss = calculate_possession()
with poss_col_a:
    if st.button(f"🏃 Posse de {st.session_state.team_a}", use_container_width=True):
        set_possession(st.session_state.team_a)
    st.metric(f"Posse {st.session_state.team_a}", f"{team_a_poss:.1f}%")
with poss_col_b:
    if st.button(f"🏃 Posse de {st.session_state.team_b}", use_container_width=True):
        set_possession(st.session_state.team_b)
    st.metric(f"Posse {st.session_state.team_b}", f"{team_b_poss:.1f}%")

# Main action buttons - Player-centric
st.header("⚽ Ações da Partida (Por Jogador)")

player_selection_col1, player_selection_col2 = st.columns(2)

with player_selection_col1:
    st.markdown(f"### {st.session_state.team_a} - Ações")
    
    # Prepara as opções para o selectbox
    player_options_a = ["Selecione um Jogador"] + st.session_state.registered_players_a["Number"].tolist()
    
    st.session_state.selected_player_team_a_num = st.selectbox(
        "Selecione o Jogador:", 
        options=player_options_a,
        format_func=lambda x: f"#{x} {st.session_state.registered_players_a[st.session_state.registered_players_a['Number'] == x]['Name'].iloc[0]}" 
                      if x != "Selecione um Jogador" and not st.session_state.registered_players_a[st.session_state.registered_players_a['Number'] == x].empty
                      else x,
        key="player_selector_a"
    )

    if st.session_state.selected_player_team_a_num and st.session_state.selected_player_team_a_num != "Selecione um Jogador":
        current_player_a_name = st.session_state.registered_players_a[
            st.session_state.registered_players_a["Number"] == st.session_state.selected_player_team_a_num
        ]["Name"].iloc[0]
        st.markdown(f"**Registrando ações para: #{st.session_state.selected_player_team_a_num} {current_player_a_name}**")

        st.markdown("#### Finalizações")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("No Alvo", key=f"shot_on_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Finalização", st.session_state.team_a, st.session_state.selected_player_team_a_num, "No Alvo"))
        with col2:
            st.button("Fora do Alvo", key=f"shot_off_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Finalização", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Fora do Alvo"))
        with col3:
            st.button("⚽ Gol", key=f"goal_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Gol", st.session_state.team_a, st.session_state.selected_player_team_a_num))
        
        st.markdown("#### Passes")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Curto ✓", key=f"short_pass_a_success_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Certo", "Curto"))
        with col2:
            st.button("Curto ✗", key=f"short_pass_a_fail_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Errado", "Curto"))
        with col3:
            st.button("Longo ✓", key=f"long_pass_a_success_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Certo", "Longo"))
        with col4:
            st.button("Longo ✗", key=f"long_pass_a_fail_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Errado", "Longo"))
        
        st.markdown("#### Cruzamentos")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Cruzamento ✓", key=f"cross_a_success_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Cruzamento", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Certo"))
        with col2:
            st.button("Cruzamento ✗", key=f"cross_a_fail_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Cruzamento", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Errado"))
        with col3:
            st.button("Escanteio", key=f"corner_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Escanteio", st.session_state.team_a, st.session_state.selected_player_team_a_num))

        st.markdown("#### Ações Defensivas / Outras")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Desarme", key=f"tackle_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Defesa", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Desarme"))
            st.button("Bolas Afastadas", key=f"clearance_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Defesa", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Bolas Afastadas"))
        with col2:
            st.button("Interceptação", key=f"interception_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Defesa", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Interceptação"))
            st.button("Falta Cometida", key=f"foul_committed_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Falta", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Cometida"))
        with col3:
            st.button("Falta Sofrida", key=f"foul_suffered_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Falta", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Sofrida"))
            st.button("Entrada no Terço Final", key=f"entry_final_third_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Ataque", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Entrada Terço Final"))
        
        st.markdown("#### Duelos Aéreos")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Vencido", key=f"aerial_won_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Duelo Aéreo", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Vencido"))
        with col2:
            st.button("Perdido", key=f"aerial_lost_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Duelo Aéreo", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Perdido"))
        
        st.markdown("#### Cartões")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Cartão Amarelo", key=f"yellow_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Cartão", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Amarelo"))
        with col2:
            st.button("Cartão Vermelho", key=f"red_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Cartão", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Vermelho"))
    else:
        st.info("Selecione um jogador do Time da Casa para registrar ações.")


with player_selection_col2:
    st.markdown(f"### {st.session_state.team_b} - Ações")

    # Prepara as opções para o selectbox
    player_options_b = ["Selecione um Jogador"] + st.session_state.registered_players_b["Number"].tolist()

    st.session_state.selected_player_team_b_num = st.selectbox(
        "Selecione o Jogador:", 
        options=player_options_b,
        format_func=lambda x: f"#{x} {st.session_state.registered_players_b[st.session_state.registered_players_b['Number'] == x]['Name'].iloc[0]}" 
                      if x != "Selecione um Jogador" and not st.session_state.registered_players_b[st.session_state.registered_players_b['Number'] == x].empty
                      else x,
        key="player_selector_b"
    )

    if st.session_state.selected_player_team_b_num and st.session_state.selected_player_team_b_num != "Selecione um Jogador":
        current_player_b_name = st.session_state.registered_players_b[
            st.session_state.registered_players_b["Number"] == st.session_state.selected_player_team_b_num
        ]["Name"].iloc[0]
        st.markdown(f"**Registrando ações para: #{st.session_state.selected_player_team_b_num} {current_player_b_name}**")

        st.markdown("#### Finalizações")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("No Alvo", key=f"shot_on_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Finalização", st.session_state.team_b, st.session_state.selected_player_team_b_num, "No Alvo"))
        with col2:
            st.button("Fora do Alvo", key=f"shot_off_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Finalização", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Fora do Alvo"))
        with col3:
            st.button("⚽ Gol", key=f"goal_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Gol", st.session_state.team_b, st.session_state.selected_player_team_b_num))
        
        st.markdown("#### Passes")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Curto ✓", key=f"short_pass_b_success_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Certo", "Curto"))
        with col2:
            st.button("Curto ✗", key=f"short_pass_b_fail_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Errado", "Curto"))
        with col3:
            st.button("Longo ✓", key=f"long_pass_b_success_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Certo", "Longo"))
        with col4:
            st.button("Longo ✗", key=f"long_pass_b_fail_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Passe", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Errado", "Longo"))
        
        st.markdown("#### Cruzamentos")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Cruzamento ✓", key=f"cross_b_success_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Cruzamento", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Certo"))
        with col2:
            st.button("Cruzamento ✗", key=f"cross_b_fail_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Cruzamento", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Errado"))
        with col3:
            st.button("Escanteio", key=f"corner_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Escanteio", st.session_state.team_b, st.session_state.selected_player_team_b_num))

        st.markdown("#### Ações Defensivas / Outras")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Desarme", key=f"tackle_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Defesa", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Desarme"))
            st.button("Bolas Afastadas", key=f"clearance_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Defesa", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Bolas Afastadas"))
        with col2:
            st.button("Interceptação", key=f"interception_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Defesa", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Interceptação"))
            st.button("Falta Cometida", key=f"foul_committed_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Falta", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Cometida"))
        with col3:
            st.button("Falta Sofrida", key=f"foul_suffered_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Falta", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Sofrida"))
            st.button("Entrada no Terço Final", key=f"entry_final_third_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Ataque", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Entrada Terço Final"))
        
        st.markdown("#### Duelos Aéreos")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Vencido", key=f"aerial_won_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Duelo Aéreo", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Vencido"))
        with col2:
            st.button("Perdido", key=f"aerial_lost_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Duelo Aéreo", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Perdido"))
        
        st.markdown("#### Cartões")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Cartão Amarelo", key=f"yellow_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Cartão", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Amarelo"))
        with col2:
            st.button("Cartão Vermelho", key=f"red_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Cartão", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Vermelho"))
    else:
        st.info("Selecione um jogador do Time Visitante para registrar ações.")

# Data reporting at bottom
st.header("📊 Relatório da Partida")
if not st.session_state.match_data.empty:
    st.dataframe(st.session_state.match_data.sort_values(["Minute", "Second"]), use_container_width=True)
    
    # Exibe estatísticas básicas por jogador
    st.subheader("Estatísticas por Jogador")
    player_stats = st.session_state.match_data.groupby(['Player', 'Event', 'Type', 'SubType']).size().reset_index(name='Count')
    st.dataframe(player_stats, use_container_width=True)

    if st.button("Exportar Relatório Completo (CSV)"):
        csv = st.session_state.match_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="match_analysis_full.csv",
            mime="text/csv"
        )
    
    if st.button("Exportar Estatísticas por Jogador (CSV)"):
        csv_stats = player_stats.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_stats,
            file_name="player_stats.csv",
            mime="text/csv"
        )
else:
    st.info("Nenhum evento registrado ainda. Cadastre jogadores e inicie o tracking!")

# Auto-refresh para atualizar o timer
if st.session_state.timer_start:
    time.sleep(1)
    st.rerun()
