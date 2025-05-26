import pandas as pd
import numpy as np
import streamlit as st
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import io
import requests
import pyarrow.parquet as pq

# Configuração da página
st.set_page_config(
    page_title="🔎 ProFutStat - Recomendador de Jogadores",
    page_icon="⚽",
    layout="wide"
)

# Função para carregar dados do GitHub
@st.cache_data
def load_data_from_github(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        file = io.BytesIO(response.content)
        return pd.read_parquet(file)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# URL do arquivo Parquet no GitHub (substitua pelo seu)
GITHUB_PARQUET_URL = "https://github.com/rafacstein/profutstat/blob/main/scouting/final_merged_data.parquet"

# Carregar dados
with st.spinner('Carregando dados... Isso pode levar alguns minutos...'):
    df = load_data_from_github(GITHUB_PARQUET_URL)

if df is None:
    st.stop()

# Pré-processamento (similar ao seu script original)
colunas_numericas = ["rating", "totalRating", "countRating", "goals", "bigChancesCreated", "bigChancesMissed", "assists",
    "goalsAssistsSum", "accuratePasses", "inaccuratePasses", "totalPasses", "accuratePassesPercentage",
    "accurateOwnHalfPasses", "accurateOppositionHalfPasses", "accurateFinalThirdPasses", "keyPasses",
    "successfulDribbles", "successfulDribblesPercentage", "tackles", "interceptions", "yellowCards",
    "directRedCards", "redCards", "accurateCrosses", "accurateCrossesPercentage", "totalShots", "shotsOnTarget",
    "shotsOffTarget", "groundDuelsWon", "groundDuelsWonPercentage", "aerialDuelsWon", "aerialDuelsWonPercentage",
    "totalDuelsWon", "totalDuelsWonPercentage", "minutesPlayed", "goalConversionPercentage", "penaltiesTaken",
    "penaltyGoals", "penaltyWon", "penaltyConceded", "shotFromSetPiece", "freeKickGoal", "goalsFromInsideTheBox",
    "goalsFromOutsideTheBox", "shotsFromInsideTheBox", "shotsFromOutsideTheBox", "headedGoals", "leftFootGoals",
    "rightFootGoals", "accurateLongBalls", "accurateLongBallsPercentage", "clearances", "errorLeadToGoal",
    "errorLeadToShot", "dispossessed", "possessionLost", "possessionWonAttThird", "totalChippedPasses",
    "accurateChippedPasses", "touches", "wasFouled", "fouls", "hitWoodwork", "ownGoals", "dribbledPast",
    "offsides", "blockedShots", "passToAssist", "saves", "cleanSheet", "penaltyFaced", "penaltySave",
    "savedShotsFromInsideTheBox", "savedShotsFromOutsideTheBox", "goalsConcededInsideTheBox",
    "goalsConcededOutsideTheBox", "punches", "runsOut", "successfulRunsOut", "highClaims", "crossesNotClaimed",
    "matchesStarted", "penaltyConversion", "setPieceConversion", "totalAttemptAssist", "totalContest",
    "totalCross", "duelLost", "aerialLost", "attemptPenaltyMiss", "attemptPenaltyPost", "attemptPenaltyTarget",
    "totalLongBalls", "goalsConceded", "tacklesWon", "tacklesWonPercentage", "scoringFrequency", "yellowRedCards",
    "savesCaught", "savesParried", "totalOwnHalfPasses", "totalOppositionHalfPasses", "totwAppearances", "expectedGoals",
    "goalKicks","ballRecovery", "appearances","player.proposedMarketValue", "age", "player.height"]

# Preencher valores nulos
df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())

# Normalizar os dados
scaler = StandardScaler()
dados_normalizados = scaler.fit_transform(df[colunas_numericas])

# Calcular similaridade (armazenar em cache)
@st.cache_data
def calculate_similarity():
    return cosine_similarity(dados_normalizados)

matriz_similaridade = calculate_similarity()
df_similaridade = pd.DataFrame(matriz_similaridade, index=df.index, columns=df.index)

