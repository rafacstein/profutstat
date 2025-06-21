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
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

# Carregar os dados do GitHub
df = load_data(GITHUB_CSV_URL)

# Pré-processamento dos dados
# 1. Agrupar por Jogo, Player, Evento e somar o Count
df_grouped = df.groupby(['Jogo', 'Player', 'Evento'])['Count'].sum().reset_index()

# 2. Calcular a média GLOBAL de cada Evento para cada Player (FIXA)
# Esta média incluirá todos os jogos do jogador na base de dados
player_overall_averages = df_grouped.groupby(['Player', 'Evento'])['Count'].mean().reset_index()
player_overall_averages.rename(columns={'Count': 'Média'}, inplace=True)


# Obter jogos e jogadores únicos para os filtros
all_games = sorted(df_grouped['Jogo'].unique().tolist())
all_players = sorted(df_grouped['Player'].unique().tolist())

# Definir eventos onde um aumento significa uma piora na performance
NEGATIVE_EVENTS = [
    'Passe Errado Curto', 'Passe Errado Longo', 'Passe Errado',
    'Chute Errado', 'Drible Errado', 'Perda da Bola', 'Falta Cometida',
    'Recepcao Errada'
]

# Função para calcular e comparar a performance
# Agora, recebe a média fixa global como argumento
def get_performance_data(current_game, player_name, df_data, player_avg_data):
    # Dados do jogo atual para o jogador selecionado
    current_game_events = df_data[(df_data['Jogo'] == current_game) & (df_data['Player'] == player_name)].copy()

    # Filtrar as médias globais para o jogador selecionado
    player_specific_avg = player_avg_data[player_avg_data['Player'] == player_name]

    # Unir os dados do jogo atual com a performance média GLOBAL do jogador
    comparison_df = pd.merge(current_game_events, player_specific_avg, on=['Evento', 'Player'], how='left')
    comparison_df.rename(columns={'Count': 'Atual'}, inplace=True)

    # Preencher valores NaN da coluna 'Média' com 0
    # (Caso um evento ocorreu no jogo atual, mas NUNCA nos outros jogos do jogador)
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
                comparison_df.loc[index, 'Mudança'] = 'Melhora (↓)'
            elif current_val > avg_val:
                comparison_df.loc[index, 'Mudança'] = 'Piora (↑)'
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
        col_widths = [80, 30, 30, 30] # Larguras em mm

        self.set_font('Arial', 'B', 9)
        for i, header in enumerate(df_to_print.columns.tolist()):
            self.cell(col_widths[i], 7, header, 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 8)
        for index, row in df_to_print.iterrows():
            for i, item in enumerate(row):
                self.cell(col_widths[i], 6, str(item), 1, 0, 'C')
            self.ln()
        self.ln(5)


def create_pdf_report(player_name, game_name, performance_df):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f'Jogador: {player_name}', 0, 1, 'L')
    pdf.cell(0, 10, f'Jogo: {game_name}', 0, 1, 'L')
    pdf.ln(5)

    df_for_pdf = performance_df[['Evento', 'Atual', 'Média', 'Mudança']].copy()
    df_for_pdf['Média'] = df_for_pdf['Média'].apply(lambda x: f"{x:.2f}")

    # Substituir caracteres problemáticos por equivalentes ASCII para o PDF
    df_for_pdf['Mudança'] = df_for_pdf['Mudança'].str.replace('↑', '(UP)').str.replace('↓', '(DOWN)').str.replace('—', '(-)')


    pdf.chapter_title('Resumo da Performance por Evento:')
    pdf.add_table(df_for_pdf)

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output.getvalue()


# --- Streamlit UI ---
st.sidebar.header('Filtros')
selected_game = st.sidebar.selectbox('Selecione o Jogo Atual:', all_games)
selected_player = st.sidebar.selectbox('Selecione o Jogador:', all_players)

if selected_game and selected_player:
    # Passar a média global para a função de performance
    performance_data = get_performance_data(selected_game, selected_player, df_grouped, player_overall_averages)

    st.subheader(f'Performance de {selected_player} no jogo: {selected_game}')

    st.write('---')
    st.markdown('**Resumo Detalhado da Performance por Evento:**')
    st.dataframe(performance_data[['Evento', 'Atual', 'Média', 'Mudança']].set_index('Evento'), use_container_width=True)

    st.write('---')
    st.subheader('Visão Rápida por Evento:')

    # Custom styling for boxes (using HTML and Markdown within st.markdown)
    # Define colors based on change status
    color_green = "#28a745" # Bootstrap success green
    color_red = "#dc3545"   # Bootstrap danger red
    color_gray = "#6c757d"  # Bootstrap secondary gray

    num_events = len(performance_data)
    num_cols = min(num_events, 3) # Max 3 columns
    cols = st.columns(num_cols)
    col_idx = 0

    for index, row in performance_data.iterrows():
        with cols[col_idx]:
            event_name = row['Evento']
            current_val = int(row['Atual'])
            avg_val = f"{row['Média']:.2f}"
            change_text = row['Mudança']

            display_arrow = ""
            display_color = color_gray # Default to gray

            # Determinar seta e cor baseadas na string de Mudança
            if 'Melhora (↑)' in change_text:
                display_arrow = "▲" # Seta para cima (Melhora)
                display_color = color_green
                indicator_text = "Melhora"
            elif 'Piora (↓)' in change_text:
                display_arrow = "▼" # Seta para baixo (Piora)
                display_color = color_red
                indicator_text = "Piora"
            else: # Mantém (—)
                display_arrow = "—" # Traço (Mantém)
                display_color = color_gray
                indicator_text = "Mantém"


            # Custom HTML/Markdown box for each statistic
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e6e6e6; /* Cor da borda mais suave */
                    border-radius: 8px; /* Cantos mais arredondados */
                    padding: 15px;
                    margin-bottom: 10px;
                    background-color: #ffffff; /* Fundo branco */
                    box-shadow: 0 4px 8px rgba(0,0,0,0.05); /* Sombra suave */
                ">
                    <h5 style="color: #333; margin-top: 0; margin-bottom: 5px; font-weight: 600;">{event_name}</h5>
                    <p style="font-size: 1.8em; font-weight: bold; color: #000; margin-bottom: 5px;">
                        {current_val} <small style="font-size: 0.5em; color: #777;">(Atual)</small>
                    </p>
                    <p style="font-size: 0.9em; color: #555; margin-bottom: 8px;">
                        Média: {avg_val}
                    </p>
                    <p style="font-size: 1.1em; font-weight: bold; color: {display_color};">
                        {display_arrow} {indicator_text}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        col_idx = (col_idx + 1) % num_cols

    st.write('---')
    pdf_bytes = create_pdf_report(selected_player, selected_game, performance_data)
    st.download_button(
        label="📄 Exportar Relatório como PDF",
        data=pdf_bytes,
        file_name=f"Relatorio_Performance_{selected_player}_{selected_game.replace(' ', '_').replace(':', '').replace('/', '_')}.pdf",
        mime="application/pdf"
    )

else:
    st.info('Por favor, selecione um jogo e um jogador para visualizar a performance.')
