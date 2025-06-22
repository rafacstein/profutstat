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


st.title('📊 Dashboard de Análise de Performance')

# --- URLs dos Arquivos CSV no GitHub (RAW) ---
# CORRIGIDO: Usando as URLs RAW do GitHub
GITHUB_INDIVIDUAL_CSV_URL = 'https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/Monitoramento%20S%C3%A3o%20Bento%20U13%20-%20CONSOLIDADO%20INDIVIDUAL.csv'
GITHUB_COLLECTIVE_CSV_URL = 'https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/Monitoramento%20S%C3%A3o%20Bento%20U13%20-%20CONSOLIDADO%20COLETIVO.csv'


# --- Funções de Carregamento de Dados (Cacheado) ---

@st.cache_data
def load_individual_data(url): # Agora aceita URL
    df = pd.read_csv(url)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Evento descrição'] = df['Evento descrição'].str.strip()
    return df

@st.cache_data
def load_collective_data(url): # Agora aceita URL
    df = pd.read_csv(url)
    # O arquivo coletivo não tem 'Timestamp'. A coluna de evento é 'Evento'.
    if 'Timestamp' in df.columns: # Checa se 'Timestamp' existe antes de converter
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Evento'] = df['Evento'].str.strip() 
    return df

# --- Definição da Natureza de Cada Evento (Positiva/Negativa) ---
# Para Estatísticas Individuais (baseado no CSV individual)
EVENTO_NATUREZA_CONFIG_INDIVIDUAL = {
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
    'Perda de Posse': True, 
    'Falta Cometida': True,
    'Gol': False, 
    'Defesa Recuperação': False, 
    'Finalização Fora do Alvo': True, 
    'Defesa Corte': False, 
    'Defesa Desarme': False, 
    'Cruzamento Errado': True, 
    'Defesa Drible Sofrido': True, 
    'Duelo Aéreo Perdido': True, 
    'Finalização No Alvo': False, 
    'Defesa Interceptação': False, 
    'Duelo Aéreo Ganho': False, 
    'Defesa Goleiro': False, 
    'Passe Chave': False, 
}

# Para Estatísticas Coletivas (Baseado EXATAMENTE nos eventos do CSV coletivo)
EVENTO_NATUREZA_CONFIG_COLETIVA = {
    'Posse de bola': False, 
    'Gols': False, 
    'Chutes no gol': False, 
    'Chutes pra fora': True, 
    'Escanteios': False, 
    'Faltas': True, 
    'Cartões amarelos': True, 
    'Cartões vermelhos': True, 
    'Impedimentos': True, 
}


# --- Funções de Cálculo de Performance (Genérica para Individual) ---

def get_performance_data_individual(player_name, game_name, df_grouped_data, overall_averages_data):
    comparison_list = []
    epsilon = 0.01 

    for event_name, is_negative_event in EVENTO_NATUREZA_CONFIG_INDIVIDUAL.items():
        current_val_series = df_grouped_data[
            (df_grouped_data['Jogo'] == game_name) &
            (df_grouped_data['Player'] == player_name) &
            (df_grouped_data['Evento descrição'] == event_name) 
        ]['Count']
        current_val = current_val_series.iloc[0] if not current_val_series.empty else 0

        avg_val_series = overall_averages_data[
            (overall_averages_data['Player'] == player_name) &
            (overall_averages_data['Evento descrição'] == event_name) 
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


# --- Nova Função de Cálculo de Performance Coletiva (Compara Casa vs Fora) ---
def get_collective_performance_data(game_name, df_collective_raw_data):
    game_data = df_collective_raw_data[df_collective_raw_data['Jogo'] == game_name]
    
    comparison_list = []
    
    # CORRIGIDO: A coluna de evento no CSV coletivo é 'Evento', não 'Evento descrição'
    for event_name, is_negative_event in EVENTO_NATUREZA_CONFIG_COLETIVA.items():
        event_row = game_data[game_data['Evento'] == event_name]
        
        casa_val = event_row['Casa'].iloc[0] if not event_row.empty else 0
        fora_val = event_row['Fora'].iloc[0] if not event_row.empty else 0

        indicator_text = "Equilíbrio" 
        display_color = "#6c757d" 
        display_arrow = "=" 

        if is_negative_event: 
            if casa_val < fora_val:
                indicator_text = "Casa Melhor"
                display_color = "#28a745" 
                display_arrow = "↓" 
            elif casa_val > fora_val:
                indicator_text = "Fora Melhor"
                display_color = "#dc3545" 
                display_arrow = "↑" 
        else: 
            if casa_val > fora_val:
                indicator_text = "Casa Melhor"
                display_color = "#28a745" 
                display_arrow = "↑" 
            elif casa_val < fora_val:
                indicator_text = "Fora Melhor"
                display_color = "#dc3545" 
                display_arrow = "↓" 

        comparison_list.append({
            'Event_Name': event_name, 
            'Casa': casa_val,
            'Fora': fora_val,
            'Comparação': indicator_text, 
            'Arrow_UI': display_arrow,
            'Color_UI': display_color
        })
    return pd.DataFrame(comparison_list).sort_values(by='Event_Name').reset_index(drop=True)


# --- Geração de PDF (Genérica para Individual/Coletiva) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Performance', 0, 1, 'C') 
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
        headers = df_to_print.columns.tolist()
        
        if 'Média' in headers: 
            col_widths = [80, 30, 30, 30] 
        else: 
            col_widths = [60, 30, 30, 60] 

        self.set_font('Arial', 'B', 9)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, 1, 0, 'C')
        self.ln()
        self.set_font('Arial', '', 8)
        for index, row in df_to_print.iterrows():
            for i, item in enumerate(row):
                if headers[i] == 'Comparação':
                    item_str = str(item).replace('Casa Melhor', 'Casa').replace('Fora Melhor', 'Fora').replace('Equilíbrio', '=')
                else:
                    item_str = str(item)
                self.cell(col_widths[i], 6, item_str, 1, 0, 'C')
            self.ln()
        self.ln(5)

