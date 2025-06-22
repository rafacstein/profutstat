import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(layout="centered", page_title="Dashboard de Performance")

st.title('📊 Comparativo de Performance do Atleta')

# --- Carregamento de Dados ---
GITHUB_CSV_URL = 'https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/Monitoramento%20S%C3%A3o%20Bento%20U13%20-%20CONSOLIDADO%20INDIVIDUAL.csv'

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

df = load_data(GITHUB_CSV_URL)

# --- Pré-processamento de Dados ---
# 1. Agrupar por Jogo, Player, Evento e somar o Count
df_grouped = df.groupby(['Jogo', 'Player', 'Evento'])['Count'].sum().reset_index()

# Obter todos os jogadores e jogos únicos para os filtros
all_games = sorted(df_grouped['Jogo'].unique().tolist())
all_players = sorted(df_grouped['Player'].unique().tolist())

# --- Definição das Categorias de Métricas e sua Natureza (Positiva/Negativa) ---
METRIC_CATEGORIES_CONFIG = {
    "Passes Certos": {'events': ['Passe Certo Curto', 'Passe Certo Longo'], 'is_negative': False},
    "Passes Errados": {'events': ['Passe Errado Curto', 'Passe Errado Longo', 'Passe Errado'], 'is_negative': True},
    "Chutes Certos": {'events': ['Chute Certo'], 'is_negative': False},
    "Chutes Errados": {'events': ['Chute Errado'], 'is_negative': True},
    "Dribles Certos": {'events': ['Drible Certo'], 'is_negative': False},
    "Dribles Errados": {'events': ['Drible Errado'], 'is_negative': True},
    "Roubadas de Bola": {'events': ['Roubada de Bola'], 'is_negative': False},
    "Perdas de Bola": {'events': ['Perda da Bola'], 'is_negative': True},
    "Faltas Cometidas": {'events': ['Falta Cometida'], 'is_negative': True},
    "Faltas Sofridas": {'events': ['Falta Sofrida'], 'is_negative': False},
    "Recepções Erradas": {'events': ['Recepcao Errada'], 'is_negative': True},
    # Se houver um evento 'Drible' genérico, decida se ele deve ser somado a Dribles Certos/Errados ou ter sua própria categoria.
    # No exemplo original, 'Drible' é um evento distinto. Para simplicidade, vamos usar apenas os 'Certo'/'Errado' para Dribles.
}


# --- Pré-cálculo das Médias Globais por Categoria e Jogador ---
# Esta etapa cria um DataFrame onde cada linha é um (Jogador, Jogo, Categoria, Contagem)
df_categorized_counts_per_game = pd.DataFrame()
for player in all_players:
    player_data = df_grouped[df_grouped['Player'] == player]
    unique_games_for_player = player_data['Jogo'].unique() # Get unique games per player
    for game in unique_games_for_player:
        game_player_data = player_data[player_data['Jogo'] == game]
        
        category_counts = {'Player': player, 'Jogo': game}
        for category_name, config in METRIC_CATEGORIES_CONFIG.items():
            # Soma os 'Count' dos eventos que compõem esta categoria neste jogo
            category_sum = game_player_data[game_player_data['Evento'].isin(config['events'])]['Count'].sum()
            category_counts[category_name] = category_sum
        
        # Concatena com um DataFrame vazio se for o primeiro, ou com o existente
        df_categorized_counts_per_game = pd.concat([df_categorized_counts_per_game, pd.DataFrame([category_counts])], ignore_index=True)


# Agora, calculamos a média global para cada categoria por jogador
# Excluímos 'Jogo' da média, pois queremos a média por jogador por categoria em todos os jogos.
player_category_overall_averages = df_categorized_counts_per_game.groupby('Player').mean(numeric_only=True).reset_index()


# --- Função para Obter Dados de Performance por Categoria ---
def get_performance_data_by_category(current_game, player_name, df_categorized_data, player_avg_category_data):
    # Dados da partida atual para o jogador, agregados por categoria
    current_game_category_data = df_categorized_data[
        (df_categorized_data['Player'] == player_name) &
        (df_categorized_data['Jogo'] == current_game)
    ]
    
    # Dados da média global por categoria para o jogador
    player_category_avg = player_avg_category_data[player_avg_category_data['Player'] == player_name]

    comparison_list = []
    for category_name, config in METRIC_CATEGORIES_CONFIG.items():
        # Valor atual: 0 se a categoria não existiu no jogo
        current_val = current_game_category_data[category_name].iloc[0] if category_name in current_game_category_data.columns and not current_game_category_data.empty else 0
        # Valor médio: 0 se a categoria não existiu para o jogador na média global
        avg_val = player_category_avg[category_name].iloc[0] if category_name in player_category_avg.columns and not player_category_avg.empty else 0

        display_arrow = ""
        indicator_text_raw = "Mantém" # Texto original (com ou sem setas para UI)
        indicator_text_pdf = "Mantém (-)" # Texto para PDF

        # Lógica de comparação
        if config['is_negative']: # Se a categoria é de eventos "ruins"
            if current_val < avg_val:
                indicator_text_raw = "Melhora (↓)" # Menos eventos ruins é melhor
                indicator_text_pdf = "Melhora (DOWN)"
            elif current_val > avg_val:
                indicator_text_raw = "Piora (↑)" # Mais eventos ruins é pior
                indicator_text_pdf = "Piora (UP)"
            # else: Mantém
        else: # Se a categoria é de eventos "bons"
            if current_val > avg_val:
                indicator_text_raw = "Melhora (↑)" # Mais eventos bons é melhor
                indicator_text_pdf = "Melhora (UP)"
            elif current_val < avg_val:
                indicator_text_raw = "Piora (↓)" # Menos eventos bons é pior
                indicator_text_pdf = "Piora (DOWN)"
            # else: Mantém

        comparison_list.append({
            'Category': category_name,
            'Atual': current_val,
            'Média': avg_val,
            'Mudança_UI': indicator_text_raw, # Para a interface do usuário (com setas Unicode)
            'Mudança_PDF': indicator_text_pdf # Para o PDF (sem caracteres Unicode problemáticos)
        })
    return pd.DataFrame(comparison_list)


