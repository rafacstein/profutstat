import streamlit as st
import pandas as pd

# Título do Dashboard
st.set_page_config(layout="wide")
st.title('Comparativo de Performance de Jogador')

# Função para carregar os dados
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

# Carregar os dados
df = load_data('Monitoramento São Bento U13 - CONSOLIDADO INDIVIDUAL.csv')

# Pré-processamento dos dados
df_grouped = df.groupby(['Jogo', 'Player', 'Evento'])['Count'].sum().reset_index()

# Obter jogos e jogadores únicos para os filtros
all_games = df_grouped['Jogo'].unique().tolist()
all_players = df_grouped['Player'].unique().tolist()

# Criar os seletores no Streamlit
st.sidebar.header('Filtros')
selected_game = st.sidebar.selectbox('Selecione o Jogo Atual:', all_games)
selected_player = st.sidebar.selectbox('Selecione o Jogador:', all_players)

# Função para calcular e comparar a performance
def get_performance_data(current_game, player_name, df_data):
    # Dados do jogo atual e jogador selecionado
    current_game_data = df_data[(df_data['Jogo'] == current_game) & (df_data['Player'] == player_name)]

    # Dados do jogador selecionado em todos os outros jogos (para calcular a média)
    other_games_data = df_data[(df_data['Jogo'] != current_game) & (df_data['Player'] == player_name)]

    # Calcular a performance média do jogador nos outros jogos
    if not other_games_data.empty:
        average_performance = other_games_data.groupby('Evento')['Count'].mean().reset_index()
        average_performance.rename(columns={'Count': 'Média'}, inplace=True)
    else:
        average_performance = pd.DataFrame(columns=['Evento', 'Média'])


    # Unir os dados do jogo atual com a performance média
    comparison_df = pd.merge(current_game_data, average_performance, on='Evento', how='left')
    comparison_df.rename(columns={'Count': 'Atual'}, inplace=True)

    # Preencher valores NaN da coluna 'Média' com 0
    comparison_df['Média'].fillna(0, inplace=True)

    # Determinar a mudança de performance
    comparison_df['Mudança'] = ''
    for index, row in comparison_df.iterrows():
        if row['Atual'] > row['Média']:
            comparison_df.loc[index, 'Mudança'] = 'Melhora (↑)'
        elif row['Atual'] < row['Média']:
            comparison_df.loc[index, 'Mudança'] = 'Piora (↓)'
        else:
            comparison_df.loc[index, 'Mudança'] = 'Mantém (—)'

    return comparison_df

if selected_game and selected_player:
    performance_data = get_performance_data(selected_game, selected_player, df_grouped)

    st.subheader(f'Performance de {selected_player} no jogo: {selected_game}')

    # Exibir tabela com todos os eventos
    st.write('**Resumo da Performance por Evento:**')
    st.dataframe(performance_data[['Evento', 'Atual', 'Média', 'Mudança']].set_index('Evento'))

    st.write('---')
    st.subheader('Detalhes por Evento:')

    # Exibir caixas individuais para cada evento
    cols = st.columns(3) # Crie 3 colunas para os cartões
    col_idx = 0

    for index, row in performance_data.iterrows():
        with cols[col_idx]:
            st.metric(
                label=row['Evento'],
                value=f"{row['Atual']} (Atual)",
                delta=f"{row['Média']:.2f} (Média) | {row['Mudança']}",
                delta_color="off" # Desativa a cor padrão do delta para usar o texto
            )
        col_idx = (col_idx + 1) % 3

else:
    st.info('Selecione um jogo e um jogador para ver a performance.')
