import streamlit as st
import pandas as pd
import time
from datetime import datetime
import io  # Importado para lidar com a exportação para Excel em memória

# --- Inicialização Robusta do st.session_state ---
# Cada variável é verificada individualmente para garantir que exista
# Isso resolve o AttributeError que estava acontecendo em certas reruns do Streamlit
if 'match_data' not in st.session_state:
    st.session_state.match_data = pd.DataFrame(columns=[
        "Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"
    ])

if 'team_a' not in st.session_state:
    st.session_state.team_a = "Time A"

if 'team_b' not in st.session_state:
    st.session_state.team_b = "Time B"

if 'timer_start' not in st.session_state:
    st.session_state.timer_start = None

if 'paused_time' not in st.session_state:
    st.session_state.paused_time = 0

if 'playback_speed' not in st.session_state:
    st.session_state.playback_speed = 1

if 'current_possession' not in st.session_state:
    st.session_state.current_possession = None

if 'possession_start' not in st.session_state:
    st.session_state.possession_start = None

if 'possession_log' not in st.session_state:
    st.session_state.possession_log = []

if 'registered_players_a' not in st.session_state:
    st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"])

if 'registered_players_b' not in st.session_state:
    st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"])

if 'selected_player_team_a_num' not in st.session_state:
    st.session_state.selected_player_team_a_num = None

if 'selected_player_team_b_num' not in st.session_state:
    st.session_state.selected_player_team_b_num = None
# --- Fim da Inicialização ---


# ========== DEFINIÇÕES DE FUNÇÕES ==========
def get_current_time():
    """Calcula e retorna o tempo atual da partida."""
    if st.session_state.timer_start is None:
        return st.session_state.paused_time * st.session_state.playback_speed
    return (time.time() - st.session_state.timer_start) * st.session_state.playback_speed

def start_timer():
    """Inicia ou retoma o cronômetro da partida."""
    st.session_state.timer_start = time.time() - st.session_state.paused_time
    if st.session_state.current_possession and not st.session_state.possession_start:
        st.session_state.possession_start = time.time()

def pause_timer():
    """Pausa o cronômetro da partida e registra a duração da posse atual."""
    if st.session_state.timer_start:
        st.session_state.paused_time = time.time() - st.session_state.timer_start
        st.session_state.timer_start = None
        log_possession_duration()

def reset_timer():
    """Reinicia o cronômetro da partida, dados de posse e todos os eventos registrados.
    Não reinicia os jogadores cadastrados por padrão, permitindo que persistam entre as partidas."""
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    st.session_state.possession_log = []
    st.session_state.current_possession = None
    st.session_state.possession_start = None
    st.session_state.match_data = pd.DataFrame(columns=[
        "Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"
    ])
    st.rerun()

def log_possession_duration():
    """Registra a duração da posse atual para o time ativo."""
    if st.session_state.current_possession and st.session_state.possession_start:
        duration = time.time() - st.session_state.possession_start
        st.session_state.possession_log.append({
            "Team": st.session_state.current_possession,
            "Start": st.session_state.possession_start,
            "Duration": duration
        })
        st.session_state.possession_start = time.time() if st.session_state.timer_start else None

def set_possession(team):
    """Define a posse atual para o time especificado."""
    log_possession_duration()
    st.session_state.current_possession = team
    st.session_state.possession_start = time.time() if st.session_state.timer_start else None
    st.rerun()

def calculate_possession():
    """Calcula e retorna as porcentagens de posse para ambos os times."""
    team_a_time = sum([p["Duration"] for p in st.session_state.possession_log if p["Team"] == st.session_state.team_a])
    team_b_time = sum([p["Duration"] for p in st.session_state.possession_log if p["Team"] == st.session_state.team_b])
    
    if st.session_state.timer_start and st.session_state.current_possession and st.session_state.possession_start:
        current_duration = time.time() - st.session_state.possession_start
        if st.session_state.current_possession == st.session_state.team_a:
            team_a_time += current_duration
        else:
            team_b_time += current_duration
            
    total_time = team_a_time + team_b_time
    if total_time > 0:
        return (team_a_time/total_time)*100, (team_b_time/total_time)*100
    return 0, 0

def record_event(event, team, player_number, event_type="", subtype=""):
    """Registra um novo evento no DataFrame de dados da partida."""
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)
    
    player_name = ""
    if team == st.session_state.team_a:
        player_row = st.session_state.registered_players_a[st.session_state.registered_players_a["Number"] == player_number]
        if not player_row.empty:
            player_name = player_row["Name"].iloc[0]
    else:
        player_row = st.session_state.registered_players_b[st.session_state.registered_players_b["Number"] == player_number]
        if not player_row.empty:
            player_name = player_row["Name"].iloc[0]
            
    full_player_display = f"#{player_number} {player_name}" if player_name else f"#{player_number} (Nome não encontrado)"

    new_event = {
        "Event": event,
        "Minute": minute,
        "Second": second,
        "Team": team,
        "Player": full_player_display,
        "Type": event_type,
        "SubType": subtype,
        "Timestamp": time.time()
    }
    
    st.session_state.match_data = pd.concat(
        [st.session_state.match_data, pd.DataFrame([new_event])],
        ignore_index=True
    )
    st.rerun()

