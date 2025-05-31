import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, Normalizer, PowerTransformer # Importar PowerTransformer
import faiss
import streamlit as st
from fuzzywuzzy import fuzz
import io
import plotly.express as px

# --- Multilingual Text Strings (as provided in your script) ---
# ... (TEXT_PT, TEXT_EN, TEXT_IT definitions) ...

# --- Streamlit Page Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title=TEXT_PT["page_title"], # Default to Portuguese for initial page title
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Custom CSS for Professional Styling (as provided in your script) ---
# ... (st.markdown for CSS) ...

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
# Define `colunas_numericas_originais` (as provided in your script)
colunas_numericas_originais = [
    "rating", "totalRating", "countRating", "goals", "bigChancesCreated", "bigChancesMissed", "assists",
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
    "offsides", "blockedShots", "passToAssist", "saves", "cleanSheet", "penaltyFaced", "penaltySave",
    "savedShotsFromInsideTheBox", "savedShotsFromOutsideTheBox", "goalsConcededInsideTheBox",
    "goalsConcededOutsideTheBox", "punches", "runsOut", "successfulRunsOut", "highClaims", "crossesNotClaimed",
    "matchesStarted", "penaltyConversion", "setPieceConversion", "totalAttemptAssist", "totalContest",
    "totalCross", "duelLost", "aerialLost", "attemptPenaltyMiss", "attemptPenaltyPost", "attemptPenaltyTarget",
    "totalLongBalls", "goalsConceded", "tacklesWon", "tacklesWonPercentage", "scoringFrequency", "yellowRedCards",
    "savesCaught", "savesParried", "totalOwnHalfPasses", "totalOppositionHalfPasses", "totwAppearances", "expectedGoals",
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
        "tackles", "interceptions", "yellowCards", "directRedCards", "redCards", "accurateCrosses",
        "totalShots", "shotsOnTarget", "shotsOffTarget", "groundDuelsWon", "aerialDuelsWon", "totalDuelsWon",
        "penaltiesTaken", "penaltyGoals", "penaltyWon", "penaltyConceded", "shotFromSetPiece", "freeKickGoal",
        "goalsFromInsideTheBox", "goalsFromOutsideTheBox", "shotsFromInsideTheBox", "shotsFromOutsideTheBox",
        "headedGoals", "leftFootGoals", "rightFootGoals", "accurateLongBalls", "clearances", "errorLeadToGoal",
        "errorLeadToShot", "dispossessed", "possessionLost", "possessionWonAttThird", "totalChippedPasses",
        "accurateChippedPasses", "touches", "wasFouled", "fouls", "hitWoodwork", "ownGoals", "dribbledPast",
        "offsides", "blockedShots", "passToAssist", "saves", "cleanSheet", "penaltyFaced", "penaltySave",
        "savedShotsFromInsideTheBox", "savedShotsFromOutsideTheBox", "goalsConcededInsideTheBox",
        "goalsConcededOutsideTheBox", "punches", "runsOut", "successfulRunsOut", "highClaims", "crossesNotClaimed",
        "totalAttemptAssist", "totalContest", "totalCross", "duelLost", "aerialLost", "attemptPenaltyMiss",
        "attemptPenaltyPost", "attemptPenaltyTarget", "totalLongBalls", "goalsConceded", "tacklesWon",
        "savesCaught", "savesParried", "totalOwnHalfPasses", "totalOppositionHalfHalfPasses", "expectedGoals",
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

    # --- Radar Chart using processed (p90 and transformed) values for conceptual comparison ---
    # Retrieve the processed (p90/transformed) data for the radar chart
    ref_player_data_model = df_processed_data.loc[ref_player_id]
    similar_player_data_model = df_processed_data.loc[selected_similar_player_original_index]

    # Select only the features actually used in the model
    radar_df_comparison_model = pd.DataFrame({
        'Estatística': numeric_features_for_model,
        lang_text["value_ref_player"].format(player_name=ref_player_name): ref_player_data_model[numeric_features_for_model].values,
        lang_text["value_similar_player"].format(player_name=similar_player_name): similar_player_data_model[numeric_features_for_model].values
    })

    radar_melted_df_model = radar_df_comparison_model.melt(id_vars=['Estatística'], var_name='Jogador', value_name='Valor')

    fig_radar_model = px.line_polar(radar_melted_df_model, r='Valor', theta='Estatística', line_close=True,
                                    color='Jogador', markers=True,
                                    title=f'Comparação de Perfis de Estatísticas (Normalizadas/Processadas)')
    st.plotly_chart(fig_radar_model, use_container_width=True)

    st.subheader(lang_text["similarity_factors_header"])

    # --- Explanation using ORIGINAL values for direct comparison ---
    # This is critical for professionals to understand the "raw" differences
    
    # For cosine similarity, looking at the absolute difference of the *scaled* features
    # that went into FAISS is more direct for "contribution".
    # However, for business users, comparing original values is more intuitive.
    # We'll calculate contribution based on the features *before* the final L2 normalization,
    # but after StandardScaler (or PowerTransformer + StandardScaler)
    
    # Get the vectors that were scaled by StandardScaler (or PowerTransformer + StandardScaler)
    # This requires running the transformation pipeline again for these two specific players
    
    # Ensure transformer_used is available in session state if it was stored
    transformer = st.session_state.get('transformer_used', None)
    if transformer is None:
        st.error("Erro: Transformer não encontrado na sessão. Recarregue a página.")
        return

    # Transform original data for these two players using the stored transformer (PowerTransformer/StandardScaler)
    ref_vector_pre_normalizer = transformer.transform(ref_player_data_original[numeric_features_for_model].values.reshape(1, -1))
    ref_vector_pre_normalizer = scaler_model.transform(ref_vector_pre_normalizer)[0] # Apply StandardScaler

    similar_vector_pre_normalizer = transformer.transform(similar_player_data_original[numeric_features_for_model].values.reshape(1, -1))
    similar_vector_pre_normalizer = scaler_model.transform(similar_vector_pre_normalizer)[0] # Apply StandardScaler


    # Calculate squared differences of the *scaled* features for contribution analysis
    diff_squared_scaled = (ref_vector_pre_normalizer - similar_vector_pre_normalizer)**2
    feature_contributions_scaled = pd.Series(diff_squared_scaled, index=numeric_features_for_model)

    # Sort by smallest difference (most similar)
    sorted_contributions_scaled = feature_contributions_scaled.sort_values(ascending=True)

    st.write(lang_text["most_similar_features"])
    st.markdown("_(Baseado nas estatísticas processadas para o modelo)_")
    for feature, contribution in sorted_contributions_scaled.head(5).items(): # Top 5 most similar
        st.write(f"- **{feature}** (contribuição: {contribution:.4f}):")
        st.write(f"  - {lang_text['value_ref_player'].format(player_name=ref_player_name)}: {df_processed_data.loc[ref_player_id, feature]:.2f}")
        st.write(f"  - {lang_text['value_similar_player'].format(player_name=similar_player_name)}: {df_processed_data.loc[selected_similar_player_original_index, feature]:.2f}")
        # Optional: Add original value if different from processed (e.g., if p90)
        if feature.endswith('_p90'):
             original_feat_name = feature.replace('_p90', '')
             st.write(f"  - _Original: {ref_player_data_original[original_feat_name]:.2f} vs {similar_player_data_original[original_feat_name]:.2f}_")


    st.write(lang_text["least_similar_features"])
    st.markdown("_(Baseado nas estatísticas processadas para o modelo)_")
    for feature, contribution in sorted_contributions_scaled.tail(5).items(): # Top 5 least similar
        st.write(f"- **{feature}** (contribuição: {contribution:.4f}):")
        st.write(f"  - {lang_text['value_ref_player'].format(player_name=ref_player_name)}: {df_processed_data.loc[ref_player_id, feature]:.2f}")
        st.write(f"  - {lang_text['value_similar_player'].format(player_name=similar_player_name)}: {df_processed_data.loc[selected_similar_player_original_index, feature]:.2f}")
        # Optional: Add original value if different from processed (e.g., if p90)
        if feature.endswith('_p90'):
            original_feat_name = feature.replace('_p90', '')
            st.write(f"  - _Original: {ref_player_data_original[original_feat_name]:.2f} vs {similar_player_data_original[original_feat_name]:.2f}_")

    # Bar chart for squared differences of SCALED features
    fig_bar_diff_scaled = px.bar(
        x=sorted_contributions_scaled.index,
        y=sorted_contributions_scaled.values,
        title=f'Contribuição das Estatísticas (Diferença Quadrática) para a Similaridade entre {ref_player_name} e {similar_player_name}',
        labels={'x': 'Estatística', 'y': 'Diferença Quadrática (Processado)'},
        color=sorted_contributions_scaled.values,
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