# --- Geração de PDF (Adaptada para as novas categorias) ---
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
        # As larguras das colunas precisarão ser ajustadas se houver mais categorias
        col_widths = [80, 30, 30, 30] 
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

def create_pdf_report(player_name, game_name, performance_data_category):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f'Jogador: {player_name}', 0, 1, 'L')
    pdf.cell(0, 10, f'Jogo: {game_name}', 0, 1, 'L')
    pdf.ln(5)

    # Prepara o DataFrame para o PDF, usando a coluna Mudança_PDF
    df_for_pdf = performance_data_category[['Category', 'Atual', 'Média', 'Mudança_PDF']].copy()
    df_for_pdf.rename(columns={'Category': 'Categoria', 'Mudança_PDF': 'Mudança'}, inplace=True)
    df_for_pdf['Média'] = df_for_pdf['Média'].apply(lambda x: f"{x:.2f}")
    
    pdf.chapter_title('Resumo da Performance por Categoria:')
    pdf.add_table(df_for_pdf)
    pdf_bytes_content = pdf.output(dest='S').encode('latin1')
    return pdf_bytes_content


# --- Streamlit UI ---

# Filtros movidos para o corpo principal, lado a lado
col1, col2 = st.columns(2)
with col1:
    selected_game = st.selectbox('Selecione o Jogo Atual:', all_games)
with col2:
    selected_player = st.selectbox('Selecione o Jogador:', all_players)


if selected_game and selected_player:
    # Obtém os dados de performance agregados por categoria
    performance_data_category = get_performance_data_by_category(selected_game, selected_player, df_categorized_counts_per_game, player_category_overall_averages)

    st.subheader(f'Performance de {selected_player} no jogo: {selected_game}')
    st.write('---')

    st.markdown('**Resumo Detalhado da Performance por Evento:**')
    
    color_green = "#28a745"
    color_red = "#dc3545"
    color_gray = "#6c757d"

    # Layout em duas colunas: Categoria à esquerda, Card de Performance à direita
    # O número de linhas será o número de categorias
    for index, row in performance_data_category.iterrows():
        col_cat_name, col_card = st.columns([0.4, 0.6]) # Proporção para a coluna da categoria e do card

        with col_cat_name:
            st.markdown(f"**<h5 style='color: #333; margin-top: 0; margin-bottom: 5px; font-weight: 600;'>{row['Category']}</h5>**", unsafe_allow_html=True)
            st.write("") # Pequeno espaço para alinhar

        with col_card:
            current_val = int(row['Atual'])
            avg_val = f"{row['Média']:.2f}"
            change_text = row['Mudança_UI'] # Usar a versão da UI com setas Unicode

            display_arrow = ""
            display_color = color_gray
            indicator_text = "Mantém"

            if 'Melhora (↑)' in change_text:
                display_arrow = "▲"
                display_color = color_green
                indicator_text = "Melhora"
            elif 'Piora (↓)' in change_text:
                display_arrow = "▼"
                display_color = color_red
                indicator_text = "Piora"
            else:
                display_arrow = "—"
                display_color = color_gray
                indicator_text = "Mantém"

            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e6e6e6;
                    border-radius: 8px;
                    padding: 10px;
                    margin-bottom: 10px;
                    background-color: #ffffff;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
                ">
                    <p style="font-size: 1.5em; font-weight: bold; color: #000; margin-bottom: 5px; margin-top: 0;">
                        {current_val} <small style="font-size: 0.45em; color: #777;">(Atual)</small>
                    </p>
                    <p style="font-size: 0.8em; color: #555; margin-bottom: 8px;">
                        Média: {avg_val}
                    </p>
                    <p style="font-size: 1.0em; font-weight: bold; color: {display_color};">
                        {display_arrow} {indicator_text}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    st.write('---') # Separador ao final dos cards

    # Botão para exportar PDF
    pdf_bytes = create_pdf_report(selected_player, selected_game, performance_data_category)
    st.download_button(
        label="📄 Exportar Relatório como PDF",
        data=pdf_bytes,
        file_name=f"Relatorio_Performance_{selected_player}_{selected_game.replace(' ', '_').replace(':', '').replace('/', '_')}.pdf",
        mime="application/pdf"
    )

else:
    st.info('Por favor, selecione um jogo e um jogador para visualizar a performance.')