def generate_excel_by_player():
    """Gera um arquivo Excel com estatísticas agregadas por jogador."""
    df = st.session_state.match_data.copy()
    
    # Criar uma coluna de evento combinado para usar como colunas no pivot
    df['CombinedEvent'] = df['Event'].fillna('') + \
                         df['Type'].apply(lambda x: f" - {x}" if x else "") + \
                         df['SubType'].apply(lambda x: f" - {x}" if x else "")

    # Usar pivot_table para transformar os dados
    # Cada jogador se torna uma linha, cada evento combinado uma coluna
    player_stats_pivot = df.pivot_table(
        index=['Player', 'Team'], 
        columns='CombinedEvent', 
        aggfunc='size', 
        fill_value=0
    )
    
    # Resetar o índice para que 'Player' e 'Team' se tornem colunas
    player_stats_pivot = player_stats_pivot.reset_index()

    # Criar um buffer de bytes para o arquivo Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        player_stats_pivot.to_excel(writer, index=False, sheet_name='Stats por Jogador')
    
    return output.getvalue()


# ========== INTERFACE DO USUÁRIO: SEÇÃO DE CADASTRO DE JOGADORES ==========
def player_registration_section():
    st.header("📋 Cadastro de Jogadores")
    registration_col1, registration_col2 = st.columns(2)

    with registration_col1:
        st.subheader(f"{st.session_state.team_a} - Cadastro")
        player_num_a = st.text_input("Número do Jogador (Time A):", key="player_num_a_input")
        player_name_a = st.text_input("Nome do Jogador (Time A):", key="player_name_a_input")
        if st.button(f"Adicionar Jogador ao {st.session_state.team_a}", key="add_player_a_btn"):
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
            st.dataframe(st.session_state.registered_players_a.sort_values(by="Number", key=lambda x: x.astype(int)), use_container_width=True)
            if st.button(f"Limpar Jogadores de {st.session_state.team_a}", key="clear_players_a_btn"):
                st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"])
                st.rerun()
        else:
            st.info("Nenhum jogador cadastrado para o Time A.")

    with registration_col2:
        st.subheader(f"{st.session_state.team_b} - Cadastro")
        player_num_b = st.text_input("Número do Jogador (Time B):", key="player_num_b_input")
        player_name_b = st.text_input("Nome do Jogador (Time B):", key="player_name_b_input")
        if st.button(f"Adicionar Jogador ao {st.session_state.team_b}", key="add_player_b_btn"):
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
            st.dataframe(st.session_state.registered_players_b.sort_values(by="Number", key=lambda x: x.astype(int)), use_container_width=True)
            if st.button(f"Limpar Jogadores de {st.session_state.team_b}", key="clear_players_b_btn"):
                st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"])
                st.rerun()
        else:
            st.info("Nenhum jogador cadastrado para o Time B.")
    
    st.markdown("---")

# ========== LAYOUT DA INTERFACE DO USUÁRIO STREAMLIT ==========
st.set_page_config(layout="wide", page_title="Football Match Tracker")
st.title("⚽ Football Match Tracker")

player_registration_section()

st.header("⚙️ Controles da Partida")
control_col1, control_col2, control_col3 = st.columns([2,2,3])
with control_col1:
    st.session_state.team_a = st.text_input("Nome do Time da Casa:", st.session_state.team_a, key="team_a_name_input")
with control_col2:
    st.session_state.team_b = st.text_input("Nome do Time Visitante:", st.session_state.team_b, key="team_b_name_input")
with control_col3:
    st.session_state.playback_speed = st.radio("Velocidade do Timer:", [1, 2], horizontal=True, index=0, key="playback_speed_radio")
    timer_col1, timer_col2, timer_col3 = st.columns(3)
    with timer_col1:
        if st.button("⏵ Iniciar", use_container_width=True, key="start_timer_btn") and st.session_state.timer_start is None:
            start_timer()
    with timer_col2:
        if st.button("⏸ Pausar", use_container_width=True, key="pause_timer_btn") and st.session_state.timer_start is not None:
            pause_timer()
    with timer_col3:
        if st.button("↻ Resetar Tudo", use_container_width=True, key="reset_all_btn"):
            reset_timer()
            st.session_state.registered_players_a = pd.DataFrame(columns=["Number", "Name"])
            st.session_state.registered_players_b = pd.DataFrame(columns=["Number", "Name"])
            st.rerun()

