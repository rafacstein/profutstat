import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import faiss
import streamlit as st # Importa o Streamlit
from fuzzywuzzy import fuzz
import matplotlib.pyplot as plt
import seaborn as sns # Mantido para qualquer visualização futura, embora não usada na UI principal


# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="ProFutStat: Recomendador de Atletas",
    page_icon="⚽",
    layout="wide" # Ocupa a largura total da tela
)

# --- Carregamento de Dados e Inicialização do Modelo (Cacheado para Performance) ---

@st.cache_resource # Usa cache_resource para carregar o dataframe e o modelo FAISS uma única vez
def load_data_and_model():
    """Carrega os dados e inicializa o scaler e o índice FAISS."""
    # Ler o arquivo Parquet (ajuste o caminho se necessário no Hugging Face Spaces)
    try:
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet')
    except FileNotFoundError:
        st.error("Erro: Arquivo 'final_merged_data.parquet' não encontrado. Certifique-se de que ele está no diretório correto.")
        st.stop() # Para a execução do script se o arquivo não for encontrado

    # Selecionar apenas colunas numéricas relevantes para a similaridade
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

    # Preencher valores nulos (ajuste a estratégia conforme necessário)
    df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())

    # Normalizar os dados
    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(df[colunas_numericas])
    dados_normalizados = dados_normalizados.astype('float32') # FAISS precisa de float32

    # Construir o índice FAISS
    dimension = dados_normalizados.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(dados_normalizados)

    return df, scaler, index, dados_normalizados

df, scaler, faiss_index, dados_normalizados = load_data_and_model()

# --- Função de Recomendação Adaptada para Streamlit ---

def recomendar_atletas_avancado(nome=None, clube=None, top_n=10, posicao=None,
                                 idade_min=None, idade_max=None,
                                 valor_min=None, valor_max=None, strict_posicao=True):
    """
    Recomenda atletas similares com múltiplos filtros usando FAISS.
    """
    
    # Verifica se o DataFrame e o índice FAISS foram carregados corretamente
    if df is None or faiss_index is None:
        st.error("Dados ou modelo não carregados. Por favor, tente novamente mais tarde.")
        return pd.DataFrame()

    atleta_id = None
    atleta_ref_name = None
    atleta_ref_club = None

    if nome and clube: # Verifica se nome e clube foram fornecidos
        df['temp_sim_nome'] = df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
        df['temp_sim_clube'] = df['player.team.name.1'].apply(lambda x: fuzz.token_set_ratio(clube, x))
        df['temp_sim_combinada'] = 0.7 * df['temp_sim_nome'] + 0.3 * df['temp_sim_clube']
        
        melhor_match = df.nlargest(1, 'temp_sim_combinada')
        
        if not melhor_match.empty and melhor_match['temp_sim_combinada'].iloc[0] >= 80:
            atleta_id = melhor_match.index[0]
            atleta_ref = df.loc[atleta_id]
            atleta_ref_name = atleta_ref['player.name']
            atleta_ref_club = atleta_ref['player.team.name.1']
            st.success(f"🔍 Atleta referência encontrado: **{atleta_ref_name}** ({atleta_ref_club})")
            st.write(f"📌 Posição: {atleta_ref['position']} | Idade: {int(atleta_ref['age'])} | Valor: ${atleta_ref['player.proposedMarketValue']:.2f}M")
            
            if strict_posicao and posicao is None:
                posicao = [atleta_ref['position']] # Garante que posicao seja uma lista
        else:
            st.warning(f"⚠️ Atleta referência não encontrado. Verifique o nome '{nome}' e o clube '{clube}'. Buscando apenas por filtros.")
            atleta_id = None # Garante que não usará o atleta de referência
        
        # Limpar colunas temporárias
        df.drop(columns=['temp_sim_nome', 'temp_sim_clube', 'temp_sim_combinada'], inplace=True)
    else:
        st.info("Nenhum atleta de referência fornecido. Buscando recomendações apenas pelos critérios de busca.")


    # Aplicar filtros
    mascara_filtros = pd.Series(True, index=df.index)
    
    if posicao: # Se a lista de posições não estiver vazia
        mascara_filtros &= df['position'].isin(posicao)
    
    if idade_min is not None:
        mascara_filtros &= df['age'] >= idade_min
    if idade_max is not None:
        mascara_filtros &= df['age'] <= idade_max
    
    if valor_min is not None:
        mascara_filtros &= df['player.proposedMarketValue'] >= valor_min
    if valor_max is not None:
        mascara_filtros &= df['player.proposedMarketValue'] <= valor_max
    
    indices_filtrados = df[mascara_filtros].index.tolist()

    if not indices_filtrados:
        st.warning("Nenhum atleta encontrado com os filtros especificados.")
        return pd.DataFrame()
    
    # Obter recomendações
    if atleta_id is not None:
        # Baseado em similaridade com atleta referência
        query_vector = dados_normalizados[df.index.get_loc(atleta_id)].reshape(1, -1)
        
        # Busca um número maior para garantir resultados após filtragem
        D, I = faiss_index.search(query_vector, max(top_n * 5, len(indices_filtrados))) 

        similaridades = D[0]
        indices_retornados = I[0]
        
        recomendacoes_brutas = pd.DataFrame({
            'original_index': indices_retornados,
            'similaridade': similaridades
        })
        
        recomendacoes_finais = recomendacoes_brutas[
            recomendacoes_brutas['original_index'].isin(indices_filtrados) & 
            (recomendacoes_brutas['original_index'] != atleta_id)
        ]
        
        recomendacoes_finais = recomendacoes_finais.sort_values(by='similaridade', ascending=False).head(top_n)
        
        if recomendacoes_finais.empty:
            st.warning("Nenhuma recomendação encontrada após aplicar filtros de similaridade.")
            return pd.DataFrame()
            
        recomendacoes = df.loc[recomendacoes_finais['original_index']]
        recomendacoes['similaridade'] = recomendacoes_finais['similaridade'].values
        
    else:
        # Caso não tenha atleta referência (busca apenas pelos filtros)
        st.info("Mostrando atletas que atendem aos filtros, sem similaridade de referência.")
        if len(indices_filtrados) < top_n:
            st.info(f"Apenas {len(indices_filtrados)} atletas encontrados com os filtros. Mostrando todos.")
        
        recomendacoes = df.loc[indices_filtrados].sample(n=min(top_n, len(indices_filtrados)), random_state=42)
        recomendacoes['similaridade'] = np.nan # Não há similaridade sem um ponto de referência
    
    # Selecionar e ordenar colunas para exibição
    cols_display = ['player.name', 'player.team.name.1', 'position', 'age', 'player.proposedMarketValue']
    if atleta_id is not None: # Adiciona 'similaridade' apenas se houver um atleta de referência
        cols_display.append('similaridade')
        # Formata a similaridade para exibição
        recomendacoes['similaridade'] = recomendacoes['similaridade'].apply(lambda x: f"{x:.2f}")
    
    # Formatar valor de mercado
    recomendacoes['player.proposedMarketValue'] = recomendacoes['player.proposedMarketValue'].apply(lambda x: f"${x:.2f}M")
    
    # Renomear colunas para exibição amigável
    recomendacoes = recomendacoes.rename(columns={
        'player.name': 'Nome do Atleta',
        'player.team.name.1': 'Clube',
        'position': 'Posição',
        'age': 'Idade',
        'player.proposedMarketValue': 'Valor de Mercado (M€)',
        'similaridade': 'Similaridade'
    })

    return recomendacoes[cols_display].sort_values(by='Similaridade', ascending=False, na_position='last').reset_index(drop=True)

