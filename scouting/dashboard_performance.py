import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(layout="centered", page_title="Dashboard de Performance")

# --- Inserção de CSS para a Fonte ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Roboto', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Roboto', sans-serif;
        font-weight: 500;
    }
    
    div[data-testid="stMarkdownContainer"] h5,
    div[data-testid="stMarkdownContainer"] p {
        font-family: 'Roboto', sans-serif;
    }

    .st-emotion-cache-1g8fg5q { 
        gap: 0.5rem; 
    }
    </style>
""", unsafe_allow_html=True)


st.title('📊 Comparativo de Performance do Atleta')

# --- Carregamento de Dados ---
GITHUB_CSV_URL = 'https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/Monitoramento%20S%C3%A3o%20Bento%20U13%20-%20CONSOLIDADO%20INDIVIDUAL.csv'

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

df = load_data(GITHUB_CSV_URL)

# --- Pré-processamento de Dados (agregado apenas por Jogo, Player, Evento) ---
df_grouped = df.groupby(['Jogo', 'Player', 'Evento'])['Count'].sum().reset_index()

all_games = sorted(df_grouped['Jogo'].unique().tolist())
all_players = sorted(df_grouped['Player'].unique().tolist())

# --- Definição da Natureza de Cada Evento (Positiva/Negativa) ---
# AGORA INCLUI 'GOL'
EVENTO_NATUREZA_CONFIG = {
    'Passe Certo Curto': False,
    'Passe Certo Longo': False,
    'Passe Errado Curto': True,
    'Passe Errado Longo': True,
    'Chute Certo': False,
    'Chute Errado': True,
    'Passe Errado': True,
    'Falta Sofrida': False,
    'Drible Certo': False,
    'Drible Errado': True,
    'Drible': False,
    'Roubada de Bola': False,
    'Perda da Bola': True,
    'Falta Cometida': True,
    'Recepcao Errada': True,
    'Gol': False, # <--- GOL ADICIONADO AQUI
}

# --- Pré-cálculo das Médias Globais por Evento e Jogador ---
player_overall_averages = df_grouped.groupby(['Player', 'Evento'])['Count'].mean().reset_index()
player_overall_averages.rename(columns={'Count': 'Média'}, inplace=True)


# --- Função para Obter Dados de Performance por Evento ---
def get_performance_data_by_event(current_game, player_name, df_grouped_data, player_avg_event_data):
    comparison_list = []
    
    epsilon = 0.01 # Tolerância para comparação de ponto flutuante

    for event_name, is_negative_event in EVENTO_NATUREZA_CONFIG.items():
        current_val_series = df_grouped_data[
            (df_grouped_data['Jogo'] == current_game) &
            (df_grouped_data['Player'] == player_name) &
            (df_grouped_data['Evento'] == event_name)
        ]['Count']
        current_val = current_val_series.iloc[0] if not current_val_series.empty else 0

        avg_val_series = player_avg_event_data[
            (player_avg_event_data['Player'] == player_name) &
            (player_avg_event_data['Evento'] == event_name)
        ]['Média']
        avg_val = avg_val_series.iloc[0] if not avg_val_series.empty else 0

        indicator_text_raw = "Mantém (—)" 
        indicator_text_pdf = "Mantém (-)" 

        if abs(current_val - avg_val) < epsilon: 
            indicator_text_raw = "Mantém (—)"
            indicator_text_pdf = "Mantém (-)"
        elif is_negative_event:
            if current_val < avg_val:
                indicator_text_raw = "Melhora (↓)" 
                indicator_text_pdf = "Melhora (DOWN)"
            else: 
                indicator_text_raw = "Piora (↑)" 
                indicator_text_pdf = "Piora (UP)"
        else:
            if current_val > avg_val:
                indicator_text_raw = "Melhora (↑)"
                indicator_text_pdf = "Melhora (UP)"
            else: 
                indicator_text_raw = "Piora (↓)"
                indicator_text_pdf = "Piora (DOWN)"

        comparison_list.append({
            'Event_Name': event_name, 
            'Atual': current_val,
            'Média': avg_val,
            'Mudança_UI': indicator_text_raw,
            'Mudança_PDF': indicator_text_pdf
        })
    return pd.DataFrame(comparison_list).sort_values(by='Event_Name').reset_index(drop=True)


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

def create_pdf_report(player_name, game_name, performance_data_event):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f'Jogador: {player_name}', 0, 1, 'L')
    pdf.cell(0, 10, f'Jogo: {game_name}', 0, 1, 'L')
    pdf.ln(5)

    df_for_pdf = performance_data_event[['Event_Name', 'Atual', 'Média', 'Mudança_PDF']].copy()
    df_for_pdf.rename(columns={'Event_Name': 'Evento', 'Mudança_PDF': 'Mudança'}, inplace=True)
    df_for_pdf['Média'] = df_for_pdf['Média'].apply(lambda x: f"{x:.2f}")
    
    pdf.chapter_title('Resumo da Performance por Evento:')
    pdf.add_table(df_for_pdf)
    pdf_bytes_content = pdf.output(dest='S').encode('latin1')
    return pdf_bytes_content


# --- Streamlit UI ---

# Filtros no corpo principal
col1, col2 = st.columns(2)
with col1:
    selected_game = st.selectbox('Selecione o Jogo Atual:', all_games)
with col2:
    selected_player = st.selectbox('Selecione o Jogador:', all_players)


if selected_game and selected_player:
    performance_data_event = get_performance_data_by_event(selected_game, selected_player, df_grouped, player_overall_averages)

    st.subheader(f'Performance de {selected_player} no jogo: {selected_game}')
    st.write('---')

    st.markdown('**Resumo Detalhado da Performance por Evento:**')
    
    color_green = "#28a745"
    color_red = "#dc3545"
    color_gray = "#6c757d"

    for index, row in performance_data_event.iterrows():
        col_name, col_value_card, col_indicator_card = st.columns([0.4, 0.4, 0.2])

        with col_name:
            st.markdown(f"<h5 style='color: #333; margin-top: 15px; margin-bottom: 0px; font-weight: 600;'>{row['Event_Name']}</h5>", unsafe_allow_html=True)

        current_val = int(row['Atual'])
        avg_val = f"{row['Média']:.2f}"
        change_text_ui = row['Mudança_UI']

        display_arrow = ""
        display_color = color_gray
        indicator_text = "Mantém"

        if 'Melhora (↑)' in change_text_ui:
            display_arrow = "▲"
            display_color = color_green
            indicator_text = "Melhora"
        elif 'Piora (↓)' in change_text_ui:
            display_arrow = "▼"
            display_color = color_red
            indicator_text = "Piora"
        else:
            display_arrow = "—"
            display_color = color_gray
            indicator_text = "Mantém"

        with col_value_card:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e6e6e6;
                    border-radius: 8px;
                    padding: 8px;
                    background-color: #ffffff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
                    height: 75px;
                    display: flex; flex-direction: column; justify-content: center;
                    margin-bottom: 10px;
                ">
                    <p style="font-size: 1.2em; font-weight: bold; color: #000; margin-bottom: 3px; margin-top: 0;">
                        {current_val} <small style="font-size: 0.4em; color: #777;">(Atual)</small>
                    </p>
                    <p style="font-size: 0.7em; color: #555; margin-bottom: 0px; margin-top: 0;">
                        Média: {avg_val}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_indicator_card:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid {display_color};
                    border-radius: 8px;
                    padding: 5px;
                    background-color: {display_color}20;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
                    height: 75px;
                    display: flex; flex-direction: column; justify-content: center; align-items: center;
                    text-align: center;
                    margin-bottom: 10px;
                ">
                    <p style="font-size: 1.5em; font-weight: bold; color: {display_color}; margin-bottom: 0; margin-top: 0;">
                        {display_arrow}
                    </p>
                    <p style="font-size: 0.7em; font-weight: bold; color: {display_color}; margin-bottom: 0; margin-top: 0;">
                        {indicator_text}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write('---') 

    pdf_bytes = create_pdf_report(selected_player, selected_game, performance_data_event)
    st.download_button(
        label="📄 Exportar Relatório como PDF",
        data=pdf_bytes,
        file_name=f"Relatorio_Performance_{selected_player}_{selected_game.replace(' ', '_').replace(':', '').replace('/', '_')}.pdf",
        mime="application/pdf"
    )

else:
    st.info('Por favor, selecione um jogo e um jogador para visualizar a performance.')
