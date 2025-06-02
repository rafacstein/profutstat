import pandas as pd
import numpy as np
import streamlit as st
from fuzzywuzzy import fuzz
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    page_title="PlayerCompare Pro",
    page_icon="⚽",
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

# --- Carregamento de Dados com Tratamento Robustecido ---
@st.cache_resource
def load_data():
    try:
        # Lista de colunas essenciais que devem existir
        essential_cols = [
            'player.name', 'player.team.name', 'position', 'age',
            'goals', 'assists', 'keyPasses', 'tackles', 'interceptions',
            'accuratePassesPercentage', 'shotsOnTarget', 'minutesPlayed'
        ]
        
        # Tenta carregar o DataFrame
        df = pd.read_parquet(
            'https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet',
            columns=essential_cols
        )
        
        # Verifica se todas as colunas essenciais existem
        missing_cols = [col for col in essential_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Colunas essenciais faltando: {', '.join(missing_cols)}")
            st.stop()
        
        # Adiciona valor de mercado se não existir (com valores padrão)
        if 'player.proposedMarketValue' not in df.columns:
            df['player.proposedMarketValue'] = 1_000_000  # Valor padrão em euros
            
        # Renomeia colunas para nomes mais simples
        df = df.rename(columns={
            'player.name': 'name',
            'player.team.name': 'team',
            'player.proposedMarketValue': 'market_value'
        })
        
        # Preenche valores ausentes
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        return df
        
    except Exception as e:
        st.error(f"Erro crítico ao carregar dados: {str(e)}")
        st.stop()

df = load_data()

# --- Funções Auxiliares ---
def find_player(name, team=None):
    """Encontra jogador usando fuzzy matching com tratamento robusto"""
    if not name or not isinstance(name, str):
        return None
    
    try:
        df_temp = df.copy()
        df_temp['name_sim'] = df_temp['name'].apply(lambda x: fuzz.token_set_ratio(name, str(x)))  # Garante conversão para string
        
        if team and isinstance(team, str):
            df_temp['team_sim'] = df_temp['team'].apply(
                lambda x: fuzz.token_set_ratio(team, str(x)))
            df_temp['score'] = 0.7 * df_temp['name_sim'] + 0.3 * df_temp['team_sim']
        else:
            df_temp['score'] = df_temp['name_sim']
        
        best_match = df_temp.nlargest(1, 'score')
        
        if not best_match.empty and best_match['score'].iloc[0] >= 70:
            return best_match.index[0]
        return None
        
    except Exception as e:
        st.error(f"Erro ao buscar jogador: {str(e)}")
        return None

def filter_players(position=None, min_age=18, max_age=40, min_value=0, max_value=100):
    """Filtra jogadores com verificação de tipos"""
    try:
        # Verifica tipos dos parâmetros
        min_age = int(min_age)
        max_age = int(max_age)
        min_value = float(min_value)
        max_value = float(max_value)
        
        mask = (
            (df['age'] >= min_age) & 
            (df['age'] <= max_age) &
            (df['market_value'] >= min_value * 1_000_000) &
            (df['market_value'] <= max_value * 1_000_000)
        )
        
        if position:
            if not isinstance(position, (list, tuple)):
                position = [position]
            mask &= df['position'].isin(position)
        
        return df[mask].copy()
        
    except Exception as e:
        st.error(f"Erro ao filtrar jogadores: {str(e)}")
        return pd.DataFrame()

def create_comparison_data(ref_player, compare_players, metrics):
    """Cria dados para comparação com verificação de colunas"""
    try:
        # Verifica se as métricas existem no DataFrame
        valid_metrics = [m for m in metrics if m in df.columns]
        if not valid_metrics:
            st.warning("Nenhuma métrica válida selecionada")
            return pd.DataFrame()
        
        # Prepara dados
        data = []
        for metric in valid_metrics:
            # Adiciona referência
            data.append({
                'Metric': metric,
                'Type': 'Referência',
                'Value': ref_player[metric],
                'Player': ref_player['name']
            })
            
            # Adiciona jogadores comparados
            for _, player in compare_players.iterrows():
                data.append({
                    'Metric': metric,
                    'Type': 'Comparação',
                    'Value': player[metric],
                    'Player': player['name']
                })
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Erro ao preparar dados: {str(e)}")
        return pd.DataFrame()

# --- Interface do Usuário ---
st.markdown("""
<div class="header">
    <h1>PlayerCompare Pro</h1>
    <p>Ferramenta avançada de análise comparativa de jogadores</p>
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
                    <h3>{ref_player['name']}</h3>
                    <p><strong>Clube:</strong> {ref_player['team']}</p>
                    <p><strong>Posição:</strong> {ref_player['position']}</p>
                    <p><strong>Idade:</strong> {int(ref_player['age'])}</p>
                    <p><strong>Valor de mercado:</strong> €{ref_player['market_value']/1_000_000:.2f}M</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Jogador não encontrado. Verifique o nome e tente novamente.")
                st.session_state['ref_player'] = None
    
    with col2:
        st.subheader("Filtros de Busca")
        
        positions = st.multiselect(
            "Posições",
            options=df['position'].unique().tolist(),
            default=['ST', 'AM'],
            key="positions"
        )
        
        min_age, max_age = st.slider(
            "Faixa de Idade",
            min_value=16, max_value=40, value=(18, 32),
            key="age_range"
        )
        
        min_value, max_value = st.slider(
            "Valor de Mercado (M€)",
            min_value=0.0, max_value=100.0, value=(1.0, 30.0),
            step=0.5,
            key="value_range"
        )
        
        if st.button("Buscar Jogadores", type="primary", key="search_button"):
            with st.spinner("Buscando jogadores..."):
                compare_players = filter_players(
                    position=positions,
                    min_age=min_age,
                    max_age=max_age,
                    min_value=min_value,
                    max_value=max_value
                )
                
                st.session_state['compare_players'] = compare_players
                
                if not compare_players.empty:
                    st.success(f"Encontrados {len(compare_players)} jogadores")
                else:
                    st.warning("Nenhum jogador encontrado com os critérios selecionados")

with tab2:
    if 'ref_player' not in st.session_state or st.session_state['ref_player'] is None:
        st.warning("Por favor, selecione um jogador de referência na aba 'Busca'")
    elif 'compare_players' not in st.session_state or st.session_state['compare_players'].empty:
        st.warning("Nenhum jogador encontrado para comparação. Ajuste os filtros e tente novamente.")
    else:
        ref_player = st.session_state['ref_player']
        compare_players = st.session_state['compare_players'].head(10)  # Limita a 10 para visualização
        
        st.subheader(f"Comparação com {ref_player['name']}")
        
        # Seleção de métricas
        available_metrics = [
            'goals', 'assists', 'keyPasses', 'tackles', 
            'interceptions', 'accuratePassesPercentage', 
            'shotsOnTarget', 'minutesPlayed', 'market_value'
        ]
        
        selected_metrics = st.multiselect(
            "Selecione métricas para comparação",
            options=available_metrics,
            default=['goals', 'assists', 'keyPasses'],
            key="metrics_select"
        )
        
        if selected_metrics:
            # Cria dados para comparação
            comparison_data = create_comparison_data(ref_player, compare_players, selected_metrics)
            
            if not comparison_data.empty:
                # Gráfico de comparação
                fig = px.bar(
                    comparison_data,
                    x='Metric', y='Value', color='Player', barmode='group',
                    title=f"Comparação com {ref_player['name']}",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela comparativa
                st.subheader("Dados Detalhados")
                
                # Prepara DataFrame para exibição
                display_df = compare_players[
                    ['name', 'team', 'position', 'age'] + selected_metrics
                ].copy()
                
                # Formata valor de mercado se estiver nas métricas selecionadas
                if 'market_value' in display_df.columns:
                    display_df['market_value'] = display_df['market_value'].apply(
                        lambda x: f"€{x/1_000_000:.2f}M")
                
                # Renomeia colunas
                display_df = display_df.rename(columns={
                    'name': 'Nome',
                    'team': 'Clube',
                    'position': 'Posição',
                    'age': 'Idade'
                })
                
                st.dataframe(
                    display_df,
                    height=400,
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning("Não foi possível gerar a comparação. Verifique as métricas selecionadas.")
        else:
            st.warning("Selecione pelo menos uma métrica para comparação")

st.markdown("---")
st.caption("© 2025 PlayerCompare Pro - Ferramenta profissional de análise de jogadores")
