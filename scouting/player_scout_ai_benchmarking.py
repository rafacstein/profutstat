import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, Normalizer
import faiss
import streamlit as st
from fuzzywuzzy import fuzz
import io
import plotly.express as px

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="PlayerBenchmark Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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
        background-color: #f8f9fa;
    }

    /* Cabeçalho */
    .header-section {
        display: flex;
        align-items: center;
        gap: 20px;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }
    .header-section h1 {
        font-size: 2.5em;
        color: #2c3e50;
        margin: 0;
        line-height: 1.2;
    }

    /* Cards de Métricas */
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metric-title {
        font-size: 0.9em;
        color: #7f8c8d;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.4em;
        font-weight: bold;
        color: #2c3e50;
    }

    /* Abas */
    .stTabs [role="tablist"] {
        background-color: #f1f3f5;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [role="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background-color: #3498db;
        color: white;
    }

    /* Gráficos */
    .plotly-graph-div {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Carregamento de Dados e Inicialização do Modelo ---
@st.cache_resource
def load_data_and_model():
    """Carrega os dados e inicializa o scaler e o índice FAISS."""
    try:
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet')
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

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

    # Tratamento de dados
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df[colunas_numericas] = df[colunas_numericas].fillna(df[colunas_numericas].median())
    df[colunas_numericas] = df[colunas_numericas].fillna(0)
    df[colunas_numericas] = df[colunas_numericas].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Normalização
    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(df[colunas_numericas])
    normalizer = Normalizer(norm='l2')
    dados_normalizados = normalizer.fit_transform(dados_normalizados)
    dados_normalizados = dados_normalizados.astype('float32')

    # Índice FAISS
    dimension = dados_normalizados.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(dados_normalizados)

    return df, scaler, index, dados_normalizados, colunas_numericas

df, scaler, faiss_index, dados_normalizados, colunas_metricas = load_data_and_model()

# --- Funções Principais ---
def encontrar_atleta_referencia(nome, clube=None):
    """Encontra o atleta de referência usando fuzzy matching."""
    if not nome:
        return None
    
    df_temp = df.copy()
    df_temp['sim_nome'] = df_temp['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
    
    if clube:
        df_temp['sim_clube'] = df_temp['player.team.name'].apply(lambda x: fuzz.token_set_ratio(clube, x))
        df_temp['score'] = 0.7 * df_temp['sim_nome'] + 0.3 * df_temp['sim_clube']
    else:
        df_temp['score'] = df_temp['sim_nome']
    
    melhor_match = df_temp.nlargest(1, 'score')
    
    if not melhor_match.empty and melhor_match['score'].iloc[0] >= 70:
        return melhor_match.index[0]
    return None

def filtrar_atletas(posicoes=None, idade_min=None, idade_max=None, valor_min=None, valor_max=None, clube=None):
    """Filtra atletas com base nos critérios."""
    mascara = pd.Series(True, index=df.index)
    
    if posicoes:
        mascara &= df['position'].isin(posicoes)
    if idade_min is not None:
        mascara &= df['age'] >= idade_min
    if idade_max is not None:
        mascara &= df['age'] <= idade_max
    if valor_min is not None:
        mascara &= df['player.proposedMarketValue'] >= valor_min
    if valor_max is not None:
        mascara &= df['player.proposedMarketValue'] <= valor_max
    if clube:
        mascara &= df['player.team.name'].str.contains(clube, case=False)
    
    return df[mascara].copy()

def gerar_benchmark(atleta_ref_id, atletas_comparacao, colunas_metricas, top_n=5):
    """Gera análise comparativa entre o atleta de referência e os comparados."""
    if atleta_ref_id not in df.index or atletas_comparacao.empty:
        return pd.DataFrame()
    
    # Dados do atleta de referência
    ref_data = df.loc[atleta_ref_id, colunas_metricas]
    
    # Calcular percentis para cada métrica
    resultados = []
    for _, atleta in atletas_comparacao.iterrows():
        comparacao = {}
        for metrica in colunas_metricas:
            valor_ref = ref_data[metrica]
            valor_comp = atleta[metrica]
            
            # Calcular diferença percentual
            if valor_ref != 0:
                diff_pct = (valor_comp - valor_ref) / valor_ref * 100
            else:
                diff_pct = 0
            
            comparacao[metrica] = diff_pct
        
        resultados.append({
            'ID': atleta.name,
            'Nome': atleta['player.name'],
            'Clube': atleta['player.team.name'],
            'Posição': atleta['position'],
            'Idade': int(atleta['age']),
            'Valor (M€)': atleta['player.proposedMarketValue'] / 1_000_000,
            'Comparacao': comparacao
        })
    
    # Criar DataFrame com os resultados
    df_resultados = pd.DataFrame(resultados)
    
    return df_resultados

def plotar_radar_chart(atleta_ref, atletas_comparacao, metricas_selecionadas):
    """Cria gráfico de radar para comparação de métricas."""
    categories = metricas_selecionadas
    
    # Preparar dados para o gráfico
    fig = px.line_polar(
        pd.DataFrame({
            'Metrica': categories,
            atleta_ref['player.name']: atleta_ref[categories].values,
            **{f"{row['player.name']} ({row['player.team.name']})": row[categories].values 
               for _, row in atletas_comparacao.iterrows()}
        }),
        r=[atleta_ref[metrica] for metrica in categories],
        theta=categories,
        line_close=True,
        template="plotly_white",
        height=600
    )
    
    fig.update_traces(fill='toself')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(atleta_ref[categories].max(), 
                            atletas_comparacao[categories].max().max()) * 1.1]
            )),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