# --- Layout da Aplicação Streamlit ---

# Título e Logo
col1, col2 = st.columns([1, 6])
with col1:
    # Ajuste o caminho da logo para o Hugging Face Spaces
    try:
        st.image("https://github.com/rafacstein/profutstat/raw/main/scouting/profutstat_logo.png", width=100)
    except FileNotFoundError:
        st.warning("Logo 'profutstat_logo.png' não encontrada.")
with col2:
    st.title("⚽ ProFutStat: Recomendador de Atletas")

st.markdown("---")

# Seção de Atleta de Referência e Critérios de Busca
st.header("Critérios de Busca")

col_ref, col_filters = st.columns(2)

with col_ref:
    st.subheader("Atleta de Referência")
    nome_atleta = st.text_input("Nome do Atleta", placeholder="Ex: Lionel Messi")
    clube_atleta = st.text_input("Clube do Atleta", placeholder="Ex: Inter Miami CF")

with col_filters:
    st.subheader("Filtros Adicionais")
    posicoes_choices = ['GK','DL', 'DC', 'DR', 'DM', 'MC', 'ML', 'MR', 'AM','LW', 'RW', 'ST']
    posicao_selecionada = st.multiselect(
        "Posição(ões)",
        options=posicoes_choices,
        help="Selecione uma ou mais posições. Se um atleta de referência for fornecido, a posição dele será usada como filtro principal a menos que 'strict_posicao' seja False (não implementado como opção na UI para simplicidade, mas a lógica está lá)."
    )

    col_idade_min, col_idade_max = st.columns(2)
    with col_idade_min:
        idade_min_val = st.number_input("Idade Mínima", min_value=15, max_value=45, value=18, step=1)
    with col_idade_max:
        idade_max_val = st.number_input("Idade Máxima", min_value=15, max_value=45, value=35, step=1)

    col_valor_min, col_valor_max = st.columns(2)
    with col_valor_min:
        valor_min_val = st.number_input("Valor Mínimo (M€)", min_value=0.1, max_value=200.0, value=1.0, step=0.1, format="%.1f")
    with col_valor_max:
        valor_max_val = st.number_input("Valor Máximo (M€)", min_value=0.1, max_value=200.0, value=50.0, step=0.1, format="%.1f")

st.markdown("---")

# Botão de Recomendação
if st.button("🔎 Recomendar Atletas", type="primary"):
    with st.spinner("Buscando recomendações..."):
        recomendacoes = recomendar_atletas_avancado(
            nome=nome_atleta,
            clube=clube_atleta,
            posicao=posicao_selecionada,
            idade_min=idade_min_val,
            idade_max=idade_max_val,
            valor_min=valor_min_val,
            valor_max=valor_max_val,
            top_n=10 # Você pode tornar isso um slider na UI se quiser
        )
        
        if not recomendacoes.empty:
            st.subheader("Atletas Recomendados")
            st.dataframe(recomendacoes, use_container_width=True)
        else:
            st.info("Nenhuma recomendação encontrada com os critérios fornecidos.")

st.markdown("---")
st.write("Powered by ProFutStat")
