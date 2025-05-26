import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# --- Defina sua lista de colunas para similaridade ---
estatisticas_cols = [
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
    "goalKicks","ballRecovery", "appearances"
]

@st.cache_data(show_spinner=True)
def carregar_dados(path):
    df = pd.read_parquet(path)
    return df

def filtrar_base(df, ligas, posicoes, idade_min, idade_max, valor_min, valor_max):
    cond = (
        (df['league'].isin(ligas)) &
        (df['positions'].isin(posicoes)) &
        (df['age'] >= idade_min) & (df['age'] <= idade_max) &
        (df['proposedMarketValue'] >= valor_min) & (df['proposedMarketValue'] <= valor_max)
    )
    return df[cond].reset_index(drop=True)

def encontrar_similares(df, nome_atleta, n=5):
    # Busca atleta
    base_nome = df[df['player.name'].str.contains(nome_atleta, case=False, na=False)]
    if base_nome.empty:
        return None, f"Nenhum atleta encontrado com nome '{nome_atleta}'"
    
    atleta_ref = base_nome.iloc[0]
    
    # Subset das estatísticas para similaridade
    base_stats = df[estatisticas_cols].fillna(0)
    
    # Normaliza estatísticas
    scaler = StandardScaler()
    base_stats_scaled = scaler.fit_transform(base_stats)
    
    # Encontra índice do atleta de referência
    idx_ref = base_nome.index[0]
    
    # Calcula similaridade pelo cosseno
    sim = cosine_similarity([base_stats_scaled[idx_ref]], base_stats_scaled)[0]
    
    # Ordena índices dos mais similares (exclui o próprio atleta)
    idx_similares = np.argsort(sim)[::-1]
    idx_similares = idx_similares[idx_similares != idx_ref]
    
    # Retorna top n atletas similares
    return df.loc[idx_similares[:n]], None

def main():
    st.title("Recomendação de Atletas Similares - Profutstat")
    
    df = carregar_dados("scouting/final_merged_data.parquet")
    
    ligas = df['league'].dropna().unique().tolist()
    posicoes = df['positions'].dropna().unique().tolist()
    
    idade_min, idade_max = int(df['age'].min()), int(df['age'].max())
    valor_min, valor_max = int(df['proposedMarketValue'].min()), int(df['proposedMarketValue'].max())
    
    st.sidebar.header("Filtros")
    liga_selecionada = st.sidebar.multiselect("Selecione as ligas", ligas, default=ligas)
    posicao_selecionada = st.sidebar.multiselect("Selecione as posições", posicoes, default=posicoes)
    idade_faixa = st.sidebar.slider("Faixa de idade", idade_min, idade_max, (idade_min, idade_max))
    valor_faixa = st.sidebar.slider("Faixa de valor de mercado", valor_min, valor_max, (valor_min, valor_max))
    
    nome_busca = st.text_input("Digite o nome do atleta para referência (busca parcial)", value="")
    
    if st.button("Buscar similares"):
        if nome_busca.strip() == "":
            st.error("Por favor, digite o nome do atleta para referência.")
            return
        
        df_filtrado = filtrar_base(df, liga_selecionada, posicao_selecionada,
                                   idade_faixa[0], idade_faixa[1], valor_faixa[0], valor_faixa[1])
        
        if df_filtrado.empty:
            st.warning("Nenhum atleta encontrado com os filtros selecionados.")
            return
        
        similares, erro = encontrar_similares(df_filtrado, nome_busca, n=5)
        if erro:
            st.warning(erro)
            return
        
        st.write(f"Atletas similares a '{nome_busca}' no conjunto filtrado:")
        st.dataframe(similares)
        
        # Botão para exportar Excel
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            similares.to_excel(writer, index=False, sheet_name='Similares')
        output.seek(0)
        
        st.download_button(label="Baixar relatório Excel", data=output, file_name="atletas_similares.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
