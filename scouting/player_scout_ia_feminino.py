import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, Normalizer
import faiss
import streamlit as st
from fuzzywuzzy import fuzz
import io
import plotly.express as px # Importar Plotly Express

# --- Multilingual Text Strings ---

# Portuguese
TEXT_PT = {
    "page_title": "PlayerScout IA - Futebol Feminino",
    "header_title": "PlayerScout IA",
    "welcome_message": "Bem-vindo à ferramenta **PlayerScout IA da ProFutStat**! Utilize nossos algoritmos de similaridade baseados em dados de performance para encontrar os jogadores ideais para o seu clube.",
    "search_criteria_header": "Critérios de Busca",
    "reference_player_subheader": "Atleta de Referência",
    "reference_player_help": "Opcional. Se não preenchido, a busca será apenas por filtros.",
    "player_name_input": "Nome do Atleta",
    "player_name_placeholder": "Ex: Marta Vieira da Silva",
    "player_club_input": "Clube do Atleta",
    "player_club_placeholder": "Ex: Orlando Pride",
    "profile_filters_subheader": "Filtros de Perfil",
    "profile_filters_help": "Defina os critérios para o perfil dos atletas desejados.",
    "position_multiselect": "Posição(ões) Desejada(s)",
    "position_help": "Selecione uma ou mais posições. Se um atleta de referência for fornecido, a posição dele será considerada.",
    "min_age_input": "Idade Mínima",
    "max_age_input": "Idade Máxima",
    "generate_recommendations_button": "🔎 Gerar Recomendações",
    "generating_spinner": "Analisando dados e buscando recomendações...",
    "results_header": "Resultados da Busca",
    "recommendations_success": "Recomendações geradas com sucesso!",
    "details_download_header": "Detalhes Completos e Download",
    "details_download_info": "Para analisar as estatísticas completas, use a tabela interativa abaixo ou baixe o arquivo.",
    "download_csv_button": "⬇️ Download CSV Completo",
    "download_csv_help": "Baixe as estatísticas completas dos atletas recomendados em formato CSV.",
    "download_excel_button": "⬇️ Download Excel Completo",
    "download_excel_help": "Baixe as estatísticas completas dos atletas recomendados em formato Excel.",
    "show_all_stats_expander": "Clique para ver todas as estatísticas dos atletas recomendados (tabela grande)",
    "no_recommendations_warning": "Nenhuma recomendação encontrada. Por favor, ajuste os critérios de busca e tente novamente.",
    "data_model_error": "Dados ou modelo não carregados. Por favor, tente novamente mais tarde.",
    "reference_player_found_success": "🔍 Atleta de Referência: **{player_name}** ({club}) encontrado.",
    "reference_player_not_found_warning": "⚠️ Atleta de referência '{player_name}' do clube '{club}' não encontrado com alta confiança. Buscando apenas por critérios de filtro.",
    "no_reference_player_info": "Nenhum atleta de referência fornecido. Buscando recomendações apenas pelos critérios de busca.",
    "no_athletes_match_filters_warning": "Nenhum atleta corresponde aos filtros especificados. Tente ajustar os critérios.",
    "no_similar_recommendations_info": "Nenhuma recomendação similar ao atleta **{player_name}** encontrada com os filtros aplicados. Tente ajustar os critérios ou o atleta de referência.",
    "showing_filtered_athletes_info": "Mostrando atletas que atendem aos filtros. Para recomendações por similaridade, forneça um atleta de referência.",
    "only_x_athletes_found_info": "Apenas {count} atletas encontrados com os filtros, mostrando todos.",
    "missing_columns_error": "Erro: As seguintes colunas numéricas essenciais não foram encontradas no arquivo de dados: **{columns}**",
    "check_column_names_info": "Por favor, verifique se os nomes das colunas na lista `colunas_numericas` correspondem exatamente aos nomes no seu arquivo Parquet.",
    "data_load_error": "Erro ao carregar o arquivo de dados. Por favor, verifique o link ou a conexão: {error_message}",
    "logo_not_found_warning": "Logo não encontrada. Verifique o caminho ou a URL da imagem.",
    "developed_by": "Desenvolvido no Brasil pela ProFutStat",
    # Column names for display
    "col_player_name": "Nome do Atleta",
    "col_club": "Clube",
    "col_position": "Posição",
    "col_age": "Idade",
    "col_similarity": "Similaridade",
    "explain_similarity_header": "Análise Detalhada de Similaridade",
    "select_player_to_explain": "Selecione uma jogadora recomendada para entender a similaridade:",
    "comparison_chart_title": "Comparação de Estatísticas: {player1_name} vs. {player2_name}",
    "similarity_factors_header": "Fatores Chave de Similaridade",
    "most_similar_features": "As estatísticas mais similares entre as jogadoras são (menor diferença):",
    "least_similar_features": "As estatísticas com maior diferença (menos similaridade) são:",
    "diff_metric_label": "Diferença Absoluta", # For L1/Euclidean
    "diff_metric_label_sq": "Diferença Quadrática", # For L2/Euclidean
    "value_ref_player": "Jogadora de Consulta ({player_name})",
    "value_similar_player": "Jogadora Similar ({player_name})",
    "no_ref_player_for_explanation": "Para analisar a similaridade, é necessário fornecer um atleta de referência na busca."
}

