import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Pegando o Sheet ID do arquivo de secrets
sheet_id = st.secrets["google_sheets"]["sheet_id"]
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
dados = pd.read_csv(sheet_url)

# Remover linhas com minutos jogados iguais a zero
dados = dados[dados["minutesPlayed"] > 0].copy()

# Título e instruções
st.title("Análise de Jogadores - Futebol ⚽")
st.write("Filtre jogadores e explore estatísticas avançadas.")

# Função para tratar valores faltantes
def tratar_valor(valor):
    return valor if pd.notna(valor) else "Não disponível"

# Função para calcular idade
def calcular_idade(timestamp):
    try:
        idade = int((pd.Timestamp.now().timestamp() - timestamp) // (365.25 * 24 * 3600))
        return idade
    except:
        return "Não disponível"

# Filtros de seleção
col1, col2 = st.columns(2)
with col1:
    nome = st.text_input("Nome do Jogador")
    equipes = st.multiselect("Equipe", sorted(dados["player.team.name"].dropna().unique().tolist()))
    pes_preferidos = st.multiselect("Pé Preferido", ["Left", "Right"])

with col2:
    posicoes = st.multiselect("Posição", sorted(dados["player.position"].dropna().unique().tolist()))
    campeonatos = st.multiselect("Campeonato", sorted(dados["campeonato"].dropna().unique().tolist()))
    altura_min, altura_max = st.slider("Altura (cm)", 150, 210, (170, 190))

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

# Exibição dos cards
for _, jogador in dados_filtrados.iterrows():
    with st.expander(f"{tratar_valor(jogador['player.name'])} ({tratar_valor(jogador['player.team.name'])})"):
        st.write(f"Posição: {tratar_valor(jogador['player.position'])}")
        st.write(f"Altura: {tratar_valor(jogador['player.height'])} cm | Pé Preferido: {tratar_valor(jogador['player.preferredFoot'])}")
        st.write(f"País: {tratar_valor(jogador['player.country.name'])} | Idade: {tratar_valor(calcular_idade(jogador['player.dateOfBirthTimestamp']))} anos")
        st.write(f"Campeonato: {tratar_valor(jogador['campeonato'])}")

        # Estatísticas avançadas
        st.subheader("Estatísticas Avançadas")
        estatisticas = {
            "Minutos Jogados": tratar_valor(jogador["minutesPlayed"]),
            "Valor de Mercado": tratar_valor(jogador["player.proposedMarketValue"]),
            "Contrato Até": tratar_valor(pd.to_datetime(jogador["player.contractUntilTimestamp"], unit='s').strftime('%d/%m/%Y') if pd.notna(jogador["player.contractUntilTimestamp"]) else "Não disponível"),
            "Número da Camisa": tratar_valor(jogador["player.shirtNumber"])
        }
        st.table(pd.DataFrame(estatisticas.items(), columns=["Estatística", "Valor"]))

        # Radar de atributos
        st.subheader("Radar de Atributos")
        atributos = ["minutesPlayed", "player.proposedMarketValue", "player.height"]
        valores = [jogador[attr] if pd.notna(jogador[attr]) else 0 for attr in atributos]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=valores, theta=atributos, fill='toself', name=tratar_valor(jogador['player.name'])))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(valores)])))
        st.plotly_chart(fig)