def create_pdf_report_generic(entity_type, entity_name, game_name, performance_data, is_collective=False):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f'{entity_type}: {entity_name}', 0, 1, 'L')
    pdf.cell(0, 10, f'Jogo: {game_name}', 0, 1, 'L')
    pdf.ln(5)

    if is_collective:
        df_for_pdf = performance_data[['Event_Name', 'Casa', 'Fora', 'Comparação']].copy()
        df_for_pdf.rename(columns={'Event_Name': 'Evento'}, inplace=True)
    else: # Individual
        df_for_pdf = performance_data[['Event_Name', 'Atual', 'Média', 'Mudança_PDF']].copy()
        df_for_pdf.rename(columns={'Event_Name': 'Evento', 'Mudança_PDF': 'Mudança'}, inplace=True)
        df_for_pdf['Média'] = df_for_pdf['Média'].apply(lambda x: f"{x:.2f}")
    
    pdf.chapter_title('Resumo da Performance por Evento:')
    pdf.add_table(df_for_pdf)
    pdf_bytes_content = pdf.output(dest='S').encode('latin1')
    return pdf_bytes_content


# --- Estrutura do Dashboard com Abas ---
tab_individual, tab_coletiva = st.tabs(["Estatísticas Individuais", "Estatísticas Coletivas"])

# --- TAB DE ESTATÍSTICAS INDIVIDUAIS ---
with tab_individual:
    st.header("Análise de Performance Individual")

    # Carrega dados individuais
    # CORRIGIDO: Usando URL RAW do GitHub
    df_individual = load_individual_data(GITHUB_INDIVIDUAL_CSV_URL)
    df_individual_grouped = df_individual.groupby(['Jogo', 'Player', 'Evento descrição'])['Count'].sum().reset_index()
    individual_overall_averages = df_individual_grouped.groupby(['Player', 'Evento descrição'])['Count'].mean().reset_index()
    individual_overall_averages.rename(columns={'Count': 'Média'}, inplace=True)

    all_individual_games = sorted(df_individual_grouped['Jogo'].unique().tolist())
    all_players = sorted(df_individual_grouped['Player'].unique().tolist())

    # Filtros individuais
    col_ind_game, col_ind_player = st.columns(2)
    with col_ind_game:
        selected_individual_game = st.selectbox('Jogo Atual (Individual):', all_individual_games)
    with col_ind_player:
        selected_player = st.selectbox('Jogador:', all_players)

    if selected_individual_game and selected_player:
        performance_data_individual = get_performance_data_individual(
            selected_player, selected_individual_game, df_individual_grouped, 
            individual_overall_averages
        )

        st.subheader(f'Performance de {selected_player} no jogo: {selected_individual_game}')
        st.write('---')

        st.markdown('**Resumo Detalhado da Performance por Evento:**')
        
        color_green = "#28a745"
        color_red = "#dc3545"
        color_gray = "#6c757d"

        for index, row in performance_data_individual.iterrows():
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

        pdf_bytes_individual = create_pdf_report_generic(
            "Jogador", selected_player, selected_individual_game, performance_data_individual, is_collective=False
        )
        st.download_button(
            label="📄 Exportar Relatório Individual como PDF",
            data=pdf_bytes_individual,
            file_name=f"Relatorio_Performance_Individual_{selected_player}_{selected_individual_game.replace(' ', '_').replace(':', '').replace('/', '_')}.pdf",
            mime="application/pdf"
        )

    else:
        st.info('Selecione um jogo e um jogador para ver a performance individual.')

