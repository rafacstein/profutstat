import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from itertools import product 

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
    df['Casa'] = pd.to_numeric(df['Casa'], errors='coerce')
    df['Fora'] = pd.to_numeric(df['Fora'], errors='coerce')
    return df

# --- Definição da Natureza de Cada Evento (Positiva/Negativa) ---
EVENTO_NATUREZA_CONFIG_INDIVIDUAL = {
    'Passe Certo Curto': False, 'Passe Certo Longo': False, 'Passe Errado Curto': True, 
    'Passe Errado Longo': True, 'Passe Errado': True, 'Falta Sofrida': False,
    'Drible Certo': False, 'Drible Errado': True, 'Drible': False, 
    'Roubada de Bola': False, 'Perda de Posse': True, 'Falta Cometida': True,
    'Gol': False, 'Defesa Recuperação': False, 'Finalização Fora do Alvo': True, 
    'Defesa Corte': False, 'Defesa Desarme': False, 'Cruzamento Errado': True, 
    'Defesa Drible Sofrido': True, 'Duelo Aéreo Perdido': True, 
    'Finalização No Alvo': False, 'Defesa Interceptação': False, 
    'Duelo Aéreo Ganho': False, 'Defesa Goleiro': False, 'Passe Chave': False, 
}

# PARA COLETIVO: AGORA SEM IS_NEGATIVE POIS NÃO HÁ COMPARAÇÃO DE MÉDIA
EVENTO_LISTA_COLETIVA = [
    'Posse de bola', 'Gols', 'Chutes no gol', 'Chutes pra fora', 
    'Escanteios', 'Faltas', 'Cartões amarelos', 'Cartões vermelhos', 
    'Impedimentos', 'Desarmes', 'Interceptações', 'Passes Certos',    
    'Passes Errados', '% de Posse de bola', 
]

# --- ORDEM DE EXIBIÇÃO PERSONALIZADA PARA ESTATÍSTICAS INDIVIDUAIS ---
INDIVIDUAL_EVENT_DISPLAY_ORDER = [
    'Gol', 'Finalização No Alvo', 'Finalização Fora do Alvo',
    'Passe Certo Curto', 'Passe Certo Longo', 'Passe Errado', 'Passe Errado Curto', 
    'Passe Errado Longo', 'Passe Chave', 'Cruzamento Errado',
    'Drible Certo', 'Drible Errado', 'Drible',
    'Defesa Goleiro', 'Defesa Recuperação', 'Defesa Corte', 'Defesa Desarme', 
    'Defesa Interceptação', 'Roubada de Bola', 'Defesa Drible Sofrido', 
    'Perda de Posse', 'Falta Sofrida', 'Falta Cometida',
    'Duelo Aéreo Ganho', 'Duelo Aéreo Perdido',
]

# --- Função de Pré-processamento para Médias Individuais ---
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

# REMOVIDO: Função de pré-processamento para média coletiva não é mais necessária
# @st.cache_data
# def preprocess_collective_data_for_averages(df_collective_raw):
#     df_collective_raw['Evento'] = df_collective_raw['Evento'].str.strip()
#     collective_overall_averages_corrected = df_collective_raw.groupby('Evento')['Casa'].mean(numeric_only=True).reset_index()
#     collective_overall_averages_corrected.rename(columns={'Casa': 'Média'}, inplace=True)
#     return collective_overall_averages_corrected


# --- Funções de Cálculo de Performance ---

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


# --- Função para Obter Nome de Exibição de Eventos (reutilizada para Individual e Coletivo) ---
def get_display_event_name(original_event_name):
    if original_event_name == 'Defesa Goleiro':
        return original_event_name
    elif original_event_name.startswith('Defesa '):
        return original_event_name.replace('Defesa ', '')
    return original_event_name


