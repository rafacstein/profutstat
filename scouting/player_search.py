import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Pegando o Sheet ID do arquivo de secrets
sheet_id = st.secrets["google_sheets"]["sheet_id"]
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
dados = pd.read_csv(sheet_url)

# Filtrar apenas atletas com minutos jogados maior que zero
dados = dados[dados["minutesPlayed"] > 0]

# Função para tratar valores em branco
def tratar_valor(valor):
    return valor if pd.notna(valor) else "Não disponível"

# Título e instruções
st.title("Análise de Jogadores - Futebol ⚽")
st.write("Filtre jogadores e explore estatísticas avançadas.")

# Filtros de seleção múltipla
col1, col2 = st.columns(2)
with col1:
    nome = st.text_input("Nome do Jogador")
    equipes = sorted([e for e in dados["player.team.name"].unique() if pd.notna(e)])
    equipe = st.multiselect("Equipe", [""] + equipes)
    pes = ["Left", "Right"]
    pe_preferido = st.multiselect("Pé Preferido", [""] + pes)

with col2:
    posicoes = sorted([p for p in dados["player.position"].unique() if pd.notna(p)])
    posicao = st.multiselect("Posição", [""] + posicoes)
    campeonatos = sorted([c for c in dados["campeonato"].unique() if pd.notna(c)])
    campeonato = st.multiselect("Campeonato", [""] + campeonatos)
    altura_min, altura_max = st.slider("Altura (cm)", 150, 210, (170, 190))

# Aplicação dos filtros
filtros = (
    (dados["player.name"].str.contains(nome, case=False, na=False)) &
    (dados["player.team.name"].isin(equipe) if equipe else True) &
    (dados["player.preferredFoot"].isin(pe_preferido) if pe_preferido else True) &
    (dados["player.position"].isin(posicao) if posicao else True) &
    (dados["campeonato"].isin(campeonato) if campeonato else True) &
    (dados["player.height"] >= altura_min) & 
    (dados["player.height"] <= altura_max)
)

dados_filtrados = dados[filtros]

st.write(f"Jogadores encontrados: {len(dados_filtrados)}")

# Exibição dos cards
for _, jogador in dados_filtrados.iterrows():
    with st.expander(f"{jogador['player.name']} ({jogador['player.team.name']})"):
        st.write(f"Posição: {tratar_valor(jogador['player.position'])}")
        st.write(f"Altura: {tratar_valor(jogador['player.height'])} cm | Pé Preferido: {tratar_valor(jogador['player.preferredFoot'])}")
        st.write(f"País: {tratar_valor(jogador['player.country.name'])} | Idade: {tratar_valor(int((pd.Timestamp.now().timestamp() - jogador['player.dateOfBirthTimestamp']) // (365.25 * 24 * 3600)) if pd.notna(jogador['player.dateOfBirthTimestamp']) else 'Não disponível')} anos")
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
        if st.button(f"Mostrar Radar de Atributos - {jogador['player.name']}"):
            categorias = ["Minutos Jogados", "Valor de Mercado", "Altura", "Idade"]
            valores = [
                jogador["minutesPlayed"] if pd.notna(jogador["minutesPlayed"]) else 0,
                jogador["player.proposedMarketValue"] if pd.notna(jogador["player.proposedMarketValue"]) else 0,
                jogador["player.height"] if pd.notna(jogador["player.height"]) else 0,
                int((pd.Timestamp.now().timestamp() - jogador["player.dateOfBirthTimestamp"]) // (365.25 * 24 * 3600)) if pd.notna(jogador["player.dateOfBirthTimestamp"]) else 0
            ]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=valores, theta=categorias, fill='toself', name=jogador['player.name']))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, max(valores) + 10])),
                showlegend=False
            )
            st.plotly_chart(fig)