# --- Interface do Usuário ---
st.markdown('<div class="header-section">', unsafe_allow_html=True)
st.image("https://github.com/rafacstein/profutstat/raw/main/scouting/profutstat_logo.png", width=100)
st.markdown("<h1>PlayerBenchmark Pro</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
**Ferramenta avançada de benchmarking de jogadores**  
Compare atletas com base em estatísticas de desempenho e encontre alternativas com perfis similares.
""")

# --- Abas Principais ---
tab1, tab2 = st.tabs(["🔍 Busca e Filtros", "📊 Análise Comparativa"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Atleta de Referência")
        nome_atleta = st.text_input("Nome do Jogador", key="nome_ref")
        clube_atleta = st.text_input("Clube (opcional)", key="clube_ref")
        
        if nome_atleta:
            atleta_id = encontrar_atleta_referencia(nome_atleta, clube_atleta)
            
            if atleta_id is not None:
                atleta_ref = df.loc[atleta_id]
                
                # Mostrar card com informações do atleta
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-title">Atleta de Referência</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{atleta_ref["player.name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'**Clube:** {atleta_ref["player.team.name"]} | **Posição:** {atleta_ref["position"]}')
                st.markdown(f'**Idade:** {int(atleta_ref["age"])} | **Valor:** €{atleta_ref["player.proposedMarketValue"]/1_000_000:.2f}M')
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Armazenar atleta de referência na sessão
                st.session_state['atleta_ref'] = atleta_ref
            else:
                st.warning("Atleta não encontrado. Verifique o nome e tente novamente.")
                st.session_state['atleta_ref'] = None
    
    with col2:
        st.subheader("Filtros de Busca")
        
        posicoes = ['GK','DL', 'DC', 'DR', 'DM', 'MC', 'ML', 'MR', 'AM','LW', 'RW', 'ST']
        posicoes_selecionadas = st.multiselect("Posições", options=posicoes, default=posicoes)
        
        col_idade, col_valor = st.columns(2)
        with col_idade:
            idade_min = st.slider("Idade Mínima", 16, 40, 18)
            idade_max = st.slider("Idade Máxima", 16, 40, 32)
        
        with col_valor:
            valor_min = st.slider("Valor Mínimo (M€)", 0.0, 100.0, 0.5)
            valor_max = st.slider("Valor Máximo (M€)", 0.0, 100.0, 30.0)
        
        clube_filtro = st.text_input("Filtrar por clube (opcional)")
        
        # Converter valores para escala completa
        valor_min *= 1_000_000
        valor_max *= 1_000_000
    
    # Botão para aplicar filtros
    if st.button("Aplicar Filtros", type="primary"):
        with st.spinner("Processando..."):
            atletas_filtrados = filtrar_atletas(
                posicoes=posicoes_selecionadas,
                idade_min=idade_min,
                idade_max=idade_max,
                valor_min=valor_min,
                valor_max=valor_max,
                clube=clube_filtro
            )
            
            st.session_state['atletas_filtrados'] = atletas_filtrados
            
            if not atletas_filtrados.empty:
                st.success(f"Encontrados {len(atletas_filtrados)} atletas com os filtros aplicados.")
                
                # Mostrar tabela resumida
                cols_display = ['player.name', 'player.team.name', 'position', 'age', 'player.proposedMarketValue']
                df_display = atletas_filtrados[cols_display].copy()
                df_display['player.proposedMarketValue'] = df_display['player.proposedMarketValue'].apply(lambda x: f"€{x/1_000_000:.2f}M")
                df_display.columns = ['Nome', 'Clube', 'Posição', 'Idade', 'Valor']
                
                st.dataframe(df_display, use_container_width=True, height=300)
            else:
                st.warning("Nenhum atleta encontrado com os filtros aplicados.")

with tab2:
    if 'atleta_ref' not in st.session_state or st.session_state['atleta_ref'] is None:
        st.warning("Selecione um atleta de referência na aba 'Busca e Filtros' para habilitar a análise comparativa.")
    elif 'atletas_filtrados' not in st.session_state or st.session_state['atletas_filtrados'].empty:
        st.warning("Aplique os filtros na aba 'Busca e Filtros' para encontrar atletas para comparação.")
    else:
        atleta_ref = st.session_state['atleta_ref']
        atletas_filtrados = st.session_state['atletas_filtrados']
        
        st.subheader(f"Análise Comparativa: {atleta_ref['player.name']}")
        
        # Selecionar métricas para comparação
        metricas_possiveis = [m for m in colunas_metricas if m not in ['age', 'player.proposedMarketValue', 'player.height']]
        metricas_selecionadas = st.multiselect(
            "Selecione as métricas para comparação",
            options=metricas_possiveis,
            default=['goals', 'assists', 'keyPasses', 'successfulDribbles', 'tackles', 'interceptions'],
            max_choices=10
        )
        
        if not metricas_selecionadas:
            st.warning("Selecione pelo menos uma métrica para comparação.")
        else:
            # Gerar benchmark
            df_benchmark = gerar_benchmark(atleta_ref.name, atletas_filtrados, metricas_selecionadas)
            
            if not df_benchmark.empty:
                # Mostrar gráfico de radar
                st.plotly_chart(
                    plotar_radar_chart(atleta_ref, atletas_filtrados.head(3), metricas_selecionadas),
                    use_container_width=True
                )
                
                # Mostrar tabela comparativa
                st.subheader("Comparação Detalhada")
                
                # Preparar dados para exibição
                comparacao_data = []
                for _, row in df_benchmark.iterrows():
                    comparacao = {
                        'Nome': row['Nome'],
                        'Clube': row['Clube'],
                        'Posição': row['Posição'],
                        'Idade': row['Idade'],
                        'Valor (M€)': row['Valor (M€)']
                    }
                    
                    for metrica in metricas_selecionadas:
                        valor_ref = atleta_ref[metrica]
                        valor_comp = atletas_filtrados.loc[row['ID'], metrica]
                        diff_pct = row['Comparacao'][metrica]
                        
                        comparacao[metrica] = f"{valor_comp:.1f} ({'+' if diff_pct > 0 else ''}{diff_pct:.1f}%)"
                        comparacao[f"{metrica}_ref"] = f"{valor_ref:.1f}"
                    
                    comparacao_data.append(comparacao)
                
                # Criar DataFrame para exibição
                cols_display = ['Nome', 'Clube', 'Posição', 'Idade', 'Valor (M€)'] + metricas_selecionadas
                df_display = pd.DataFrame(comparacao_data)[cols_display]
                
                # Mostrar tabela
                st.dataframe(df_display, use_container_width=True, height=400)
                
                # Opções de download
                st.download_button(
                    label="📥 Exportar Dados Comparativos",
                    data=df_benchmark.to_csv(index=False).encode('utf-8'),
                    file_name=f"benchmark_{atleta_ref['player.name'].replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Não foi possível gerar a análise comparativa. Verifique os filtros aplicados.")

# --- Rodapé ---
st.markdown("---")
st.markdown("""
**PlayerBenchmark Pro** - Ferramenta de análise comparativa de jogadores  
Desenvolvido por ProFutStat | Dados atualizados em 30/05/2025
""")