# --- TAB DE ESTATÍSTICAS COLETIVAS ---
with tab_coletiva:
    st.header("Análise de Performance Coletiva")

    # Carrega dados coletivos
    # CORRIGIDO: Usando URL RAW do GitHub
    df_collective = load_collective_data(GITHUB_COLLECTIVE_CSV_URL)
    
    # NÃO HÁ GROUPBY POR TEAM OU MÉDIA AQUI - A ESTRUTURA É DIFERENTE
    # Apenas pegamos os jogos únicos para o filtro
    all_collective_games = sorted(df_collective['Jogo'].unique().tolist())
    
    # Filtro coletivo (apenas por Jogo)
    selected_collective_game = st.selectbox('Jogo Atual (Coletivo):', all_collective_games)

    if selected_collective_game:
        # Chama a nova função para dados coletivos
        performance_data_collective = get_collective_performance_data(
            selected_collective_game, df_collective
        )

        st.subheader(f'Performance no jogo: {selected_collective_game}')
        st.write('---')

        st.markdown('**Comparativo Casa vs Fora por Evento:**')
        
        # Cores já definidas acima
        color_green = "#28a745"
        color_red = "#dc3545"
        color_gray = "#6c757d"


        for index, row in performance_data_collective.iterrows():
            # A linha principal terá 4 colunas: Nome do Evento | Valor Casa | Valor Fora | Indicador
            col_name, col_casa_val, col_fora_val, col_indicator_collective = st.columns([0.25, 0.25, 0.25, 0.25]) 
            
            with col_name:
                st.markdown(f"<h5 style='color: #333; margin-top: 15px; margin-bottom: 0px; font-weight: 600;'>{row['Event_Name']}</h5>", unsafe_allow_html=True)

            with col_casa_val:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #e6e6e6;
                        border-radius: 8px;
                        padding: 8px;
                        background-color: #ffffff;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
                        height: 75px;
                        display: flex; flex-direction: column; justify-content: center; align-items: center;
                        margin-bottom: 10px;
                    ">
                        <p style="font-size: 1.2em; font-weight: bold; color: #000; margin-bottom: 3px; margin-top: 0;">
                            {int(row['Casa'])}
                        </p>
                        <p style="font-size: 0.7em; color: #777; margin-bottom: 0px; margin-top: 0;">
                            (Casa)
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col_fora_val:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #e6e6e6;
                        border-radius: 8px;
                        padding: 8px;
                        background-color: #ffffff;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
                        height: 75px;
                        display: flex; flex-direction: column; justify-content: center; align-items: center;
                        margin-bottom: 10px;
                    ">
                        <p style="font-size: 1.2em; font-weight: bold; color: #000; margin-bottom: 3px; margin-top: 0;">
                            {int(row['Fora'])}
                        </p>
                        <p style="font-size: 0.7em; color: #777; margin-bottom: 0px; margin-top: 0;">
                            (Fora)
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_indicator_collective:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid {row['Color_UI']};
                        border-radius: 8px;
                        padding: 5px;
                        background-color: {row['Color_UI']}20;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
                        height: 75px;
                        display: flex; flex-direction: column; justify-content: center; align-items: center;
                        text-align: center;
                        margin-bottom: 10px;
                    ">
                        <p style="font-size: 1.5em; font-weight: bold; color: {row['Color_UI']}; margin-bottom: 0; margin-top: 0;">
                            {row['Arrow_UI']}
                        </p>
                        <p style="font-size: 0.7em; font-weight: bold; color: {row['Color_UI']}; margin-bottom: 0; margin-top: 0;">
                            {row['Comparação'].split(' ')[0]}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.write('---') 

        pdf_bytes_collective = create_pdf_report_generic(
            "Jogo", selected_collective_game, "", performance_data_collective, is_collective=True
        )
        st.download_button(
            label="📄 Exportar Relatório Coletivo como PDF",
            data=pdf_bytes_collective,
            file_name=f"Relatorio_Performance_Coletiva_{selected_collective_game.replace(' ', '_').replace(':', '').replace('/', '_')}.pdf",
            mime="application/pdf"
        )

    else:
        st.info('Selecione um jogo para ver a performance coletiva.')
