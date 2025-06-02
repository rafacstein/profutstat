import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, Normalizer
import faiss
import streamlit as st
from fuzzywuzzy import fuzz
import io

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="PlayerScout IA - Benchmarking Estatístico (Por 90 Minutos)",
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
    .stDownloadButton>button {
        background-color: #007bff; /* Azul para download */
        color: white;
        border-radius: 8px;
        padding: 8px 20px;
        font-size: 1em;
        font-weight: normal;
        transition: background-color 0.3s ease;
    }
    .stDownloadButton>button:hover {
        background-color: #0056b3;
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

# --- Lista de Colunas para Cálculo Por 90 Minutos ---
cols_to_p90 = [
    "goals", "bigChancesCreated", "bigChancesMissed", "assists", "accuratePasses", "inaccuratePasses", "totalPasses", "keyPasses", "successfulDribbles",
    "tackles", "interceptions", "yellowCards", "redCards", "accurateCrosses",
    "totalShots", "shotsOnTarget", "shotsOffTarget", "groundDuelsWon", "aerialDuelsWon", "totalDuelsWon",
    "penaltiesTaken", "penaltyGoals", "shotFromSetPiece", "freeKickGoal",
    "goalsFromInsideTheBox", "goalsFromOutsideTheBox", "shotsFromInsideTheBox", "shotsFromOutsideTheBox",
    "headedGoals", "leftFootGoals", "rightFootGoals", "accurateLongBalls", "clearances", "errorLeadToGoal",
    "errorLeadToShot", "dispossessed", "possessionLost", "possessionWonAttThird", "totalChippedPasses",
    "accurateChippedPasses", "touches", "wasFouled", "fouls", "hitWoodwork", "ownGoals", "dribbledPast",
    "offsides", "blockedShots", "passToAssist", "cleanSheet",
    "totalAttemptAssist", "totalContest", "totalCross", "duelLost", "aerialLost", "totalLongBalls", "goalsConceded", "tacklesWon",
    "totalOwnHalfPasses", "totalOppositionHalfPasses", "expectedGoals",
    "goalKicks", "ballRecovery"
]

# Colunas adicionais que serão usadas no modelo, mas não são "por 90 minutos"
# e não foram especificadas para serem removidas (ex: rating, valor de mercado)
colunas_diretas = ["rating", "player.proposedMarketValue"]

# Colunas de identificação e filtro que não vão para o scaler
colunas_id_filtro = [
    "player.name", "player.team.name", "position", "age", "player.height", "league", "minutesPlayed"
]


# --- Carregamento de Dados e Inicialização do Modelo (Cacheado para Performance) ---
@st.cache_resource
def load_data_and_model():
    """Carrega os dados, calcula estatísticas por 90 minutos, e inicializa o scaler e o índice FAISS."""
    try:
        # Carrega apenas as colunas necessárias para evitar excesso de memória
        all_relevant_cols = list(set(cols_to_p90 + colunas_diretas + colunas_id_filtro))
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet', columns=all_relevant_cols)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de dados. Por favor, verifique o link ou a conexão: {e}")
        st.stop()

    # --- Pré-processamento e Cálculo Por 90 Minutos ---

    # Garantir que todas as colunas necessárias para o cálculo existam
    # e converter para numérico, preenchendo NaNs se necessário
    cols_check = list(set(cols_to_p90 + colunas_diretas + ['minutesPlayed']))
    missing_cols_df = [col for col in cols_check if col not in df.columns]
    if missing_cols_df:
        st.error(f"Erro: As seguintes colunas essenciais não foram encontradas no arquivo de dados: **{', '.join(missing_cols_df)}**")
        st.info("Por favor, verifique se os nomes das colunas na lista correspondem exatamente aos nomes no seu arquivo Parquet.")
        st.stop()

    for col in cols_check:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        # Preencher NaNs com a mediana, e depois 0 para casos de colunas inteiras em NaN
        df[col] = df[col].fillna(df[col].median()).fillna(0)
        df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Filtrar jogadores com minutos jogados insuficientes para evitar divisões por zero ou estatísticas distorcidas
    # Definindo um mínimo razoável de minutos, ex: 90 minutos (1 jogo completo)
    min_minutes_threshold = 90
    df_filtered = df[df['minutesPlayed'] >= min_minutes_threshold].copy()

    if df_filtered.empty:
        st.error("Não há atletas com minutos jogados suficientes para análise. Ajuste a base de dados ou o limiar de minutos.")
        st.stop()

    # Calcular estatísticas por 90 minutos
    for col in cols_to_p90:
        # Renomear a coluna original para 'col_raw' ou similar se precisar manter
        # df_filtered[f'{col}_raw'] = df_filtered[col] 
        df_filtered[f'{col}_p90'] = (df_filtered[col] / df_filtered['minutesPlayed']) * 90
        # Lidar com possíveis NaNs ou infinitos que podem surgir da divisão por zero (se minutesPlayed for 0 para algum motivo)
        df_filtered[f'{col}_p90'] = df_filtered[f'{col}_p90'].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Definir as colunas que serão usadas para o modelo FAISS (apenas as _p90, rating e market value)
    colunas_numericas_para_analise = [f'{col}_p90' for col in cols_to_p90] + colunas_diretas
    
    # Certificar que todas as colunas para análise existem
    missing_analysis_cols = [col for col in colunas_numericas_para_analise if col not in df_filtered.columns]
    if missing_analysis_cols:
        st.error(f"Erro: As seguintes colunas calculadas para análise não foram encontradas: **{', '.join(missing_analysis_cols)}**")
        st.stop()

    # Escalonar os dados para o FAISS
    scaler = StandardScaler()
    dados_escalados = scaler.fit_transform(df_filtered[colunas_numericas_para_analise])
    
    # Normalização L2 para garantir que o produto interno seja a similaridade de cosseno
    normalizer = Normalizer(norm='l2')
    dados_escalados_l2 = normalizer.fit_transform(dados_escalados)
    
    dados_escalados_l2 = dados_escalados_l2.astype('float32') # FAISS precisa de float32

    dimension = dados_escalados_l2.shape[1]
    index = faiss.IndexFlatIP(dimension) # IndexFlatIP espera vetores normalizados para similaridade de cosseno
    index.add(dados_escalados_l2)

    return df_filtered, scaler, index, dados_escalados_l2, colunas_numericas_para_analise

# Carrega os dados e o modelo
df, scaler, faiss_index, dados_escalados_l2, colunas_numericas_para_analise = load_data_and_model()


# --- Função para Calcular Percentis ---
def calcular_percentis(df_referencia, df_alvo_indices, colunas_para_percentil):
    """
    Calcula o percentil de cada estatística para atletas em df_alvo_indices
    em relação à distribuição das estatísticas em df_referencia (já filtrado).
    """
    percentis_dict = {}
    
    # Garante que df_referencia contém as colunas para percentil
    cols_to_process = [col for col in colunas_para_percentil if col in df_referencia.columns]

    for col in cols_to_process:
        if not df_referencia[col].empty and df_referencia[col].nunique() > 1: # Precisa de mais de 1 valor único para percentil
            percentis = df.loc[df_alvo_indices][col].apply(lambda x: (df_referencia[col] <= x).mean() * 100)
            percentis_dict[col + '_Percentil'] = percentis.round(0)
        else:
            # Se a coluna não tiver variância ou estiver vazia, retorna 0 ou 100 ou NaN
            percentis_dict[col + '_Percentil'] = np.nan # Ou 50, dependendo da interpretação
    
    return pd.DataFrame(percentis_dict, index=df_alvo_indices)


# --- Função de Recomendação Adaptada para Streamlit e Benchmarking ---
def recomendar_atletas_para_benchmarking(nome=None, clube=None, top_n=10, posicao=None,
                                         idade_min=None, idade_max=None,
                                         valor_min=None, valor_max=None, strict_posicao=True,
                                         ligas_selecionadas=None):
    """
    Recomenda atletas similares com múltiplos filtros usando FAISS e prepara dados para benchmarking.
    Retorna o atleta de referência e os atletas recomendados, ambos com suas estatísticas e percentis.
    """
    
    if df is None or faiss_index is None:
        st.error("Dados ou modelo não carregados. Por favor, tente novamente mais tarde.")
        return None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame() 

    atleta_ref_df = None
    atleta_id = None

    if nome and clube:
        df_temp = df.copy() 
        df_temp['temp_sim_nome'] = df_temp['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
        df_temp['temp_sim_clube'] = df_temp['player.team.name'].apply(lambda x: fuzz.token_set_ratio(clube, x))
        df_temp['temp_sim_combinada'] = 0.7 * df_temp['temp_sim_nome'] + 0.3 * df_temp['temp_sim_clube']
        
        melhor_match = df_temp.nlargest(1, 'temp_sim_combinada')
        
        if not melhor_match.empty and melhor_match['temp_sim_combinada'].iloc[0] >= 80:
            atleta_id = melhor_match.index[0]
            atleta_ref_df = df.loc[[atleta_id]].copy() # Usar loc com lista para manter como DataFrame
            st.success(f"🔍 Atleta de Referência: **{atleta_ref_df['player.name'].iloc[0]}** ({atleta_ref_df['player.team.name'].iloc[0]}) encontrado.")
            st.info(f"Posição: {atleta_ref_df['position'].iloc[0]} | Idade: **{int(atleta_ref_df['age'].iloc[0])}** | Valor: **${atleta_ref_df['player.proposedMarketValue'].iloc[0] / 1_000_000:.2f}M**")
            
            if strict_posicao and posicao is None:
                posicao = [atleta_ref_df['position'].iloc[0]]
        else:
            st.warning(f"⚠️ Atleta de referência '{nome}' do clube '{clube}' não encontrado com alta confiança. A busca será apenas por critérios de filtro.")
            atleta_id = None
    else:
        st.info("Nenhum atleta de referência fornecido. A busca será apenas pelos critérios de busca.")

    mascara_filtros = pd.Series(True, index=df.index)
    
    if posicao:
        mascara_filtros &= df['position'].isin(posicao)
    
    if idade_min is not None:
        mascara_filtros &= df['age'] >= idade_min
    if idade_max is not None:
        mascara_filtros &= df['age'] <= idade_max
    
    if valor_min is not None:
        mascara_filtros &= df['player.proposedMarketValue'] >= valor_min
    if valor_max is not None:
        mascara_filtros &= df['player.proposedMarketValue'] <= valor_max

    # NOVO FILTRO: Ligas
    if ligas_selecionadas:
        mascara_filtros &= df['league'].isin(ligas_selecionadas) # Usando 'league' como o nome da coluna

    indices_filtrados = df[mascara_filtros].index.tolist()

    if not indices_filtrados:
        st.warning("Nenhum atleta corresponde aos filtros especificados. Tente ajustar os critérios.")
        return atleta_ref_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    # Obter recomendações por similaridade ou amostra
    if atleta_id is not None:
        # AQUI USAMOS O DATAFRAME FILTRADO PARA OBTER O VETOR DO ATLETA DE REFERÊNCIA
        # Certifique-se que o atleta_id ainda está no df_filtered (o df que foi usado para FAISS)
        if atleta_id not in df.index:
            st.error("Erro: Atleta de referência não encontrado após os filtros iniciais ou processamento. Verifique se ele atende aos mínimos de minutos jogados.")
            return None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Precisamos da localização do atleta no array que o FAISS usa
        # O FAISS foi construído com base em df_filtered, então usamos seu índice para obter a localização correta
        query_vector = dados_escalados_l2[df.index.get_loc(atleta_id)].reshape(1, -1)
        
        # Buscar mais resultados do que o top_n para garantir que teremos o suficiente após o filtro
        D, I = faiss_index.search(query_vector, max(top_n * 5, len(indices_filtrados) + 1)) 

        similaridades = D[0]
        indices_retornados = I[0]
        
        recomendacoes_brutas = pd.DataFrame({
            'original_index': indices_retornados,
            'similaridade': similaridades
        })
        
        # Filtra os resultados do FAISS pelos critérios e remove o próprio atleta de referência
        recomendacoes_finais = recomendacoes_brutas[
            recomendacoes_brutas['original_index'].isin(indices_filtrados) & 
            (recomendacoes_brutas['original_index'] != atleta_id)
        ]
        
        recomendacoes_finais = recomendacoes_finais.sort_values(by='similaridade', ascending=False).head(top_n)
        
        if recomendacoes_finais.empty:
            st.info(f"Nenhuma recomendação similar ao atleta **{atleta_ref_df['player.name'].iloc[0]}** encontrada com os filtros aplicados. Tente ajustar os critérios ou o atleta de referência.")
            return atleta_ref_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
        recomendacoes_df = df.loc[recomendacoes_finais['original_index']].copy()
        recomendacoes_df['similaridade'] = recomendacoes_finais['similaridade'].values
        
    else:
        st.info(f"Mostrando uma amostra de {top_n} atletas que atendem aos filtros. Para recomendações por similaridade, forneça um atleta de referência.")
        if len(indices_filtrados) < top_n:
            st.info(f"Apenas {len(indices_filtrados)} atletas encontrados com os filtros, mostrando todos.")
        
        recomendacoes_df = df.loc[indices_filtrados].sample(n=min(top_n, len(indices_filtrados)), random_state=42).copy()
        recomendacoes_df['similaridade'] = np.nan # Não há similaridade se não há atleta de referência

    # --- Cálculo de Percentis para o Atleta de Referência e os Recomendados ---
    # Grupo de referência para os percentis: Todos os atletas que passaram pelos filtros
    df_para_percentil_referencia = df.loc[indices_filtrados].copy()
    
    # Colunas para as quais o percentil será calculado (as _p90 e as diretas)
    cols_for_percentil = colunas_numericas_para_analise

    if atleta_ref_df is not None:
        atleta_ref_percentis = calcular_percentis(df_para_percentil_referencia, atleta_ref_df.index, cols_for_percentil)
        atleta_ref_df = pd.concat([atleta_ref_df, atleta_ref_percentis], axis=1)

    if not recomendacoes_df.empty:
        recomendacoes_percentis = calcular_percentis(df_para_percentil_referencia, recomendacoes_df.index, cols_for_percentil)
        recomendacoes_df = pd.concat([recomendacoes_df, recomendacoes_percentis], axis=1)

    # --- PREPARAÇÃO DOS DATAFRAMES PARA EXIBIÇÃO E DOWNLOAD ---
    # Colunas para download (todos os dados brutos e calculados + percentis)
    # Inclui colunas de identificação e as P90 e diretas, mais os percentis
    cols_para_download = [
        'player.name', 'player.team.name', 'position', 'age', 'player.height', 'league', 'minutesPlayed',
        'player.proposedMarketValue', 'rating'
    ] + [f'{col}_p90' for col in cols_to_p90] + [f'{col}_p90_Percentil' for col in cols_to_p90] + \
      [f'{col}_Percentil' for col in colunas_diretas] # Percentis para rating/marketValue

    if 'similaridade' in recomendacoes_df.columns:
        cols_para_download.append('similaridade')

    # Ajusta as colunas para download no atleta de referência também
    if atleta_ref_df is not None:
        atleta_ref_para_download = atleta_ref_df[cols_para_download].copy()
        atleta_ref_para_download['similaridade'] = 1.0 # Similaridade 100% com ele mesmo
    else:
        atleta_ref_para_download = pd.DataFrame() # Vazio se não houver ref

    recomendacoes_para_download = recomendacoes_df[cols_para_download].copy()

    # --- Formatação e Renomeação de Colunas para Exibição na UI ---
    def formatar_df_display(df_input, is_ref_athlete=False):
        df_display = df_input.copy()
        if 'age' in df_display.columns:
            df_display['age'] = df_display['age'].apply(lambda x: int(x) if pd.notna(x) else x)
        if 'player.proposedMarketValue' in df_display.columns:
            df_display['player.proposedMarketValue'] = df_display['player.proposedMarketValue'].apply(lambda x: f"${x / 1_000_000:.2f}M")
        if 'similaridade' in df_display.columns and not is_ref_athlete: # Nao formatar similaridade do proprio atleta de ref
            df_display['similaridade'] = df_display['similaridade'].apply(lambda x: f"{max(0, min(100, x * 100)):.0f}%")
        
        df_display = df_display.rename(columns={
            'player.name': 'Nome do Atleta',
            'player.team.name': 'Clube',
            'position': 'Posição',
            'age': 'Idade',
            'player.proposedMarketValue': 'Valor de Mercado',
            'similaridade': 'Similaridade (%)',
            'league': 'Liga',
            'minutesPlayed': 'Minutos Jogados',
            'rating': 'Rating'
        })
        # Renomear as colunas _p90 para exibição mais limpa
        for col in cols_to_p90:
            if f'{col}_p90' in df_display.columns:
                df_display = df_display.rename(columns={f'{col}_p90': f'{col} (p90)'})
            if f'{col}_p90_Percentil' in df_display.columns:
                df_display = df_display.rename(columns={f'{col}_p90_Percentil': f'{col} (p90) %'})
        # Renomear percentis de colunas diretas
        for col in colunas_diretas:
            if f'{col}_Percentil' in df_display.columns:
                df_display = df_display.rename(columns={f'{col}_Percentil': f'{col} %'})


        return df_display

    recomendacoes_display = formatar_df_display(recomendacoes_df)
    if atleta_ref_df is not None:
        atleta_ref_display = formatar_df_display(atleta_ref_df, is_ref_athlete=True)
    else:
        atleta_ref_display = pd.DataFrame()

    # Definir as colunas para exibição principal na tabela
    cols_display_final = ['Nome do Atleta', 'Clube', 'Posição', 'Idade', 'Valor de Mercado', 'Liga']
    if atleta_id is not None:
        cols_display_final.append('Similaridade (%)')
    
    if not recomendacoes_display.empty:
        # Se não houver similaridade (atleta de ref não fornecido), ordenar por rating ou valor de mercado, por exemplo
        sort_col = 'Similaridade (%)' if 'Similaridade (%)' in recomendacoes_display.columns else 'Rating'
        recomendacoes_display = recomendacoes_display[cols_display_final].sort_values(
            by=sort_col, ascending=False, na_position='last'
        ).reset_index(drop=True)

    return atleta_ref_df, recomendacoes_display, recomendacoes_completas, atleta_ref_para_download


# --- Layout da Aplicação Streamlit ---

# Cabeçalho com Logo e Título
st.markdown('<div class="header-section">', unsafe_allow_html=True)
try:
    st.image("https://github.com/rafacstein/profutstat/raw/main/scouting/profutstat_logo.png", width=100)
except Exception:
    st.warning("Logo não encontrada. Verifique o caminho ou a URL da imagem.")
st.markdown("<h1>PlayerScout IA - Benchmarking Estatístico (Por 90 Minutos)</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("Bem-vindo à ferramenta **PlayerScout IA da ProFutStat**! Utilize nossos algoritmos para **benchmarking estatístico por 90 minutos** e encontre atletas com performance comparável, identificando pontos fortes e fracos em relação aos seus pares.")

# Seção de Atleta de Referência e Critérios de Busca
st.header("1. Defina Seus Critérios")

col_ref, col_filters = st.columns([1, 1.5])

with col_ref:
    st.subheader("Atleta de Referência (Opcional)")
    st.markdown("Compare outros atletas a um jogador específico. Se não preenchido, a busca será apenas por filtros.")
    nome_atleta = st.text_input("Nome do Atleta", placeholder="Ex: Lionel Messi").strip()
    clube_atleta = st.text_input("Clube do Atleta", placeholder="Ex: Inter Miami CF").strip()

with col_filters:
    st.subheader("Filtros para o Grupo de Comparação")
    st.markdown("Defina os critérios para o grupo de atletas que serão comparados.")
    posicoes_choices = sorted(df['position'].unique().tolist()) # Pega posições únicas do DataFrame
    posicao_selecionada = st.multiselect(
        "Posição(ões) do Grupo de Comparação",
        options=posicoes_choices,
        default=[],
        help="Selecione uma ou mais posições. Se um atleta de referência for fornecido, a posição dele será considerada como padrão."
    )

    # NOVO CAMPO: Filtro de Ligas
    ligas_unicas = sorted(df['league'].unique().tolist()) # Usando 'league' como o nome da coluna
    ligas_selecionadas = st.multiselect(
        "Ligas para Comparação",
        options=ligas_unicas,
        default=[],
        help="Selecione as ligas dos atletas que farão parte do grupo de comparação."
    )

    col_idade_min, col_idade_max = st.columns(2)
    with col_idade_min:
        idade_min_val = st.number_input("Idade Mínima", min_value=15, max_value=45, value=18, step=1)
    with col_idade_max:
        idade_max_val = st.number_input("Idade Máxima", min_value=15, max_value=45, value=35, step=1)

    min_market_value_M = 0.01
    max_market_value_M = df['player.proposedMarketValue'].max() / 1_000_000 # Max value from data
    default_min_M = 0.5
    default_max_M = min(25.0, max_market_value_M) # Default max, capped by actual max

    valor_min_M, valor_max_M = st.slider(
        "Valor de Mercado Estimado (M€)",
        min_value=min_market_value_M,
        max_value=max_market_value_M,
        value=(default_min_M, default_max_M),
        step=0.1,
        format="€%.1fM",
        help="Faixa de valor de mercado dos atletas em milhões de Euros."
    )
    valor_min_val = valor_min_M * 1_000_000
    valor_max_val = valor_max_M * 1_000_000

st.markdown("---")

# Botão de Recomendação
if st.button("🔎 Gerar Benchmarking", type="primary"):
    with st.spinner("Analisando dados e gerando relatório de benchmarking..."):
        atleta_referencia_info, recomendacoes_display, recomendacoes_completas, atleta_ref_para_download = \
            recomendar_atletas_para_benchmarking(
                nome=nome_atleta if nome_atleta else None,
                clube=clube_atleta if clube_atleta else None,
                posicao=posicao_selecionada,
                idade_min=idade_min_val,
                idade_max=idade_max_val,
                valor_min=valor_min_val,
                valor_max=valor_max_val,
                top_n=10, # Mantendo 10 para a tabela principal
                ligas_selecionadas=ligas_selecionadas # PASSE O NOVO PARÂMETRO AQUI
            )
        
        if not recomendacoes_display.empty:
            st.subheader("2. Atletas Recomendados (Baseado nos Filtros)")
            if atleta_referencia_info is not None:
                st.write("Estes atletas são os mais **estatisticamente similares (por 90 minutos)** ao seu atleta de referência, dentro dos filtros aplicados.")
            else:
                st.write("Estes atletas são uma **amostra** dos jogadores que atendem aos filtros especificados.")
            
            st.dataframe(recomendacoes_display, use_container_width=True)
            st.success("Relatório de Benchmarking gerado com sucesso!")

            # --- Seção de Comparação Detalhada de Estatísticas ---
            if atleta_referencia_info is not None:
                st.markdown("---")
                st.subheader("3. Comparação Detalhada (Benchmarking por 90 Minutos)")
                st.markdown(f"Compare o atleta de referência **{atleta_referencia_info['player.name'].iloc[0]}** com os atletas recomendados nas principais estatísticas. Os **percentis** indicam a posição do atleta no grupo de comparação filtrado (ex: 90% significa melhor que 90% dos atletas do grupo).")
                
                # Selecionar um atleta recomendado para comparação detalhada
                st.write("Selecione um atleta recomendado para ver o detalhe das estatísticas:")
                nomes_recomendados = recomendacoes_display['Nome do Atleta'].tolist()
                atleta_comparar_nome = st.selectbox("Escolha um atleta para comparar", nomes_recomendados)

                if atleta_comparar_nome:
                    atleta_comparar_df = recomendacoes_completas[
                        recomendacoes_completas['player.name'] == atleta_comparar_nome
                    ].iloc[0] # Pega a série do atleta escolhido

                    # Tabela de Comparação Estatística
                    comparacao_data = []
                    # Inclui estatísticas por 90 minutos
                    for col_p90 in colunas_numericas_para_analise:
                        if '_p90' in col_p90 or col_p90 in colunas_diretas: # Apenas as colunas que estão no modelo
                            ref_val = atleta_referencia_info[col_p90].iloc[0]
                            ref_percentil_col = f"{col_p90}_Percentil"
                            ref_percentil = atleta_referencia_info[ref_percentil_col].iloc[0] if ref_percentil_col in atleta_referencia_info.columns else np.nan

                            comp_val = atleta_comparar_df[col_p90]
                            comp_percentil_col = f"{col_p90}_Percentil"
                            comp_percentil = atleta_comparar_df[comp_percentil_col] if comp_percentil_col in atleta_comparar_df else np.nan
                            
                            comparacao_data.append({
                                'Estatística': col_p90.replace('_p90', ' (p90)').replace('player.proposedMarketValue', 'Valor de Mercado').replace('rating', 'Rating'), # Exibição amigável
                                f'{atleta_referencia_info["player.name"].iloc[0]} (Valor)': f"{ref_val:.2f}",
                                f'{atleta_referencia_info["player.name"].iloc[0]} (Percentil)': f"{int(ref_percentil)}%" if pd.notna(ref_percentil) else "N/A",
                                f'{atleta_comparar_df["player.name"]} (Valor)': f"{comp_val:.2f}",
                                f'{atleta_comparar_df["player.name"]} (Percentil)': f"{int(comp_percentil)}%" if pd.notna(comp_percentil) else "N/A"
                            })
                    
                    df_comparacao = pd.DataFrame(comparacao_data)
                    st.dataframe(df_comparacao, use_container_width=True)
                    st.info("Para exportar esta tabela completa e realizar análises adicionais, utilize as opções de download abaixo.")

            # --- Seção de Detalhes Completos e Download ---
            st.markdown("---")
            st.subheader("4. Detalhes Completos e Exportação")
            st.info("Baixe o relatório completo com **todas as estatísticas (inclusive por 90 minutos) e percentis** dos atletas para análise aprofundada.")
            
            # Concatena o atleta de referência (se existir) com os recomendados para o download
            df_final_download = pd.concat([atleta_ref_para_download, recomendacoes_completas], ignore_index=True) if not atleta_ref_para_download.empty else recomendacoes_completas

            csv_buffer = io.StringIO()
            df_final_download.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_bytes = csv_buffer.getvalue().encode('utf-8')

            excel_buffer = io.BytesIO()
            df_final_download.to_excel(excel_buffer, index=False, engine='xlsxwriter')
            excel_buffer.seek(0)

            col_download_csv, col_download_excel = st.columns(2)
            with col_download_csv:
                st.download_button(
                    label="⬇️ Download CSV Completo",
                    data=csv_bytes,
                    file_name="relatorio_benchmarking_atletas.csv",
                    mime="text/csv",
                    help="Baixe todas as estatísticas e percentis dos atletas no relatório em formato CSV."
                )
            with col_download_excel:
                st.download_button(
                    label="⬇️ Download Excel Completo",
                    data=excel_buffer,
                    file_name="relatorio_benchmarking_atletas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Baixe todas as estatísticas e percentis dos atletas no relatório em formato Excel."
                )

            with st.expander("Clique para ver todas as estatísticas e percentis dos atletas no relatório"):
                st.dataframe(df_final_download, use_container_width=True)

        else:
            st.warning("Nenhuma recomendação encontrada com os filtros e/ou atleta de referência. Por favor, ajuste os critérios de busca e tente novamente.")

st.markdown("---")
st.write("Desenvolvido no Brasil pela ProFutStat")
