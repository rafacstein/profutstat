import streamlit as st
import pandas as pd
import time
from datetime import datetime
import io

# --- Configuração da Página e Inicialização Robusta do st.session_state ---
st.set_page_config(layout="wide", page_title="Scout Match Tracker")

# Dicionário para inicialização limpa do session_state
initial_state = {
    'match_data': pd.DataFrame(columns=["Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp"]),
    'team_a': "Time A",
    'team_b': "Time B",
    'timer_start': None,
    'paused_time': 0,
    'playback_speed': 1,
    'registered_players_a': pd.DataFrame(columns=["Number", "Name"]),
    'registered_players_b': pd.DataFrame(columns=["Number", "Name"]),
    'youtube_url': ""
}

for key, value in initial_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ========== FUNÇÕES PRINCIPAIS (CORE) ==========
def get_current_time():
    """Calcula e retorna o tempo de partida decorrido."""
    if st.session_state.timer_start is None:
        return st.session_state.paused_time
    return time.time() - st.session_state.timer_start + st.session_state.paused_time

def start_timer():
    """Inicia ou retoma o cronômetro."""
    if st.session_state.timer_start is None:
        st.session_state.timer_start = time.time()

def pause_timer():
    """Pausa o cronômetro."""
    if st.session_state.timer_start:
        st.session_state.paused_time += time.time() - st.session_state.timer_start
        st.session_state.timer_start = None

def reset_timer():
    """Reseta o cronômetro e todos os dados da partida."""
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    st.session_state.match_data = pd.DataFrame(columns=initial_state['match_data'].columns)
    st.rerun()

def record_event(event, team, player_number, event_type="", subtype=""):
    """Registra um evento de jogo para um jogador."""
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)

    # Identifica o time e busca o nome do jogador
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

def generate_excel_by_player():
    """Gera um arquivo Excel com estatísticas agregadas por jogador."""
    if st.session_state.match_data.empty:
        return io.BytesIO().getvalue()
        
    df = st.session_state.match_data.copy()
    # Concatena Event, Type e SubType para criar uma coluna de evento combinado
    df['CombinedEvent'] = df.apply(lambda row: ' - '.join(filter(None, [row['Event'], str(row['Type']), str(row['SubType'])])), axis=1)

    player_stats_pivot = pd.pivot_table(
        df, index=['Player', 'Team'], columns='CombinedEvent', aggfunc='size', fill_value=0
    ).reset_index()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        player_stats_pivot.to_excel(writer, index=False, sheet_name='Stats por Jogador')
    
    return output.getvalue()

# ========== INTERFACE DO USUÁRIO: BARRA LATERAL (SIDEBAR) ==========
with st.sidebar:
    st.title("⚙️ Configuração")
    
    st.header("📺 Vídeo da Partida")
    st.session_state.youtube_url = st.text_input("Cole o link do YouTube aqui:", placeholder="https://www.youtube.com/watch?v=...")

    st.header("📋 Cadastro")
    st.session_state.team_a = st.text_input("Time da Casa:", st.session_state.team_a)
    st.session_state.team_b = st.text_input("Time Visitante:", st.session_state.team_b)

    # Formulários de cadastro em expanders para economizar espaço
    with st.expander(f"Jogadores - {st.session_state.team_a}"):
        with st.form(f"form_a", clear_on_submit=True):
            col1, col2 = st.columns(2)
            player_num_a = col1.text_input("Nº", key="num_a")
            player_name_a = col2.text_input("Nome", key="name_a")
            submitted = st.form_submit_button(f"Adicionar ao {st.session_state.team_a}", use_container_width=True)
            if submitted and player_num_a and player_name_a:
                if player_num_a not in st.session_state.registered_players_a["Number"].values:
                    new_player = pd.DataFrame([{"Number": player_num_a, "Name": player_name_a}])
                    st.session_state.registered_players_a = pd.concat([st.session_state.registered_players_a, new_player], ignore_index=True)
                else:
                    st.warning(f"Nº {player_num_a} já existe.")
        st.dataframe(st.session_state.registered_players_a.sort_values(by="Number", key=lambda x: pd.to_numeric(x, errors='coerce')), use_container_width=True, hide_index=True)

    with st.expander(f"Jogadores - {st.session_state.team_b}"):
        with st.form(f"form_b", clear_on_submit=True):
            col1, col2 = st.columns(2)
            player_num_b = col1.text_input("Nº", key="num_b")
            player_name_b = col2.text_input("Nome", key="name_b")
            submitted = st.form_submit_button(f"Adicionar ao {st.session_state.team_b}", use_container_width=True)
            if submitted and player_num_b and player_name_b:
                if player_num_b not in st.session_state.registered_players_b["Number"].values:
                    new_player = pd.DataFrame([{"Number": player_num_b, "Name": player_name_b}])
                    st.session_state.registered_players_b = pd.concat([st.session_state.registered_players_b, new_player], ignore_index=True)
                else:
                    st.warning(f"Nº {player_num_b} já existe.")
        st.dataframe(st.session_state.registered_players_b.sort_values(by="Number", key=lambda x: pd.to_numeric(x, errors='coerce')), use_container_width=True, hide_index=True)

# ========== LAYOUT PRINCIPAL DA INTERFACE ==========
st.title("⚽ Scout Match Tracker")

main_col1, main_col2 = st.columns([0.6, 0.4]) # 60% da tela para o vídeo, 40% para as ações