time_col, poss_col_a, poss_col_b = st.columns([2,1,1])
with time_col:
    current_time = get_current_time()
    display_min = int(current_time // 60)
    display_sec = int(current_time % 60)
    st.metric("Tempo de Jogo", f"{display_min}:{display_sec:02d}")

team_a_poss, team_b_poss = calculate_possession()
with poss_col_a:
    if st.button(f"🏃 Posse de {st.session_state.team_a}", use_container_width=True, key="poss_a_btn"):
        set_possession(st.session_state.team_a)
    st.metric(f"Posse {st.session_state.team_a}", f"{team_a_poss:.1f}%")
with poss_col_b:
    if st.button(f"🏃 Posse de {st.session_state.team_b}", use_container_width=True, key="poss_b_btn"):
        set_possession(st.session_state.team_b)
    st.metric(f"Posse {st.session_state.team_b}", f"{team_b_poss:.1f}%")

st.header("⚽ Ações da Partida (Por Jogador)")
player_selection_col1, player_selection_col2 = st.columns(2)

with player_selection_col1:
    st.markdown(f"### {st.session_state.team_a} - Ações")
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

        # NOVA SEÇÃO: DRIBLES E PERDAS
        st.markdown("#### Dribles & Perdas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Drible Certo ✓", key=f"drible_success_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Drible", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Certo"))
        with col2:
            st.button("Drible Errado ✗", key=f"drible_fail_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Drible", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Errado"))
        with col3:
            st.button("Perda de Posse", key=f"possession_lost_a_{st.session_state.selected_player_team_a_num}", 
                      on_click=record_event, args=("Perda de Posse", st.session_state.team_a, st.session_state.selected_player_team_a_num))

        st.markdown("#### Ações Defensivas / Outras")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Desarme", key=f"tackle_a_{st.session_state.selected_player_team_a_num}", on_click=record_event, args=("Defesa", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Desarme"))
        with col2:
            st.button("Interceptação", key=f"interception_a_{st.session_state.selected_player_team_a_num}", on_click=record_event, args=("Defesa", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Interceptação"))
        with col3:
            st.button("Falta Cometida", key=f"foul_committed_a_{st.session_state.selected_player_team_a_num}", on_click=record_event, args=("Falta", st.session_state.team_a, st.session_state.selected_player_team_a_num, "Cometida"))

    else:
        st.info("Selecione um jogador do Time da Casa para registrar ações.")

with player_selection_col2:
    st.markdown(f"### {st.session_state.team_b} - Ações")
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

        # NOVA SEÇÃO: DRIBLES E PERDAS
        st.markdown("#### Dribles & Perdas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Drible Certo ✓", key=f"drible_success_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Drible", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Certo"))
        with col2:
            st.button("Drible Errado ✗", key=f"drible_fail_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Drible", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Errado"))
        with col3:
            st.button("Perda de Posse", key=f"possession_lost_b_{st.session_state.selected_player_team_b_num}", 
                      on_click=record_event, args=("Perda de Posse", st.session_state.team_b, st.session_state.selected_player_team_b_num))

        st.markdown("#### Ações Defensivas / Outras")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Desarme", key=f"tackle_b_{st.session_state.selected_player_team_b_num}", on_click=record_event, args=("Defesa", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Desarme"))
        with col2:
            st.button("Interceptação", key=f"interception_b_{st.session_state.selected_player_team_b_num}", on_click=record_event, args=("Defesa", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Interceptação"))
        with col3:
            st.button("Falta Cometida", key=f"foul_committed_b_{st.session_state.selected_player_team_b_num}", on_click=record_event, args=("Falta", st.session_state.team_b, st.session_state.selected_player_team_b_num, "Cometida"))

    else:
        st.info("Selecione um jogador do Time Visitante para registrar ações.")

# 5. Seção de Relatórios de Dados
st.header("📊 Relatório da Partida")
if not st.session_state.match_data.empty:
    st.dataframe(st.session_state.match_data.sort_values(["Minute", "Second"]), use_container_width=True)
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        # Botão para exportar o log de eventos brutos (como antes)
        csv_full = st.session_state.match_data.to_csv(index=False).encode('utf-8')
        st.download_button(
           label="Exportar Log de Eventos (CSV)",
           data=csv_full,
           file_name=f"log_eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
           mime="text/csv",
           key="export_full_csv_btn",
           use_container_width=True
        )

    with export_col2:
        # NOVO BOTÃO: Exportar para Excel com dados por jogador
        excel_data = generate_excel_by_player()
        st.download_button(
            label="Exportar para Excel (por Jogador)",
            data=excel_data,
            file_name=f"relatorio_por_jogador_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="export_excel_player_stats_btn",
            use_container_width=True
        )

else:
    st.info("Nenhum evento registrado ainda. Cadastre jogadores e inicie o tracking!")

# Auto-atualização para o timer a cada segundo se estiver rodando
if st.session_state.timer_start:
    time.sleep(1)
    st.rerun()
