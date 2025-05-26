import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import pyarrow.parquet as pq
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz

st.set_page_config(page_title="Football Scout", page_icon="⚽")

@st.cache_data(show_spinner=True)
def load_parquet_from_github(url):
    response = requests.get(url)
    response.raise_for_status()
    buffer = BytesIO(response.content)
    table = pq.read_table(buffer)
    return table.to_pandas()

# URL do parquet no GitHub
GITHUB_URL = "https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/final_merged_data.parquet"

# Carrega dados
with st.spinner("Carregando dados..."):
    df = load_parquet_from_github(GITHUB_URL)

# Verifique se as colunas existem mesmo:
required_cols = ['player.name', 'age', 'position', 'player.team.name.1', 'player.proposedMarketValue']
for c in required_cols:
    if c not in df.columns:
        st.error(f"Coluna obrigatória '{c}' não encontrada no dataframe!")
        st.stop()

# Colunas numéricas para análise e normalização (ajuste se precisar)
colunas_numericas = [
    "rating", "totalRating", "countRating", "goals", "bigChancesCreated", "bigChancesMissed", "assists",
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
    "goalKicks","ballRecovery", "appearances","player.proposedMarketValue", "age", "player.height"
]

# Ajuste colunas faltantes (caso haja)
colunas_numericas_existentes = [c for c in colunas_numericas if c in df.columns]

# Preencher NAs e normalizar
df[colunas_numericas_existentes] = df[colunas_numericas_existentes].fillna(df[colunas_numericas_existentes].median())
scaler = StandardScaler()
dados_normalizados = scaler.fit_transform(df[colunas_numericas_existentes])

similaridade = cosine_similarity(dados_normalizados)
df_similaridade = pd.DataFrame(similaridade, index=df.index, columns=df.index)

# Interface
st.title("Football Scout - Recomendação de Jogadores Similares")

nome_input = st.text_input("Nome do atleta (deixe vazio para ignorar):").strip()
idade_min = st.number_input("Idade mínima", min_value=10, max_value=50, value=15)
idade_max = st.number_input("Idade máxima", min_value=10, max_value=50, value=40)
posicoes = df['position'].dropna().unique()
posicao_selecionada = st.selectbox("Selecione posição (opcional)", options=["Todas"] + list(posicoes))

# Filtro idade e posição
filtro = (df['age'] >= idade_min) & (df['age'] <= idade_max)
if posicao_selecionada != "Todas":
    filtro &= (df['position'] == posicao_selecionada)

df_filtrado = df[filtro].copy()

def encontrar_atleta_por_nome(nome, df_local):
    if nome == "":
        return None
    # fuzzy matching: pegar o mais parecido
    df_local = df_local.copy()  # evitar warning
    df_local['similaridade_nome'] = df_local['player.name'].apply(lambda x: fuzz.token_set_ratio(nome.lower(), str(x).lower()))
    melhor = df_local['similaridade_nome'].idxmax()
    if df_local.loc[melhor, 'similaridade_nome'] < 60:
        return None
    return melhor

id_referencia = encontrar_atleta_por_nome(nome_input, df_filtrado)

if id_referencia is None and nome_input != "":
    st.warning("Atleta não encontrado no filtro atual. Tente ajustar o nome ou filtros.")
elif id_referencia is None:
    st.info("Digite um nome para obter recomendações, ou ajuste os filtros.")
else:
    pos_ref = df.loc[id_referencia, 'position']
    df_mesma_pos = df_filtrado[df_filtrado['position'] == pos_ref]

    similaridades = df_similaridade.loc[id_referencia, df_mesma_pos.index].sort_values(ascending=False)
    similaridades = similaridades.drop(id_referencia, errors='ignore')

    top5 = similaridades.head(5).index
    recomendados = df.loc[top5, ['player.name', 'position', 'age', 'player.team.name.1', 'player.proposedMarketValue']]

    st.write(f"Recomendações similares para **{df.loc[id_referencia, 'player.name']}** ({pos_ref}):")
    st.dataframe(recomendados.reset_index(drop=True))
