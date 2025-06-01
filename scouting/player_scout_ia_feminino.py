import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, Normalizer, PowerTransformer
import faiss
import streamlit as st
from fuzzywuzzy import fuzz
import io
import plotly.express as px

# --- Multilingual Text Strings ---
# É CRUCIAL que esses dicionários sejam definidos ANTES de st.set_page_config
TEXT_PT = {
    "page_title": "ProFutStat - Scouting de Jogadoras",
    "header_title": "ProFutStat - Scouting de Jogadoras",
    "welcome_message": "Use esta ferramenta para encontrar jogadoras com perfis de desempenho semelhantes.",
    "search_criteria_header": "Critérios de Busca",
    "reference_player_subheader": "Jogadora de Referência (Opcional)",
    "reference_player_help": "Insira o nome e o clube de uma jogadora para encontrar atletas com perfil semelhante. Se não informar, o sistema buscará atletas nos filtros selecionados.",
    "player_name_input": "Nome da Jogadora",
    "player_name_placeholder": "Ex: Marta Vieira da Silva",
    "player_club_input": "Clube da Jogadora",
    "player_club_placeholder": "Ex: Orlando Pride",
    "profile_filters_subheader": "Filtros de Perfil",
    "profile_filters_help": "Defina filtros para a busca, mesmo que não informe uma jogadora de referência.",
    "position_multiselect": "Posição(ões)",
    "position_help": "Selecione uma ou mais posições para filtrar as jogadoras.",
    "min_age_input": "Idade Mínima",
    "max_age_input": "Idade Máxima",
    "generate_recommendations_button": "Gerar Recomendações",
    "generating_spinner": "Gerando recomendações, por favor aguarde...",
    "results_header": "Jogadoras Recomendadas",
    "recommendations_success": "Recomendações geradas com sucesso!",
    "details_download_header": "Detalhes e Download",
    "details_download_info": "Baixe os dados completos das jogadoras recomendadas e suas estatísticas detalhadas.",
    "download_csv_button": "Baixar como CSV",
    "download_csv_help": "Baixa a tabela de recomendações em formato CSV.",
    "download_excel_button": "Baixar como Excel",
    "download_excel_help": "Baixa a tabela de recomendações em formato XLSX.",
    "show_all_stats_expander": "Mostrar Todas as Estatísticas",
    "explain_similarity_header": "Análise Detalhada de Similaridade",
    "select_player_to_explain": "Selecione uma jogadora recomendada para entender a similaridade:",
    "comparison_chart_title": "Comparação de Estatísticas entre {player1_name} e {player2_name}",
    "value_ref_player": "Valor de {player_name} (Processado)",
    "value_similar_player": "Valor de {player_name} (Processado)",
    "similarity_factors_header": "Fatores Chave de Similaridade",
    "most_similar_features": "As 5 estatísticas mais similares entre as jogadoras são:",
    "least_similar_features": "As 5 estatísticas mais diferentes entre as jogadoras são:",
    "no_ref_player_for_explanation": "Por favor, selecione uma jogadora de referência para habilitar a explicação detalhada de similaridade.",
    "data_load_error": "Erro ao carregar os dados: {error_message}. Verifique a URL do arquivo ou a conectividade.",
    "missing_columns_error": "Colunas esperadas ausentes no arquivo de dados: {columns}.",
    "check_column_names_info": "Verifique se os nomes das colunas no seu arquivo Parquet correspondem aos nomes esperados no script.",
    "logo_not_found_warning": "Logo não encontrado, continuando sem ele.",
    "reference_player_found_success": "Jogadora de referência encontrada: **{player_name}** ({club})",
    "reference_player_not_found_warning": "Jogadora de referência '{player_name}' do clube '{club}' não encontrada. Buscando apenas por filtros.",
    "no_reference_player_info": "Nenhuma jogadora de referência informada. As recomendações serão baseadas apenas nos filtros.",
    "no_athletes_match_filters_warning": "Nenhuma atleta corresponde aos filtros selecionados. Tente ajustar os critérios.",
    "no_similar_recommendations_info": "Não foram encontradas recomendações similares para **{player_name}** com os filtros aplicados.",
    "showing_filtered_athletes_info": "Exibindo uma amostra de atletas que correspondem aos seus filtros.",
    "only_x_athletes_found_info": "Apenas {count} atletas encontradas com os filtros aplicados.",
    "no_recommendations_warning": "Não foi possível gerar recomendações com os critérios fornecidos. Tente ajustar os filtros ou o nome da jogadora de referência.",
    "developed_by": "Desenvolvido por RafaCStein",
    "data_model_error": "Erro: Dados ou modelo não carregados corretamente. Por favor, tente novamente.",
    "col_player_name": "Nome da Jogadora",
    "col_club": "Clube",
    "col_position": "Posição",
    "col_age": "Idade",
    "col_similarity": "Similaridade",
    "stats_comparison_chart_title": "Comparação de Estatísticas Chave (Valores Originais)"
}
TEXT_EN = {
    "page_title": "ProFutStat - Player Scouting",
    "header_title": "ProFutStat - Player Scouting",
    "welcome_message": "Use this tool to find players with similar performance profiles.",
    "search_criteria_header": "Search Criteria",
    "reference_player_subheader": "Reference Player (Optional)",
    "reference_player_help": "Enter the name and club of a player to find athletes with a similar profile. If not provided, the system will search based on selected filters.",
    "player_name_input": "Player Name",
    "player_name_placeholder": "Ex: Marta Vieira da Silva",
    "player_club_input": "Player's Club",
    "player_club_placeholder": "Ex: Orlando Pride",
    "profile_filters_subheader": "Profile Filters",
    "profile_filters_help": "Define filters for the search, even if you don't provide a reference player.",
    "position_multiselect": "Position(s)",
    "position_help": "Select one or more positions to filter players.",
    "min_age_input": "Minimum Age",
    "max_age_input": "Maximum Age",
    "generate_recommendations_button": "Generate Recommendations",
    "generating_spinner": "Generating recommendations, please wait...",
    "results_header": "Recommended Players",
    "recommendations_success": "Recommendations generated successfully!",
    "details_download_header": "Details and Download",
    "details_download_info": "Download full data of recommended players and their detailed statistics.",
    "download_csv_button": "Download as CSV",
    "download_csv_help": "Downloads the recommendations table in CSV format.",
    "download_excel_button": "Download as Excel",
    "download_excel_help": "Downloads the recommendations table in XLSX format.",
    "show_all_stats_expander": "Show All Statistics",
    "explain_similarity_header": "Detailed Similarity Analysis",
    "select_player_to_explain": "Select a recommended player to understand similarity:",
    "comparison_chart_title": "Statistics Comparison between {player1_name} and {player2_name}",
    "value_ref_player": "{player_name}'s Value (Processed)",
    "value_similar_player": "{player_name}'s Value (Processed)",
    "similarity_factors_header": "Key Similarity Factors",
    "most_similar_features": "The 5 most similar statistics between the players are:",
    "least_similar_features": "The 5 most different statistics between the players are:",
    "no_ref_player_for_explanation": "Please select a reference player to enable detailed similarity explanation.",
    "data_load_error": "Error loading data: {error_message}. Check the file URL or connectivity.",
    "missing_columns_error": "Expected columns missing from data file: {columns}.",
    "check_column_names_info": "Please ensure column names in your Parquet file match the expected names in the script.",
    "logo_not_found_warning": "Logo not found, continuing without it.",
    "reference_player_found_success": "Reference player found: **{player_name}** ({club})",
    "reference_player_not_found_warning": "Reference player '{player_name}' from club '{club}' not found. Searching by filters only.",
    "no_reference_player_info": "No reference player provided. Recommendations will be based on filters only.",
    "no_athletes_match_filters_warning": "No athletes match the selected filters. Try adjusting the criteria.",
    "no_similar_recommendations_info": "No similar recommendations found for **{player_name}** with the applied filters.",
    "showing_filtered_athletes_info": "Displaying a sample of athletes matching your filters.",
    "only_x_athletes_found_info": "Only {count} athletes found with the applied filters.",
    "no_recommendations_warning": "Could not generate recommendations with the provided criteria. Try adjusting filters or the reference player's name.",
    "developed_by": "Developed by RafaCStein",
    "data_model_error": "Error: Data or model not loaded correctly. Please try again.",
    "col_player_name": "Player Name",
    "col_club": "Club",
    "col_position": "Position",
    "col_age": "Age",
    "col_similarity": "Similarity",
    "stats_comparison_chart_title": "Key Statistics Comparison (Original Values)"
}
TEXT_IT = {
    "page_title": "ProFutStat - Scouting Giocatrici",
    "header_title": "ProFutStat - Scouting Giocatrici",
    "welcome_message": "Usa questo strumento per trovare giocatrici con profili di prestazione simili.",
    "search_criteria_header": "Criteri di Ricerca",
    "reference_player_subheader": "Giocatrice di Riferimento (Opzionale)",
    "reference_player_help": "Inserisci il nome e il club di una giocatrice per trovare atlete con un profilo simile. Se non fornito, il sistema cercherà in base ai filtri selezionati.",
    "player_name_input": "Nome Giocatrice",
    "player_name_placeholder": "Es: Marta Vieira da Silva",
    "player_club_input": "Club della Giocatrice",
    "player_club_placeholder": "Es: Orlando Pride",
    "profile_filters_subheader": "Filtri Profilo",
    "profile_filters_help": "Definisci i filtri per la ricerca, anche se non fornisci una giocatrice di riferimento.",
    "position_multiselect": "Posizione(i)",
    "position_help": "Seleziona una o più posizioni per filtrare le giocatrici.",
    "min_age_input": "Età Minima",
    "max_age_input": "Età Massima",
    "generate_recommendations_button": "Genera Raccomandazioni",
    "generating_spinner": "Generazione raccomandazioni, attendere prego...",
    "results_header": "Giocatrici Raccomandate",
    "recommendations_success": "Raccomandazioni generate con successo!",
    "details_download_header": "Dettagli e Download",
    "details_download_info": "Scarica i dati completi delle giocatrici raccomandate e le loro statistiche dettagliate.",
    "download_csv_button": "Scarica come CSV",
    "download_csv_help": "Scarica la tabella delle raccomandazioni in formato CSV.",
    "download_excel_button": "Scarica come Excel",
    "download_excel_help": "Scarica la tabella delle raccomandazioni in formato XLSX.",
    "show_all_stats_expander": "Mostra Tutte le Statistiche",
    "explain_similarity_header": "Analisi Dettagliata della Similarità",
    "select_player_to_explain": "Seleziona una giocatrice raccomandata per capire la similarità:",
    "comparison_chart_title": "Confronto Statistiche tra {player1_name} e {player2_name}",
    "value_ref_player": "Valore di {player_name} (Elaborato)",
    "value_similar_player": "Valore di {player_name} (Elaborato)",
    "similarity_factors_header": "Fattori Chiave di Similarità",
    "most_similar_features": "Le 5 statistiche più simili tra le giocatrici sono:",
    "least_similar_features": "Le 5 statistiche più diverse tra le giocatrici sono:",
    "no_ref_player_for_explanation": "Seleziona una giocatrice di riferimento per abilitare la spiegazione dettagliata della similarità.",
    "data_load_error": "Erro nel caricamento dei dati: {error_message}. Controlla l'URL del file o la connettività.",
    "missing_columns_error": "Colonne attese mancanti nel file di dati: {columns}.",
    "check_column_names_info": "Verifica che i nomi delle colonne nel tuo file Parquet corrispondano ai nomi attesi nello script.",
    "logo_not_found_warning": "Logo non trovato, continuo senza di esso.",
    "reference_player_found_success": "Giocatrice di riferimento trovada: **{player_name}** ({club})",
    "reference_player_not_found_warning": "Giocatrice di riferimento '{player_name}' do clube '{club}' non trovata. Ricerca solo per filtri.",
    "no_reference_player_info": "Nessuna giocatrice di riferimento fornita. Le raccomandazioni saranno basate solo sui filtri.",
    "no_athletes_match_filters_warning": "Nessuna atleta corrisponde ai filtri selezionati. Prova a regolare i criteri.",
    "no_similar_recommendations_info": "Nessuna raccomandazione simile trovada para **{player_name}** com i filtri applicati.",
    "showing_filtered_athletes_info": "Visualizzazione di um campione di atlete che corrispondono ai tuoi filtri.",
    "only_x_athletes_found_info": "Solo {count} atlete trovate con i filtri applicati.",
    "no_recommendations_warning": "Impossibile generare raccomandazioni con i criteri forniti. Prova a regolare i filtri ou o nome da giocatrice de riferimento.",
    "developed_by": "Sviluppato da RafaCStein",
    "data_model_error": "Errore: Dati ou modello non caricati correttamente. Per favore, riprova.",
    "col_player_name": "Nome Giocatrice",
    "col_club": "Club",
    "col_position": "Posizione",
    "col_age": "Età",
    "col_similarity": "Similarità",
    "stats_comparison_chart_title": "Confronto Statistiche Chiave (Valori Originali)"
}

