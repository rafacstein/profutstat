# %%
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from fuzzywuzzy import fuzz

# %%
# Caminho do CSV (substitua pelo seu caminho real)
caminho_csv = 'https://github.com/rafacstein/profutstat/blob/main/scouting/final_merged_data.csv'
df = pd.read_csv(caminho_csv)

# %%
# Exibir estrutura do dataframe
print(df.info())

# %%
# Lista de colunas numéricas utilizadas na análise
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
    "goalKicks","ballRecovery", "appearances","player.proposedMarketValue", "age", "player.height"]  # MANTENHA A LISTA COMPLETA QUE VOCÊ JÁ DEFINIU AQUI

# Preencher valores nulos com a mediana
df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())

# Normalizar os dados
scaler = StandardScaler()
dados_normalizados = scaler.fit_transform(df[colunas_numericas])

# %%
# Redução de dimensionalidade para visualização
pca = PCA(n_components=2)
dados_pca = pca.fit_transform(dados_normalizados)
df['pca1'] = dados_pca[:, 0]
df['pca2'] = dados_pca[:, 1]

# Visualização
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df, x='pca1', y='pca2', hue='league')  # Ajuste a coluna conforme necessário
plt.title('Distribuição de Atletas no Espaço PCA')
plt.show()

# %%
# Matriz de similaridade
matriz_similaridade = cosine_similarity(dados_normalizados)
df_similaridade = pd.DataFrame(matriz_similaridade, index=df.index, columns=df.index)

# %%
def recomendar_atletas_similares_por_posicao(id_atleta, df, df_similaridade, top_n=5):
    posicao_referencia = df.loc[id_atleta, 'position']
    df_posicao = df[df['position'] == posicao_referencia]
    indices_posicao = df_posicao.index
    similaridades = df_similaridade.loc[id_atleta, indices_posicao].sort_values(ascending=False)
    similaridades = similaridades.drop(id_atleta, errors='ignore')
    top_similares = similaridades.head(top_n)
    return df.loc[top_similares.index]

# %%
# Exemplo de atleta aleatório
atleta_teste = df.sample(1).index[0]
print("Atleta referência:", df.loc[atleta_teste, ['player.name', 'position', 'league']])
recomendacoes = recomendar_atletas_similares_por_posicao(atleta_teste, df, df_similaridade)
print("\nRecomendações:")
print(recomendacoes[['player.name', 'position', 'league', 'age', 'goals', 'minutesPlayed']])

# %%
# Exemplo com nome
player_target = df[df['player.name'].str.contains('Lucas Silva', case=False)].index[0]
recomendacoes = recomendar_atletas_similares_por_posicao(player_target, df, df_similaridade)
print(f"Referência: {df.loc[player_target, 'player.name']} ({df.loc[player_target, 'position']})")
print("\nDMs similares:")
print(recomendacoes[['player.name', 'position', 'age', 'player.team.name', 'goals', 'appearances', 'tackles', 'minutesPlayed']])

# %%
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
            print("⚠️ Atleta não encontrado. Verifique nome e clube.")
            return None

        atleta_id = melhor_match.index[0]
        atleta_ref = df.loc[atleta_id]
        print(f"\n🔍 Atleta referência encontrado: {atleta_ref['player.name']} ({atleta_ref['player.team.name.1']})")
        print(f"📌 Posição: {atleta_ref['position']} | Idade: {atleta_ref['age']} | Valor: {atleta_ref['player.proposedMarketValue']:.2f}M")

        if strict_posicao and posicao is None:
            posicao = atleta_ref['position']
    
    # Aplicar filtros
    filtro = pd.Series(True, index=df.index)
    
    if posicao:
        if isinstance(posicao, str): posicao = [posicao]
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
        print("⚠️ Nenhum atleta encontrado após aplicação dos filtros.")
        return None

    if atleta_id is not None:
        similaridades = df_similaridade.loc[atleta_id, df_filtrado.index].sort_values(ascending=False)
        similaridades = similaridades.drop(atleta_id, errors='ignore')
        indices_recomendados = similaridades.head(top_n).index
        return df.loc[indices_recomendados]
    else:
        print("⚠️ Para recomendação avançada sem referência, implemente lógica adicional (ex: média da posição).")
        return None
