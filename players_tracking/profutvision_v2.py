import streamlit as st
import pandas as pd
import time
from datetime import datetime
import io

# --- Inicialização Robusta do st.session_state ---
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

def pause_timer():
    """Pausa o cronômetro da partida."""
    if st.session_state.timer_start:
        st.session_state.paused_time = time.time() - st.session_state.timer_start
        st.session_state.timer_start = None

def reset_timer():
    """Reinicia o cronômetro da partida e todos os eventos registrados."""
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    st.session_state.match_data = pd.DataFrame(columns=[
        "Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"
    ])
    st.rerun()

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
    
    df['CombinedEvent'] = df['Event'].fillna('') + \
                         df['Type'].apply(lambda x: f" - {x}" if x else "") + \
                         df['SubType'].apply(lambda x: f" - {x}" if x else "")

    player_stats_pivot = df.pivot_table(
        index=['Player', 'Team'], 
        columns='CombinedEvent', 
        aggfunc='size', 
        fill_value=0
    )
    
    player_stats_pivot = player_stats_pivot.reset_index()

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
control_col1, control_col2 = st.columns(2)
with control_col1:
    st.session_state.team_a = st.text_input("Nome do Time da Casa:", st.session_state.team_a, key="team_a_name_input")
with control_col2:
    st.session_state.team_b = st.text_input("Nome do Time Visitante:", st.session_state.team_b, key="team_b_name_input")

timer_display_col, timer_controls_col = st.columns([1, 2])
with timer_display_col:
    current_time = get_current_time()
    display_min = int(current_time // 60)
    display_sec = int(current_time % 60)
    st.metric("Tempo de Jogo", f"{display_min}:{display_sec:02d}")
    
with timer_controls_col:
    st.session_state.playback_speed = st.radio("Velocidade do Timer:", [1, 2], horizontal=True, index=0, key="playback_speed_radio")
    timer_col1, timer_col2, timer_col3 = st.columns(3)
    with timer_col1:
        if st.button("⏵ Iniciar", use_container_width=True, key="start_timer_btn") and st.session_state.timer_start is None:
            start_timer()
    with timer_col2:
        if st.button("⏸ Pausar", use_container_width=True, key="pause_timer_btn") and st.session_state.timer_start is not None:
            pause_timer()
    with timer_col3:
        if st.button("↻ Resetar Partida", use_container_width=True, key="reset_match_btn"):
            reset_timer()
            st.rerun()

st.header("⚽ Ações da Partida (Por Jogador)")
player_selection_col1, player_selection_col2 = st.columns(2)

# Coluna de Ações para o Time A
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
        player_num = st.session_state.selected_player_team_a_num
        team_name = st.session_state.team_a
        player_name = st.session_state.registered_players_a[st.session_state.registered_players_a["Number"] == player_num]["Name"].iloc[0]
        st.markdown(f"**Registrando ações para: #{player_num} {player_name}**")

        st.markdown("#### Finalizações")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("No Alvo", key=f"shot_on_a_{player_num}", on_click=record_event, args=("Finalização", team_name, player_num, "No Alvo"))
        with col2:
            st.button("Fora do Alvo", key=f"shot_off_a_{player_num}", on_click=record_event, args=("Finalização", team_name, player_num, "Fora do Alvo"))
        with col3:
            st.button("⚽ Gol", key=f"goal_a_{player_num}", on_click=record_event, args=("Gol", team_name, player_num))
        
        st.markdown("#### Passes")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Curto ✓", key=f"short_pass_a_success_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Certo", "Curto"))
        with col2:
            st.button("Curto ✗", key=f"short_pass_a_fail_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Errado", "Curto"))
        with col3:
            st.button("Longo ✓", key=f"long_pass_a_success_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Certo", "Longo"))
        with col4:
            st.button("Longo ✗", key=f"long_pass_a_fail_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Errado", "Longo"))

        st.markdown("#### Dribles & Perdas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Drible Certo ✓", key=f"drible_success_a_{player_num}", on_click=record_event, args=("Drible", team_name, player_num, "Certo"))
        with col2:
            st.button("Drible Errado ✗", key=f"drible_fail_a_{player_num}", on_click=record_event, args=("Drible", team_name, player_num, "Errado"))
        with col3:
            st.button("Perda de Posse", key=f"possession_lost_a_{player_num}", on_click=record_event, args=("Perda de Posse", team_name, player_num))

        st.markdown("#### Duelos Aéreos")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Vencido", key=f"aerial_won_a_{player_num}", on_click=record_event, args=("Duelo Aéreo", team_name, player_num, "Vencido"))
        with col2:
            st.button("Perdido", key=f"aerial_lost_a_{player_num}", on_click=record_event, args=("Duelo Aéreo", team_name, player_num, "Perdido"))

        st.markdown("#### Ações Defensivas / Outras")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Desarme", key=f"tackle_a_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Desarme"))
            st.button("Interceptação", key=f"interception_a_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Interceptação"))
            st.button("Corte", key=f"clearance_a_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Corte"))
        with col2:
            st.button("Falta Cometida", key=f"foul_committed_a_{player_num}", on_click=record_event, args=("Falta", team_name, player_num, "Cometida"))
            st.button("Falta Sofrida", key=f"foul_suffered_a_{player_num}", on_click=record_event, args=("Falta", team_name, player_num, "Sofrida"))
        with col3:
            st.button("Drible Sofrido", key=f"dribbled_past_a_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Drible Sofrido"))
            st.button("Erro p/ Finalização", key=f"error_shot_a_{player_num}", on_click=record_event, args=("Erro", team_name, player_num, "Erro que levou a finalização"))
    else:
        st.info("Selecione um jogador do Time da Casa para registrar ações.")