# --- Streamlit Page Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title=TEXT_PT["page_title"], # Default to Portuguese for initial page title
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Custom CSS for Professional Styling ---
st.markdown("""
<style>
    .reportview-container {
        background: #F0F2F6;
    }
    .sidebar .sidebar-content {
        background: #FFFFFF;
        padding-top: 2rem;
    }
    .css-1d391kg { /* Main app container */
        padding: 1rem 3rem 1rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #0E1117;
        font-family: 'Montserrat', sans-serif;
    }
    .header-section {
        display: flex;
        align-items: center;
        gap: 20px; /* Space between logo and title */
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #ccc;
    }
    .stButton>button {
        background-color: #4CAF50; /* Green */
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect {
        margin-bottom: 15px;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


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
colunas_numericas_originais = [
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
    "offsides", "blockedShots", "passToAssist", "saves", "cleanSheet", "matchesStarted", "penaltyConversion", 
    "setPieceConversion", "totalAttemptAssist", "totalContest",
    "totalCross", "duelLost", "aerialLost", "attemptPenaltyMiss", "attemptPenaltyPost", "attemptPenaltyTarget",
    "totalLongBalls", "goalsConceded", "tacklesWon", "tacklesWonPercentage", "scoringFrequency", "yellowRedCards",
    "totalOwnHalfPasses", "totalOppositionHalfPasses", "totwAppearances", "expectedGoals",
    "goalKicks","ballRecovery", "appearances", "age", "player.height"
]

@st.cache_resource
def load_data_and_model(lang_text, original_numeric_cols):
    """Loads data, preprocesses, and initializes the scaler and FAISS index."""
    try:
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data_feminino.parquet')
    except Exception as e:
        st.error(lang_text["data_load_error"].format(error_message=e))
        st.stop()

    missing_columns = [col for col in original_numeric_cols if col not in df.columns]
    if missing_columns:
        st.error(lang_text["missing_columns_error"].format(columns=', '.join(missing_columns)))
        st.info(lang_text["check_column_names_info"])
        st.stop()

    # Ensure selected columns are numeric type before imputation
    for col in original_numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill NaN values with the median of each column for original columns
    df[original_numeric_cols] = df[original_numeric_cols].fillna(df[original_numeric_cols].median())

    # Handle cases where an entire column might be NaN even after median
    df[original_numeric_cols] = df[original_numeric_cols].fillna(0)

    # Replace infinite values with NaN, then fill those NaNs
    df[original_numeric_cols] = df[original_numeric_cols].replace([np.inf, -np.inf], np.nan)
    df[original_numeric_cols] = df[original_numeric_cols].fillna(0)


    # --- FEATURE ENGINEERING: Convert to per 90 minutes (p90) and apply transformations ---
    # Create a copy to work on processed features for the model, keep original df intact
    df_processed = df.copy()

    # Ensure 'minutesPlayed' is not zero to avoid division by zero
    df_processed['minutesPlayed'] = df_processed['minutesPlayed'].replace(0, 1) # Replace 0 with 1 to avoid division by zero

    # List of columns to convert to per 90 minutes
    # Exclude percentages, ratings, age, height, and already per-90 metrics like scoringFrequency
    cols_to_p90 = [
        "goals", "bigChancesCreated", "bigChancesMissed", "assists", "goalsAssistsSum",
        "accuratePasses", "inaccuratePasses", "totalPasses", "keyPasses", "successfulDribbles",
        "tackles", "interceptions", "yellowCards", "redCards", "accurateCrosses",
        "totalShots", "shotsOnTarget", "shotsOffTarget", "groundDuelsWon", "aerialDuelsWon", "totalDuelsWon",
        "penaltiesTaken", "penaltyGoals", "shotFromSetPiece", "freeKickGoal",
        "goalsFromInsideTheBox", "goalsFromOutsideTheBox", "shotsFromInsideTheBox", "shotsFromOutsideTheBox",
        "headedGoals", "leftFootGoals", "rightFootGoals", "accurateLongBalls", "clearances", "errorLeadToGoal",
        "errorLeadToShot", "dispossessed", "possessionLost", "possessionWonAttThird", "totalChippedPasses",
        "accurateChippedPasses", "touches", "wasFouled", "fouls", "hitWoodwork", "ownGoals", "dribbledPast",
        "offsides", "blockedShots", "passToAssist", "cleanSheet", "penaltyFaced", 
         "totalAttemptAssist", "totalContest", "totalCross", "duelLost", "aerialLost", "totalLongBalls", "goalsConceded", "tacklesWon",
        "totalOwnHalfPasses", "totalOppositionHalfPasses", "expectedGoals",
        "goalKicks", "ballRecovery"
    ]

    # New list of features to be used by the model
    features_for_model = []

    for col in original_numeric_cols:
        if col in cols_to_p90:
            new_col_name = f"{col}_p90"
            df_processed[new_col_name] = (df_processed[col] / df_processed['minutesPlayed']) * 90
            features_for_model.append(new_col_name)
        elif "Percentage" in col or col in ["rating", "totalRating", "countRating", "age", "player.height", "matchesStarted", "totwAppearances", "appearances", "scoringFrequency", "penaltyConversion", "setPieceConversion"]:
            # Keep percentages, ratings, age, height, matchesStarted, appearances as is
            features_for_model.append(col)
        # Exclude minutesPlayed itself, as it's used for normalization

    # Optional: Apply log transform to some p90 features that might still have skewed distributions
    # Example (adjust based on your data distribution):
    # for col in ["goals_p90", "assists_p90", "shots_p90", "keyPasses_p90"]:
    #    if col in features_for_model: # Ensure the p90 column exists
    #        df_processed[col] = np.log1p(df_processed[col])

    # Apply PowerTransformer to all features for model after p90 conversion
    # This helps in handling skewed data better than just StandardScaler
    # Use float64 for PowerTransformer input to avoid overflow issues during transformation
    power_transformer = PowerTransformer(method='yeo-johnson') # Yeo-Johnson handles zeros and negative values
    try:
        X_processed = power_transformer.fit_transform(df_processed[features_for_model].astype(np.float64))
    except ValueError as e:
        st.error(f"Erro ao aplicar PowerTransformer: {e}. Isso pode ocorrer se uma coluna tiver todos os valores iguais.")
        # Fallback to StandardScaler if PowerTransformer fails
        st.warning("Voltando para StandardScaler. Verifique se há colunas com valores constantes.")
        scaler = StandardScaler()
        X_processed = scaler.fit_transform(df_processed[features_for_model].astype(np.float64))
        # Keep track of the actual scaler used
        st.session_state['transformer_used'] = scaler
    else:
        # If PowerTransformer was successful, save it
        st.session_state['transformer_used'] = power_transformer

    # Now apply StandardScaler for final scaling
    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(X_processed)
    
    # --- L2 Normalization for Cosine Similarity (as you had) ---
    normalizer = Normalizer(norm='l2')
    dados_normalizados = normalizer.fit_transform(dados_normalizados)
    dados_normalizados = dados_normalizados.astype('float32') # FAISS requires float32

    dimension = dados_normalizados.shape[1]
    index = faiss.IndexFlatIP(dimension) # IndexFlatIP for cosine similarity
    index.add(dados_normalizados)

    # Store the actual features used for the model, and the original features for comparison
    return df, scaler, index, dados_normalizados, features_for_model, df_processed

# Pass current_lang_text and colunas_numericas_originais to the cached function
# Note: df_processed is also returned now, it contains the _p90 features
df, scaler, faiss_index, dados_normalizados, features_for_model, df_processed = load_data_and_model(current_lang_text, colunas_numericas_originais)

# --- Recommendation Function Adapted for Streamlit ---

def recommend_players_advanced(name=None, club=None, top_n=10, position=None,
                                 min_age=None, max_age=None, lang_text=TEXT_PT):
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
            player_ref_name = df.loc[player_id, 'player.name']
            player_ref_club = df.loc[player_id, 'player.team.name']
            st.success(lang_text["reference_player_found_success"].format(player_name=player_ref_name, club=player_ref_club))
            
            # If no position is explicitly selected, use the reference player's position
            if not position: # Check if position list is empty
                position = [df.loc[player_id, 'position']]
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
        # Use the processed data for querying FAISS
        query_vector = dados_normalizados[df.index.get_loc(player_id)].reshape(1, -1)
        
        # Search in the FAISS index with a larger number of results to filter later
        D, I = faiss_index.search(query_vector, max(top_n * 5, len(filtered_indices) + 1)) 

        similarities = D[0]
        returned_indices = I[0]
        
        recommendations_raw = pd.DataFrame({
            'original_index': returned_indices,
            'similaridade': similarities
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
        recommendations_df = df.loc[final_recommendations['original_index']].copy()
        
        # Now, map the similarity scores to the correct players in recommendations_df
        recommendations_df['similaridade'] = recommendations_df.index.map(
            final_recommendations.set_index('original_index')['similaridade']
        )
        
    else:
        st.info(lang_text["showing_filtered_athletes_info"])
        if len(filtered_indices) < top_n:
            st.info(lang_text["only_x_athletes_found_info"].format(count=len(filtered_indices)))
        
        # If no reference player, just show a sample of filtered players
        recommendations_df = df.loc[filtered_indices].sample(n=min(top_n, len(filtered_indices)), random_state=42).copy()
        recommendations_df['similaridade'] = np.nan
    
    # --- Prepare full DataFrame for download (BEFORE any display formatting) ---
    recommendations_for_download = recommendations_df.copy()

    # --- Formatting for UI Display ONLY ---
    if 'age' in recommendations_df.columns:
        recommendations_df['age'] = recommendations_df['age'].apply(lambda x: int(x) if pd.notna(x) else x)

    if player_id is not None and 'similaridade' in recommendations_df.columns:
        recommendations_df['similaridade'] = recommendations_df['similaridade'].apply(lambda x: f"{max(0, min(100, x * 100)):.0f}%")
    
    recommendations_display = recommendations_df.rename(columns={
        'player.name': lang_text['col_player_name'],
        'player.team.name': lang_text['col_club'],
        'position': lang_text['col_position'],
        'age': lang_text['col_age'],
        'similaridade': lang_text['col_similarity']
    })

    cols_display_final = [lang_text['col_player_name'], lang_text['col_club'],
                          lang_text['col_position'], lang_text['col_age']]
    if player_id is not None:
        cols_display_final.append(lang_text['col_similarity'])
    
    return recommendations_display[cols_display_final].sort_values(by=lang_text['col_similarity'], ascending=False, na_position='last').reset_index(drop=True), recommendations_for_download, player_id

# --- Function to display detailed similarity analysis ---
def display_detailed_similarity(ref_player_id, selected_similar_player_original_index,
                                df_original, df_processed_data, numeric_features_for_model, scaler_model, lang_text):
    """
    Displays a detailed comparison and explanation of similarity between two players.
    Uses original and processed data for better insights.
    """
    if ref_player_id is None:
        st.warning(lang_text["no_ref_player_for_explanation"])
        return

    ref_player_data_original = df_original.loc[ref_player_id]
    similar_player_data_original = df_original.loc[selected_similar_player_original_index]

    ref_player_name = ref_player_data_original['player.name']
    similar_player_name = similar_player_data_original['player.name']

    st.subheader(lang_text["comparison_chart_title"].format(player1_name=ref_player_name, player2_name=similar_player_name))

    # --- Bar Chart for Selected Key Statistics (using ORIGINAL values for clarity) ---
    selected_stats_for_comparison = [
        "minutesPlayed", "appearances", "goals", "assists", "totalDuelsWon",
        "shotsOnTarget", "tackles", "accuratePasses", "accurateLongBalls"
    ]

    # Filter to only include stats that exist in the original dataframe
    available_stats = [stat for stat in selected_stats_for_comparison if stat in df_original.columns]
    
    if not available_stats:
        st.warning("Nenhuma das estatísticas chave selecionadas está disponível para comparação.")
        return

    comparison_data = {
        'Estatística': [],
        'Valor': [],
        'Jogador': []
    }

    for stat in available_stats:
        comparison_data['Estatística'].append(stat)
        comparison_data['Valor'].append(ref_player_data_original[stat])
        comparison_data['Jogador'].append(ref_player_name)

        comparison_data['Estatística'].append(stat)
        comparison_data['Valor'].append(similar_player_data_original[stat])
        comparison_data['Jogador'].append(similar_player_name)
    
    comparison_df = pd.DataFrame(comparison_data)

    fig_bar_comparison = px.bar(
        comparison_df,
        x='Estatística',
        y='Valor',
        color='Jogador',
        barmode='group',
        title=lang_text["stats_comparison_chart_title"],
        labels={'Estatística': 'Estatística', 'Valor': 'Valor (Original)'}
    )
    st.plotly_chart(fig_bar_comparison, use_container_width=True)


    st.subheader(lang_text["similarity_factors_header"])

    # Ensure transformer_used is available in session state if it was stored
    transformer = st.session_state.get('transformer_used', None)
    if transformer is None:
        st.error("Erro: Transformer não encontrado na sessão. Recarregue a página.")
        return

    # Use df_processed_data for feature transformation
    ref_vector_pre_normalizer = transformer.transform(df_processed_data.loc[ref_player_id, numeric_features_for_model].values.reshape(1, -1))
    ref_vector_pre_normalizer = scaler_model.transform(ref_vector_pre_normalizer)[0] # Apply StandardScaler

    similar_vector_pre_normalizer = transformer.transform(df_processed_data.loc[selected_similar_player_original_index, numeric_features_for_model].values.reshape(1, -1))
    similar_vector_pre_normalizer = scaler_model.transform(similar_vector_pre_normalizer)[0] # Apply StandardScaler

    # Calculate absolute differences of the *scaled* features for contribution analysis
    # Using absolute difference directly for easier interpretation of "similarity"
    abs_diff_scaled = np.abs(ref_vector_pre_normalizer - similar_vector_pre_normalizer)
    feature_differences_scaled = pd.Series(abs_diff_scaled, index=numeric_features_for_model)

    # Sort by smallest difference (most similar)
    sorted_differences_scaled = feature_differences_scaled.sort_values(ascending=True)

    st.write(lang_text["most_similar_features"])
    st.markdown("_(Baseado nas estatísticas processadas para o modelo - **Menor diferença absoluta indica maior similaridade**)_")
    for feature, diff_val in sorted_differences_scaled.head(5).items(): # Top 5 most similar
        st.write(f"- **{feature}** (diferença absoluta: {diff_val:.4f}):")
        st.write(f"  - {lang_text['value_ref_player'].format(player_name=ref_player_name)}: {df_processed_data.loc[ref_player_id, feature]:.2f}")
        st.write(f"  - {lang_text['value_similar_player'].format(player_name=similar_player_name)}: {df_processed_data.loc[selected_similar_player_original_index, feature]:.2f}")
        # Add original value if different from processed (e.g., if p90)
        if feature.endswith('_p90'):
             original_feat_name = feature.replace('_p90', '')
             if original_feat_name in ref_player_data_original and original_feat_name in similar_player_data_original:
                st.write(f"  - _Original: {ref_player_data_original[original_feat_name]:.2f} vs {similar_player_data_original[original_feat_name]:.2f}_")


    st.write(lang_text["least_similar_features"])
    st.markdown("_(Baseado nas estatísticas processadas para o modelo - **Maior diferença absoluta indica menor similaridade**)_")
    for feature, diff_val in sorted_differences_scaled.tail(5).items(): # Top 5 least similar
        st.write(f"- **{feature}** (diferença absoluta: {diff_val:.4f}):")
        st.write(f"  - {lang_text['value_ref_player'].format(player_name=ref_player_name)}: {df_processed_data.loc[ref_player_id, feature]:.2f}")
        st.write(f"  - {lang_text['value_similar_player'].format(player_name=similar_player_name)}: {df_processed_data.loc[selected_similar_player_original_index, feature]:.2f}")
        # Add original value if different from processed (e.g., if p90)
        if feature.endswith('_p90'):
            original_feat_name = feature.replace('_p90', '')
            if original_feat_name in ref_player_data_original and original_feat_name in similar_player_data_original:
                st.write(f"  - _Original: {ref_player_data_original[original_feat_name]:.2f} vs {similar_player_data_original[original_feat_name]:.2f}_")

    # Bar chart for absolute differences of SCALED features
    fig_bar_diff_scaled = px.bar(
        x=sorted_differences_scaled.index,
        y=sorted_differences_scaled.values,
        title=f'Diferença Absoluta das Estatísticas (Processado) entre {ref_player_name} e {similar_player_name}',
        labels={'x': 'Estatística', 'y': 'Diferença Absoluta (Processado)'},
        color=sorted_differences_scaled.values,
        color_continuous_scale=px.colors.sequential.Plasma_r # Invert color scale for better viz
    )
    fig_bar_diff_scaled.update_layout(xaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar_diff_scaled, use_container_width=True)


# --- Streamlit Application Layout (continuation) ---

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
            lang_text=current_lang_text
        )
        
        st.session_state['recommendations_display'] = recommendations_display
        st.session_state['complete_recommendations'] = complete_recommendations
        st.session_state['reference_player_idx_found'] = reference_player_idx_found
        st.session_state['search_executed'] = True
        st.session_state['current_lang_text'] = current_lang_text

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

        st.markdown("### " + current_lang_text_session["details_download_header"])
        st.info(current_lang_text_session["details_download_info"])
        
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

        if reference_player_idx_found is not None:
            st.markdown("---")
            st.header(current_lang_text_session["explain_similarity_header"])
            
            player_names_for_selection = {
                idx: complete_recommendations.loc[idx, 'player.name']
                for idx in complete_recommendations.index
            }
            
            selected_player_name_for_explanation = st.selectbox(
                current_lang_text_session["select_player_to_explain"],
                options=list(player_names_for_selection.values()),
                key='explanation_player_select'
            )

            selected_similar_player_original_index = None
            for idx, name in player_names_for_selection.items():
                if name == selected_player_name_for_explanation:
                    selected_similar_player_original_index = idx
                    break

            if selected_similar_player_original_index is not None:
                display_detailed_similarity(
                    ref_player_id=reference_player_idx_found,
                    selected_similar_player_original_index=selected_similar_player_original_index,
                    df_original=df, # Pass original df
                    df_processed_data=df_processed, # Pass processed df
                    numeric_features_for_model=features_for_model, # Pass the list of features used in the model
                    scaler_model=scaler, # Pass the scaler model
                    lang_text=current_lang_text_session
                )
            else:
                st.warning("Selecione uma jogadora válida para a explicação.")
        else:
            st.info(current_lang_text_session["no_ref_player_for_explanation"])

    else:
        st.warning(current_lang_text_session["no_recommendations_warning"])
else:
    st.info("Aguardando critérios de busca para gerar recomendações.")


st.markdown("---")
st.write(current_lang_text["developed_by"])
