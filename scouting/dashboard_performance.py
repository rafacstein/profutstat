import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from itertools import product # Importado para ajudar na criação de combinações

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
GITHUB_INDIVIDUAL_CSV_URL = 'https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/Monitoramento%20S%C3%A3o%20Bento%20U13%20-%20CONSOLIDADO%20INDIVIDUAL.csv'
GITHUB_COLLECTIVE_CSV_URL = 'https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/Monitoramento%20S%C3%A3o%20Bento%20U13%20-%20CONSOLIDADO%20COLETIVO.csv'

# --- URLs das Imagens dos Escudos ---
PROFUTSTAT_LOGO_URL = "https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/profutstat_logo.png"
SAO_BENTO_LOGO_URL = "https://raw.githubusercontent.com/rafacstein/profutstat/main/scouting/ec_sao_bento.png"


# --- Funções de Carregamento de Dados ---
@st.cache_data
def load_individual_data(url):
    df = pd.read_csv(url)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Evento descrição'] = df['Evento descrição'].str.strip()
    return df

@st.cache_data
def load_collective_data(url):
    df = pd.read_csv(url)
    if 'Timestamp' in df.columns: 
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Evento'] = df['Evento'].str.strip() 
    return df

# --- Definição da Natureza de Cada Evento (Positiva/Negativa) ---
# Para Estatísticas Individuais (baseado no CSV individual e inspecionado)
EVENTO_NATUREZA_CONFIG_INDIVIDUAL = {
    'Passe Certo Curto': False,
    'Passe Certo Longo': False,
    'Passe Errado Curto': True,
    'Passe Errado Longo': True,
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

# Para Estatísticas Coletivas (Baseado EXATAMENTE nos eventos do CSV coletivo e INCLUINDO NOVOS)
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
    'Desarmes': False,         
    'Interceptações': False,   
    'Passes Certos': False,    
    'Passes Errados': True,    
}

# --- ORDEM DE EXIBIÇÃO PERSONALIZADA PARA ESTATÍSTICAS INDIVIDUAIS ---
INDIVIDUAL_EVENT_DISPLAY_ORDER = [
    # Finalizações
    'Gol',
    'Finalização No Alvo',
    'Finalização Fora do Alvo',
    # Passes
    'Passe Certo Curto',
    'Passe Certo Longo',
    'Passe Errado',
    'Passe Errado Curto',
    'Passe Errado Longo',
    'Passe Chave',
    'Cruzamento Errado',
    # Dribles
    'Drible Certo',
    'Drible Errado',
    'Drible',
    # Ações de Defesa (exceto Duelos Aéreos)
    'Defesa Goleiro',
    'Defesa Recuperação',
    'Defesa Corte',
    'Defesa Desarme',
    'Defesa Interceptação',
    'Roubada de Bola',
    'Defesa Drible Sofrido', 
    'Perda de Posse',
    'Falta Sofrida',
    'Falta Cometida',
    # Duelos Aéreos (AGORA NO FINAL DA LISTA)
    'Duelo Aéreo Ganho',
    'Duelo Aéreo Perdido',
]

# --- Função de Pré-processamento CORRIGIDA para Médias Individuais ---
@st.cache_data
def preprocess_individual_data_for_averages(df_raw_individual):
    df_raw_individual['Evento descrição'] = df_raw_individual['Evento descrição'].str.strip()

    all_players = df_raw_individual['Player'].unique().tolist()
    all_games_individual = df_raw_individual['Jogo'].unique().tolist()
    all_event_descriptions = df_raw_individual['Evento descrição'].unique().tolist()
    
    actual_player_game_pairs = df_raw_individual[['Player', 'Jogo']].drop_duplicates()
    
    all_relevant_combinations = pd.DataFrame(list(product(
        actual_player_game_pairs['Player'].unique(), 
        actual_player_game_pairs['Jogo'].unique(),   
        all_event_descriptions
    )), columns=['Player', 'Jogo', 'Evento descrição'])
    
    all_relevant_combinations = pd.merge(
        all_relevant_combinations, 
        actual_player_game_pairs, 
        on=['Player', 'Jogo'], 
        how='inner'
    )

    df_grouped_per_event_per_game = df_raw_individual.groupby(
        ['Jogo', 'Player', 'Evento descrição']
    )['Count'].sum().reset_index()

    df_full_individual_counts = pd.merge(
        all_relevant_combinations, 
        df_grouped_per_event_per_game, 
        on=['Jogo', 'Player', 'Evento descrição'], 
        how='left'
    )
    df_full_individual_counts['Count'].fillna(0, inplace=True)

    player_overall_averages_corrected = df_full_individual_counts.groupby(['Player', 'Evento descrição'])['Count'].mean().reset_index()
    player_overall_averages_corrected.rename(columns={'Count': 'Média'}, inplace=True)
    
    return df_grouped_per_event_per_game, player_overall_averages_corrected


