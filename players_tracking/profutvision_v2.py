import streamlit as st
import pandas as pd
import time
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA E INICIALIZAÇÃO DO ESTADO ---
st.set_page_config(layout="wide", page_title="Scout Match Tracker")

# Dicionário para inicialização limpa e completa do session_state
initial_state = {
    'match_data': pd.DataFrame(columns=["Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"]),
    'team_a': "Time A",
    'team_b': "Time B",
    'timer_start': None,
    'paused_time': 0,
    'registered_players_a': pd.DataFrame(columns=["Number", "Name"]),
    'registered_players_b': pd.DataFrame(columns=["Number", "Name"]),
    'youtube_url': "",
    # Novas variáveis para controle de posse de bola
    'possession_team': None, # 'team_a', 'team_b', ou None
    'possession_start_time': 0,
    'team_a_possession_seconds': 0.0,
    'team_b_possession_seconds': 0.0,
}

for key, value in initial_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ========== FUNÇÕES PRINCIPAIS (CORE) ==========
def get_current_time():
    if st.session_state.timer_start is None:
        return st.session_state.paused_time
    return time.time() - st.session_state.timer_start + st.session_state.paused_time

def start_timer():
    if st.session_state.timer_start is None:
        st.session_state.timer_start = time.time()
        # Inicia a contagem de posse se um time já tiver a bola
        if st.session_state.possession_team:
            st.session_state.possession_start_time = time.time()

def pause_timer():
    if st.session_state.timer_start:
        # Pausa o cronômetro principal
        st.session_state.paused_time += time.time() - st.session_state.timer_start
        st.session_state.timer_start = None
        # Pausa a contagem de posse
        update_possession_time()
        st.session_state.possession_start_time = 0

def reset_timer():
    # Reseta o timer
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    # Reseta os dados da partida
    st.session_state.match_data = pd.DataFrame(columns=initial_state['match_data'].columns)
    # Reseta a posse de bola
    st.session_state.possession_team = None
    st.session_state.possession_start_time = 0
    st.session_state.team_a_possession_seconds = 0.0
    st.session_state.team_b_possession_seconds = 0.0
    st.rerun()

def update_possession_time():
    """Calcula e adiciona o tempo decorrido ao time que tinha a posse."""
    if st.session_state.possession_team and st.session_state.possession_start_time > 0:
        elapsed = time.time() - st.session_state.possession_start_time
        if st.session_state.possession_team == 'team_a':
            st.session_state.team_a_possession_seconds += elapsed
        elif st.session_state.possession_team == 'team_b':
            st.session_state.team_b_possession_seconds += elapsed
        # Reseta o início para o tempo atual para continuar a contagem
        st.session_state.possession_start_time = time.time()

def set_possession(new_team):
    """Define o novo time com posse de bola e atualiza os contadores."""
    if st.session_state.timer_start is None: # Não faz nada se o jogo estiver pausado
        st.warning("Inicie o cronômetro para controlar a posse de bola.")
        return
        
    update_possession_time() # Atualiza o tempo do time anterior
    st.session_state.possession_team = new_team
    if new_team is not None:
        st.session_state.possession_start_time = time.time()
    else:
        st.session_state.possession_start_time = 0

def record_event(event, team, player_number, event_type="", subtype=""):
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)
    
    registered_players = st.session_state.registered_players_a if team == st.session_state.team_a else st.session_state.registered_players_b
    player_row = registered_players[registered_players["Number"] == player_number]
    player_name = player_row["Name"].iloc[0] if not player_row.empty else "(não cadastrado)"
    full_player_display = f"#{player_number} {player_name}"

    new_event = {
        "Event": event, "Minute": minute, "Second": second, "Team": team,
        "Player": full_player_display, "Type": event_type, "SubType": subtype,
        "Timestamp": datetime.now()
    }
    
    st.session_state.match_data = pd.concat(
        [st.session_state.match_data, pd.DataFrame([new_event])], ignore_index=True
    )
    st.rerun()

