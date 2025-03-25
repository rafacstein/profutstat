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

# Tratamento de valores ausentes
def tratar_valor(valor):
    return valor if pd.notna(valor) else 'Não disponível'

# Função para calcular idade
def calcular_idade(timestamp):
    if pd.notna(timestamp):
        idade = int((pd.Timestamp.now().timestamp() - timestamp) // (365.25 * 24 * 3600))
        return idade
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

# Função para gerar radar de atributos
def gerar_radar(jogador):
    categorias = ['Minutos Jogados', 'Valor de Mercado', 'Altura', 'Número da Camisa']
    valores = [
        tratar_valor(jogador['minutesPlayed']),
        tratar_valor(jogador['player.proposedMarketValue']),
        tratar_valor(jogador['player.height']),
        tratar_valor(jogador['player.shirtNumber'])
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=valores, theta=categorias, fill='toself', name=jogador['player.name']))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False)
    st.plotly_chart(fig)

# Exibição dos cards
for _, jogador in dados_filtrados.iterrows():
    with st.expander(f"{tratar_valor(jogador['player.name'])} ({tratar_valor(jogador['player.team.name'])})"):
        st.write(f"Posição: {tratar_valor(jogador['player.position'])}")
        st.write(f"Altura: {tratar_valor(jogador['player.height'])} cm | Pé Preferido: {tratar_valor(jogador['player.preferredFoot'])}")
        st.write(f"País: {tratar_valor(jogador['player.country.name'])} | Idade: {tratar_valor(calcular_idade(jogador['player.dateOfBirthTimestamp']))} anos")
        st.write(f"Campeonato: {tratar_valor(jogador['campeonato'])}")

        # Estatísticas avançadas
        st.subheader('Estatísticas Avançadas')
        estatisticas = {
            'Minutos Jogados': tratar_valor(jogador['minutesPlayed']),
            'Valor de Mercado': tratar_valor(jogador['player.proposedMarketValue']),
            'Contrato Até': tratar_valor(pd.to_datetime(jogador['player.contractUntilTimestamp'], unit='s', errors='coerce').strftime('%d/%m/%Y') if pd.notna(jogador['player.contractUntilTimestamp']) else 'Não disponível'),
            'Número da Camisa': tratar_valor(jogador['player.shirtNumber'])
        }
        st.table(pd.DataFrame(estatisticas.items(), columns=['Estatística', 'Valor']))

        # Radar de atributos
        st.subheader('Radar de Atributos')
        gerar_radar(jogador)
