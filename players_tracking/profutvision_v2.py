import streamlit as st
import pandas as pd
import time
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA E INICIALIZAÇÃO DO ESTADO ---
st.set_page_config(layout="wide", page_title="Scout Match Tracker (Um Time)")

# Dicionário para inicialização limpa e completa do session_state
initial_state = {
    'match_data': pd.DataFrame(columns=["Event", "Minute", "Second", "Team", "Player", "Type", "SubType", "Timestamp", "Observation"]),
    'main_team_name': "Meu Time", # Renomeado para 'main_team_name'
    'opponent_team_name': "Time Oponente", # Adicionado para referência, mas sem funcionalidade ativa de scout
    'timer_start': None,
    'paused_time': 0,
    'registered_players': pd.DataFrame(columns=["Number", "Name"]), # Apenas um set de jogadores
    'possession_team_active': None, # 'main_team' ou None (para bola fora/disputa)
    'possession_start_time': 0,
    'main_team_possession_seconds': 0.0,
    'match_observations': [] # Para observações gerais
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
        if st.session_state.possession_team_active: # Inicia posse se já estiver definida
            st.session_state.possession_start_time = time.time()

def pause_timer():
    if st.session_state.timer_start:
        st.session_state.paused_time += time.time() - st.session_state.timer_start
        st.session_state.timer_start = None
        update_possession_time()
        st.session_state.possession_start_time = 0

def reset_timer():
    for key, value in initial_state.items():
        st.session_state[key] = value # Reseta todo o session_state para os valores iniciais
    st.rerun()

def update_possession_time():
    if st.session_state.possession_team_active and st.session_state.possession_start_time > 0 and st.session_state.timer_start is not None:
        elapsed = time.time() - st.session_state.possession_start_time
        st.session_state.main_team_possession_seconds += elapsed
        st.session_state.possession_start_time = time.time()

def set_possession(new_team_state):
    if st.session_state.timer_start is None:
        st.warning("Inicie o cronômetro para controlar a posse de bola.")
        return
    update_possession_time() # Atualiza posse antes de mudar
    st.session_state.possession_team_active = new_team_state
    if new_team_state is not None: # Se a posse foi para o time principal
        st.session_state.possession_start_time = time.time()
    else: # Se a posse é neutra
        st.session_state.possession_start_time = 0

def record_event(event, player_number, event_type="", subtype="", observation=""):
    current_time = get_current_time()
    minute = int(current_time // 60)
    second = int(current_time % 60)
    
    player_row = st.session_state.registered_players[st.session_state.registered_players["Number"] == player_number]
    player_name = player_row["Name"].iloc[0] if not player_row.empty else "(não cadastrado)"
    full_player_display = f"#{player_number} {player_name}"

    new_event = {
        "Event": event, "Minute": minute, "Second": second, "Team": st.session_state.main_team_name,
        "Player": full_player_display, "Type": event_type, "SubType": subtype,
        "Timestamp": datetime.now(), "Observation": observation
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
    
    # Adicionando 'Observation' ao DataFrame para exportação, mas não no pivot de stats por evento
    df_export = df[['Minute', 'Second', 'Team', 'Player', 'CombinedEvent', 'Observation', 'Timestamp']]
    
    player_stats_pivot = pd.pivot_table(
        df, index=['Player', 'Team'], columns='CombinedEvent', aggfunc='size', fill_value=0
    ).reset_index()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Log Completo de Eventos')
        player_stats_pivot.to_excel(writer, index=False, sheet_name='Stats por Jogador')
    return output.getvalue()

# ========== BARRA LATERAL (SIDEBAR) ==========
with st.sidebar:
    st.title("⚙️ Configuração")
    st.header("📋 Cadastro de Equipe e Jogadores")
    st.session_state.main_team_name = st.text_input("Nome do Time:", st.session_state.main_team_name)
    st.session_state.opponent_team_name = st.text_input("Nome do Time Oponente:", st.session_state.opponent_team_name)


    with st.expander(f"Jogadores - {st.session_state.main_team_name}", expanded=True):
        with st.form(f"form_players", clear_on_submit=True):
            col1, col2 = st.columns(2)
            player_num = col1.text_input("Nº", key="num_player")
            player_name = col2.text_input("Nome", key="name_player")
            if st.form_submit_button(f"Adicionar Jogador", use_container_width=True):
                if player_num and player_name:
                    if player_num not in st.session_state.registered_players["Number"].values:
                        new_player = pd.DataFrame([{"Number": player_num, "Name": player_name}])
                        st.session_state.registered_players = pd.concat([st.session_state.registered_players, new_player], ignore_index=True)
                    else: st.warning(f"Nº {player_num} já existe.")
        st.dataframe(st.session_state.registered_players.sort_values(by="Number", key=lambda x: pd.to_numeric(x, errors='coerce')), use_container_width=True, hide_index=True)

# ========== LAYOUT PRINCIPAL DA INTERFACE ==========
st.title("⚽ Scout Match Tracker (Um Time)")

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
update_possession_time() # Garante que a posse é atualizada antes de exibir
total_game_time = max(1, current_time) # Evita divisão por zero
perc_main_team = (st.session_state.main_team_possession_seconds / total_game_time * 100) if total_game_time > 0 else 0
perc_opponent_team = 100 - perc_main_team

col_pos1, col_pos2, col_pos3 = st.columns(3)
col_pos1.metric(f"Posse {st.session_state.main_team_name}", f"{perc_main_team:.0f}%", delta_color="off")
col_pos2.metric(f"Posse {st.session_state.opponent_team_name}", f"{perc_opponent_team:.0f}%", delta_color="off")
col_pos3.empty() # Placeholder para balancear

pos_btn_c1, pos_btn_c2 = st.columns(2)
pos_btn_c1.button(f"Posse: {st.session_state.main_team_name}", key="pos_main", use_container_width=True, on_click=set_possession, args=('main_team',), type="primary" if st.session_state.possession_team_active == 'main_team' else "secondary")
pos_btn_c2.button("Posse: Oponente / Disputa", key="pos_none", use_container_width=True, on_click=set_possession, args=(None,), type="secondary" if st.session_state.possession_team_active == 'main_team' else "primary")

st.markdown("---")

# --- Painel de Ações do Time Principal ---
st.header(f"⚡ Ações: {st.session_state.main_team_name}")

if st.session_state.registered_players.empty:
    st.warning(f"⬅️ Cadastre jogadores para o '{st.session_state.main_team_name}' na barra lateral para começar a registrar eventos.")
else:
    def format_func_player(player_num):
        player_info = st.session_state.registered_players[st.session_state.registered_players['Number'] == player_num]
        return f"#{player_num} - {player_info['Name'].iloc[0]}" if not player_info.empty else f"#{player_num}"

    selected_player_num = st.selectbox("Selecione o Jogador:", options=st.session_state.registered_players["Number"].tolist(), format_func=format_func_player, key=f"player_selector_main")
    
    if selected_player_num:
        st.info(f"**Registrando para: {format_func_player(selected_player_num)}**")
        p = selected_player_num
        
        st.markdown("##### Finalização e Criação")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.button("Gol ⚽", key=f"goal_{p}", on_click=record_event, args=("Gol", p), use_container_width=True)
        c2.button("Chute G.", key=f"shot_on_{p}", on_click=record_event, args=("Finalização", p, "No Alvo"), use_container_width=True)
        c3.button("Chute F.", key=f"shot_off_{p}", on_click=record_event, args=("Finalização", p, "Fora do Alvo"), use_container_width=True)
        c4.button("Assist.", key=f"assist_{p}", on_click=record_event, args=("Assistência", p), use_container_width=True)
        c5.button("Passe Chave", key=f"keypass_{p}", on_click=record_event, args=("Passe", p, "Chave"), use_container_width=True)

        st.markdown("##### Passes")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("Curto ✓", key=f"p_c_ok_{p}", on_click=record_event, args=("Passe", p, "Certo", "Curto"), use_container_width=True)
        c2.button("Curto ✗", key=f"p_c_er_{p}", on_click=record_event, args=("Passe", p, "Errado", "Curto"), use_container_width=True)
        c3.button("Longo ✓", key=f"p_l_ok_{p}", on_click=record_event, args=("Passe", p, "Certo", "Longo"), use_container_width=True)
        c4.button("Longo ✗", key=f"p_l_er_{p}", on_click=record_event, args=("Passe", p, "Errado", "Longo"), use_container_width=True)
        
        st.markdown("##### Cruzamentos e Duelos")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.button("Cruz. ✓", key=f"cruz_ok_{p}", on_click=record_event, args=("Cruzamento", p, "Certo"), use_container_width=True)
        c2.button("Cruz. ✗", key=f"cruz_er_{p}", on_click=record_event, args=("Cruzamento", p, "Errado"), use_container_width=True)
        c3.button("Duelo Aéreo ✓", key=f"aer_ok_{p}", on_click=record_event, args=("Duelo Aéreo", p, "Ganho"), use_container_width=True)
        c4.button("Duelo Aéreo ✗", key=f"aer_er_{p}", on_click=record_event, args=("Duelo Aéreo", p, "Perdido"), use_container_width=True)
        c5.button("Duelo Chão", key=f"duel_ground_{p}", on_click=record_event, args=("Duelo (Chão)", p), use_container_width=True) # Novo botão de duelo

        st.markdown("##### Dribles")
        c1, c2, c3 = st.columns(3)
        c1.button("Drible Certo ✓", key=f"drib_ok_{p}", on_click=record_event, args=("Drible", p, "Certo"), use_container_width=True)
        c2.button("Drible Errado ✗", key=f"drib_er_{p}", on_click=record_event, args=("Drible", p, "Errado"), use_container_width=True)
        c3.button("Drible Sofrido", key=f"drib_past_{p}", on_click=record_event, args=("Defesa", p, "Drible Sofrido"), use_container_width=True)

        st.markdown("##### Ações Defensivas")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.button("Desarme", key=f"tackle_{p}", on_click=record_event, args=("Defesa", p, "Desarme"), use_container_width=True)
        c2.button("Intercept.", key=f"intercept_{p}", on_click=record_event, args=("Defesa", p, "Interceptação"), use_container_width=True)
        c3.button("Corte", key=f"clear_{p}", on_click=record_event, args=("Defesa", p, "Corte"), use_container_width=True)
        c4.button("Recuperação", key=f"recover_{p}", on_click=record_event, args=("Defesa", p, "Recuperação"), use_container_width=True)
        c5.button("Pressão", key=f"pressure_{p}", on_click=record_event, args=("Pressão", p), use_container_width=True) # Novo botão de pressão

        st.markdown("##### Goleiro e Faltas")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("Defesa Goleiro", key=f"gk_save_{p}", on_click=record_event, args=("Defesa Goleiro", p), use_container_width=True) # Novo botão de defesa do goleiro
        c2.button("Perda de Posse", key=f"poss_lost_{p}", on_click=record_event, args=("Perda de Posse", p), use_container_width=True)
        c3.button("Falta Cometida", key=f"foul_c_{p}", on_click=record_event, args=("Falta", p, "Cometida"), use_container_width=True)
        c4.button("Falta Sofrida", key=f"foul_s_{p}", on_click=record_event, args=("Falta", p, "Sofrida"), use_container_width=True)

# --- Caixa de Eventos para Observações ---
st.markdown("---")
st.header("📝 Observações do Jogo")
with st.form("observation_form", clear_on_submit=True):
    observation_text = st.text_area("Adicione uma observação geral do jogo ou um comentário sobre um momento específico:", height=100)
    if st.form_submit_button("Registrar Observação", use_container_width=True):
        if observation_text:
            current_time_obs = get_current_time()
            minute_obs = int(current_time_obs // 60)
            second_obs = int(current_time_obs % 60)
            record_event("Observação", player_number="N/A", observation=f"[{minute_obs}:{second_obs:02d}] {observation_text}")
            st.success("Observação registrada!")

# --- Seção de Relatórios e Log ---
st.markdown("---")
with st.expander("📊 Ver Log de Eventos e Exportar Dados", expanded=True): # Expander aberto por padrão
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
