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
    'possession_team': None,
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
        if st.session_state.possession_team:
            st.session_state.possession_start_time = time.time()

def pause_timer():
    if st.session_state.timer_start:
        st.session_state.paused_time += time.time() - st.session_state.timer_start
        st.session_state.timer_start = None
        update_possession_time()
        st.session_state.possession_start_time = 0

def reset_timer():
    st.session_state.timer_start = None
    st.session_state.paused_time = 0
    st.session_state.match_data = pd.DataFrame(columns=initial_state['match_data'].columns)
    st.session_state.possession_team = None
    st.session_state.possession_start_time = 0
    st.session_state.team_a_possession_seconds = 0.0
    st.session_state.team_b_possession_seconds = 0.0
    st.rerun()

def update_possession_time():
    if st.session_state.possession_team and st.session_state.possession_start_time > 0:
        elapsed = time.time() - st.session_state.possession_start_time
        if st.session_state.possession_team == 'team_a':
            st.session_state.team_a_possession_seconds += elapsed
        elif st.session_state.possession_team == 'team_b':
            st.session_state.team_b_possession_seconds += elapsed
        st.session_state.possession_start_time = time.time()

def set_possession(new_team):
    if st.session_state.timer_start is None:
        st.warning("Inicie o cronômetro para controlar a posse de bola.")
        return
    update_possession_time()
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

def generate_excel_by_player():
    if st.session_state.match_data.empty:
        return io.BytesIO().getvalue()
    df = st.session_state.match_data.copy()
    df['CombinedEvent'] = df.apply(lambda row: ' - '.join(filter(None, [row['Event'], str(row['Type']), str(row['SubType'])])), axis=1)
    player_stats_pivot = pd.pivot_table(
        df, index=['Player', 'Team'], columns='CombinedEvent', aggfunc='size', fill_value=0
    ).reset_index()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        player_stats_pivot.to_excel(writer, index=False, sheet_name='Stats por Jogador')
    return output.getvalue()

# ========== BARRA LATERAL (SIDEBAR) ==========
with st.sidebar:
    st.title("⚙️ Configuração")
    st.header("📋 Cadastro de Equipes e Jogadores")
    st.session_state.team_a = st.text_input("Time da Casa:", st.session_state.team_a)
    st.session_state.team_b = st.text_input("Time Visitante:", st.session_state.team_b)

    with st.expander(f"Jogadores - {st.session_state.team_a}", expanded=True):
        with st.form(f"form_a", clear_on_submit=True):
            col1, col2 = st.columns(2)
            player_num_a = col1.text_input("Nº", key="num_a")
            player_name_a = col2.text_input("Nome", key="name_a")
            if st.form_submit_button(f"Adicionar ao {st.session_state.team_a}", use_container_width=True):
                if player_num_a and player_name_a:
                    if player_num_a not in st.session_state.registered_players_a["Number"].values:
                        new_player = pd.DataFrame([{"Number": player_num_a, "Name": player_name_a}])
                        st.session_state.registered_players_a = pd.concat([st.session_state.registered_players_a, new_player], ignore_index=True)
                    else: st.warning(f"Nº {player_num_a} já existe.")
        st.dataframe(st.session_state.registered_players_a.sort_values(by="Number", key=lambda x: pd.to_numeric(x, errors='coerce')), use_container_width=True, hide_index=True)

    with st.expander(f"Jogadores - {st.session_state.team_b}", expanded=True):
        with st.form(f"form_b", clear_on_submit=True):
            col1, col2 = st.columns(2)
            player_num_b = col1.text_input("Nº", key="num_b")
            player_name_b = col2.text_input("Nome", key="name_b")
            if st.form_submit_button(f"Adicionar ao {st.session_state.team_b}", use_container_width=True):
                if player_num_b and player_name_b:
                    if player_num_b not in st.session_state.registered_players_b["Number"].values:
                        new_player = pd.DataFrame([{"Number": player_num_b, "Name": player_name_b}])
                        st.session_state.registered_players_b = pd.concat([st.session_state.registered_players_b, new_player], ignore_index=True)
                    else: st.warning(f"Nº {player_num_b} já existe.")
        st.dataframe(st.session_state.registered_players_b.sort_values(by="Number", key=lambda x: pd.to_numeric(x, errors='coerce')), use_container_width=True, hide_index=True)

# ========== LAYOUT PRINCIPAL DA INTERFACE ==========
st.title("⚽ Scout Match Tracker")

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

st.markdown("##### Posse de Bola")
update_possession_time()
total_possession = st.session_state.team_a_possession_seconds + st.session_state.team_b_possession_seconds
perc_a = (st.session_state.team_a_possession_seconds / total_possession * 100) if total_possession > 0 else 0
perc_b = (st.session_state.team_b_possession_seconds / total_possession * 100) if total_possession > 0 else 0
team_a_label = f"{st.session_state.team_a} ({perc_a:.0f}%)"
team_b_label = f"{st.session_state.team_b} ({perc_b:.0f}%)"

if st.session_state.possession_team == 'team_a': st.success(f"**Posse: {st.session_state.team_a}**")
elif st.session_state.possession_team == 'team_b': st.info(f"**Posse: {st.session_state.team_b}**")
else: st.warning("**Posse: Bola fora ou em disputa**")

pos_c1, pos_c2, pos_c3 = st.columns(3)
pos_c1.button(team_a_label, key="pos_a", use_container_width=True, on_click=set_possession, args=('team_a',))
pos_c2.button("Bola Fora / Disputa", key="pos_none", use_container_width=True, on_click=set_possession, args=(None,))
pos_c3.button(team_b_label, key="pos_b", use_container_width=True, on_click=set_possession, args=('team_b',))

st.markdown("---")

# --- Painéis de Ações Lado a Lado ---
col_team_a, col_team_b = st.columns(2)

def create_action_buttons(team_name, registered_players, key_prefix):
    """Gera o painel completo de botões de ação para um time."""
    if registered_players.empty:
        st.warning(f"⬅️ Cadastre jogadores para o '{team_name}' na barra lateral.")
        return

    def format_func(player_num):
        player_info = registered_players[registered_players['Number'] == player_num]
        return f"#{player_num} - {player_info['Name'].iloc[0]}" if not player_info.empty else f"#{player_num}"

    selected_player_num = st.selectbox("Selecione o Jogador:", options=registered_players["Number"].tolist(), format_func=format_func, key=f"player_selector_{key_prefix}", label_visibility="collapsed")
    
    if not selected_player_num: return
    p = selected_player_num
    
    st.info(f"**Registrando para: {format_func(p)}**")

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

with col_team_a:
    st.header(f"⚡ Ações: {st.session_state.team_a}")
    create_action_buttons(st.session_state.team_a, st.session_state.registered_players_a, "a")

with col_team_b:
    st.header(f"⚡ Ações: {st.session_state.team_b}")
    create_action_buttons(st.session_state.team_b, st.session_state.registered_players_b, "b")

# --- Seção de Relatórios e Log ---
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

# --- Atualização Contínua do Cronômetro ---
if st.session_state.timer_start:
    time.sleep(1)
    st.rerun()