# --- Nova Função de Cálculo de Performance Coletiva (APENAS VALORES CASA E FORA) ---
# A média e indicadores complexos foram removidos.
def get_collective_performance_data(game_name, df_collective_raw_data):
    game_data = df_collective_raw_data[df_collective_raw_data['Jogo'] == game_name]
    
    comparison_list = []
    
    # NÃO HÁ EPSILON AQUI, POIS NÃO HÁ COMPARAÇÃO OU INDICADOR DE SETA
    for event_name in EVENTO_LISTA_COLETIVA: # Itera pela nova lista de eventos coletivos
        event_row = game_data[game_data['Evento'] == event_name]
        
        # Obter valores de Casa e Fora, tratando NaN para int
        casa_val = event_row['Casa'].iloc[0] if not event_row.empty and pd.notnull(event_row['Casa'].iloc[0]) else 0
        fora_val = event_row['Fora'].iloc[0] if not event_row.empty and pd.notnull(event_row['Fora'].iloc[0]) else 0

        comparison_list.append({
            'Event_Name': event_name, 
            'Casa': casa_val, 
            'Fora': fora_val, 
        })
    
    # Garante que as colunas essenciais existam
    df_result = pd.DataFrame(comparison_list).sort_values(by='Event_Name').reset_index(drop=True)
    required_cols = ['Event_Name', 'Casa', 'Fora']
    for col in required_cols:
        if col not in df_result.columns:
            df_result[col] = 0.0 if col in ['Casa', 'Fora'] else ''
    
    return df_result


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
        
        # Ajusta larguras de coluna para o PDF
        if 'Média' in headers and 'Atual' in headers: # Individual
            col_widths = [80, 30, 30, 30] # Evento, Atual, Média, Mudança
        elif 'Casa' in headers and 'Fora' in headers: # Coletivo (Evento, Casa, Fora)
            col_widths = [80, 45, 45] # Ajustado para 3 colunas
        else: # Fallback
            col_widths = [80] * len(headers) 

        self.set_font('Arial', 'B', 9)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, 1, 0, 'C')
        self.ln()
        self.set_font('Arial', '', 8)
        for index, row in df_to_print.iterrows():
            for i, header in enumerate(headers): 
                item = row[header] 
                item_str = str(item)

                if header == 'Mudança': # Individual
                    item_str = str(item).replace('↑', '(UP)').replace('↓', '(DOWN)').replace('—', '(-)')
                elif header in ['Atual', 'Média', 'Casa', 'Fora']: # Numéricos
                    try:
                        # Verifica se a coluna 'Evento' (o nome original Event_Name) é '% de Posse de bola'
                        if 'Evento' in row.index and row['Evento'] == '% de Posse de bola' and header in ['Atual', 'Média', 'Casa', 'Fora']: # Apply to Actual, Casa, Fora for %
                            item_str = f"{float(item):.2f}%" 
                        elif header == 'Média':
                            item_str = f"{float(item):.2f}"
                        else: # Outros numéricos inteiros
                            item_str = str(int(float(item))) 
                    except ValueError:
                        item_str = str(item) # Caso seja NaN ou outro não-numérico
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
        df_for_pdf = performance_data[['Event_Name', 'Casa', 'Fora']].copy() # Apenas estas colunas para PDF coletivo
        df_for_pdf.rename(columns={'Event_Name': 'Evento', 'Casa': 'Casa', 'Fora': 'Fora'}, inplace=True)
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

    df_individual_raw = load_individual_data(GITHUB_INDIVIDUAL_CSV_URL)
    df_grouped_per_event_per_game_individual, player_overall_averages_corrected = preprocess_individual_data_for_averages(df_individual_raw)

    all_individual_games = sorted(df_grouped_per_event_per_game_individual['Jogo'].unique().tolist())
    all_players = sorted(df_grouped_per_event_per_game_individual['Player'].unique().tolist())

    col_ind_game, col_ind_player = st.columns(2)
    with col_ind_game:
        selected_individual_game = st.selectbox('Jogo Atual (Individual):', all_individual_games)
    with col_ind_player:
        selected_player = st.selectbox('Jogador:', all_players)

    if selected_individual_game and selected_player:
        performance_data_individual = get_performance_data_individual(
            selected_player, selected_individual_game, 
            df_grouped_per_event_per_game_individual, player_overall_averages_corrected 
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

            current_val = int(row['Atual']) if pd.notnull(row['Atual']) else 0
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
                    f"""<div style="border: 1px solid #e6e6e6; border-radius: 8px; padding: 8px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.03); height: 75px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px;">
                        <p style="font-size: 1.2em; font-weight: bold; color: #000; margin-bottom: 3px; margin-top: 0;">{current_val} <small style="font-size: 0.4em; color: #777;">(Atual)</small></p>
                        <p style="font-size: 0.7em; color: #555; margin-bottom: 0px; margin-top: 0;">Média: {avg_val}</p>
                    </div>""",
                    unsafe_allow_html=True
                )

            with col_indicator_card:
                st.markdown(
                    f"""<div style="border: 1px solid {display_color}; border-radius: 8px; padding: 5px; background-color: {display_color}20; box-shadow: 0 2px 4px rgba(0,0,0,0.03); height: 75px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; margin-bottom: 10px;">
                        <p style="font-size: 1.5em; font-weight: bold; color: {display_color}; margin-bottom: 0; margin-top: 0;">{display_arrow}</p>
                        <p style="font-size: 0.7em; font-weight: bold; color: {display_color}; margin-bottom: 0; margin-top: 0;">{indicator_text}</p>
                    </div>""",
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

    df_collective_raw = load_collective_data(GITHUB_COLLECTIVE_CSV_URL) 
    collective_overall_averages_corrected = preprocess_collective_data_for_averages(df_collective_raw)
    
    all_collective_games = sorted(df_collective_raw['Jogo'].unique().tolist()) 
    
    selected_collective_game = st.selectbox('Jogo Atual (Coletivo):', all_collective_games)

    if selected_collective_game:
        performance_data_collective = get_collective_performance_data(
            selected_collective_game, df_collective_raw, collective_overall_averages_corrected
        )

        st.subheader(f'Performance do EC São Bento no jogo: {selected_collective_game}')
        st.write('---')

        st.markdown('**Comparativo de Performance por Evento (EC São Bento vs. Média, e Time de Fora):**') 
        
        color_green = "#28a745"
        color_red = "#dc3545"
        color_gray = "#6c757d"

        def get_display_event_name(original_event_name):
            if original_event_name == 'Defesa Goleiro':
                return original_event_name
            elif original_event_name.startswith('Defesa '):
                return original_event_name.replace('Defesa ', '')
            return original_event_name


        for index, row in performance_data_collective.iterrows():
            # Layout com 3 colunas para o coletivo: Nome do Evento | Valor Casa | Valor Fora
            col_name, col_casa_val, col_fora_val = st.columns([0.33, 0.33, 0.34]) # Removida coluna de indicador
            
            with col_name:
                st.markdown(f"<h5 style='color: #333; margin-top: 15px; margin-bottom: 0px; font-weight: 600;'>{get_display_event_name(row['Event_Name'])}</h5>", unsafe_allow_html=True)

            with col_casa_val:
                st.markdown(
                    f"""<div style="border: 1px solid #e6e6e6; border-radius: 8px; padding: 8px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.03); height: 75px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px;">
                        <p style="font-size: 1.2em; font-weight: bold; color: #000; margin-bottom: 3px; margin-top: 0;">{int(row['Atual']) if pd.notnull(row['Atual']) else 0} <small style="font-size: 0.4em; color: #777;">(Casa)</small></p>
                    </div>""",
                    unsafe_allow_html=True
                )
            
            with col_fora_val: 
                st.markdown(
                    f"""<div style="border: 1px solid #e6e6e6; border-radius: 8px; padding: 8px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.03); height: 75px; display: flex; flex-direction: column; justify-content: center; align-items: center; margin-bottom: 10px;">
                        <p style="font-size: 1.2em; font-weight: bold; color: #000; margin-bottom: 3px; margin-top: 0;">{int(row['Fora']) if pd.notnull(row['Fora']) else 0}</p>
                        <p style="font-size: 0.7em; color: #777; margin-bottom: 0px; margin-top: 0;">(Fora)</p>
                    </div>""",
                    unsafe_allow_html=True
                )
            # A coluna do indicador coletivo foi REMOVIDA AQUI
            # with col_indicator_collective: 
            #    st.markdown(...)

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