# --- Função de Pré-processamento para Médias Coletivas (EC São Bento - COLUNA CASA) ---
@st.cache_data
def preprocess_collective_data_for_averages(df_collective_raw):
    df_collective_raw['Evento'] = df_collective_raw['Evento'].str.strip()
    
    # A média é calculada APENAS sobre a coluna 'Casa', assumindo que é sempre o EC São Bento.
    collective_overall_averages_corrected = df_collective_raw.groupby('Evento')['Casa'].mean().reset_index()
    collective_overall_averages_corrected.rename(columns={'Casa': 'Média'}, inplace=True)
    
    return collective_overall_averages_corrected


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
    
    df_performance = pd.DataFrame(comparison_list)
    
    all_possible_events_in_order = [e for e in INDIVIDUAL_EVENT_DISPLAY_ORDER if e in df_performance['Event_Name'].unique()]
    df_performance['Event_Name'] = pd.Categorical(
        df_performance['Event_Name'], 
        categories=all_possible_events_in_order, 
        ordered=True
    )
    df_performance = df_performance.sort_values('Event_Name').reset_index(drop=True)
    
    return df_performance


# --- Nova Função de Cálculo de Performance Coletiva (Compara com a Média da Coluna Casa) ---
def get_collective_performance_data(game_name, df_collective_raw_data, collective_overall_averages):
    game_data = df_collective_raw_data[df_collective_raw_data['Jogo'] == game_name]
    
    comparison_list = []
    
    epsilon = 0.01

    for event_name, is_negative_event in EVENTO_NATUREZA_CONFIG_COLETIVA.items():
        current_val_casa_series = game_data[game_data['Evento'] == event_name]['Casa']
        current_val_casa = current_val_casa_series.iloc[0] if not current_val_casa_series.empty else 0

        avg_val_casa_series = collective_overall_averages[collective_overall_averages['Evento'] == event_name]['Média']
        avg_val_casa = avg_val_casa_series.iloc[0] if not avg_val_casa_series.empty else 0


        indicator_text = "Mantém" 
        display_color = "#6c757d" 
        display_arrow = "" # Seta removida para análise coletiva

        if abs(current_val_casa - avg_val_casa) < epsilon: 
            indicator_text = "Mantém"
            display_color = "#6c757d" 
        elif is_negative_event: 
            if current_val_casa < avg_val_casa:
                indicator_text = "Melhor"
                display_color = "#28a745" 
            else: 
                indicator_text = "Pior"
                display_color = "#dc3545" 
        else: 
            if current_val_casa > avg_val_casa:
                indicator_text = "Melhor"
                display_color = "#28a745" 
            elif current_val_casa < avg_val_casa:
                indicator_text = "Pior"
                display_color = "#dc3545" 
        
        comparison_list.append({
            'Event_Name': event_name, 
            'Atual': current_val_casa, 
            'Média': avg_val_casa, 
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
        df_for_pdf = performance_data[['Event_Name', 'Atual', 'Média', 'Comparação']].copy()
        df_for_pdf.rename(columns={'Event_Name': 'Evento', 'Atual': 'Atual (Casa)', 'Média': 'Média (Casa)', 'Comparação': 'Status'}, inplace=True)
        df_for_pdf['Média'] = df_for_pdf['Média'].apply(lambda x: f"{x:.2f}")
    else: # Individual
        df_for_pdf = performance_data[['Event_Name', 'Atual', 'Média', 'Mudança_PDF']].copy()
        df_for_pdf.rename(columns={'Event_Name': 'Evento', 'Mudança_PDF': 'Mudança'}, inplace=True)
        df_for_pdf['Média'] = df_for_pdf['Média'].apply(lambda x: f"{x:.2f}")
    
    pdf.chapter_title('Resumo da Performance por Evento:')
    pdf.add_table(df_for_pdf)
    pdf_bytes_content = pdf.output(dest='S').encode('latin1')
    return pdf_bytes_content


# --- Estrutura do Dashboard com Abas ---
# Adiciona os escudos no topo do dashboard
col_logo1, col_title_main, col_logo2 = st.columns([0.15, 0.7, 0.15])

with col_logo1:
    st.image(PROFUTSTAT_LOGO_URL, width=80) 
with col_title_main:
    st.markdown("<h1 style='text-align: center; color: #333; font-size: 2em;'>📊 Dashboard de Análise de Performance</h1>", unsafe_allow_html=True)
with col_logo2:
    st.image(SAO_BENTO_LOGO_URL, width=80) 

st.write("---") 


tab_individual, tab_coletiva = st.tabs(["Estatísticas Individuais", "Estatísticas Coletivas"])

# --- TAB DE ESTATÍSTICAS INDIVIDUAIS ---
with tab_individual:
    st.header("Análise de Performance Individual")

    # Carrega dados individuais (e faz o pré-processamento para médias corrigidas)
    df_individual_raw = load_individual_data(GITHUB_INDIVIDUAL_CSV_URL)
    df_grouped_per_event_per_game_individual, player_overall_averages_corrected = preprocess_individual_data_for_averages(df_individual_raw)

    # Usamos os dados do preprocessamento para popular os selectboxes
    all_individual_games = sorted(df_grouped_per_event_per_game_individual['Jogo'].unique().tolist())
    all_players = sorted(df_grouped_per_event_per_game_individual['Player'].unique().tolist())

    # Filtros individuais
    col_ind_game, col_ind_player = st.columns(2)
    with col_ind_game:
        selected_individual_game = st.selectbox('Jogo Atual (Individual):', all_individual_games)
    with col_ind_player:
        selected_player = st.selectbox('Jogador:', all_players)

    if selected_individual_game and selected_player:
        performance_data_individual = get_performance_data_individual(
            selected_player, selected_individual_game, 
            df_grouped_per_event_per_game_individual, player_overall_averages_corrected # Passa os DFs processados
        )

        st.subheader(f'Performance de {selected_player} no jogo: {selected_individual_game}')
        st.write('---')

        st.markdown('**Resumo Detalhado da Performance por Evento:**')
        
        color_green = "#28a745"
        color_red = "#dc3545"
        color_gray = "#6c757d"

        # Função para obter o nome do evento para exibição no card
        def get_display_event_name(original_event_name):
            if original_event_name == 'Defesa Goleiro':
                return original_event_name
            elif original_event_name.startswith('Defesa '):
                return original_event_name.replace('Defesa ', '')
            return original_event_name


        for index, row in performance_data_individual.iterrows():
            col_name, col_value_card, col_indicator_card = st.columns([0.4, 0.4, 0.2])

            with col_name:
                st.markdown(f"<h5 style='color: #333; margin-top: 15px; margin-bottom: 0px; font-weight: 600;'>{get_display_event_name(row['Event_Name'])}</h5>", unsafe_allow_html=True)

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

    # Carrega dados coletivos e faz o pré-processamento para médias corrigidas da coluna 'Casa'
    df_collective_raw = load_collective_data(GITHUB_COLLECTIVE_CSV_URL) 
    collective_overall_averages_corrected = preprocess_collective_data_for_averages(df_collective_raw)
    
    all_collective_games = sorted(df_collective_raw['Jogo'].unique().tolist()) # Usa os jogos do DF raw
    
    selected_collective_game = st.selectbox('Jogo Atual (Coletivo):', all_collective_games)

    if selected_collective_game:
        performance_data_collective = get_collective_performance_data(
            selected_collective_game, df_collective_raw, collective_overall_averages_corrected
        )

        # O subheader agora é fixo para "EC São Bento" como time da casa
        st.subheader(f'Performance do EC São Bento no jogo: {selected_collective_game}')
        st.write('---')

        st.markdown('**Comparativo de Performance por Evento (EC São Bento vs. Média):**') # Título ajustado
        
        color_green = "#28a745"
        color_red = "#dc3545"
        color_gray = "#6c757d"

        # Reutiliza a função get_display_event_name
        
        for index, row in performance_data_collective.iterrows():
            # Layout com 3 colunas: Nome do Evento | Valor Atual (Casa) | Indicador
            col_name, col_value_card, col_indicator_collective = st.columns([0.4, 0.4, 0.2]) 
            
            with col_name:
                st.markdown(f"<h5 style='color: #333; margin-top: 15px; margin-bottom: 0px; font-weight: 600;'>{get_display_event_name(row['Event_Name'])}</h5>", unsafe_allow_html=True)

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
                            {int(row['Atual'])} <small style="font-size: 0.4em; color: #777;">(Atual)</small>
                        </p>
                        <p style="font-size: 0.7em; color: #555; margin-bottom: 0px; margin-top: 0;">
                            Média: {row['Média']:.2f} <small style="font-size: 0.4em; color: #777;">(Casa)</small>
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
            "Time", "EC São Bento", selected_collective_game, performance_data_collective, is_collective=True 
        )
        st.download_button(
            label="📄 Exportar Relatório Coletivo como PDF",
            data=pdf_bytes_collective,
            file_name=f"Relatorio_Performance_Coletiva_EC_Sao_Bento_{selected_collective_game.replace(' ', '_').replace(':', '').replace('/', '_')}.pdf",
            mime="application/pdf"
        )

    else:
        st.info('Selecione um jogo para ver a performance coletiva do EC São Bento.')
