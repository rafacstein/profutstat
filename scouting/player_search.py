import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Função para tratar valores nulos
def tratar_valor(valor):
    return valor if pd.notna(valor) else "Não disponível"

# Função para criar o radar de atributos
def radar_atributos(jogador, dados):
    atributos = ["tackles", "interceptions", "clearances", "duelsWon"]
    labels = ["Tackles", "Interceptações", "Rebatidas", "Duelos Ganhos"]

    # Normalizar os valores entre 0 e 100 para o radar
    max_valores = dados[atributos].max()
    min_valores = dados[atributos].min()

    valores_jogador = [
        (jogador[atributo] - min_valores[atributo]) / (max_valores[atributo] - min_valores[atributo]) * 100
        if max_valores[atributo] != min_valores[atributo] else 50
        for atributo in atributos
    ]

    # Configuração do gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores_jogador,
        theta=labels,
        fill='toself',
        name=jogador['player.name']
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title=f"Radar de Atributos - {jogador['player.name']}"
    )

    st.plotly_chart(fig)

# Pegando o Sheet ID do arquivo de secrets
sheet_id = st.secrets["google_sheets"]["sheet_id"]
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# Título e instruções
st.title("Análise de Jogadores - Futebol ⚽")
st.write("Filtre jogadores e explore estatísticas avançadas.")

# Filtros de seleção múltipla
col1, col2 = st.columns(2)
with col1:
    nome = st.text_input("Nome do Jogador")
    equipes = st.multiselect("Equipe", [])
    pes_preferidos = st.multiselect("Pé Preferido", ["Left", "Right"])

with col2:
    posicoes = st.multiselect("Posição", [])
    campeonatos = st.multiselect("Campeonato", [])
    altura_min = st.slider("Altura mínima (cm)", 150, 210, 170)
    altura_max = st.slider("Altura máxima (cm)", 150, 210, 190)

# Carregamento e filtragem de dados somente ao clicar no botão
dados_filtrados = pd.DataFrame()  # Inicialmente vazio

if st.button("Aplicar Filtros"):
    dados = pd.read_csv(sheet_url)
    dados = dados[dados["minutesPlayed"] > 0]  # Filtra jogadores com minutos jogados

    # Atualiza opções de filtros após carregar os dados
    equipes = st.multiselect("Equipe", sorted(dados["player.team.name"].dropna().unique()), equipes)
    posicoes = st.multiselect("Posição", sorted(dados["player.position"].dropna().unique()), posicoes)
    campeonatos = st.multiselect("Campeonato", sorted(dados["campeonato"].dropna().unique()), campeonatos)

    # Aplicação dos filtros
    filtros = (
        (dados["player.name"].str.contains(nome, case=False, na=False)) &
        (dados["player.team.name"].isin(equipes) if equipes else True) &
        (dados["player.preferredFoot"].isin(pes_preferidos) if pes_preferidos else True) &
        (dados["player.position"].isin(posicoes) if posicoes else True) &
        (dados["campeonato"].isin(campeonatos) if campeonatos else True) &
        (dados["player.height"] >= altura_min) & 
        (dados["player.height"] <= altura_max)
    )

    dados_filtrados = dados[filtros]
    st.write(f"Jogadores encontrados: {len(dados_filtrados)}")

    # Exibição dos jogadores filtrados com opção de radar de atributos
    for _, jogador in dados_filtrados.iterrows():
        with st.expander(f"{jogador['player.name']} ({tratar_valor(jogador['player.team.name'])})"):
            st.write(f"Posição: {tratar_valor(jogador['player.position'])}")
            st.write(f"Altura: {tratar_valor(jogador['player.height'])} cm | Pé Preferido: {tratar_valor(jogador['player.preferredFoot'])}")
            st.write(f"País: {tratar_valor(jogador['player.country.name'])} | Idade: {tratar_valor(int((pd.Timestamp.now().timestamp() - jogador['player.dateOfBirthTimestamp']) // (365.25 * 24 * 3600)))} anos")
            st.write(f"Campeonato: {tratar_valor(jogador['campeonato'])}")

            # Estatísticas Avançadas
            st.subheader("Estatísticas Avançadas")
            estatisticas = {
                "Minutos Jogados": tratar_valor(jogador["minutesPlayed"]),
                "Valor de Mercado": tratar_valor(jogador["player.proposedMarketValue"]),
                "Contrato Até": tratar_valor(pd.to_datetime(jogador["player.contractUntilTimestamp"], unit='s').strftime('%d/%m/%Y') if pd.notna(jogador["player.contractUntilTimestamp"]) else "Não disponível"),
                "Número da Camisa": tratar_valor(jogador["player.shirtNumber"])
            }
            st.table(pd.DataFrame(estatisticas.items(), columns=["Estatística", "Valor"]))

            # Botão para exibir radar de atributos
            if st.button(f"Mostrar Radar de Atributos - {jogador['player.name']}", key=f"radar_{jogador['player.name']}"):
                radar_atributos(jogador, dados)

else:
    st.warning("Aplique os filtros para carregar os jogadores!")

