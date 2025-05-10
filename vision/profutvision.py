import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Configuração inicial
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=[
        "Evento", "Minuto", "Segundo", "Time", "Jogador", "Tipo"
    ])
    st.session_state.time_a = "Time A"
    st.session_state.time_b = "Time B"
    st.session_state.tempo_inicio = None
    st.session_state.tempo_pausado = 0
    st.session_state.velocidade = 1
    st.session_state.ultimo_tempo = 0

# Funções do cronômetro
def iniciar_cronometro():
    st.session_state.tempo_inicio = time.time() - st.session_state.tempo_pausado

def pausar_cronometro():
    if st.session_state.tempo_inicio is not None:
        st.session_state.tempo_pausado = time.time() - st.session_state.tempo_inicio
        st.session_state.tempo_inicio = None

def get_tempo_atual():
    if st.session_state.tempo_inicio is None:
        return st.session_state.tempo_pausado * st.session_state.velocidade
    return (time.time() - st.session_state.tempo_inicio) * st.session_state.velocidade

# Função para registrar eventos
def registrar_evento(evento, time, jogador="", tipo=""):
    tempo_atual = get_tempo_atual()
    minuto = int(tempo_atual // 60)
    segundo = int(tempo_atual % 60)
    
    novo_evento = {
        "Evento": evento,
        "Minuto": minuto,
        "Segundo": segundo,
        "Time": time,
        "Jogador": jogador,
        "Tipo": tipo
    }
    st.session_state.dados = pd.concat(
        [st.session_state.dados, pd.DataFrame([novo_evento])],
        ignore_index=True
    )
    st.session_state.ultimo_tempo = tempo_atual
    st.rerun()

# Interface
st.title("⚽ Análise Completa de Jogo")

# --- Configuração dos Times ---
col1, col2 = st.columns(2)
with col1:
    st.session_state.time_a = st.text_input("Nome Time A:", "Time A")
with col2:
    st.session_state.time_b = st.text_input("Nome Time B:", "Time B")

# --- Controle do Cronômetro ---
st.header("Cronômetro")
col_vel, col_ctrl = st.columns([1, 2])
with col_vel:
    st.session_state.velocidade = st.radio("Velocidade:", [1, 2], index=0)
with col_ctrl:
    if st.button("⏵ Iniciar") and st.session_state.tempo_inicio is None:
        iniciar_cronometro()
    if st.button("⏸ Pausar") and st.session_state.tempo_inicio is not None:
        pausar_cronometro()
    if st.button("↻ Resetar"):
        st.session_state.tempo_inicio = None
        st.session_state.tempo_pausado = 0
        st.session_state.ultimo_tempo = 0

# Mostra o tempo atual
tempo_atual = get_tempo_atual()
minutos = int(tempo_atual // 60)
segundos = int(tempo_atual % 60)
st.metric("Tempo", f"{minutos}:{segundos:02d}")

# --- Botões de Ações ---
def criar_botao_acao(acao, time, tipo="", jogador=False, col=None):
    with col:
        if jogador:
            jogador_nome = st.text_input(f"Jogador ({acao}):", key=f"jogador_{acao}_{time}")
            if st.button(acao, key=f"{acao}_{time}"):
                registrar_evento(acao, time, jogador_nome, tipo)
        else:
            if st.button(acao, key=f"{acao}_{time}"):
                registrar_evento(acao, time, "", tipo)

st.header("Ações de Posse")
col1, col2 = st.columns(2)
criar_botao_acao("Posse de Bola", st.session_state.time_a, col=col1)
criar_botao_acao("Posse de Bola", st.session_state.time_b, col=col2)

st.header("Finalizações")
col3, col4 = st.columns(2)
criar_botao_acao("Finalização no Alvo", st.session_state.time_a, col=col3)
criar_botao_acao("Finalização no Alvo", st.session_state.time_b, col=col4)
criar_botao_acao("Finalização Fora", st.session_state.time_a, col=col3)
criar_botao_acao("Finalização Fora", st.session_state.time_b, col=col4)

st.header("Gols e Assistências")
col5, col6 = st.columns(2)
criar_botao_acao("⚽ Gol", st.session_state.time_a, "Gol", True, col5)
criar_botao_acao("⚽ Gol", st.session_state.time_b, "Gol", True, col6)
criar_botao_acao("🅰️ Assistência", st.session_state.time_a, "Assistência", True, col5)
criar_botao_acao("🅰️ Assistência", st.session_state.time_b, "Assistência", True, col6)

st.header("Lances Aéreos")
col7, col8 = st.columns(2)
criar_botao_acao("Duelo Aéreo Vencido", st.session_state.time_a, col=col7)
criar_botao_acao("Duelo Aéreo Vencido", st.session_state.time_b, col=col8)
criar_botao_acao("Duelo Aéreo Perdido", st.session_state.time_a, col=col7)
criar_botao_acao("Duelo Aéreo Perdido", st.session_state.time_b, col=col8)

st.header("Outras Ações")
col9, col10 = st.columns(2)
criar_botao_acao("Escanteio", st.session_state.time_a, col=col9)
criar_botao_acao("Escanteio", st.session_state.time_b, col=col10)
criar_botao_acao("Interceptação", st.session_state.time_a, col=col9)
criar_botao_acao("Interceptação", st.session_state.time_b, col=col10)
criar_botao_acao("Desarme", st.session_state.time_a, col=col9)
criar_botao_acao("Desarme", st.session_state.time_b, col=col10)

# --- Estatísticas ---
st.header("Relatório")
if not st.session_state.dados.empty:
    # Filtros
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        filtro_time = st.selectbox("Filtrar por time:", 
                                 ["Todos"] + [st.session_state.time_a, st.session_state.time_b])
    with col_filtro2:
        filtro_evento = st.selectbox("Filtrar por evento:", 
                                   ["Todos"] + list(st.session_state.dados["Evento"].unique()))
    
    # Aplicar filtros
    dados_filtrados = st.session_state.dados
    if filtro_time != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados["Time"] == filtro_time]
    if filtro_evento != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados["Evento"] == filtro_evento]
    
    # Mostrar dados
    st.dataframe(dados_filtrados.sort_values(by=["Minuto", "Segundo"]))

    # Estatísticas resumidas
    st.subheader("Resumo por Time")
    st.table(dados_filtrados["Time"].value_counts())

# Exportar
if st.button("Exportar CSV"):
    st.download_button(
        label="Baixar Dados",
        data=st.session_state.dados.to_csv(index=False),
        file_name="dados_jogo.csv",
        mime="text/csv"
    )
