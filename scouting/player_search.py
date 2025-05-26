import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import pyarrow.parquet as pq
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz

st.set_page_config(page_title="Football Scout", page_icon="⚽")

@st.cache_data
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

# Colunas numéricas para análise e normalização
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

# Preencher NAs e normalizar
df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())
scaler = StandardScaler()
dados_normalizados = scaler.fit_transform(df[colunas_numericas])

# Calcular matriz de similaridade
similaridade = cosine_similarity(dados_normalizados)
df_similaridade = pd.DataFrame(similaridade, index=df.index, columns=df.index)

# Interface para filtro
st.title("Football Scout - Recomendação de Jogadores Similares")

nome_input = st.text_input("Nome do atleta (deixe vazio para ignorar):").strip()
idade_min = st.number_input("Idade mínima", min_value=10, max_value=50, value=15)
idade_max = st.number_input("Idade máxima", min_value=10, max_value=50, value=40)
posicoes = df['position'].dropna().unique()
posicao_selecionada = st.selectbox("Selecione posição (opcional)", options=["Todas"] + list(posicoes))

# Filtragem básica por idade e posição
filtro = (df['age'] >= idade_min) & (df['age'] <= idade_max)
if posicao_selecionada != "Todas":
    filtro &= (df['position'] == posicao_selecionada)

df_filtrado = df[filtro]

def encontrar_atleta_por_nome(nome, df):
    if nome == "":
        return None
    # fuzzy matching: pegar o mais parecido
    df['similaridade_nome'] = df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome.lower(), str(x).lower()))
    melhor = df['similaridade_nome'].idxmax()
    if df.loc[melhor, 'similaridade_nome'] < 60:
        return None
    return melhor

id_referencia = encontrar_atleta_por_nome(nome_input, df_filtrado)

if id_referencia is None and nome_input != "":
    st.warning("Atleta não encontrado no filtro atual. Tente ajustar o nome ou filtros.")
elif id_referencia is None:
    st.info("Digite um nome para obter recomendações, ou ajuste os filtros.")
else:
    # pegar similares na mesma posição dentro do filtro
    pos_ref = df.loc[id_referencia, 'position']
    df_mesma_posicao = df_filtrado[df_filtrado['position'] == pos_ref]

    similaridades = df_similaridade.loc[id_referencia, df_mesma_posicao.index].sort_values(ascending=False)
    similaridades = similaridades.drop(id_referencia, errors='ignore')

    top5 = similaridades.head(5).index
    recomendados = df.loc[top5, ['player.name', 'position', 'age', 'player.team.name.1', 'player.proposedMarketValue']]

    st.write(f"Recomendações similares para **{df.loc[id_referencia, 'player.name']}** ({pos_ref}):")
    st.dataframe(recomendados.reset_index(drop=True))

