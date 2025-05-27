import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from fuzzywuzzy import fuzz

# Função para carregar e processar dados
@st.cache_data(show_spinner=True)
def carregar_dados(caminho_arquivo):
    df = pd.read_parquet(caminho_arquivo)
    df = df.sample(frac=0.1, random_state=42)  # 10% dos dados
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
    
    df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())
    
    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(df[colunas_numericas])
    
    matriz_similaridade = cosine_similarity(dados_normalizados)
    df_similaridade = pd.DataFrame(matriz_similaridade, index=df.index, columns=df.index)
    
    return df, df_similaridade

# Função de recomendação (adaptada para Streamlit)
def recomendar_atletas_avancado(nome=None, clube=None, df=None, df_similaridade=None,
                              top_n=5, posicao=None, idade_min=None, idade_max=None,
                              valor_min=None, valor_max=None, strict_posicao=True):
    if nome is not None and clube is None:
        st.error("Para busca por nome, deve especificar o clube também")
        return None
    
    if nome is not None:
        df['temp_sim_nome'] = df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
        df['temp_sim_clube'] = df['player.team.name.1'].apply(lambda x: fuzz.token_set_ratio(clube, x))
        df['temp_sim_combinada'] = 0.7*df['temp_sim_nome'] + 0.3*df['temp_sim_clube']
        
        melhor_match = df.nlargest(1, 'temp_sim_combinada')
        df.drop(['temp_sim_nome', 'temp_sim_clube', 'temp_sim_combinada'], axis=1, inplace=True)
        
        if melhor_match.empty or melhor_match['temp_sim_combinada'].iloc[0] < 80:
            st.warning(f"Atleta não encontrado. Verifique nome '{nome}' e clube '{clube}'")
            return None
        
        atleta_id = melhor_match.index[0]
        atleta_ref = df.loc[atleta_id]
        st.write(f"**Atleta referência:** {atleta_ref['player.name']} ({atleta_ref['player.team.name.1']})")
        st.write(f"Posição: {atleta_ref['position']} | Idade: {atleta_ref['age']} | Valor: {atleta_ref['player.proposedMarketValue']:.2f}M")
        
        if strict_posicao and posicao is None:
            posicao = atleta_ref['position']
    else:
        atleta_id = None
    
    mascara_filtros = pd.Series(True, index=df.index)
    
    if posicao is not None:
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
    
    if atleta_id is not None:
        similaridades = df_similaridade.loc[atleta_id].sort_values(ascending=False)
        similaridades = similaridades[mascara_filtros]
        similaridades = similaridades.drop(atleta_id, errors='ignore')
        recomendacoes = df.loc[similaridades.head(top_n).index].copy()
        recomendacoes['similaridade'] = similaridades.head(top_n).values
    else:
        recomendacoes = df[mascara_filtros].sample(min(top_n, len(df[mascara_filtros]))).copy()
        recomendacoes['similaridade'] = None
    
    return recomendacoes

# --- Streamlit app ---
st.title("🔍 Recomendador de Atletas ProfutStat")

# Upload arquivo local (ou use caminho fixo aqui)
arquivo = st.file_uploader("Faça upload do arquivo .parquet", type=['parquet'])

if arquivo is not None:
    with st.spinner('Carregando dados...'):
        df, df_similaridade = carregar_dados(arquivo)
    
    with st.sidebar:
        st.header("Filtros de Recomendação")
        nome = st.text_input("Nome do atleta referência")
        clube = st.text_input("Clube do atleta referência")
        posicao = st.text_input("Posição (ex: DL)")
        idade_min = st.number_input("Idade mínima", min_value=0, max_value=50, value=0)
        idade_max = st.number_input("Idade máxima", min_value=0, max_value=50, value=50)
        valor_min = st.number_input("Valor mínimo (milhões)", min_value=0.0, value=0.0)
        valor_max = st.number_input("Valor máximo (milhões)", min_value=0.0, value=1000.0)
        top_n = st.slider("Número de recomendações", min_value=1, max_value=20, value=5)
    
    if st.button("Gerar Recomendações"):
        resultado = recomendar_atletas_avancado(
            nome=nome if nome else None,
            clube=clube if clube else None,
            df=df,
            df_similaridade=df_similaridade,
            top_n=top_n,
            posicao=posicao if posicao else None,
            idade_min=idade_min,
            idade_max=idade_max,
            valor_min=valor_min,
            valor_max=valor_max,
            strict_posicao=True
        )
        if resultado is not None and not resultado.empty:
            st.dataframe(resultado[['player.name', 'player.team.name.1', 'position', 'age', 'player.proposedMarketValue', 'minutesPlayed', 'similaridade']])
        else:
            st.write("Nenhuma recomendação encontrada com os filtros aplicados.")
else:
    st.info("Por favor, faça upload do arquivo Parquet para iniciar.")