# ========== BARRA LATERAL (SIDEBAR) ==========
with st.sidebar:
    st.title("⚙️ Configuração")
    st.header("📺 Vídeo da Partida")
    st.session_state.youtube_url = st.text_input("Cole o link do YouTube aqui:")
    st.header("📋 Cadastro")
    st.session_state.team_a = st.text_input("Time da Casa:", st.session_state.team_a)
    st.session_state.team_b = st.text_input("Time Visitante:", st.session_state.team_b)

    with st.expander(f"Jogadores - {st.session_state.team_a}"):
        # Formulário de cadastro
        ...
    with st.expander(f"Jogadores - {st.session_state.team_b}"):
        # Formulário de cadastro
        ...

# ========== LAYOUT PRINCIPAL DA INTERFACE ==========
st.title("⚽ Scout Match Tracker")

main_col1, main_col2 = st.columns([0.55, 0.45])

with main_col1:
    if st.session_state.youtube_url:
        st.video(st.session_state.youtube_url)
    else:
        st.info("⬅️ Cole um link do YouTube na barra lateral para começar.")

    # --- Controles de Tempo e Posse ---
    st.markdown("---")
    current_time = get_current_time()
    display_min = int(current_time // 60)
    display_sec = int(current_time % 60)

    col_metric, col_start, col_pause, col_reset = st.columns([1.5, 1, 1, 1])
    col_metric.metric("Tempo", f"{display_min}:{display_sec:02d}")
    col_start.button("▶️ Iniciar", use_container_width=True, on_click=start_timer, disabled=st.session_state.timer_start is not None)
    col_pause.button("⏸️ Pausar", use_container_width=True, on_click=pause_timer, disabled=st.session_state.timer_start is None)
    col_reset.button("🔄 Resetar", use_container_width=True, on_click=reset_timer)

    # --- NOVO: Seção de Posse de Bola ---
    st.markdown("##### Posse de Bola")
    update_possession_time() # Garante que o tempo seja calculado a cada rerun
    
    total_possession = st.session_state.team_a_possession_seconds + st.session_state.team_b_possession_seconds
    perc_a = (st.session_state.team_a_possession_seconds / total_possession * 100) if total_possession > 0 else 0
    perc_b = (st.session_state.team_b_possession_seconds / total_possession * 100) if total_possession > 0 else 0

    team_a_label = f"{st.session_state.team_a} ({perc_a:.0f}%)"
    team_b_label = f"{st.session_state.team_b} ({perc_b:.0f}%)"
    
    # Indicador de posse atual
    if st.session_state.possession_team == 'team_a':
        st.success(f"**Posse: {st.session_state.team_a}**")
    elif st.session_state.possession_team == 'team_b':
        st.info(f"**Posse: {st.session_state.team_b}**")
    else:
        st.warning("**Posse: Bola fora ou em disputa**")

    pos_c1, pos_c2, pos_c3 = st.columns(3)
    pos_c1.button(team_a_label, key="pos_a", use_container_width=True, on_click=set_possession, args=('team_a',))
    pos_c2.button("Bola Fora / Disputa", key="pos_none", use_container_width=True, on_click=set_possession, args=(None,))
    pos_c3.button(team_b_label, key="pos_b", use_container_width=True, on_click=set_possession, args=('team_b',))


with main_col2:
    st.header("⚡ Ações da Partida")
    tab1, tab2 = st.tabs([f"Ações: {st.session_state.team_a}", f"Ações: {st.session_state.team_b}"])

    def create_action_buttons(team_name, registered_players, key_prefix):
        if registered_players.empty:
            st.warning(f"⬅️ Cadastre jogadores para o '{team_name}' na barra lateral.")
            return

        def format_func(player_num):
            player_info = registered_players[registered_players['Number'] == player_num]
            return f"#{player_num} - {player_info['Name'].iloc[0]}" if not player_info.empty else f"#{player_num}"

        selected_player_num = st.selectbox("Selecione o Jogador:", options=registered_players["Number"].tolist(), format_func=format_func, key=f"player_selector_{key_prefix}")
        
        if not selected_player_num: return
        p = selected_player_num
        
        st.markdown(f"**Registrando para: {format_func(p)}**")

        st.markdown("##### Finalização e Criação")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.button("Gol ⚽", key=f"goal_{key_prefix}_{p}", on_click=record_event, args=("Gol", team_name, p), use_container_width=True)
        c2.button("Chute G.", key=f"shot_on_{key_prefix}_{p}", on_click=record_event, args=("Finalização", team_name, p, "No Alvo"), use_container_width=True)
        c3.button("Chute F.", key=f"shot_off_{key_prefix}_{p}", on_click=record_event, args=("Finalização", team_name, p, "Fora do Alvo"), use_container_width=True)
        c4.button("Assist.", key=f"assist_{key_prefix}_{p}", on_click=record_event, args=("Assistência", team_name, p), use_container_width=True)
        c5.button("Passe Chave", key=f"keypass_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Chave"), use_container_width=True)

        st.markdown("##### Passes")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("Curto ✓", key=f"p_c_ok_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Certo", "Curto"), use_container_width=True)
        c2.button("Curto ✗", key=f"p_c_er_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Errado", "Curto"), use_container_width=True)
        c3.button("Longo ✓", key=f"p_l_ok_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Certo", "Longo"), use_container_width=True)
        c4.button("Longo ✗", key=f"p_l_er_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Errado", "Longo"), use_container_width=True)
        
        st.markdown("##### Cruzamentos e Duelos")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("Cruz. ✓", key=f"cruz_ok_{key_prefix}_{p}", on_click=record_event, args=("Cruzamento", team_name, p, "Certo"), use_container_width=True)
        c2.button("Cruz. ✗", key=f"cruz_er_{key_prefix}_{p}", on_click=record_event, args=("Cruzamento", team_name, p, "Errado"), use_container_width=True)
        c3.button("Duelo Aéreo ✓", key=f"aer_ok_{key_prefix}_{p}", on_click=record_event, args=("Duelo Aéreo", team_name, p, "Ganho"), use_container_width=True)
        c4.button("Duelo Aéreo ✗", key=f"aer_er_{key_prefix}_{p}", on_click=record_event, args=("Duelo Aéreo", team_name, p, "Perdido"), use_container_width=True)
        
        st.markdown("##### Dribles")
        c1, c2, c3 = st.columns(3)
        c1.button("Drible Certo ✓", key=f"drib_ok_{key_prefix}_{p}", on_click=record_event, args=("Drible", team_name, p, "Certo"), use_container_width=True)
        c2.button("Drible Errado ✗", key=f"drib_er_{key_prefix}_{p}", on_click=record_event, args=("Drible", team_name, p, "Errado"), use_container_width=True)
        c3.button("Drible Sofrido", key=f"drib_past_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Drible Sofrido"), use_container_width=True)

        st.markdown("##### Ações Defensivas")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("Desarme", key=f"tackle_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Desarme"), use_container_width=True)
        c2.button("Intercept.", key=f"intercept_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Interceptação"), use_container_width=True)
        c3.button("Corte", key=f"clear_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Corte"), use_container_width=True)
        c4.button("Recuperação", key=f"recover_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Recuperação"), use_container_width=True)
        
        st.markdown("##### Geral e Faltas")
        c1, c2, c3 = st.columns(3)
        c1.button("Perda de Posse", key=f"poss_lost_{key_prefix}_{p}", on_click=record_event, args=("Perda de Posse", team_name, p), use_container_width=True)
        c2.button("Falta Cometida", key=f"foul_c_{key_prefix}_{p}", on_click=record_event, args=("Falta", team_name, p, "Cometida"), use_container_width=True)
        c3.button("Falta Sofrida", key=f"foul_s_{key_prefix}_{p}", on_click=record_event, args=("Falta", team_name, p, "Sofrida"), use_container_width=True)


    with tab1: create_action_buttons(st.session_state.team_a, st.session_state.registered_players_a, "a")
    with tab2: create_action_buttons(st.session_state.team_b, st.session_state.registered_players_b, "b")

# --- Atualização Contínua do Cronômetro ---
if st.session_state.timer_start:
    time.sleep(1)
    st.rerun()
