import dask.dataframe as dd
import streamlit as st

# Carregar dados com Dask
sheet_id = st.secrets['google_sheets']['sheet_id']
sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
dados = dd.read_csv(sheet_url)

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
equipe = st.multiselect('Equipe', sorted(dados['player.team.name'].dropna().unique().compute().tolist()))
posicao = st.multiselect('Posição', sorted(dados['player.position'].dropna().unique().compute().tolist()))
pe_preferido = st.multiselect('Pé Preferido', sorted(dados['player.preferredFoot'].dropna().unique().compute().tolist()))
campeonato = st.multiselect('Campeonato', sorted(dados['campeonato'].dropna().unique().compute().tolist()))

# Aplicação dos filtros
filtros = (
    (dados['player.name'].str.contains(nome, case=False, na=False)) &
    (dados['player.team.name'].isin(equipe) if equipe else True) &
    (dados['player.position'].isin(posicao) if posicao else True) &
    (dados['player.preferredFoot'].isin(pe_preferido) if pe_preferido else True) &
    (dados['campeonato'].isin(campeonato) if campeonato else True)
)
dados_filtrados = dados[filtros]

st.write(f'Jogadores encontrados: {len(dados_filtrados.compute())}')

# Função para exibir os dados ofensivos
def mostrar_dados_ofensivos(jogador):
    dados_ofensivos = {
        'Participações em Gols': tratar_valor(jogador, 'goalsAssistsSum'),
        '% de passes corretos': tratar_valor(jogador, 'accuratePassesPercentage'),
        '% de Dribles corretos': tratar_valor(jogador, 'successfulDribblesPercentage'),
        'Passes certos no último terço': tratar_valor(jogador, 'accurateFinalThirdPasses')
    }
    return pd.DataFrame(dados_ofensivos.items(), columns=['Atributo', 'Valor'])

# Função para exibir os dados defensivos
def mostrar_dados_defensivos(jogador):
    dados_defensivos = {
        'Duelos aéreos ganhos': tratar_valor(jogador, 'aerialDuelsWonPercentage'),
        'Duelos ganhos no chão': tratar_valor(jogador, 'totalDuelsWonPercentage'),
        'Recuperação de bolas': tratar_valor(jogador, 'BallRecovery'),
        'Dribles sofridos': tratar_valor(jogador, 'dribbledPast')
    }
    return pd.DataFrame(dados_defensivos.items(), columns=['Atributo', 'Valor'])

# Exibição dos cards
# Convertendo para pandas para exibição
dados_filtrados_pandas = dados_filtrados.compute()

for _, jogador in dados_filtrados_pandas.iterrows():
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

        # Dados ofensivos
        st.subheader('Dados Ofensivos')
        st.table(mostrar_dados_ofensivos(jogador))

        # Dados defensivos
        st.subheader('Dados Defensivos')
        st.table(mostrar_dados_defensivos(jogador))
