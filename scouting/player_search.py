import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import faiss
import streamlit as st
from fuzzywuzzy import fuzz

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="ProFutStat: Scout de Atletas",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- CSS Customizado para Estilo Profissional ---
st.markdown(
    """
    <style>
    /* Estilos Gerais */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333333;
    }
    .stApp {
        background-color: #f0f2f6;
    }

    /* Cabeçalho - Logo e Título */
    .header-section {
        display: flex;
        align-items: center;
        gap: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 30px;
    }
    .header-section h1 {
        font-size: 2.8em; /* Ajuste o tamanho da fonte para o título principal */
        color: #004d99; /* Azul corporativo */
        margin: 0;
        line-height: 1.2;
    }

    /* Subtítulos */
    h2 {
        color: #0056b3;
        font-size: 1.8em;
        border-bottom: 2px solid #0056b3;
        padding-bottom: 5px;
        margin-bottom: 20px;
    }
    h3 {
        color: #0056b3;
        font-size: 1.4em;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* Botões */
    .stButton>button {
        background-color: #28a745; /* Verde para ação principal */
        color: white;
        border-radius: 8px;
        padding: 10px 25px;
        font-size: 1.1em;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #218838;
    }

    /* Dataframe */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .dataframe th {
        background-color: #e9ecef;
        color: #495057;
        font-weight: bold;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f8f9fa;
    }

    /* Mensagens de feedback */
    .stAlert {
        border-radius: 8px;
    }

    /* Controles de Input */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stMultiSelect>div>div>div>div {
        border-radius: 8px;
        border: 1px solid #ced4da;
        padding: 8px 12px;
    }
    .stSlider > div > div > div:nth-child(2) > div {
        background-color: #007bff; /* Cor do slider */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Carregamento de Dados e Inicialização do Modelo (Cacheado para Performance) ---

@st.cache_resource
def load_data_and_model():
    """Carrega os dados e inicializa o scaler e o índice FAISS."""
    try:
        # Usando o link raw do GitHub para acesso direto
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet')
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de dados. Por favor, verifique o link ou a conexão: {e}")
        st.stop()

    # Selecionar apenas colunas numéricas relevantes para a similaridade
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

    # --- VERIFICAÇÃO DE COLUNAS (AJUSTADA PARA URL) ---
    # É CRUCIAL que os nomes das colunas aqui correspondam EXATAMENTE aos nomes no seu arquivo parquet.
    # O erro 'accurateOppositionHalfHalfPasses' foi corrigido para 'accurateOppositionHalfPasses'
    # conforme a correção anterior, caso não seja o nome exato no seu parquet, ajuste aqui.
    missing_columns = [col for col in colunas_numericas if col not in df.columns]
    if missing_columns:
        st.error(f"Erro: As seguintes colunas numéricas essenciais não foram encontradas no arquivo de dados: **{', '.join(missing_columns)}**")
        st.info("Por favor, verifique se os nomes das colunas na lista `colunas_numericas` correspondem exatamente aos nomes no seu arquivo Parquet.")
        st.stop()

    df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())

    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(df[colunas_numericas])
    dados_normalizados = dados_normalizados.astype('float32')

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
    
    if df is None or faiss_index is None:
        st.error("Dados ou modelo não carregados. Por favor, tente novamente mais tarde.")
        return pd.DataFrame()

    atleta_id = None
    atleta_ref_name = None
    atleta_ref_club = None

    if nome and clube:
        # Copia do DF para evitar SettingWithCopyWarning ao adicionar colunas temporárias
        df_temp = df.copy() 
        df_temp['temp_sim_nome'] = df_temp['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
        df_temp['temp_sim_clube'] = df_temp['player.team.name.1'].apply(lambda x: fuzz.token_set_ratio(clube, x))
        df_temp['temp_sim_combinada'] = 0.7 * df_temp['temp_sim_nome'] + 0.3 * df_temp['temp_sim_clube']
        
        melhor_match = df_temp.nlargest(1, 'temp_sim_combinada')
        
        if not melhor_match.empty and melhor_match['temp_sim_combinada'].iloc[0] >= 80:
            atleta_id = melhor_match.index[0]
            atleta_ref = df.loc[atleta_id] # Usa o DF original para o atleta de referência
            atleta_ref_name = atleta_ref['player.name']
            atleta_ref_club = atleta_ref['player.team.name.1']
            st.success(f"🔍 Atleta de Referência: **{atleta_ref_name}** ({atleta_ref_club}) encontrado.")
            st.info(f"Posição: {atleta_ref['position']} | Idade: {int(atleta_ref['age'])} | Valor: **${atleta_ref['player.proposedMarketValue']:.2f}M**")
            
            if strict_posicao and posicao is None:
                posicao = [atleta_ref['position']]
        else:
            st.warning(f"⚠️ Atleta de referência '{nome}' do clube '{clube}' não encontrado com alta confiança. Buscando apenas por critérios de filtro.")
            atleta_id = None
    else:
        st.info("Nenhum atleta de referência fornecido. Buscando recomendações apenas pelos critérios de busca.")

    mascara_filtros = pd.Series(True, index=df.index)
    
    if posicao:
        mascara_filtros &= df['position'].isin(posicao)
    
    if idade_min is not None:
        mascara_filtros &= df['age'] >= idade_min
    if idade_max is not None:
        mascara_filtros &= df['age'] <= idade_max
    
    # Converter valores de mercado de volta para o formato original para filtragem
    if valor_min is not None:
        mascara_filtros &= df['player.proposedMarketValue'] >= valor_min
    if valor_max is not None:
        mascara_filtros &= df['player.proposedMarketValue'] <= valor_max
    
    indices_filtrados = df[mascara_filtros].index.tolist()

    if not indices_filtrados:
        st.warning("Nenhum atleta corresponde aos filtros especificados. Tente ajustar os critérios.")
        return pd.DataFrame()
    
    # Obter recomendações
    if atleta_id is not None:
        query_vector = dados_normalizados[df.index.get_loc(atleta_id)].reshape(1, -1)
        
        D, I = faiss_index.search(query_vector, max(top_n * 5, len(indices_filtrados) + 1)) 

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
            st.info(f"Nenhuma recomendação similar ao atleta **{atleta_ref_name}** encontrada com os filtros aplicados. Tente ajustar os critérios ou o atleta de referência.")
            return pd.DataFrame()
            
        recomendacoes = df.loc[recomendacoes_finais['original_index']].copy() # Usar .copy() para evitar SettingWithCopyWarning
        recomendacoes['similaridade'] = recomendacoes_finais['similaridade'].values
        
    else:
        st.info("Mostrando atletas que atendem aos filtros. Para recomendações por similaridade, forneça um atleta de referência.")
        if len(indices_filtrados) < top_n:
            st.info(f"Apenas {len(indices_filtrados)} atletas encontrados com os filtros, mostrando todos.")
        
        # Amostrar diretamente do DataFrame filtrado
        recomendacoes = df.loc[indices_filtrados].sample(n=min(top_n, len(indices_filtrados)), random_state=42).copy()
        recomendacoes['similaridade'] = np.nan
    
    # --- Formatação e Renomeação de Colunas (Corrigido para evitar KeyError) ---
    
    # Aplicar formatação ANTES da renomeação para que os valores sejam numéricos na formatação
    if 'player.proposedMarketValue' in recomendacoes.columns:
        recomendacoes['player.proposedMarketValue'] = recomendacoes['player.proposedMarketValue'].apply(lambda x: f"${x / 1_000_000:.2f}M")
    
    # Formata a similaridade apenas se ela for relevante (i.e., atleta_id não é None)
    if atleta_id is not None and 'similaridade' in recomendacoes.columns:
        recomendacoes['similaridade'] = recomendacoes['similaridade'].apply(lambda x: f"{x:.2f}")
    
    # Renomear colunas para exibição amigável
    recomendacoes = recomendacoes.rename(columns={
        'player.name': 'Nome do Atleta',
        'player.team.name.1': 'Clube',
        'position': 'Posição',
        'age': 'Idade',
        'player.proposedMarketValue': 'Valor de Mercado',
        'similaridade': 'Similaridade'
    })

    # Definir cols_display com os nomes JÁ RENOMEADOS
    cols_display_final = ['Nome do Atleta', 'Clube', 'Posição', 'Idade', 'Valor de Mercado']
    if atleta_id is not None:
        cols_display_final.append('Similaridade') # Adiciona 'Similaridade' (já renomeada)
    
    # Selecionar e ordenar as colunas usando os nomes renomeados
    return recomendacoes[cols_display_final].sort_values(by='Similaridade', ascending=False, na_position='last').reset_index(drop=True)

# --- Layout da Aplicação Streamlit ---

# Cabeçalho com Logo e Título
st.markdown('<div class="header-section">', unsafe_allow_html=True)
try:
    st.image("https://github.com/rafacstein/profutstat/raw/main/scouting/profutstat_logo.png", width=100)
except Exception: # Captura qualquer erro ao carregar a imagem
    st.warning("Logo não encontrada. Verifique o caminho ou a URL da imagem.")
st.markdown("<h1>ProFutStat: Scout de Atletas</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("Bem-vindo à ferramenta de **Scout de Atletas ProFutStat**! Utilize nossos algoritmos de similaridade baseados em dados de performance para encontrar os jogadores ideais para o seu clube.")

# Seção de Atleta de Referência e Critérios de Busca
st.header("Critérios de Busca")

col_ref, col_filters = st.columns([1, 1.5]) # Proporção ajustada

with col_ref:
    st.subheader("Atleta de Referência")
    st.markdown("Busque atletas similares a um jogador específico.", help="Opcional. Se não preenchido, a busca será apenas por filtros.")
    nome_atleta = st.text_input("Nome do Atleta", placeholder="Ex: Lionel Messi").strip()
    clube_atleta = st.text_input("Clube do Atleta", placeholder="Ex: Inter Miami CF").strip()

with col_filters:
    st.subheader("Filtros de Perfil")
    st.markdown("Defina os critérios para o perfil dos atletas desejados.")
    posicoes_choices = ['GK','DL', 'DC', 'DR', 'DM', 'MC', 'ML', 'MR', 'AM','LW', 'RW', 'ST']
    posicao_selecionada = st.multiselect(
        "Posição(ões) Desejada(s)",
        options=posicoes_choices,
        default=[], # Nenhum padrão selecionado
        help="Selecione uma ou mais posições. Se um atleta de referência for fornecido, a posição dele será considerada."
    )

    col_idade_min, col_idade_max = st.columns(2)
    with col_idade_min:
        idade_min_val = st.number_input("Idade Mínima", min_value=15, max_value=45, value=18, step=1)
    with col_idade_max:
        idade_max_val = st.number_input("Idade Máxima", min_value=15, max_value=45, value=35, step=1)

    # Convertendo para milhões para o slider, mas usando o valor real internamente para o modelo
    min_market_value_M = 0.1
    max_market_value_M = 150.0 # Ajustado para um valor máximo mais realista
    default_min_M = 1.0
    default_max_M = 50.0

    valor_min_M, valor_max_M = st.slider(
        "Valor de Mercado Estimado (M€)",
        min_value=min_market_value_M,
        max_value=max_market_value_M,
        value=(default_min_M, default_max_M),
        step=0.1,
        format="€%.1fM",
        help="Faixa de valor de mercado do atleta em milhões de Euros."
    )
    # Converta os valores do slider de volta para o formato original se precisar para o modelo
    valor_min_val = valor_min_M * 1_000_000
    valor_max_val = valor_max_M * 1_000_000

st.markdown("---")

# Botão de Recomendação
if st.button("🔎 Gerar Recomendações", type="primary"):
    with st.spinner("Analisando dados e buscando recomendações..."):
        recomendacoes = recomendar_atletas_avancado(
            nome=nome_atleta if nome_atleta else None, # Passa None se a string for vazia
            clube=clube_atleta if clube_atleta else None, # Passa None se a string for vazia
            posicao=posicao_selecionada,
            idade_min=idade_min_val,
            idade_max=idade_max_val,
            valor_min=valor_min_val,
            valor_max=valor_max_val,
            top_n=10
        )
        
        if not recomendacoes.empty:
            st.subheader("Resultados da Busca")
            st.dataframe(recomendacoes, use_container_width=True)
            st.success("Recomendações geradas com sucesso!")
        else:
            st.warning("Nenhuma recomendação encontrada. Por favor, ajuste os critérios de busca e tente novamente.")

st.markdown("---")
st.write("Powered by ProFutStat")