# Coluna de Ações para o Time B
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
        player_num = st.session_state.selected_player_team_b_num
        team_name = st.session_state.team_b
        player_name = st.session_state.registered_players_b[st.session_state.registered_players_b["Number"] == player_num]["Name"].iloc[0]
        st.markdown(f"**Registrando ações para: #{player_num} {player_name}**")

        st.markdown("#### Finalizações")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("No Alvo", key=f"shot_on_b_{player_num}", on_click=record_event, args=("Finalização", team_name, player_num, "No Alvo"))
        with col2:
            st.button("Fora do Alvo", key=f"shot_off_b_{player_num}", on_click=record_event, args=("Finalização", team_name, player_num, "Fora do Alvo"))
        with col3:
            st.button("⚽ Gol", key=f"goal_b_{player_num}", on_click=record_event, args=("Gol", team_name, player_num))
        
        st.markdown("#### Passes")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Curto ✓", key=f"short_pass_b_success_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Certo", "Curto"))
        with col2:
            st.button("Curto ✗", key=f"short_pass_b_fail_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Errado", "Curto"))
        with col3:
            st.button("Longo ✓", key=f"long_pass_b_success_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Certo", "Longo"))
        with col4:
            st.button("Longo ✗", key=f"long_pass_b_fail_{player_num}", on_click=record_event, args=("Passe", team_name, player_num, "Errado", "Longo"))

        st.markdown("#### Dribles & Perdas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Drible Certo ✓", key=f"drible_success_b_{player_num}", on_click=record_event, args=("Drible", team_name, player_num, "Certo"))
        with col2:
            st.button("Drible Errado ✗", key=f"drible_fail_b_{player_num}", on_click=record_event, args=("Drible", team_name, player_num, "Errado"))
        with col3:
            st.button("Perda de Posse", key=f"possession_lost_b_{player_num}", on_click=record_event, args=("Perda de Posse", team_name, player_num))

        st.markdown("#### Duelos Aéreos")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Vencido", key=f"aerial_won_b_{player_num}", on_click=record_event, args=("Duelo Aéreo", team_name, player_num, "Vencido"))
        with col2:
            st.button("Perdido", key=f"aerial_lost_b_{player_num}", on_click=record_event, args=("Duelo Aéreo", team_name, player_num, "Perdido"))

        st.markdown("#### Ações Defensivas / Outras")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Desarme", key=f"tackle_b_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Desarme"))
            st.button("Interceptação", key=f"interception_b_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Interceptação"))
            st.button("Corte", key=f"clearance_b_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Corte"))
        with col2:
            st.button("Falta Cometida", key=f"foul_committed_b_{player_num}", on_click=record_event, args=("Falta", team_name, player_num, "Cometida"))
            st.button("Falta Sofrida", key=f"foul_suffered_b_{player_num}", on_click=record_event, args=("Falta", team_name, player_num, "Sofrida"))
        with col3:
            st.button("Drible Sofrido", key=f"dribbled_past_b_{player_num}", on_click=record_event, args=("Defesa", team_name, player_num, "Drible Sofrido"))
            st.button("Erro p/ Finalização", key=f"error_shot_b_{player_num}", on_click=record_event, args=("Erro", team_name, player_num, "Erro que levou a finalização"))
    else:
        st.info("Selecione um jogador do Time Visitante para registrar ações.")

# Seção de Relatórios de Dados
st.header("📊 Relatório da Partida")
if not st.session_state.match_data.empty:
    st.dataframe(st.session_state.match_data.sort_values(["Minute", "Second"]), use_container_width=True)
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
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

if st.session_state.timer_start:
    time.sleep(1)
    st.rerun()
