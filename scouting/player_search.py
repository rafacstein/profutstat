import streamlit as st
import pandas as pd
import math
from utils import gerar_radar_geral, tratar_valor  # Certifique-se de que esses módulos estão disponíveis

# Carregamento eficiente dos dados
@st.cache_data
def carregar_dados():
    sheet_id = st.secrets['google_sheets']['sheet_id']
    sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
    return pd.read_csv(sheet_url)

dados = carregar_dados()

# Filtro de busca otimizado
nome = st.text_input('Nome do Jogador').strip().lower()
if nome:
    dados = dados[dados['player.name'].str.lower().str.startswith(nome)]

# Filtro de campeonato otimizado
if 'campeonato' in dados.columns:
    campeonato = st.selectbox('Campeonato', ['Todos'] + sorted(dados['campeonato'].dropna().unique().tolist()))
    if campeonato != 'Todos':
        dados = dados[dados['campeonato'] == campeonato]

# Paginação para melhorar a performance
jogadores_por_pagina = 10
total_paginas = max(1, math.ceil(len(dados) / jogadores_por_pagina))
pagina = st.number_input('Página', min_value=1, max_value=total_paginas, value=1)

dados_pagina = dados.iloc[(pagina - 1) * jogadores_por_pagina : pagina * jogadores_por_pagina]

# Exibição dos jogadores
for _, jogador in dados_pagina.iterrows():
    with st.expander(f"{tratar_valor(jogador, 'player.name')} ({tratar_valor(jogador, 'player.team.name')})"):
        st.write(f"Posição: {tratar_valor(jogador, 'player.position')}")
        
        # Botão para gerar radar sob demanda
        if st.button(f"Mostrar Radar - {tratar_valor(jogador, 'player.name')}"):
            gerar_radar_geral(jogador)
