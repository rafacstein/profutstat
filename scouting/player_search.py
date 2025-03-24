import streamlit as st
import pandas as pd

# Pegando o Sheet ID do arquivo de secrets
sheet_id = st.secrets["google_sheets"]["sheet_id"]
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
dados = pd.read_csv(sheet_url)

# Título e instruções
st.title("Análise de Jogadores - Futebol ⚽")
st.write("Filtre jogadores e explore estatísticas avançadas.")

# Filtros de seleção (Agora com multiselect)
col1, col2 = st.columns(2)
with col1:
    nome = st.text_input("Nome do Jogador")
    
    # Filtro para equipe com multiselect
    equipe = st.multiselect("Equipe", [""] + sorted(dados["player.team.name"].dropna().unique().tolist()))
    
    # Filtro para pé preferido com multiselect
    pe_preferido = st.multiselect("Pé Preferido", ["", "Left", "Right"])
    
with col2:
    # Filtro para posição com multiselect
    posicao = st.multiselect("Posição", [""] + sorted(dados["player.position"].dropna().unique().tolist()))
    
    # Filtro para campeonato com multiselect
    campeonato = st.multiselect("Campeonato", [""] + sorted(dados["campeonato"].dropna().unique().tolist()))
    
    # Filtro para altura mínima e máxima
    altura_min = st.slider("Altura mínima (cm)", 150, 210, 170)
    altura_max = st.slider("Altura máxima (cm)", 150, 210, 190)

# Aplicação dos filtros
filtros = (
    (dados["player.name"].str.contains(nome, case=False)) &
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
        st.write(f"Posição: {jogador['player.position']}")
        st.write(f"Altura: {jogador['player.height']} cm | Pé Preferido: {jogador['player.preferredFoot']}")
        st.write(f"País: {jogador['player.country.name']} | Idade: {int((pd.Timestamp.now().timestamp() - jogador['player.dateOfBirthTimestamp']) // (365.25 * 24 * 3600))} anos")
        st.write(f"Campeonato: {jogador['campeonato']}")
        
        # Estatísticas avançadas simuladas
        st.subheader("Estatísticas Avançadas")
        estatisticas = {
            "Minutos Jogados": jogador["minutesPlayed"],
            "Valor de Mercado": jogador["player.proposedMarketValue"],
            "Contrato Até": pd.to_datetime(jogador["player.contractUntilTimestamp"], unit='s').strftime('%d/%m/%Y'),
            "Número da Camisa": jogador["player.shirtNumber"]
        }
        st.table(pd.DataFrame(estatisticas.items(), columns=["Estatística", "Valor"]))
