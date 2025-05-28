import streamlit as st
import pandas as pd
import numpy as np
import faiss
from fuzzywuzzy import fuzz
from sklearn.preprocessing import StandardScaler

# --- 1. Carregar dados e recursos no começo ---
@st.cache_data(show_spinner=True)
def carregar_dados(caminho_arquivo):
    df = pd.read_parquet(caminho_arquivo)
    # selecionar colunas numéricas (reutilize o que você já tem)
    features_cols = ["rating", "totalRating", "countRating", "goals", "bigChancesCreated", "bigChancesMissed", 
                     "assists", "goalsAssistsSum", "accuratePasses", "inaccuratePasses", "totalPasses",
                     "accuratePassesPercentage", "accurateOwnHalfPasses", "accurateOppositionHalfPasses",
                     "accurateFinalThirdPasses", "keyPasses", "successfulDribbles", "successfulDribblesPercentage",
                     "tackles", "interceptions", "yellowCards", "directRedCards", "redCards", "accurateCrosses",
                     "accurateCrossesPercentage", "totalShots", "shotsOnTarget", "shotsOffTarget", "groundDuelsWon",
                     "groundDuelsWonPercentage", "aerialDuelsWon", "aerialDuelsWonPercentage", "totalDuelsWon",
                     "totalDuelsWonPercentage", "minutesPlayed", "goalConversionPercentage", "penaltiesTaken",
                     "penaltyGoals", "penaltyWon", "penaltyConceded", "shotFromSetPiece", "freeKickGoal",
                     "goalsFromInsideTheBox", "goalsFromOutsideTheBox", "shotsFromInsideTheBox", "shotsFromOutsideTheBox",
                     "headedGoals", "leftFootGoals", "rightFootGoals", "accurateLongBalls", "accurateLongBallsPercentage",
                     "clearances", "errorLeadToGoal", "errorLeadToShot", "dispossessed", "possessionLost",
                     "possessionWonAttThird", "totalChippedPasses", "accurateChippedPasses", "touches", "wasFouled",
                     "fouls", "hitWoodwork", "ownGoals", "dribbledPast", "offsides", "blockedShots", "passToAssist",
                     "saves", "cleanSheet", "penaltyFaced", "penaltySave", "savedShotsFromInsideTheBox",
                     "savedShotsFromOutsideTheBox", "goalsConcededInsideTheBox", "goalsConcededOutsideTheBox",
                     "punches", "runsOut", "successfulRunsOut", "highClaims", "crossesNotClaimed", "matchesStarted",
                     "penaltyConversion", "setPieceConversion", "totalAttemptAssist", "totalContest", "totalCross",
                     "duelLost", "aerialLost", "attemptPenaltyMiss", "attemptPenaltyPost", "attemptPenaltyTarget",
                     "totalLongBalls", "goalsConceded", "tacklesWon", "tacklesWonPercentage", "scoringFrequency",
                     "yellowRedCards", "savesCaught", "savesParried", "totalOwnHalfPasses", "totalOppositionHalfPasses",
                     "totwAppearances", "expectedGoals", "goalKicks", "ballRecovery", "appearances",
                     "player.proposedMarketValue", "age", "player.height"]
    
    X = df[features_cols]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    features = np.ascontiguousarray(X_scaled.astype('float32'))
    
    # FAISS Index
    faiss.normalize_L2(features)
    index = faiss.IndexFlatIP(features.shape[1])
    index.add(features)
    
    return df, features, index

df, features, index = load_data()

# --- 2. Função de recomendação ---
def recomendar_faiss(nome, clube=None, posicao=None, idade_min=None, idade_max=None,
                     valor_min=None, valor_max=None, top_n=5):
    
    df['sim_nome'] = df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
    
    if clube:
        df['sim_clube'] = df['player.team.name.1'].apply(lambda x: fuzz.token_set_ratio(clube, x))
        df['sim_total'] = 0.7 * df['sim_nome'] + 0.3 * df['sim_clube']
    else:
        df['sim_total'] = df['sim_nome']
    
    jogador_ref = df.loc[df['sim_total'].idxmax()]
    idx_ref = jogador_ref.name
    vetor_ref = features[idx_ref].reshape(1, -1)
    
    D, I = index.search(vetor_ref, 100)
    similares = df.iloc[I[0]].copy()
    similares['similaridade'] = D[0]
    
    # Filtros
    if posicao:
        similares = similares[similares['position'].str.split(',').str[0].str.strip() == posicao]
    if idade_min:
        similares = similares[similares['age'] >= idade_min]
    if idade_max:
        similares = similares[similares['age'] <= idade_max]
    if valor_min:
        similares = similares[similares['player.proposedMarketValue'] >= valor_min]
    if valor_max:
        similares = similares[similares['player.proposedMarketValue'] <= valor_max]
    
    similares = similares[similares.index != idx_ref]

    return similares.nlargest(top_n, 'similaridade')[[
        'player.name', 'player.team.name.1', 'position', 'player.country.name','age','minutesPlayed',
        'player.proposedMarketValue', 'similaridade'
    ]]

# --- 3. Interface Streamlit ---
st.title("Recomendador de Jogadores Similar com FAISS")

with st.form(key='form_faiss'):
    nome = st.text_input("Nome do jogador para buscar similaridade", "Mandaca")
    clube = st.text_input("Clube (opcional)", "")
    posicao = st.selectbox("Posição (opcional)", options=[None] + sorted(df['position'].dropna().unique()))
    idade_min = st.number_input("Idade mínima (opcional)", min_value=0, max_value=100, value=20)
    idade_max = st.number_input("Idade máxima (opcional)", min_value=0, max_value=100, value=30)
    valor_min = st.number_input("Valor mínimo de mercado (opcional)", min_value=0, value=0, step=10000)
    valor_max = st.number_input("Valor máximo de mercado (opcional)", min_value=0, value=2000000, step=10000)
    top_n = st.slider("Quantidade de recomendações", min_value=1, max_value=20, value=10)
    
    submit_button = st.form_submit_button(label='Buscar Jogadores Similares')

if submit_button:
    resultados = recomendar_faiss(nome, clube or None, posicao or None, idade_min, idade_max, valor_min, valor_max, top_n)
    st.write(f"### Resultados para jogador similar a '{nome}':")
    st.dataframe(resultados)
