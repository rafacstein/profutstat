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

# --- CSS Customizado ---
st.markdown("""
<style>
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
    .stTabs [role="tablist"] {
        background-color: #f1f3f5;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [role="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background-color: #3498db;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Carregamento de Dados ---
@st.cache_resource
def load_data():
    try:
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet')
        
        colunas_numericas = [
            "rating", "goals", "assists", "keyPasses", "successfulDribbles", 
            "tackles", "interceptions", "accuratePassesPercentage", 
            "shotsOnTarget", "minutesPlayed", "player.proposedMarketValue", "age"
        ]
        
        # Processamento dos dados
        for col in colunas_numericas:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median())
        
        return df, colunas_numericas
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.stop()

df, colunas_metricas = load_data()

# --- Funções Principais ---
def encontrar_atleta(nome, clube=None):
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

def filtrar_atletas(posicoes=None, idade_min=18, idade_max=40, valor_min=0, valor_max=100):
    mascara = (
        (df['age'] >= idade_min) & 
        (df['age'] <= idade_max) &
        (df['player.proposedMarketValue'] >= valor_min * 1_000_000) &
        (df['player.proposedMarketValue'] <= valor_max * 1_000_000)
    
    if posicoes:
        mascara &= df['position'].isin(posicoes)
    
    return df[mascara].copy()

def criar_grafico_comparacao(atleta_ref, comparados, metricas):
    fig = px.bar(
        pd.DataFrame({
            'Metrica': metricas,
            'Referência': [atleta_ref[m] for m in metricas],
            **{f"{row['player.name']}": [row[m] for m in metricas] 
               for _, row in comparados.iterrows()}
        }).melt(id_vars=['Metrica']),
        x='Metrica', y='value', color='variable', barmode='group',
        title="Comparação de Métricas", height=500
    )
    return fig

# --- Interface do Usuário ---
st.title("⚽ PlayerBenchmark Pro")
st.markdown("Compare jogadores e encontre atletas com perfis similares")

tab1, tab2 = st.tabs(["🔍 Busca", "📊 Comparação"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Atleta de Referência")
        nome_ref = st.text_input("Nome do Jogador", key="nome_ref")
        clube_ref = st.text_input("Clube (opcional)", key="clube_ref")
        
        if nome_ref:
            atleta_id = encontrar_atleta(nome_ref, clube_ref)
            
            if atleta_id is not None:
                ref = df.loc[atleta_id]
                st.session_state['ref'] = ref
                
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-title">Atleta de Referência</div>
                    <div class="metric-value">{}</div>
                    <div>{} | {} anos | {:.2f}M €</div>
                </div>
                """.format(
                    ref['player.name'],
                    ref['player.team.name'],
                    int(ref['age']),
                    ref['player.proposedMarketValue']/1_000_000
                ), unsafe_allow_html=True)
            else:
                st.warning("Jogador não encontrado")
                st.session_state['ref'] = None
    
    with col2:
        st.subheader("Filtros")
        posicoes = st.multiselect(
            "Posições",
            options=df['position'].unique(),
            default=['ST', 'AM', 'LW', 'RW']
        )
        
        idade_min, idade_max = st.slider(
            "Faixa de Idade",
            min_value=16, max_value=40, value=(18, 32)
        )
        
        valor_min, valor_max = st.slider(
            "Valor de Mercado (M€)",
            min_value=0, max_value=100, value=(1, 30)
        )
        
        if st.button("Buscar Jogadores", type="primary"):
            comparados = filtrar_atletas(
                posicoes=posicoes if posicoes else None,
                idade_min=idade_min,
                idade_max=idade_max,
                valor_min=valor_min,
                valor_max=valor_max
            )
            
            st.session_state['comparados'] = comparados
            st.success(f"Encontrados {len(comparados)} jogadores")

with tab2:
    if 'ref' not in st.session_state or st.session_state['ref'] is None:
        st.warning("Selecione um atleta de referência na aba 'Busca'")
    elif 'comparados' not in st.session_state or st.session_state['comparados'].empty:
        st.warning("Aplique os filtros na aba 'Busca' para encontrar jogadores para comparação")
    else:
        ref = st.session_state['ref']
        comparados = st.session_state['comparados'].head(5)  # Limitar a 5 para a visualização
        
        st.subheader(f"Comparação com {ref['player.name']}")
        
        # Seleção de métricas
        metricas = st.multiselect(
            "Selecione as métricas para comparação",
            options=colunas_metricas,
            default=['goals', 'assists', 'keyPasses', 'tackles', 'interceptions']
        )
        
        if metricas:
            st.plotly_chart(
                criar_grafico_comparacao(ref, comparados, metricas),
                use_container_width=True
            )
            
            # Tabela comparativa
            st.dataframe(
                comparados[['player.name', 'player.team.name', 'position', 'age'] + metricas]
                .assign(Valor=lambda x: x['player.proposedMarketValue']/1_000_000)
                .rename(columns={
                    'player.name': 'Nome',
                    'player.team.name': 'Clube',
                    'position': 'Posição',
                    'age': 'Idade',
                    'player.proposedMarketValue': 'Valor (M€)'
                }),
                height=400
            )
        else:
            st.warning("Selecione pelo menos uma métrica para comparação")

st.markdown("---")
st.caption("PlayerBenchmark Pro - Ferramenta de análise comparativa de jogadores")
