import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import pyarrow.parquet as pq
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from fuzzywuzzy import fuzz

# Configuração da página
st.set_page_config(page_title="Football Scout", page_icon="⚽")

@st.cache_data
def load_parquet_from_github(url):
    """
    Carrega arquivo Parquet do GitHub com verificação robusta
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        if not response.content[:4] == b'PAR1':
            st.error("O arquivo não parece ser um Parquet válido")
            return None
        buffer = BytesIO(response.content)
        table = pq.read_table(buffer)
        return table.to_pandas()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao baixar arquivo: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro ao ler Parquet: {str(e)}")
        return None

# Interface Streamlit
st.title("⚽ Football Scout")

GITHUB_URL = "https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/final_merged_data.parquet"

with st.spinner("Carregando dados..."):
    df = load_parquet_from_github(GITHUB_URL)

if df is not None:
    st.success("Dados carregados com sucesso!")
    st.write(f"Total de jogadores: {len(df)}")
    st.dataframe(df.head())

    # Lista das colunas numéricas para análise
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

    # Preencher valores nulos com mediana para as colunas numéricas
    df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())

    # Normalizar dados numéricos
    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(df[colunas_numericas])

    # Aplicar PCA para reduzir dimensionalidade a 2 componentes para visualização
    pca = PCA(n_components=2)
    dados_pca = pca.fit_transform(dados_normalizados)
    df['pca1'] = dados_pca[:, 0]
    df['pca2'] = dados_pca[:, 1]

    # Visualização com seaborn
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=df, x='pca1', y='pca2', hue='league')  # Ajuste o nome da coluna 'league' se for diferente
    plt.title('Distribuição de Atletas no Espaço PCA')
    st.pyplot(plt)

    # Calcular matriz de similaridade (cosseno)
    matriz_similaridade = cosine_similarity(dados_normalizados)
    df_similaridade = pd.DataFrame(matriz_similaridade, index=df.index, columns=df.index)

    def recomendar_atletas_similares_por_posicao(id_atleta, df, df_similaridade, top_n=5):
        posicao_referencia = df.loc[id_atleta, 'position']
        df_posicao = df[df['position'] == posicao_referencia]
        indices_posicao = df_posicao.index
        similaridades = df_similaridade.loc[id_atleta, indices_posicao].sort_values(ascending=False)
        similaridades = similaridades.drop(id_atleta, errors='ignore')
        top_similares = similaridades.head(top_n)
        return df.loc[top_similares.index]

    # Exemplo de uso da recomendação
    atleta_teste = df.sample(1).index[0]
    st.write("Atleta referência:")
    st.write(df.loc[atleta_teste, ['player.name', 'position', 'league']])

    recomendacoes = recomendar_atletas_similares_por_posicao(atleta_teste, df, df_similaridade)
    st.write("Recomendações similares:")
    st.dataframe(recomendacoes[['player.name', 'position', 'league', 'age', 'goals', 'minutesPlayed']])

    # Função de recomendação avançada com filtros (usando fuzzywuzzy para busca aproximada)
    def recomendar_atletas_avancado(nome=None, clube=None, df=None, df_similaridade=None,
                                     top_n=5, posicao=None, idade_min=None, idade_max=None,
                                     valor_min=None, valor_max=None, strict_posicao=True):

        if nome is not None and clube is None:
            raise ValueError("Se fornecer o nome, deve fornecer também o clube.")

        atleta_id = None

        if nome is not None:
            df['temp_sim_nome'] = df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
            df['temp_sim_clube'] = df['player.team.name.1'].apply(lambda x: fuzz.token_set_ratio(clube, x))
            df['temp_sim_combinada'] = 0.7 * df['temp_sim_nome'] + 0.3 * df['temp_sim_clube']
            melhor_match = df.nlargest(1, 'temp_sim_combinada')
            df.drop(['temp_sim_nome', 'temp_sim_clube', 'temp_sim_combinada'], axis=1, inplace=True)

            if melhor_match.empty or melhor_match.index[0] not in df.index:
                st.warning("⚠️ Atleta não encontrado. Verifique nome e clube.")
                return None

            atleta_id = melhor_match.index[0]
            atleta_ref = df.loc[atleta_id]
            st.write(f"🔍 Atleta referência encontrado: {atleta_ref['player.name']} ({atleta_ref['player.team.name.1']})")
            st.write(f"📌 Posição: {atleta_ref['position']} | Idade: {atleta_ref['age']} | Valor: {atleta_ref['player.proposedMarketValue']:.2f}M")

            if strict_posicao and posicao is None:
                posicao = atleta_ref['position']

        filtro = pd.Series(True, index=df.index)

        if posicao:
            if isinstance(posicao, str):
                posicao = [posicao]
            filtro &= df['position'].isin(posicao)

        if idade_min is not None:
            filtro &= df['age'] >= idade_min
        if idade_max is not None:
            filtro &= df['age'] <= idade_max

        if valor_min is not None:
            filtro &= df['player.proposedMarketValue'] >= valor_min
        if valor_max is not None:
            filtro &= df['player.proposedMarketValue'] <= valor_max

        df_filtrado = df[filtro]

        if df_filtrado.empty:
            st.warning("⚠️ Nenhum atleta encontrado após aplicação dos filtros.")
            return None

        if atleta_id is not None:
            similaridades = df_similaridade.loc[atleta_id, df_filtrado.index].sort_values(ascending=False)
            similaridades = similaridades.drop(atleta_id, errors='ignore')
            indices_recomendados = similaridades.head(top_n).index
            return df.loc[indices_recomendados]
        else:
            st.info("⚠️ Para recomendação avançada sem referência, implemente lógica adicional.")
            return None

else:
    st.error("Falha ao carregar os dados. Verifique:")
    st.markdown("""
    1. O link do GitHub está correto?
    2. O arquivo é um Parquet válido?
    3. O arquivo não está corrompido?
    """)

