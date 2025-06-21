import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

# Título do Dashboard
st.set_page_config(layout="wide")
st.title('📊 Comparativo de Performance de Jogador')

# URL do arquivo CSV no GitHub (RAW)
GITHUB_CSV_URL = 'https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/Monitoramento%20S%C3%A3o%20Bento%20U13%20-%20CONSOLIDADO%20INDIVIDUAL.csv'

# Função para carregar os dados
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    # Ensure 'Timestamp' is datetime for chronological sorting
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

# Carregar os dados do GitHub
df = load_data(GITHUB_CSV_URL)

# Pré-processamento dos dados
# Agrupar por Jogo, Player, Evento e somar o Count
df_grouped = df.groupby(['Jogo', 'Player', 'Evento'])['Count'].sum().reset_index()

# Obter o timestamp máximo para cada jogo (para ordenação cronológica dos jogos)
game_max_timestamps = df.groupby('Jogo')['Timestamp'].max().reset_index()
game_max_timestamps.rename(columns={'Timestamp': 'MaxGameTimestamp'}, inplace=True)

# Unir o timestamp máximo de volta ao df_grouped
df_grouped = pd.merge(df_grouped, game_max_timestamps, on='Jogo', how='left')


# Obter jogos e jogadores únicos para os filtros
all_games = sorted(df_grouped['Jogo'].unique().tolist()) # Ordenar para consistência
all_players = sorted(df_grouped['Player'].unique().tolist())

# Definir eventos onde um aumento significa uma piora na performance
NEGATIVE_EVENTS = [
    'Passe Errado Curto', 'Passe Errado Longo', 'Passe Errado',
    'Chute Errado', 'Drible Errado', 'Perda da Bola', 'Falta Cometida',
    'Recepcao Errada'
]

# Função para calcular e comparar a performance
def get_performance_data(current_game, player_name, df_data):
    # Filtrar dados para o jogador selecionado
    player_all_data = df_data[df_data['Player'] == player_name].copy()

    # Dados do jogo atual para o jogador selecionado
    current_game_events = player_all_data[player_all_data['Jogo'] == current_game]

    # Filtrar o jogo atual dos dados do jogador para encontrar "outros" jogos
    other_games_for_player = player_all_data[player_all_data['Jogo'] != current_game]

    # Obter jogos únicos jogados pelo atleta (excluindo o jogo atual), ordenados pelo timestamp mais recente
    unique_other_games = other_games_for_player[['Jogo', 'MaxGameTimestamp']].drop_duplicates()
    unique_other_games_sorted = unique_other_games.sort_values(by='MaxGameTimestamp', ascending=False)

    # Selecionar os dois jogos mais recentes (ou um, se só houver um)
    games_for_average = unique_other_games_sorted['Jogo'].head(2).tolist()

    # Calcular a performance média do atleta a partir desses 1 ou 2 jogos
    average_performance_df = pd.DataFrame(columns=['Evento', 'Média'])
    if games_for_average:
        data_for_average = player_all_data[player_all_data['Jogo'].isin(games_for_average)]
        if not data_for_average.empty:
            average_performance_df = data_for_average.groupby('Evento')['Count'].mean().reset_index()
            average_performance_df.rename(columns={'Count': 'Média'}, inplace=True)

    # Unir os dados do jogo atual com a performance média
    comparison_df = pd.merge(current_game_events, average_performance_df, on='Evento', how='left')
    comparison_df.rename(columns={'Count': 'Atual'}, inplace=True)

    # Preencher valores NaN da coluna 'Média' com 0 onde não há média correspondente
    comparison_df['Média'].fillna(0, inplace=True)

    # Determinar a mudança de performance e o ícone
    comparison_df['Mudança'] = ''
    for index, row in comparison_df.iterrows():
        current_val = row['Atual']
        avg_val = row['Média']
        event_name = row['Evento']

        if event_name in NEGATIVE_EVENTS:
            # Para eventos negativos, menos é melhor (redução = melhora)
            if current_val < avg_val:
                comparison_df.loc[index, 'Mudança'] = 'Melhora (↓)' # Diminuiu um evento ruim
            elif current_val > avg_val:
                comparison_df.loc[index, 'Mudança'] = 'Piora (↑)' # Aumentou um evento ruim
            else:
                comparison_df.loc[index, 'Mudança'] = 'Mantém (—)'
        else:
            # Para eventos positivos, mais é melhor (aumento = melhora)
            if current_val > avg_val:
                comparison_df.loc[index, 'Mudança'] = 'Melhora (↑)'
            elif current_val < avg_val:
                comparison_df.loc[index, 'Mudança'] = 'Piora (↓)'
            else:
                comparison_df.loc[index, 'Mudança'] = 'Mantém (—)'

    return comparison_df

