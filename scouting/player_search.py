import streamlit as st
import pandas as pd
import numpy as np
import faiss
from sklearn.preprocessing import StandardScaler
from fuzzywuzzy import fuzz
import os # To check for file existence

st.set_page_config(layout="wide", page_title="PlayerScout IA")

st.title("⚽ PlayerScout IA - Encontre o Talento Ideal!")

# --- Data Loading and Preprocessing ---

# Use st.cache_data for functions that return data frames or other data structures
# This ensures data is loaded and processed only once
@st.cache_data
def load_data():
    try:
        # pandas can read parquet directly from a URL
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet')
        return df
    except Exception as e:
        st.error(f"Error loading data from URL: {e}")
        st.error("Please ensure the URL is correct and the file is accessible.")
        return None

@st.cache_data
def preprocess_data(df_in):
    # Select numerical columns
    X = df_in[["rating", "totalRating", "countRating", "goals", "bigChancesCreated", "bigChancesMissed", "assists",
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
                "goalKicks","ballRecovery", "appearances","player.proposedMarketValue", "age", "player.height"]]

    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled.astype('float32'), X.columns

# Use st.cache_resource for objects that should be persisted across reruns
# like FAISS indexes
@st.cache_resource
def build_faiss_index(features):
    # Ensure float32 and C-contiguous
    features = np.ascontiguousarray(features.astype('float32'))
    index = faiss.IndexFlatIP(features.shape[1])  # IP = Inner Product
    faiss.normalize_L2(features) # Normalize for cosine similarity (equivalent to IP with normalized vectors)
    index.add(features)
    return index

df = load_data()

if df is not None:
    with st.spinner("Preparando os dados..."):
        features, feature_columns = preprocess_data(df.copy()) # Pass a copy to avoid modifying original df
        faiss_index = build_faiss_index(features)

    st.success("Dados carregados e índice FAISS construído!")

    # --- Recommendation Function ---
    def recomendar_faiss(nome, clube=None, posicao=None, idade_min=None, idade_max=None,
                         valor_min=None, valor_max=None, top_n=5, dataframe=df, faiss_idx=faiss_index, feats=features):
        
        temp_df = dataframe.copy() # Work on a copy to avoid modifying the cached dataframe
        
        # Fuzzy matching for player name
        temp_df['sim_nome'] = temp_df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
        
        if clube:
            temp_df['sim_clube'] = temp_df['player.team.name.1'].apply(lambda x: fuzz.token_set_ratio(clube, x))
            temp_df['sim_total'] = 0.7 * temp_df['sim_nome'] + 0.3 * temp_df['sim_clube']
        else:
            temp_df['sim_total'] = temp_df['sim_nome']
        
        # Find the reference player
        if temp_df['sim_total'].max() == 0: # If no player found with given name
            st.warning(f"Jogador '{nome}' não encontrado na base de dados. Tentando encontrar os mais próximos...")
            # Fallback: if no strong name match, just pick the top name match for initial search
            jogador_ref = temp_df.loc[temp_df['sim_nome'].idxmax()]
        else:
            jogador_ref = temp_df.loc[temp_df['sim_total'].idxmax()]
        
        idx_ref = jogador_ref.name
        vetor_ref = feats[idx_ref].reshape(1, -1)
        
        # Search FAISS index
        D, I = faiss_idx.search(vetor_ref, 200) # Search a larger pool for filtering
        similares = dataframe.iloc[I[0]].copy() # Use the original dataframe for iloc
        similares['similaridade'] = D[0]
        
        # Apply filters
        # Ensure 'position' column is handled correctly (split by comma and take first)
        if posicao:
            similares['main_position'] = similares['position'].str.split(',').str[0].str.strip()
            similares = similares[similares['main_position'] == posicao]
        
        if idade_min:
            similares = similares[similares['age'] >= idade_min]
        if idade_max:
            similares = similares[similares['age'] <= idade_max]
        if valor_min:
            similares = similares[similares['player.proposedMarketValue'] >= valor_min]
        if valor_max:
            similares = similares[similares['player.proposedMarketValue'] <= valor_max]
        
        # Exclude the reference player from results
        similares = similares[similares.index != idx_ref]

        if similares.empty:
            return pd.DataFrame() # Return empty DataFrame if no matches after filtering
            
        return similares.nlargest(top_n, 'similaridade')[[
            'player.name', 'player.team.name.1', 'position', 'player.country.name','age','minutesPlayed',
            'player.proposedMarketValue', 'similaridade'
        ]]

    # --- Streamlit UI ---
    st.header("Parâmetros de Busca")

    col1, col2, col3 = st.columns(3)

    with col1:
        player_name = st.text_input("Nome do Jogador de Referência", "Mandaca")
        player_club = st.text_input("Clube (Opcional)", "Juventude")
        
        # Get unique positions from your data for the selectbox
        all_positions = df['position'].str.split(',').explode().str.strip().unique()
        all_positions = sorted([p for p in all_positions if p]) # Remove empty strings and sort
        
        selected_position = st.selectbox("Posição (Opcional)", [""] + list(all_positions)) # Add empty option

    with col2:
        min_age, max_age = st.slider(
            "Faixa Etária (Anos)",
            min_value=15,
            max_value=45,
            value=(20, 30)
        )
        min_value, max_value = st.slider(
            "Valor de Mercado (Opcional - Em milhões)",
            min_value=0,
            max_value=100000000, # Assuming max value in your dataset is around this
            value=(0, 2000000), # Default range
            step=100000
        )
        num_recommendations = st.number_input("Número de Recomendações", min_value=1, max_value=20, value=10)

    st.markdown("---")

    if st.button("Buscar Recomendações"):
        if not player_name:
            st.warning("Por favor, insira o nome do jogador de referência.")
        else:
            with st.spinner("Buscando jogadores semelhantes..."):
                recommendations = recomendar_faiss(
                    nome=player_name,
                    clube=player_club if player_club else None,
                    posicao=selected_position if selected_position else None,
                    idade_min=min_age,
                    idade_max=max_age,
                    valor_min=min_value,
                    valor_max=max_value,
                    top_n=num_recommendations
                )
            
            if not recommendations.empty:
                st.subheader(f"Jogadores Semelhantes a {player_name}:")
                # Format market value for better display
                recommendations['player.proposedMarketValue'] = recommendations['player.proposedMarketValue'].apply(
                    lambda x: f"€{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )
                st.dataframe(recommendations)
            else:
                st.info("Nenhum jogador encontrado com os filtros especificados.")

else:
    st.error("Não foi possível carregar os dados. Verifique o arquivo 'final_merged_data.parquet'.")