# Função de recomendação aprimorada
def recomendar_atletas_avancado(nome=None, clube=None, posicao=None, idade_min=None, idade_max=None,
                              valor_min=None, valor_max=None, strict_posicao=True, top_n=5):
    """
    Função adaptada para o Streamlit com tratamento de erros
    """
    try:
        mascara_filtros = pd.Series(True, index=df.index)
        atleta_id = None
        
        # Busca por nome e clube
        if nome:
            if not clube:
                st.warning("Por favor, informe o clube para evitar homônimos")
                return None
                
            # Fuzzy matching para nome e clube
            df['temp_sim_nome'] = df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
            df['temp_sim_clube'] = df['player.team.name'].apply(lambda x: fuzz.token_set_ratio(clube, x))
            df['temp_sim_combinada'] = 0.7*df['temp_sim_nome'] + 0.3*df['temp_sim_clube']
            
            melhor_match = df.nlargest(1, 'temp_sim_combinada')
            df.drop(['temp_sim_nome', 'temp_sim_clube', 'temp_sim_combinada'], axis=1, inplace=True)
            
            if melhor_match.empty or melhor_match['temp_sim_combinada'].iloc[0] < 80:
                st.warning(f"⚠️ Atleta não encontrado. Verifique nome '{nome}' e clube '{clube}'")
                return None
            
            atleta_id = melhor_match.index[0]
            atleta_ref = df.loc[atleta_id]
            
            # Definir posição de referência se strict_posicao=True
            if strict_posicao and posicao is None:
                posicao = atleta_ref['position']
        
        # Aplicar filtros
        if posicao:
            if isinstance(posicao, str):
                posicao = [posicao]
            mascara_filtros &= df['position'].isin(posicao)
        
        if idade_min is not None:
            mascara_filtros &= df['age'] >= idade_min
        if idade_max is not None:
            mascara_filtros &= df['age'] <= idade_max
        
        if valor_min is not None:
            mascara_filtros &= df['player.proposedMarketValue'] >= valor_min
        if valor_max is not None:
            mascara_filtros &= df['player.proposedMarketValue'] <= valor_max
        
        # Obter recomendações
        if atleta_id is not None:
            similaridades = df_similaridade.loc[atleta_id].sort_values(ascending=False)
            similaridades = similaridades[mascara_filtros]
            similaridades = similaridades.drop(atleta_id, errors='ignore')
            recomendacoes = df.loc[similaridades.head(top_n).index]
            recomendacoes['similaridade'] = similaridades.head(top_n).values
        else:
            recomendacoes = df[mascara_filtros].sample(min(top_n, len(df[mascara_filtros])))
            recomendacoes['similaridade'] = None
        
        return recomendacoes
    
    except Exception as e:
        st.error(f"Erro na recomendação: {e}")
        return None

# Interface do Streamlit
st.title("⚽ Football Scout - Recomendador de Jogadores")
st.markdown("Encontre jogadores similares com base em estatísticas avançadas")

tab1, tab2 = st.tabs(["🔍 Busca por Jogador", "⚙️ Busca por Características"])