# --- Geração de PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Performance do Jogador', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 6, title, 0, 1, 'L')
        self.ln(2)

    def add_table(self, df_to_print):
        # Defina as larguras das colunas - ajuste conforme necessário
        # Assumindo 4 colunas: Evento, Atual, Média, Mudança
        # Largura total da página - margens (20mm de cada lado) = 210 - 40 = 170mm
        col_widths = [80, 30, 30, 30] # Exemplo de larguras em mm

        # Cabeçalho da Tabela
        self.set_font('Arial', 'B', 9)
        for i, header in enumerate(df_to_print.columns.tolist()):
            self.cell(col_widths[i], 7, header, 1, 0, 'C')
        self.ln()

        # Linhas da Tabela
        self.set_font('Arial', '', 8)
        # Iterate over DataFrame rows and add to PDF
        for index, row in df_to_print.iterrows():
            for i, item in enumerate(row):
                self.cell(col_widths[i], 6, str(item), 1, 0, 'C')
            self.ln()
        self.ln(5)


def create_pdf_report(player_name, game_name, performance_df):
    pdf = PDF()
    pdf.add_page()

    # Adicionar informações do jogador e jogo
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f'Jogador: {player_name}', 0, 1, 'L')
    pdf.cell(0, 10, f'Jogo: {game_name}', 0, 1, 'L')
    pdf.ln(5)

    # Adicionar tabela resumo da performance
    pdf.chapter_title('Resumo da Performance por Evento:')
    # Selecionar colunas para imprimir no PDF e formatar 'Média'
    df_for_pdf = performance_df[['Evento', 'Atual', 'Média', 'Mudança']].copy()
    df_for_pdf['Média'] = df_for_pdf['Média'].apply(lambda x: f"{x:.2f}")

    pdf.add_table(df_for_pdf)

    # Saída como bytes para download
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output.getvalue()


# --- Streamlit UI ---
st.sidebar.header('Filtros')
selected_game = st.sidebar.selectbox('Selecione o Jogo Atual:', all_games)
selected_player = st.sidebar.selectbox('Selecione o Jogador:', all_players)

if selected_game and selected_player:
    performance_data = get_performance_data(selected_game, selected_player, df_grouped)

    st.subheader(f'Performance de {selected_player} no jogo: {selected_game}')

    # Exibir tabela com todos os eventos
    st.write('---')
    st.markdown('**Resumo Detalhado da Performance por Evento:**')
    st.dataframe(performance_data[['Evento', 'Atual', 'Média', 'Mudança']].set_index('Evento'), use_container_width=True)

    st.write('---')
    st.subheader('Visão Rápida por Evento:')

    # Exibir caixas individuais para cada evento
    # Crie as colunas dinamicamente com base no número de eventos ou fixe 3
    num_events = len(performance_data)
    num_cols = min(num_events, 3) # Max 3 columns
    cols = st.columns(num_cols)
    col_idx = 0

    for index, row in performance_data.iterrows():
        with cols[col_idx]:
            # Ajuste para cores de delta e ícones de acordo com 'Melhora (↑)' ou 'Piora (↓)'
            delta_text = row['Mudança']
            delta_color = "normal" # Default color, no specific highlight

            if 'Melhora' in delta_text:
                # Green for positive improvements, including reduction of negative events
                delta_color = "inverse" if row['Evento'] in NEGATIVE_EVENTS else "normal"
                # For negative events, inverse color to make less red more green
                # Streamlit metric delta_color: "normal" (green for positive delta), "inverse" (red for positive delta), "off" (no color)

            elif 'Piora' in delta_text:
                # Red for worsening, including increase of negative events
                delta_color = "normal" if row['Evento'] in NEGATIVE_EVENTS else "inverse"


            st.metric(
                label=row['Evento'],
                value=f"{int(row['Atual'])} (Atual)", # Exibir como inteiro se for um contador
                delta=f"{row['Média']:.2f} (Média) | {delta_text}",
                delta_color=delta_color
            )
        col_idx = (col_idx + 1) % num_cols

    st.write('---')
    # Botão para exportar para PDF
    pdf_bytes = create_pdf_report(selected_player, selected_game, performance_data)
    st.download_button(
        label="📄 Exportar Relatório como PDF",
        data=pdf_bytes,
        file_name=f"Relatorio_Performance_{selected_player}_{selected_game.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

else:
    st.info('Por favor, selecione um jogo e um jogador para visualizar a performance.')
