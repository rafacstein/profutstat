import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard de Performance dos Atletas")

# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                # Assumimos que o log completo está na primeira aba ou em 'Log Completo de Eventos'
                df = pd.read_excel(uploaded_file, sheet_name='Log Completo de Eventos')
            else:
                st.error("Formato de arquivo não suportado. Por favor, carregue um CSV ou XLSX.")
                return pd.DataFrame()
            
            # Garante que as colunas essenciais existem
            required_cols = ["Event", "Minute", "Second", "Team", "Player", "Type", "SubType"]
            if not all(col in df.columns for col in required_cols):
                st.error(f"O arquivo não contém todas as colunas necessárias: {', '.join(required_cols)}. Verifique se você exportou o 'Log Completo de Eventos'.")
                return pd.DataFrame()

            # Processamento básico para garantir tipos corretos
            df['Minute'] = pd.to_numeric(df['Minute'], errors='coerce').fillna(0).astype(int)
            df['Second'] = pd.to_numeric(df['Second'], errors='coerce').fillna(0).astype(int)
            
            # Criar uma coluna 'Evento Completo' para facilitar a pivotagem e visualização
            df['CombinedEvent'] = df.apply(lambda row: ' - '.join(filter(None, [row['Event'], str(row['Type']), str(row['SubType'])])).strip(' -'), axis=1)
            
            return df
        except Exception as e:
            st.error(f"Erro ao carregar ou processar o arquivo: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- TÍTULO DO DASHBOARD ---
st.title("📊 Dashboard de Performance dos Atletas")
st.markdown("Analise o desempenho individual dos jogadores do seu time.")

# --- SEÇÃO DE CARREGAMENTO DE ARQUIVO ---
st.sidebar.header("📁 Carregar Dados do Scout")
uploaded_file = st.sidebar.file_uploader("Arraste e solte seu arquivo .csv ou .xlsx aqui", type=["csv", "xlsx"])

df_match = load_data(uploaded_file)

if df_match.empty:
    st.info("⬆️ Por favor, carregue um arquivo de log do scout para visualizar o dashboard.")
else:
    st.success(f"Dados carregados com sucesso de '{uploaded_file.name}'!")

    # --- FILTROS LATERAIS ---
    st.sidebar.header("⚙️ Opções de Visualização")
    all_players = sorted(df_match['Player'].unique().tolist())
    selected_players = st.sidebar.multiselect("Filtrar por Jogador(es):", all_players, default=all_players)

    all_events = sorted(df_match['Event'].unique().tolist())
    selected_events = st.sidebar.multiselect("Filtrar por Tipo de Evento:", all_events, default=all_events)

    filtered_df = df_match[
        (df_match['Player'].isin(selected_players)) &
        (df_match['Event'].isin(selected_events))
    ].copy() # Usar .copy() para evitar SettingWithCopyWarning

    if filtered_df.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados. Tente ajustar os filtros.")
    else:
        # --- VISÃO GERAL DO TIME (KPIs) ---
        st.markdown("---")
        st.header("Visão Geral do Time")
        
        team_name = filtered_df['Team'].iloc[0] if not filtered_df.empty else "Time"
        st.subheader(f"Métricas para: **{team_name}**")

        col1, col2, col3, col4 = st.columns(4)
        
        total_goals = filtered_df[filtered_df['Event'] == 'Gol'].shape[0]
        total_shots = filtered_df[filtered_df['Event'] == 'Finalização'].shape[0]
        total_assists = filtered_df[filtered_df['Event'] == 'Assistência'].shape[0]
        total_passes_attempted = filtered_df[filtered_df['Event'] == 'Passe'].shape[0]

        col1.metric("Gols Marcados", total_goals)
        col2.metric("Total de Finalizações", total_shots)
        col3.metric("Assistências", total_assists)
        col4.metric("Passes Tentados", total_passes_attempted)

        # --- PERFORMANCE INDIVIDUAL DOS ATLETAS ---
        st.markdown("---")
        st.header("Performance Individual dos Atletas")

        # Preparar dados para gráficos de barras por jogador
        player_performance = filtered_df.groupby(['Player', 'CombinedEvent']).size().unstack(fill_value=0).reset_index()
        
        # Opcional: Calcular porcentagens para alguns eventos (ex: passes)
        passes_correct = filtered_df[(filtered_df['Event'] == 'Passe') & (filtered_df['Type'] == 'Certo')].groupby('Player').size()
        passes_total = filtered_df[filtered_df['Event'] == 'Passe'].groupby('Player').size()
        
        # Calcular a eficiência dos passes e fusão com player_performance
        pass_efficiency = ((passes_correct / passes_total) * 100).fillna(0).round(1).reset_index(name='Eficiência de Passe (%)')
        if not pass_efficiency.empty:
             player_performance = pd.merge(player_performance, pass_efficiency, on='Player', how='left').fillna(0)

        # 1. Tabela de Resumo por Jogador
        st.subheader("Resumo de Eventos por Jogador")
        st.dataframe(player_performance.sort_values(by="Player"), use_container_width=True)

        # 2. Gráfico de Barras: Gols e Assistências por Jogador
        st.subheader("Gols e Assistências por Jogador")
        goals_assists = filtered_df[filtered_df['Event'].isin(['Gol', 'Assistência'])]
        if not goals_assists.empty:
            fig_ga = px.bar(
                goals_assists.groupby(['Player', 'Event']).size().reset_index(name='Count'),
                x='Player',
                y='Count',
                color='Event',
                barmode='group',
                title='Gols e Assistências',
                labels={'Count': 'Contagem de Eventos', 'Player': 'Jogador', 'Event': 'Evento'},
                hover_data={'Count':True, 'Event':True}
            )
            fig_ga.update_layout(xaxis_title="Jogador", yaxis_title="Número de Gols/Assistências")
            st.plotly_chart(fig_ga, use_container_width=True)
        else:
            st.info("Nenhum gol ou assistência encontrado com os filtros aplicados.")

        # 3. Gráfico de Barras: Ações Defensivas por Jogador
        st.subheader("Ações Defensivas por Jogador")
        defensive_actions = filtered_df[filtered_df['Event'].isin(['Defesa', 'Interceptação', 'Corte', 'Recuperação', 'Pressão'])]
        if not defensive_actions.empty:
            # Reagrupando 'Defesa' para incluir subtipos se existirem, ou usar o Event principal
            defensive_actions['DisplayEvent'] = defensive_actions.apply(
                lambda row: f"{row['Event']} - {row['SubType']}" if pd.notna(row['SubType']) and row['SubType'] != '' else row['Event'], axis=1)

            fig_def = px.bar(
                defensive_actions.groupby(['Player', 'DisplayEvent']).size().reset_index(name='Count'),
                x='Player',
                y='Count',
                color='DisplayEvent',
                barmode='stack',
                title='Ações Defensivas',
                labels={'Count': 'Contagem de Ações', 'Player': 'Jogador', 'DisplayEvent': 'Tipo de Ação'},
                hover_data={'Count':True, 'DisplayEvent':True}
            )
            fig_def.update_layout(xaxis_title="Jogador", yaxis_title="Número de Ações Defensivas")
            st.plotly_chart(fig_def, use_container_width=True)
        else:
            st.info("Nenhuma ação defensiva encontrada com os filtros aplicados.")
        
        # 4. Gráfico de Pizza: Tipos de Passes (se houver dados)
        st.subheader("Eficiência de Passe por Jogador")
        if 'Eficiência de Passe (%)' in player_performance.columns and not player_performance.empty:
            # Filtra apenas jogadores com alguma tentativa de passe
            players_with_passes = player_performance[player_performance['Eficiência de Passe (%)'] > 0]
            if not players_with_passes.empty:
                fig_pass_eff = px.bar(
                    players_with_passes,
                    x='Player',
                    y='Eficiência de Passe (%)',
                    color='Eficiência de Passe (%)',
                    color_continuous_scale=px.colors.sequential.Viridis,
                    title='Eficiência de Passe por Jogador',
                    labels={'Eficiência de Passe (%)': 'Eficiência (%)', 'Player': 'Jogador'},
                    hover_data={'Eficiência de Passe (%)': ':.1f'}
                )
                fig_pass_eff.update_layout(xaxis_title="Jogador", yaxis_title="Eficiência de Passe (%)")
                st.plotly_chart(fig_pass_eff, use_container_width=True)
            else:
                st.info("Nenhum passe tentado pelos jogadores selecionados para calcular a eficiência.")
        else:
            st.info("Dados de passes insuficientes para exibir a eficiência.")

        # --- Log de Observações (opcional) ---
        st.markdown("---")
        st.header("📝 Observações do Jogo")
        observations_df = filtered_df[filtered_df['Event'] == 'Observação'][['Minute', 'Second', 'Observation', 'Timestamp']]
        if not observations_df.empty:
            st.dataframe(observations_df.sort_values(by=['Minute', 'Second']), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma observação registrada para os filtros selecionados.")