# English
TEXT_EN = {
    "page_title": "PlayerScout AI - Women's Football",
    "header_title": "PlayerScout AI",
    "welcome_message": "Welcome to **ProFutStat's PlayerScout AI** tool! Use our similarity algorithms based on performance data to find the ideal players for your club.",
    "search_criteria_header": "Search Criteria",
    "reference_player_subheader": "Reference Player",
    "reference_player_help": "Optional. If left blank, the search will be filter-based only.",
    "player_name_input": "Player Name",
    "player_name_placeholder": "Ex: Megan Rapinoe",
    "player_club_input": "Player Club",
    "player_club_placeholder": "Ex: OL Reign",
    "profile_filters_subheader": "Profile Filters",
    "profile_filters_help": "Define the criteria for the desired player profiles.",
    "position_multiselect": "Desired Position(s)",
    "position_help": "Select one or more positions. If a reference player is provided, their position will be considered.",
    "min_age_input": "Minimum Age",
    "max_age_input": "Maximum Age",
    "generate_recommendations_button": "🔎 Generate Recommendations",
    "generating_spinner": "Analyzing data and searching for recommendations...",
    "results_header": "Search Results",
    "recommendations_success": "Recommendations generated successfully!",
    "details_download_header": "Complete Details and Download",
    "details_download_info": "To analyze complete statistics, use the interactive table below or download the file.",
    "download_csv_button": "⬇️ Download Full CSV",
    "download_csv_help": "Download complete statistics of recommended athletes in CSV format.",
    "download_excel_button": "⬇️ Download Full Excel",
    "download_excel_help": "Download complete statistics of recommended athletes in Excel format.",
    "show_all_stats_expander": "Click to see all recommended players' statistics (large table)",
    "no_recommendations_warning": "No recommendations found. Please adjust search criteria and try again.",
    "data_model_error": "Data or model not loaded. Please try again later.",
    "reference_player_found_success": "🔍 Reference Player: **{player_name}** ({club}) found.",
    "reference_player_not_found_warning": "⚠️ Reference player '{player_name}' from club '{club}' not found with high confidence. Searching only by filter criteria.",
    "no_reference_player_info": "No reference player provided. Searching for recommendations only by search criteria.",
    "no_athletes_match_filters_warning": "No athletes match the specified filters. Try adjusting the criteria.",
    "no_similar_recommendations_info": "No recommendations similar to player **{player_name}** found with the applied filters. Try adjusting the criteria or the reference player.",
    "showing_filtered_athletes_info": "Showing athletes that meet the filters. For similarity recommendations, provide a reference athlete.",
    "only_x_athletes_found_info": "Only {count} athletes found with filters, showing all.",
    "missing_columns_error": "Error: The following essential numeric columns were not found in the data file: **{columns}**",
    "check_column_names_info": "Please ensure the column names in the `colunas_numericas` list exactly match the names in your Parquet file.",
    "data_load_error": "Error loading data file. Please check the link or connection: {error_message}",
    "logo_not_found_warning": "Logo not found. Check image path or URL.",
    "developed_by": "Developed in Brazil by ProFutStat",
    # Column names for display
    "col_player_name": "Player Name",
    "col_club": "Club",
    "col_position": "Position",
    "col_age": "Age",
    "col_similarity": "Similarity",
    "explain_similarity_header": "Detailed Similarity Analysis",
    "select_player_to_explain": "Select a recommended player to understand similarity:",
    "comparison_chart_title": "Statistics Comparison: {player1_name} vs. {player2_name}",
    "similarity_factors_header": "Key Similarity Factors",
    "most_similar_features": "The most similar statistics between players are (smallest difference):",
    "least_similar_features": "The statistics with the largest difference (least similarity) are:",
    "diff_metric_label": "Absolute Difference",
    "diff_metric_label_sq": "Squared Difference",
    "value_ref_player": "Reference Player ({player_name})",
    "value_similar_player": "Similar Player ({player_name})",
    "no_ref_player_for_explanation": "To analyze similarity, a reference athlete must be provided in the search."
}

