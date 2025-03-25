import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Pegando o Sheet ID do arquivo de secrets
sheet_id = st.secrets['google_sheets']['sheet_id']
sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
dados = pd.read_csv(sheet_url)

# Filtrando apenas jogadores com minutos jogados > 0
dados = dados[dados['minutesPlayed'] > 0]

st.title('Análise de Jogadores - Futebol ⚽')
st.write('Filtre jogadores e explore estatísticas avançadas.')

# Tratamento de valores ausentes ou chaves inexistentes
def tratar_valor(dicionario, chave):
    try:
        valor = dicionario.get(chave, 'Não disponível')
        return valor if pd.notna(valor) else 'Não disponível'
    except Exception:
        return 'Não disponível'

# Função para calcular idade com tratamento de erros
def calcular_idade(timestamp):
    try:
        if pd.notna(timestamp):
            idade = int((pd.Timestamp.now().timestamp() - timestamp) // (365.25 * 24 * 3600))
            return idade
    except Exception:
        pass
    return 'Não disponível'

# Opções de filtros
nome = st.text_input('Nome do Jogador')
equipe = st.multiselect('Equipe', sorted(dados['player.team.name'].dropna().unique().tolist()))
posicao = st.multiselect('Posição', sorted(dados['player.position'].dropna().unique().tolist()))
pe_preferido = st.multiselect('Pé Preferido', sorted(dados['player.preferredFoot'].dropna().unique().tolist()))
campeonato = st.multiselect('Campeonato', sorted(dados['campeonato'].dropna().unique().tolist()))

# Aplicação dos filtros
filtros = (
    (dados['player.name'].str.contains(nome, case=False, na=False)) &
    (dados['player.team.name'].isin(equipe) if equipe else True) &
    (dados['player.position'].isin(posicao) if posicao else True) &
    (dados['player.preferredFoot'].isin(pe_preferido) if pe_preferido else True) &
    (dados['campeonato'].isin(campeonato) if campeonato else True)
)
dados_filtrados = dados[filtros]

st.write(f'Jogadores encontrados: {len(dados_filtrados)}')

# Função para gerar radar de atributos gerais
def gerar_radar_geral(jogador):
    categorias = ['Minutos Jogados', 'Valor de Mercado', 'Altura', 'Número da Camisa']
    valores = [
        tratar_valor(jogador, 'minutesPlayed'),
        tratar_valor(jogador, 'player.proposedMarketValue'),
        tratar_valor(jogador, 'player.height'),
        tratar_valor(jogador, 'player.shirtNumber')
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=valores, theta=categorias, fill='toself', name=tratar_valor(jogador, 'player.name')))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False)
    st.plotly_chart(fig)

# Função para gerar radar de atributos ofensivos e defensivos
def gerar_radar_atributos(jogador, tipo='ofensivo'):
    if tipo == 'ofensivo':
        categorias = ['Gols', 'Assistências', 'Finalizações', 'Passes Chave']
        valores = [
            tratar_valor(jogador, 'player.goals'),
            tratar_valor(jogador, 'player.assists'),
            tratar_valor(jogador, 'player.shots'),
            tratar_valor(jogador, 'player.keyPasses')
        ]
    else:  # Radar defensivo
        categorias = ['Desarmes', 'Interceptações', 'Cortes', 'Duelos Vencidos']
        valores = [
            tratar_valor(jogador, 'player.tackles'),
            tratar_valor(jogador, 'player.interceptions'),
            tratar_valor(jogador, 'player.clearances'),
            tratar_valor(jogador, 'player.duelsWon')
        ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=valores, theta=categorias, fill='toself', name=tratar_valor(jogador, 'player.name')))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False)
    st.plotly_chart(fig)

# Exibição dos cards
for _, jogador in dados_filtrados.iterrows():
    with st.expander(f"{tratar_valor(jogador, 'player.name')} ({tratar_valor(jogador, 'player.team.name')})"):
        st.write(f"Posição: {tratar_valor(jogador, 'player.position')}")
        st.write(f"Altura: {tratar_valor(jogador, 'player.height')} cm | Pé Preferido: {tratar_valor(jogador, 'player.preferredFoot')}")
        st.write(f"País: {tratar_valor(jogador, 'player.country.name')} | Idade: {calcular_idade(jogador.get('player.dateOfBirthTimestamp', None))} anos")
        st.write(f"Contrato: {tratar_valor(jogador, 'player.contractUntilTimestamp')}")

        # Estatísticas avançadas
        st.subheader('Estatísticas Avançadas')
        estatisticas = {
            'Minutos Jogados': tratar_valor(jogador, 'minutesPlayed'),
            'Valor de Mercado': tratar_valor(jogador, 'player.proposedMarketValue'),
            'Contrato Até': tratar_valor(jogador, 'player.contractUntilTimestamp'),
            'Número da Camisa': tratar_valor(jogador, 'player.shirtNumber')
        }
        st.table(pd.DataFrame(estatisticas.items(), columns=['Estatística', 'Valor']))

        # Radar de atributos gerais
        st.subheader('Radar de Atributos Gerais')
        gerar_radar_geral(jogador)

        # Radar de atributos ofensivos
        st.subheader('Radar de Atributos Ofensivos')
        gerar_radar_atributos(jogador, tipo='ofensivo')

        # Radar de atributos defensivos
        st.subheader('Radar de Atributos Defensivos')
        gerar_radar_atributos(jogador, tipo='defensivo')