# --- Coluna da Esquerda: Vídeo e Cronômetro ---
with main_col1:
    if st.session_state.youtube_url:
        st.video(st.session_state.youtube_url)
    else:
        st.info("⬅️ Para começar, cole um link do YouTube na barra lateral.")

    # Controles do Cronômetro
    current_time = get_current_time()
    display_min = int(current_time // 60)
    display_sec = int(current_time % 60)

    timer_display_col, timer_controls_col = st.columns([1, 3])
    timer_display_col.metric("Tempo", f"{display_min}:{display_sec:02d}")
    
    with timer_controls_col:
        btn_cols = st.columns(3)
        btn_cols[0].button("▶️ Iniciar", use_container_width=True, on_click=start_timer, disabled=st.session_state.timer_start is not None)
        btn_cols[1].button("⏸️ Pausar", use_container_width=True, on_click=pause_timer, disabled=st.session_state.timer_start is None)
        btn_cols[2].button("🔄 Resetar", use_container_width=True, on_click=reset_timer)

# --- Coluna da Direita: Abas de Ações ---
with main_col2:
    st.header("⚡ Ações da Partida")
    
    tab1, tab2 = st.tabs([f"Ações: {st.session_state.team_a}", f"Ações: {st.session_state.team_b}"])

    def create_action_buttons(team_name, registered_players, key_prefix):
        """Função para gerar a interface de botões de ação para um time."""
        if registered_players.empty:
            st.warning(f"⬅️ Cadastre jogadores para o '{team_name}' na barra lateral.")
            return

        def format_func(player_num):
            player_info = registered_players[registered_players['Number'] == player_num]
            return f"#{player_num} - {player_info['Name'].iloc[0]}" if not player_info.empty else f"#{player_num}"

        selected_player_num = st.selectbox("Selecione o Jogador:", options=registered_players["Number"].tolist(), format_func=format_func, key=f"player_selector_{key_prefix}")
        
        if not selected_player_num: return

        p = selected_player_num # Alias para encurtar
        st.markdown(f"**Registrando para: {format_func(p)}**")
        
        st.markdown("##### Finalização e Gol")
        c1, c2, c3 = st.columns(3)
        c1.button("No Alvo", key=f"son_{key_prefix}_{p}", on_click=record_event, args=("Finalização", team_name, p, "No Alvo"), use_container_width=True)
        c2.button("Fora", key=f"soff_{key_prefix}_{p}", on_click=record_event, args=("Finalização", team_name, p, "Fora do Alvo"), use_container_width=True)
        c3.button("⚽ Gol", key=f"goal_{key_prefix}_{p}", on_click=record_event, args=("Gol", team_name, p), use_container_width=True)

        st.markdown("##### Passes")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("Curto ✓", key=f"psc_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Certo", "Curto"), use_container_width=True)
        c2.button("Curto ✗", key=f"psf_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Errado", "Curto"), use_container_width=True)
        c3.button("Longo ✓", key=f"plg_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Certo", "Longo"), use_container_width=True)
        c4.button("Longo ✗", key=f"plf_{key_prefix}_{p}", on_click=record_event, args=("Passe", team_name, p, "Errado", "Longo"), use_container_width=True)
        
        st.markdown("##### Duelos e Faltas")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("Drible ✓", key=f"drs_{key_prefix}_{p}", on_click=record_event, args=("Drible", team_name, p, "Certo"), use_container_width=True)
        c2.button("Perda Posse", key=f"pl_{key_prefix}_{p}", on_click=record_event, args=("Perda de Posse", team_name, p), use_container_width=True)
        c3.button("Falta Cometida", key=f"fc_{key_prefix}_{p}", on_click=record_event, args=("Falta", team_name, p, "Cometida"), use_container_width=True)
        c4.button("Falta Sofrida", key=f"fs_{key_prefix}_{p}", on_click=record_event, args=("Falta", team_name, p, "Sofrida"), use_container_width=True)

        st.markdown("##### Ações Defensivas")
        c1, c2, c3 = st.columns(3)
        c1.button("Desarme", key=f"tkl_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Desarme"), use_container_width=True)
        c2.button("Interceptação", key=f"int_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Interceptação"), use_container_width=True)
        c3.button("Corte", key=f"clr_{key_prefix}_{p}", on_click=record_event, args=("Defesa", team_name, p, "Corte"), use_container_width=True)

    with tab1: create_action_buttons(st.session_state.team_a, st.session_state.registered_players_a, "a")
    with tab2: create_action_buttons(st.session_state.team_b, st.session_state.registered_players_b, "b")

# --- Seção de Relatórios e Log (Oculta por padrão) ---
with st.expander("📊 Ver Log de Eventos e Exportar Dados"):
    if not st.session_state.match_data.empty:
        st.dataframe(st.session_state.match_data.sort_values(["Minute", "Second"], ascending=[False, False]), use_container_width=True, hide_index=True)
        
        export_col1, export_col2 = st.columns(2)
        csv_full = st.session_state.match_data.to_csv(index=False).encode('utf-8')
        export_col1.download_button("Exportar Log (CSV)", csv_full, f"log_eventos_{datetime.now():%Y%m%d_%H%M%S}.csv", "text/csv", use_container_width=True)
        
        excel_data = generate_excel_by_player()
        export_col2.download_button("Exportar Stats (Excel)", excel_data, f"relatorio_jogador_{datetime.now():%Y%m%d_%H%M%S}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.info("Nenhum evento registrado ainda.")

# --- Lógica de Rerun para o Cronômetro (executa a cada segundo se o timer estiver ativo) ---
if st.session_state.timer_start:
    time.sleep(1)
    st.rerun()