# Italian
TEXT_IT = {
    "page_title": "PlayerScout IA - Calcio Femminile",
    "header_title": "PlayerScout IA",
    "welcome_message": "Benvenuti nello strumento **PlayerScout IA di ProFutStat**! Utilizzate i nostri algoritmi di similarità basati sui dati di performance per trovare i giocatori ideali per il vostro club.",
    "search_criteria_header": "Criteri di Ricerca",
    "reference_player_subheader": "Atleta di Riferimento",
    "reference_player_help": "Opzionale. Se non compilato, la ricerca sarà solo basata sui filtri.",
    "player_name_input": "Nome dell'Atleta",
    "player_name_placeholder": "Es: Cristiana Girelli",
    "player_club_input": "Club dell'Atleta",
    "player_club_placeholder": "Es: Juventus FC",
    "profile_filters_subheader": "Filtri del Profilo",
    "profile_filters_help": "Definisci i criteri per il profilo degli atleti desiderati.",
    "position_multiselect": "Posizione(i) Desiderata(e)",
    "position_help": "Seleziona una o più posizioni. Se viene fornito un atleta di riferimento, la sua posizione sarà considerata.",
    "min_age_input": "Età Minima",
    "max_age_input": "Età Massima",
    "generate_recommendations_button": "🔎 Genera Raccomandazioni",
    "generating_spinner": "Analisi dei dati e ricerca di raccomandazioni...",
    "results_header": "Risultati della Ricerca",
    "recommendations_success": "Raccomandazioni generate con successo!",
    "details_download_header": "Dettagli Completi e Download",
    "details_download_info": "Per analizzare le statistiche complete, usa la tabella interattiva qui sotto o scarica il file.",
    "download_csv_button": "⬇️ Scarica CSV Completo",
    "download_csv_help": "Scarica le statistiche complete degli atleti raccomandati in formato CSV.",
    "download_excel_button": "⬇️ Scarica Excel Completo",
    "download_excel_help": "Scarica le statistiche complete degli atleti raccomandati in formato Excel.",
    "show_all_stats_expander": "Clicca per vedere tutte le statistiche degli atleti raccomandati (tabella grande)",
    "no_recommendations_warning": "Nessuna raccomandazione trovata. Si prega di regolare i criteri di ricerca e riprovare.",
    "data_model_error": "Dati o modello non caricati. Si prega di riprovare più tardi.",
    "reference_player_found_success": "🔍 Atleta di Riferimento: **{player_name}** ({club}) trovato.",
    "reference_player_not_found_warning": "⚠️ Atleta di riferimento '{player_name}' dal club '{club}' non trovato con alta confidenza. Ricerca solo per criteri di filtro.",
    "no_reference_player_info": "Nessun atleta di riferimento fornito. Ricerca raccomandazioni solo per criteri di ricerca.",
    "no_athletes_match_filters_warning": "Nessun atleta corrisponde ai filtri specificati. Prova a regolare i criteri.",
    "no_similar_recommendations_info": "Nessuna raccomandazione simile all'atleta **{player_name}** trovata con i filtri applicati. Prova a regolare i criteri o l'atleta di riferimento.",
    "showing_filtered_athletes_info": "Mostrando atleti che soddisfano i filtri. Per raccomandazioni per similarità, fornisci un atleta di riferimento.",
    "only_x_athletes_found_info": "Solo {count} atleti trovati con i filtri, mostrando tutti.",
    "missing_columns_error": "Errore: Le seguenti colunas numéricas essenziali não foram encontradas no arquivo de dados: **{columns}**",
    "check_column_names_info": "Si prega di assicurarsi che i nomi delle colonne nell'elenco `colunas_numericas` corrispondano esattamente ai nomi nel file Parquet.",
    "data_load_error": "Erro durante il caricamento del file di dati. Si prega di controllare il link o la connessione: {error_message}",
    "logo_not_found_warning": "Logo non trovato. Controlla il percorso o l'URL dell'immagine.",
    "developed_by": "Sviluppato in Brasile da ProFutStat",
    # Column names for display
    "col_player_name": "Nome Atleta",
    "col_club": "Club",
    "col_position": "Posizione",
    "col_age": "Età",
    "col_similarity": "Similarità",
    "explain_similarity_header": "Analisi Dettagliata della Similarità",
    "select_player_to_explain": "Seleziona una giocatrice raccomandata per capire la similarità:",
    "comparison_chart_title": "Confronto Statistiche: {player1_name} vs. {player2_name}",
    "similarity_factors_header": "Fattori Chiave di Similarità",
    "most_similar_features": "Le statistiche più simili tra i giocatori sono (differenza minore):",
    "least_similar_features": "Le statistiche con la maggiore differenza (minore similarità) sono:",
    "diff_metric_label": "Differenza Assoluta",
    "diff_metric_label_sq": "Differenza Quadrata",
    "value_ref_player": "Giocatore di Riferimento ({player_name})",
    "value_similar_player": "Giocatore Simile ({player_name})",
    "no_ref_player_for_explanation": "Per analizzare la similarità, è necessario fornire un atleta di riferimento nella ricerca."
}

