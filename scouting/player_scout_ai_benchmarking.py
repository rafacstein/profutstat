import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import streamlit as st
from fuzzywuzzy import fuzz
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    page_title="PlayerBench Pro",
    page_icon="📊",
    layout="wide"
)

# --- Estilos CSS ---
st.markdown("""
<style>
    .header {
        padding: 20px;
        background: #f0f2f6;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .metric-title {
        color: #555;
        font-size: 14px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# --- Carregamento de Dados ---
@st.cache_resource
def load_data():
    try:
        # Carrega apenas colunas essenciais para economizar memória
        cols = [
            'player.name', 'player.team.name', 'position', 'age', 
            'goals', 'assists', 'keyPasses', 'tackles', 'interceptions',
            'accuratePassesPercentage', 'shotsOnTarget', 'minutesPlayed',
            'market_value'  # Alterado para um nome mais simples
        ]
        
        df = pd.read_parquet(
            'https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet',
            columns=cols
        )
        
        # Renomeia colunas para nomes mais simples
        df = df.rename(columns={
            'player.name': 'name',
            'player.team.name': 'team',
            'player.proposedMarketValue': 'market_value'  # Garante compatibilidade
        })
        
        # Preenche valores ausentes
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.stop()

df = load_data()

# --- Funções Auxiliares ---
def find_player(name, team=None):
    if not name:
        return None
    
    df_temp = df.copy()
    df_temp['name_sim'] = df_temp['name'].apply(lambda x: fuzz.token_set_ratio(name, x))
    
    if team:
        df_temp['team_sim'] = df_temp['team'].apply(lambda x: fuzz.token_set_ratio(team, x))
        df_temp['score'] = 0.7 * df_temp['name_sim'] + 0.3 * df_temp['team_sim']
    else:
        df_temp['score'] = df_temp['name_sim']
    
    best_match = df_temp.nlargest(1, 'score')
    
    if not best_match.empty and best_match['score'].iloc[0] >= 70:
        return best_match.index[0]
    return None

def filter_players(position=None, min_age=18, max_age=40, min_value=0, max_value=100):
    mask = (
        (df['age'] >= min_age) & 
        (df['age'] <= max_age) &
        (df['market_value'] >= min_value * 1_000_000) &
        (df['market_value'] <= max_value * 1_000_000)
    )
    
    if position:
        mask &= df['position'].isin(position)
    
    return df[mask].copy()

def create_comparison_chart(ref_player, compare_players, metrics):
    # Prepara dados para o gráfico
    data = []
    for metric in metrics:
        row = {'Metric': metric, 'Type': 'Referência', 'Value': ref_player[metric]}
        data.append(row)
        
        for _, player in compare_players.iterrows():
            row = {
                'Metric': metric,
                'Type': f"{player['name']} ({player['team']})",
                'Value': player[metric]
            }
            data.append(row)
    
    # Cria gráfico de barras
    fig = px.bar(
        pd.DataFrame(data),
        x='Metric', y='Value', color='Type', barmode='group',
        title="Comparação de Métricas",
        height=500
    )
    
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# --- Interface do Usuário ---
st.markdown("""
<div class="header">
    <h1>PlayerBench Pro</h1>
    <p>Ferramenta avançada de comparação de jogadores</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 Busca", "📊 Comparação"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Jogador de Referência")
        player_name = st.text_input("Nome do Jogador", key="player_name")
        team_name = st.text_input("Clube (opcional)", key="team_name")
        
        if player_name:
            player_id = find_player(player_name, team_name)
            
            if player_id is not None:
                ref_player = df.loc[player_id]
                st.session_state['ref_player'] = ref_player
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Jogador de Referência</div>
                    <div class="metric-value">{ref_player['name']}</div>
                    <div>{ref_player['team']} | {int(ref_player['age'])} anos | €{ref_player['market_value']/1_000_000:.2f}M</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Jogador não encontrado. Verifique o nome e tente novamente.")
                st.session_state['ref_player'] = None
    
    with col2:
        st.subheader("Filtros de Busca")
        
        positions = st.multiselect(
            "Posições",
            options=df['position'].unique(),
            default=['ST', 'AM', 'LW', 'RW']
        )
        
        min_age, max_age = st.slider(
            "Faixa de Idade",
            min_value=16, max_value=40, value=(18, 32)
        )
        
        min_value, max_value = st.slider(
            "Valor de Mercado (M€)",
            min_value=0, max_value=100, value=(1, 30)
        )
        
        if st.button("Buscar Jogadores", type="primary"):
            compare_players = filter_players(
                position=positions if positions else None,
                min_age=min_age,
                max_age=max_age,
                min_value=min_value,
                max_value=max_value
            )
            
            st.session_state['compare_players'] = compare_players
            st.success(f"Encontrados {len(compare_players)} jogadores")

with tab2:
    if 'ref_player' not in st.session_state or st.session_state['ref_player'] is None:
        st.warning("Por favor, selecione um jogador de referência na aba 'Busca'")
    elif 'compare_players' not in st.session_state or st.session_state['compare_players'].empty:
        st.warning("Nenhum jogador encontrado com os filtros aplicados. Ajuste os critérios e tente novamente.")
    else:
        ref_player = st.session_state['ref_player']
        compare_players = st.session_state['compare_players'].head(5)  # Limita a 5 para visualização
        
        st.subheader(f"Comparando com {ref_player['name']}")
        
        # Seleção de métricas
        available_metrics = [
            'goals', 'assists', 'keyPasses', 'tackles', 
            'interceptions', 'accuratePassesPercentage', 
            'shotsOnTarget', 'minutesPlayed'
        ]
        
        selected_metrics = st.multiselect(
            "Métricas para comparação",
            options=available_metrics,
            default=['goals', 'assists', 'keyPasses'],
            key="metrics_selector"
        )
        
        if selected_metrics:
            # Gráfico de comparação
            st.plotly_chart(
                create_comparison_chart(ref_player, compare_players, selected_metrics),
                use_container_width=True
            )
            
            # Tabela comparativa
            st.dataframe(
                compare_players[['name', 'team', 'position', 'age'] + selected_metrics]
                .assign(Valor_M€=lambda x: x['market_value']/1_000_000)
                .rename(columns={
                    'name': 'Nome',
                    'team': 'Clube',
                    'position': 'Posição',
                    'age': 'Idade'
                }),
                height=400,
                hide_index=True
            )
        else:
            st.warning("Selecione pelo menos uma métrica para comparação")

st.markdown("---")
st.caption("© 2025 PlayerBench Pro - Ferramenta de análise de jogadores")
