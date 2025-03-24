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

# Função para tratar valores ausentes e exibir texto padrão
def tratar_valor(valor, texto_padrao="Não disponível"):
    if pd.isna(valor):
        return texto_padrao
    return valor

# Função para tratar data (Contrato até)
def tratar_data(valor):
    if pd.isna(valor):
        return "Não disponível"
    try:
        return pd.to_datetime(valor, unit='s').strftime('%d/%m/%Y')
    except Exception:
        return "Erro ao formatar data"

# Exibição dos cards
for _, jogador in dados_filtrados.iterrows():
    with st.expander(f"{tratar_valor(jogador['player.name'], 'Nome não disponível')} ({tratar_valor(jogador['player.team.name'], 'Equipe não disponível')})"):
        st.write(f"Posição: {tratar_valor(jogador['player.position'])}")
        st.write(f"Altura: {tratar_valor(jogador['player.height'])} cm | Pé Preferido: {tratar_valor(jogador['player.preferredFoot'])}")
        st.write(f"País: {tratar_valor(jogador['player.country.name'])}")
        
        # Verificar e calcular a idade com data de nascimento
        if pd.notna(jogador["player.dateOfBirthTimestamp"]):
            try:
                nascimento = pd.to_datetime(jogador["player.dateOfBirthTimestamp"], errors='coerce')
                if pd.notna(nascimento):
                    idade = int((pd.Timestamp.now().timestamp() - nascimento.timestamp()) // (365.25 * 24 * 3600))
                    st.write(f"Idade: {idade} anos")
                else:
                    st.write("Idade: Não disponível")
            except Exception:
                st.write("Idade: Erro ao calcular a idade")
        else:
            st.write("Idade: Não disponível")
        
        st.write(f"Campeonato: {tratar_valor(jogador['campeonato'])}")
        
        # Estatísticas avançadas simuladas
        st.subheader("Estatísticas Avançadas")
        estatisticas = {
            "Minutos Jogados": tratar_valor(jogador["minutesPlayed"]),
            "Valor de Mercado": tratar_valor(jogador["player.proposedMarketValue"]),
            "Contrato Até": tratar_data(jogador["player.contractUntilTimestamp"]),
            "Número da Camisa": tratar_valor(jogador["player.shirtNumber"])
        }
        st.table(pd.DataFrame(estatisticas.items(), columns=["Estatística", "Valor"]))