# --- Streamlit Page Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title=TEXT_PT["page_title"], # Default to Portuguese for initial page title
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Custom CSS for Professional Styling ---
st.markdown(
    """
    <style>
    /* General Styles */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333333;
    }
    .stApp {
        background-color: #f0f2f6;
    }

    /* Header - Logo and Title */
    .header-section {
        display: flex;
        align-items: center;
        gap: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 30px;
    }
    .header-section h1 {
        font-size: 2.8em; /* Adjust font size for main title */
        color: #004d99; /* Corporate Blue */
        margin: 0;
        line-height: 1.2;
    }

    /* Subtitles */
    h2 {
        color: #0056b3;
        font-size: 1.8em;
        border-bottom: 2px solid #0056b3;
        padding-bottom: 5px;
        margin-bottom: 20px;
    }
    h3 {
        color: #0056b3;
        font-size: 1.4em;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* Buttons */
    .stButton>button {
        background-color: #28a745; /* Green for primary action */
        color: white;
        border-radius: 8px;
        padding: 10px 25px;
        font-size: 1.1em;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #218838;
    }
    .stDownloadButton>button {
        background-color: #007bff; /* Blue for download */
        color: white;
        border-radius: 8px;
        padding: 8px 20px;
        font-size: 1em;
        font-weight: normal;
        transition: background-color 0.3s ease;
    }
    .stDownloadButton>button:hover {
        background-color: #0056b3;
    }

    /* Dataframe */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .dataframe th {
        background-color: #e9ecef;
        color: #495057;
        font-weight: bold;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f8f9fa;
    }

    /* Feedback Messages */
    .stAlert {
        border-radius: 8px;
    }

    /* Input Controls */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stMultiSelect>div>div>div>div {
        border-radius: 8px;
        border: 1px solid #ced4da;
        padding: 8px 12px;
    }
    .stSlider > div > div > div:nth-child(2) > div {
        background-color: #007bff; /* Slider color */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Language Selection (moved AFTER st.set_page_config) ---
st.sidebar.title("Language / Idioma / Lingua")
language_option = st.sidebar.selectbox(
    "Select Language",
    options=["Português", "English", "Italiano"]
)

if language_option == "Português":
    current_lang_text = TEXT_PT
elif language_option == "English":
    current_lang_text = TEXT_EN
else:
    current_lang_text = TEXT_IT

# --- Global variable for numeric columns list ---
# Define `colunas_numericas` globally or pass it
colunas_numericas = [
    "rating", "goals", "bigChancesCreated", "bigChancesMissed", "assists",
    "goalsAssistsSum", "accuratePasses", "inaccuratePasses", "totalPasses", "accuratePassesPercentage",
    "accurateOwnHalfPasses", "accurateOppositionHalfPasses", "accurateFinalThirdPasses", "keyPasses",
    "successfulDribbles", "successfulDribblesPercentage", "tackles", "interceptions", "yellowCards",
    "directRedCards", "redCards", "accurateCrosses", "accurateCrossesPercentage", "totalShots", "shotsOnTarget",
    "shotsOffTarget", "groundDuelsWon", "groundDuelsWonPercentage", "aerialDuelsWon", "aerialDuelsWonPercentage",
    "totalDuelsWon", "totalDuelsWonPercentage", "minutesPlayed", "goalConversionPercentage", "penaltiesTaken",
    "penaltyGoals", "penaltyWon", "penaltyConceded", "shotFromSetPiece", "freeKickGoal", "goalsFromInsideTheBox",
    "goalsFromOutsideTheBox", "shotsFromInsideTheBox", "shotsFromOutsideTheBox", "headedGoals", "leftFootGoals",
    "rightFootGoals", "accurateLongBalls", "accurateLongBallsPercentage", "clearances", "errorLeadToGoal",
    "errorLeadToShot", "dispossessed", "possessionLost", "possessionWonAttThird", "totalChippedPasses",
    "accurateChippedPasses", "touches", "wasFouled", "fouls", "hitWoodwork", "ownGoals", "dribbledPast",
    "offsides", "blockedShots", "passToAssist", "penaltyFaced",
    "goalsConcededInsideTheBox",
    "goalsConcededOutsideTheBox","highClaims", "crossesNotClaimed",
    "matchesStarted", "penaltyConversion", "setPieceConversion", "totalAttemptAssist", "totalContest",
    "totalCross", "duelLost", "aerialLost", "attemptPenaltyMiss", "attemptPenaltyPost", "attemptPenaltyTarget",
    "totalLongBalls", "goalsConceded", "tacklesWon", "tacklesWonPercentage", "scoringFrequency", "yellowRedCards","totalOwnHalfPasses", "totalOppositionHalfPasses", "totwAppearances", "expectedGoals","ballRecovery", "appearances", "age", "player.height"
]

@st.cache_resource
def load_data_and_model(lang_text, numeric_cols): # Pass numeric_cols to the cached function
    """Loads data and initializes the scaler and FAISS index."""
    try:
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data_feminino.parquet')
    except Exception as e:
        st.error(lang_text["data_load_error"].format(error_message=e))
        st.stop()

    missing_columns = [col for col in numeric_cols if col not in df.columns]
    if missing_columns:
        st.error(lang_text["missing_columns_error"].format(columns=', '.join(missing_columns)))
        st.info(lang_text["check_column_names_info"])
        st.stop()

    # Ensure selected columns are numeric type before imputation
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce') # Coerce non-numeric to NaN

    # Fill NaN values with the median of each column
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    # Handle cases where an entire column might be NaN even after median (e.g., if all values were NaN)
    df[numeric_cols] = df[numeric_cols].fillna(0) # Fill any remaining NaNs with 0

    # Replace infinite values with NaN, then fill those NaNs
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    df[numeric_cols] = df[numeric_cols].fillna(0) # Fill any NaNs created from infinite values with 0

    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(df[numeric_cols])
    
    # --- L2 Normalization to ensure dot product is cosine similarity ---
    normalizer = Normalizer(norm='l2')
    dados_normalizados = normalizer.fit_transform(dados_normalizados)
    # --- End of L2 Normalization ---

    dados_normalizados = dados_normalizados.astype('float32') # FAISS requires float32

    dimension = dados_normalizados.shape[1]
    index = faiss.IndexFlatIP(dimension) # IndexFlatIP expects normalized vectors for cosine similarity
    index.add(dados_normalizados)

    return df, scaler, index, dados_normalizados


# Pass current_lang_text and colunas_numericas to the cached function
df, scaler, faiss_index, dados_normalizados = load_data_and_model(current_lang_text, colunas_numericas)

# --- Recommendation Function Adapted for Streamlit ---

def recommend_players_advanced(name=None, club=None, top_n=10, position=None,
                                 min_age=None, max_age=None, lang_text=TEXT_PT): # Pass lang_text here
    """
    Recommends similar players with multiple filters using FAISS.
    Returns: recommendations_display, complete_recommendations, reference_player_id
    """
    
    if df is None or faiss_index is None:
        st.error(lang_text["data_model_error"])
        return pd.DataFrame(), pd.DataFrame(), None # Returns empty DFs and None for player_id

    player_id = None
    player_ref_name = None
    player_ref_club = None

    if name and club:
        df_temp = df.copy()
        df_temp['temp_sim_nome'] = df_temp['player.name'].apply(lambda x: fuzz.token_set_ratio(name, x))
        df_temp['temp_sim_clube'] = df_temp['player.team.name'].apply(lambda x: fuzz.token_set_ratio(club, x))
        df_temp['temp_sim_combinada'] = 0.7 * df_temp['temp_sim_nome'] + 0.3 * df_temp['temp_sim_clube']
        
        best_match = df_temp.nlargest(1, 'temp_sim_combinada')
        
        if not best_match.empty and best_match['temp_sim_combinada'].iloc[0] >= 80:
            player_id = best_match.index[0]
            player_ref = df.loc[player_id]
            player_ref_name = player_ref['player.name']
            player_ref_club = player_ref['player.team.name']
            st.success(lang_text["reference_player_found_success"].format(player_name=player_ref_name, club=player_ref_club))
            
            # If no position is explicitly selected, use the reference player's position
            if not position: # Check if position list is empty
                position = [player_ref['position']]
        else:
            st.warning(lang_text["reference_player_not_found_warning"].format(player_name=name, club=club))
            player_id = None
    else:
        st.info(lang_text["no_reference_player_info"])

    filter_mask = pd.Series(True, index=df.index)
    
    if position:
        filter_mask &= df['position'].isin(position)
    
    if min_age is not None:
        filter_mask &= df['age'] >= min_age
    if max_age is not None:
        filter_mask &= df['age'] <= max_age
    
    filtered_indices = df[filter_mask].index.tolist()

    if not filtered_indices:
        st.warning(lang_text["no_athletes_match_filters_warning"])
        return pd.DataFrame(), pd.DataFrame(), None
    
    # Get recommendations
    if player_id is not None:
        query_vector = dados_normalizados[df.index.get_loc(player_id)].reshape(1, -1)
        
        # Search in the FAISS index with a larger number of results to filter later
        D, I = faiss_index.search(query_vector, max(top_n * 5, len(filtered_indices) + 1)) 

        similarities = D[0]
        returned_indices = I[0]
        
        recommendations_raw = pd.DataFrame({
            'original_index': returned_indices,
            'similaridade': similarities # Keep the name as 'similaridade' for consistency with male code
        })
        
        final_recommendations = recommendations_raw[
            recommendations_raw['original_index'].isin(filtered_indices) & 
            (recommendations_raw['original_index'] != player_id) # Exclude the reference player themselves
        ]
        
        final_recommendations = final_recommendations.sort_values(by='similaridade', ascending=False).head(top_n)
        
        if final_recommendations.empty:
            st.info(lang_text["no_similar_recommendations_info"].format(player_name=player_ref_name))
            return pd.DataFrame(), pd.DataFrame(), player_id
            
        # Get the full data for recommended players using their original_index
        # This will preserve all original columns and their types
        recommendations_df = df.loc[final_recommendations['original_index']].copy()
        
        # Now, map the similarity scores to the correct players in recommendations_df
        # Using .set_index() and .map() is more robust for alignment
        recommendations_df['similaridade'] = recommendations_df.index.map(
            final_recommendations.set_index('original_index')['similaridade']
        )
        
    else:
        st.info(lang_text["showing_filtered_athletes_info"])
        if len(filtered_indices) < top_n:
            st.info(lang_text["only_x_athletes_found_info"].format(count=len(filtered_indices)))
        
        # If no reference player, just show a sample of filtered players
        recommendations_df = df.loc[filtered_indices].sample(n=min(top_n, len(filtered_indices)), random_state=42).copy()
        recommendations_df['similaridade'] = np.nan # No similarity score when no reference
    
    # --- Prepare full DataFrame for download (BEFORE any display formatting) ---
    recommendations_for_download = recommendations_df.copy()

    # --- Formatting for UI Display ONLY ---
    # Apply display formatting only to the DataFrame intended for display
    
    # Formatar Idade para Inteiro
    if 'age' in recommendations_df.columns:
        recommendations_df['age'] = recommendations_df['age'].apply(lambda x: int(x) if pd.notna(x) else x)

    # Formatar Similaridade de 0-1 para 0-100 (Após normalização L2, estará entre 0 e 1)
    if player_id is not None and 'similaridade' in recommendations_df.columns:
        recommendations_df['similaridade'] = recommendations_df['similaridade'].apply(lambda x: f"{max(0, min(100, x * 100)):.0f}%") # Garante entre 0 e 100
    
    # Renomear colunas para exibição amigável
    recommendations_display = recommendations_df.rename(columns={
        'player.name': lang_text['col_player_name'],
        'player.team.name': lang_text['col_club'],
        'position': lang_text['col_position'],
        'age': lang_text['col_age'],
        'similaridade': lang_text['col_similarity'] # Use the formatted similarity column
    })

    # Define columns for primary display in the table
    cols_display_final = [lang_text['col_player_name'], lang_text['col_club'],
                          lang_text['col_position'], lang_text['col_age']]
    if player_id is not None:
        cols_display_final.append(lang_text['col_similarity'])
    
    # Return the main DataFrame with formatted and sorted columns, and the full DF for download
    # Ensure sorting by the DISPLAY similarity, not the raw one
    return recommendations_display[cols_display_final].sort_values(by=lang_text['col_similarity'], ascending=False, na_position='last').reset_index(drop=True), recommendations_for_download, player_id

# --- Function to display detailed similarity analysis ---
def display_detailed_similarity(ref_player_id, selected_similar_player_original_index,
                                df_data, scaler_model, numeric_features, lang_text):
    """
    Displays a detailed comparison and explanation of similarity between two players.
    """
    if ref_player_id is None:
        st.warning(lang_text["no_ref_player_for_explanation"])
        return

    ref_player_data = df_data.loc[ref_player_id]
    similar_player_data = df_data.loc[selected_similar_player_original_index]

    ref_player_name = ref_player_data['player.name']
    similar_player_name = similar_player_data['player.name']

    st.subheader(lang_text["comparison_chart_title"].format(player1_name=ref_player_name, player2_name=similar_player_name))

    # Prepare data for Radar Chart (using original, unscaled values for better human readability)
    radar_df_comparison = pd.DataFrame({
        'Estatística': numeric_features,
        lang_text["value_ref_player"].format(player_name=ref_player_name): ref_player_data[numeric_features].values,
        lang_text["value_similar_player"].format(player_name=similar_player_name): similar_player_data[numeric_features].values
    })

    # Melt DataFrame for Plotly Express
    radar_melted_df = radar_df_comparison.melt(id_vars=['Estatística'], var_name='Jogador', value_name='Valor')

    fig = px.line_polar(radar_melted_df, r='Valor', theta='Estatística', line_close=True,
                        color='Jogador', markers=True,
                        title=lang_text["comparison_chart_title"].format(player1_name=ref_player_name, player2_name=similar_player_name))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(lang_text["similarity_factors_header"])

    # Get scaled vectors
    ref_vector_scaled = scaler_model.transform(ref_player_data[numeric_features].values.reshape(1, -1))[0]
    similar_vector_scaled = scaler_model.transform(similar_player_data[numeric_features].values.reshape(1, -1))[0]

    # Calculate squared differences (since FAISS is using IndexFlatIP after L2 normalization,
    # the underlying distance for cosine similarity is related to Euclidean distance between normalized vectors.
    # We can still use squared differences for *contribution* analysis, or just absolute difference if preferred)
    # Given IndexFlatIP + Normalizer, the actual "distance" is 1 - cosine_similarity.
    # The term (a_i - b_i)^2 is a component of squared Euclidean distance, which is NOT what IP directly calculates.
    # For cosine similarity, it's about the alignment of vectors.
    # A simpler way to explain "importance" of a feature for cosine similarity is to look at the absolute difference
    # of the *normalized* values, or the absolute difference of the *original* values.
    
    # Let's use absolute difference of the ORIGINAL values for easier understanding
    diff_abs = np.abs(ref_player_data[numeric_features].values - similar_player_data[numeric_features].values)
    feature_contributions = pd.Series(diff_abs, index=numeric_features)

    # Sort by smallest difference (most similar)
    sorted_contributions = feature_contributions.sort_values(ascending=True)

    st.write(lang_text["most_similar_features"])
    for feature, diff_val in sorted_contributions.head(5).items(): # Top 5 most similar
        st.write(f"- **{feature}**: ({lang_text['value_ref_player'].format(player_name=ref_player_name)}: {ref_player_data[feature]:.2f}, "
                 f"{lang_text['value_similar_player'].format(player_name=similar_player_name)}: {similar_player_data[feature]:.2f}) "
                 f"- {lang_text['diff_metric_label']}: {diff_val:.2f}")

    st.write(lang_text["least_similar_features"])
    for feature, diff_val in sorted_contributions.tail(5).items(): # Top 5 least similar
        st.write(f"- **{feature}**: ({lang_text['value_ref_player'].format(player_name=ref_player_name)}: {ref_player_data[feature]:.2f}, "
                 f"{lang_text['value_similar_player'].format(player_name=similar_player_name)}: {similar_player_data[feature]:.2f}) "
                 f"- {lang_text['diff_metric_label']}: {diff_val:.2f}")

    # Bar chart for absolute differences
    fig_bar_diff = px.bar(
        x=sorted_contributions.index,
        y=sorted_contributions.values,
        title=f'Diferença Absoluta por Estatística entre {ref_player_name} e {similar_player_name}',
        labels={'x': 'Estatística', 'y': 'Diferença Absoluta'},
        color=sorted_contributions.values,
        color_continuous_scale=px.colors.sequential.Plasma_r # Invert color scale for better viz
    )
    fig_bar_diff.update_layout(xaxis={'categoryorder':'total ascending'}) # Ordena do menor para o maior
    st.plotly_chart(fig_bar_diff, use_container_width=True)


# --- Streamlit Application Layout ---

# Header with Logo and Title
st.markdown('<div class="header-section">', unsafe_allow_html=True)
try:
    st.image("https://github.com/rafacstein/profutstat/raw/main/scouting/profutstat_logo.png", width=100)
except Exception:
    st.warning(current_lang_text["logo_not_found_warning"])
st.markdown(f"<h1>{current_lang_text['header_title']}</h1>", unsafe_allow_html=True) # Use h1 for the main title
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(current_lang_text["welcome_message"])

# Search Criteria Section
st.header(current_lang_text["search_criteria_header"])

col_ref, col_filters = st.columns([1, 1.5])

with col_ref:
    st.subheader(current_lang_text["reference_player_subheader"])
    st.markdown(current_lang_text["reference_player_help"], help=current_lang_text["reference_player_help"])
    player_name = st.text_input(current_lang_text["player_name_input"], placeholder=current_lang_text["player_name_placeholder"]).strip()
    player_club = st.text_input(current_lang_text["player_club_input"], placeholder=current_lang_text["player_club_placeholder"]).strip()

with col_filters:
    st.subheader(current_lang_text["profile_filters_subheader"])
    st.markdown(current_lang_text["profile_filters_help"])
    positions_choices = ['GK','DL', 'DC', 'DR', 'DM', 'MC', 'ML', 'MR', 'AM','LW', 'RW', 'ST']
    selected_position = st.multiselect(
        current_lang_text["position_multiselect"],
        options=positions_choices,
        default=[],
        help=current_lang_text["position_help"]
    )

    col_min_age, col_max_age = st.columns(2)
    with col_min_age:
        min_age_val = st.number_input(current_lang_text["min_age_input"], min_value=15, max_value=45, value=18, step=1)
    with col_max_age:
        max_age_val = st.number_input(current_lang_text["max_age_input"], min_value=15, max_value=45, value=35, step=1)

st.markdown("---")

# Recommendation Button
if st.button(current_lang_text["generate_recommendations_button"], type="primary"):
    with st.spinner(current_lang_text["generating_spinner"]):
        recommendations_display, complete_recommendations, reference_player_idx_found = recommend_players_advanced(
            name=player_name if player_name else None,
            club=player_club if player_club else None,
            position=selected_position,
            min_age=min_age_val,
            max_age=max_age_val,
            top_n=10,
            lang_text=current_lang_text # Pass language text to the function
        )
        
        # Store results in session state to persist them across reruns
        st.session_state['recommendations_display'] = recommendations_display
        st.session_state['complete_recommendations'] = complete_recommendations
        st.session_state['reference_player_idx_found'] = reference_player_idx_found
        st.session_state['search_executed'] = True
        st.session_state['current_lang_text'] = current_lang_text # Store language for explanation

# Display recommendations and explanation section if search was executed
if 'search_executed' in st.session_state and st.session_state['search_executed']:
    recommendations_display = st.session_state['recommendations_display']
    complete_recommendations = st.session_state['complete_recommendations']
    reference_player_idx_found = st.session_state['reference_player_idx_found']
    current_lang_text_session = st.session_state['current_lang_text']

    if not recommendations_display.empty:
        st.subheader(current_lang_text_session["results_header"])
        st.dataframe(recommendations_display, use_container_width=True)
        st.success(current_lang_text_session["recommendations_success"])

        # --- Details and Download Section ---
        st.markdown("### " + current_lang_text_session["details_download_header"])
        st.info(current_lang_text_session["details_download_info"])
        
        # Download options
        csv_buffer = io.StringIO()
        complete_recommendations.to_csv(csv_buffer, index=True, encoding='utf-8')
        csv_bytes = csv_buffer.getvalue().encode('utf-8')

        excel_buffer = io.BytesIO()
        complete_recommendations.to_excel(excel_buffer, index=True, engine='xlsxwriter')
        excel_buffer.seek(0)

        col_download_csv, col_download_excel = st.columns(2)
        with col_download_csv:
            st.download_button(
                label=current_lang_text_session["download_csv_button"],
                data=csv_bytes,
                file_name="recommended_players.csv",
                mime="text/csv",
                help=current_lang_text_session["download_csv_help"]
            )
        with col_download_excel:
            st.download_button(
                label=current_lang_text_session["download_excel_button"],
                data=excel_buffer,
                file_name="recommended_players.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help=current_lang_text_session["download_excel_help"]
            )

        with st.expander(current_lang_text_session["show_all_stats_expander"]):
            st.dataframe(complete_recommendations, use_container_width=True)

        # --- Detailed Similarity Explanation Section ---
        if reference_player_idx_found is not None:
            st.markdown("---")
            st.header(current_lang_text_session["explain_similarity_header"])

            # Dropdown to select one of the recommended players for detailed analysis
            # We need the original index from `complete_recommendations` for `display_detailed_similarity`
            # And player name for the selectbox
            
            # Map original indices to player names for the selectbox
            player_names_for_selection = {
                idx: complete_recommendations.loc[idx, 'player.name']
                for idx in complete_recommendations.index
            }
            
            selected_player_name_for_explanation = st.selectbox(
                current_lang_text_session["select_player_to_explain"],
                options=list(player_names_for_selection.values()),
                key='explanation_player_select' # Unique key for this selectbox
            )

            # Find the original index based on the selected player name
            selected_similar_player_original_index = None
            for idx, name in player_names_for_selection.items():
                if name == selected_player_name_for_explanation:
                    selected_similar_player_original_index = idx
                    break

            if selected_similar_player_original_index is not None:
                display_detailed_similarity(
                    ref_player_id=reference_player_idx_found,
                    selected_similar_player_original_index=selected_similar_player_original_index,
                    df_data=df, # Pass the original DataFrame
                    scaler_model=scaler, # Pass the scaler model
                    numeric_features=colunas_numericas, # Pass the list of numeric features
                    lang_text=current_lang_text_session
                )
            else:
                st.warning("Selecione uma jogadora válida para a explicação.")
        else:
            st.info(current_lang_text_session["no_ref_player_for_explanation"])

    else:
        st.warning(current_lang_text_session["no_recommendations_warning"])
else:
    # Initial state when app loads or after a full refresh
    st.info("Aguardando critérios de busca para gerar recomendações.")


st.markdown("---")
st.write(current_lang_text["developed_by"])