with tab1:
    st.header("Buscar por jogador específico")
    col1, col2 = st.columns(2)
    with col1:
        nome_jogador = st.text_input("Nome do jogador", key="nome_jogador")
    with col2:
        clube_jogador = st.text_input("Clube", key="clube_jogador")
    
    strict_pos = st.checkbox("Exigir mesma posição", value=True, key="strict_pos")
    
    with st.expander("Filtros adicionais"):
        idade_min = st.number_input("Idade mínima", min_value=16, max_value=45, value=None, key="idade_min1")
        idade_max = st.number_input("Idade máxima", min_value=16, max_value=45, value=None, key="idade_max1")
        valor_min = st.number_input("Valor mínimo (€)", min_value=0, value=None, key="valor_min1")
        valor_max = st.number_input("Valor máximo (€)", min_value=0, value=None, key="valor_max1")
    
    if st.button("Buscar Recomendações", key="btn_busca1"):
        if nome_jogador:
            with st.spinner("Procurando jogadores similares..."):
                rec = recomendar_atletas_avancado(
                    nome=nome_jogador,
                    clube=clube_jogador,
                    posicao=None,
                    idade_min=idade_min,
                    idade_max=idade_max,
                    valor_min=valor_min,
                    valor_max=valor_max,
                    strict_posicao=strict_pos,
                    top_n=10
                )
            
            if rec is not None and not rec.empty:
                st.success(f"🎯 {len(rec)} recomendações encontradas")
                
                # Mostrar atleta de referência
                st.subheader("Atleta de Referência")
                ref_id = df[df['player.name'].str.contains(nome_jogador, case=False)].index[0]
                atleta_ref = df.loc[ref_id]
                cols_ref = ['player.name', 'player.team.name', 'position', 'age', 
                           'player.proposedMarketValue', 'goals', 'assists']
                st.dataframe(atleta_ref[cols_ref])
                
                # Mostrar recomendações
                st.subheader("Jogadores Recomendados")
                cols_rec = ['player.name', 'player.team.name', 'position', 'age', 
                          'player.proposedMarketValue', 'similaridade', 'goals', 'assists']
                st.dataframe(rec[cols_rec].sort_values('similaridade', ascending=False))
                
                # Visualização PCA
                st.subheader("Visualização no Espaço PCA")
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.scatterplot(data=df, x='pca1', y='pca2', color='gray', alpha=0.2, ax=ax)
                sns.scatterplot(data=rec, x='pca1', y='pca2', color='red', label='Recomendados', ax=ax)
                sns.scatterplot(x=[atleta_ref['pca1']], y=[atleta_ref['pca2']], 
                               color='blue', s=200, label='Referência', ax=ax)
                plt.legend()
                st.pyplot(fig)
            else:
                st.warning("Nenhum jogador encontrado com os critérios informados")

with tab2:
    st.header("Buscar por características")
    
    col1, col2 = st.columns(2)
    with col1:
        posicao = st.multiselect("Posição", options=df['position'].unique(), key="posicao")
    with col2:
        top_n = st.number_input("Número de recomendações", min_value=1, max_value=20, value=5, key="top_n")
    
    with st.expander("Filtros avançados"):
        idade_min = st.number_input("Idade mínima", min_value=16, max_value=45, value=None, key="idade_min2")
        idade_max = st.number_input("Idade máxima", min_value=16, max_value=45, value=None, key="idade_max2")
        valor_min = st.number_input("Valor mínimo (€)", min_value=0, value=None, key="valor_min2")
        valor_max = st.number_input("Valor máximo (€)", min_value=0, value=None, key="valor_max2")
    
    if st.button("Buscar Recomendações", key="btn_busca2"):
        with st.spinner("Procurando jogadores..."):
            rec = recomendar_atletas_avancado(
                nome=None,
                clube=None,
                posicao=posicao if posicao else None,
                idade_min=idade_min,
                idade_max=idade_max,
                valor_min=valor_min,
                valor_max=valor_max,
                strict_posicao=False,
                top_n=top_n
            )
        
        if rec is not None and not rec.empty:
            st.success(f"🎯 {len(rec)} recomendações encontradas")
            cols_rec = ['player.name', 'player.team.name', 'position', 'age', 
                      'player.proposedMarketValue', 'goals', 'assists', 'tackles']
            st.dataframe(rec[cols_rec])
            
            # Visualização PCA
            st.subheader("Visualização no Espaço PCA")
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.scatterplot(data=df, x='pca1', y='pca2', color='gray', alpha=0.2, ax=ax)
            sns.scatterplot(data=rec, x='pca1', y='pca2', color='red', label='Recomendados', ax=ax)
            plt.legend()
            st.pyplot(fig)
        else:
            st.warning("Nenhum jogador encontrado com os critérios informados")

# Rodapé
st.markdown("---")
st.markdown("**Football Scout** - Ferramenta de análise de jogadores")
