import streamlit as st # Make sure this is one of the first lines
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, Normalizer
import faiss
from fuzzywuzzy import fuzz
import io

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="PlayerScout IA",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- CSS Customizado para Estilo Profissional ---

# --- Carregamento de Dados e Inicialização do Modelo (Cacheado para Performance) ---
@st.cache_resource # Now 'st' is defined when Python reads this line
def load_data_and_model():
    # ... rest of your function
    try:
        df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet')
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de dados. Por favor, verifique o link ou a conexão: {e}")
        st.stop()
    # ... (the rest of your script)

# --- Carregamento de Dados e Inicialização do Modelo (Cacheado) ---
@st.cache_resource
def load_data_and_model():
    # ... (como antes, mas garantir que todas as colunas usadas para benchmarking/filtros estejam aqui) ...
    # Adicionar uma cópia do DF original antes da normalização para cálculos de benchmark
    df_original = df.copy()
    # ... (scaler, normalizer, FAISS index) ...
    return df, df_original, scaler, index, dados_normalizados, colunas_numericas # Retornar df_original e colunas_numericas

df, df_original, scaler, faiss_index, dados_normalizados, colunas_numericas_disponiveis = load_data_and_model()

# --- Função de Benchmarking ---
def gerar_benchmark_atleta(atleta_id_ref, df_comparacao, metricas_benchmark):
    """
    Gera dados de benchmarking para um atleta em relação a um DataFrame de comparação.
    """
    if atleta_id_ref is None or atleta_id_ref not in df_original.index:
        return pd.DataFrame()

    atleta_stats = df_original.loc[atleta_id_ref][metricas_benchmark]
    
    benchmark_data = {}
    for metrica in metricas_benchmark:
        if metrica in df_comparacao.columns:
            desc = df_comparacao[metrica].describe(percentiles=[.25, .5, .75, .9])
            benchmark_data[metrica] = {
                'Jogador': atleta_stats.get(metrica, np.nan),
                'Média Grupo': desc.get('mean', np.nan),
                'Mediana Grupo (50%)': desc.get('50%', np.nan),
                '25%': desc.get('25%', np.nan),
                '75%': desc.get('75%', np.nan),
                '90%': desc.get('90%', np.nan)
            }
    return pd.DataFrame(benchmark_data).T.reset_index().rename(columns={'index': 'Métrica'})


# --- Função de Recomendação e Filtragem Adaptada ---
def encontrar_atletas(nome_ref=None, clube_ref=None, top_n=10, posicoes_desejadas=None,
                      idade_min=None, idade_max=None,
                      valor_min=None, valor_max=None,
                      filtros_estatisticos=None, # Novo: dict com {'metrica': (min_val, max_val)}
                      strict_posicao_ref=True):
    # ... (lógica para encontrar atleta de referência como antes) ...
    # atleta_id, atleta_ref_info = encontrar_jogador_referencia(nome_ref, clube_ref)

    mascara_filtros = pd.Series(True, index=df.index)
    
    # Filtros existentes
    if posicoes_desejadas:
        mascara_filtros &= df['position'].isin(posicoes_desejadas)
    # ... (idade, valor) ...

    # NOVO: Aplicar filtros estatísticos avançados
    if filtros_estatisticos:
        for metrica, (min_val, max_val) in filtros_estatisticos.items():
            if metrica in df.columns:
                if min_val is not None:
                    mascara_filtros &= (df[metrica] >= min_val)
                if max_val is not None:
                    mascara_filtros &= (df[metrica] <= max_val)
            else:
                st.warning(f"Métrica de filtro '{metrica}' não encontrada nos dados.")

    indices_filtrados_inicial = df[mascara_filtros].index.tolist()

    if not indices_filtrados_inicial:
        st.warning("Nenhum atleta corresponde aos filtros gerais/estatísticos. Tente ajustar.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame() # DF de exibição, DF completo, DF benchmark

    df_atletas_filtrados = df.loc[indices_filtrados_inicial]
    
    # Lógica de Similaridade (se atleta de referência foi encontrado)
    recomendacoes_df = pd.DataFrame()
    atleta_ref_dados = None

    if atleta_id is not None: # Se um atleta de referência foi encontrado
        # ... (lógica FAISS para encontrar similares como antes, mas usando df_atletas_filtrados para refinar)
        # Garantir que o atleta de referência não esteja nas recomendações e aplicar top_n
        # Adicionar coluna de similaridade
        query_vector = dados_normalizados[df.index.get_loc(atleta_id)].reshape(1, -1)
        
        # Busca inicial em todo o dataset para obter os vetores mais próximos
        # Aumentar k para ter mais candidatos antes de filtrar
        num_candidatos_brutos = max(top_n * 10, len(df) // 100, 100) # Heurística
        
        D_bruto, I_bruto = faiss_index.search(query_vector, num_candidatos_brutos)
        
        similares_brutos_indices = I_bruto[0]
        similares_brutos_scores = D_bruto[0]

        # Criar DataFrame temporário com os resultados brutos da similaridade
        df_similares_brutos = pd.DataFrame({
            'original_index': df.index[similares_brutos_indices], # Mapear para o índice original do df
            'similaridade': similares_brutos_scores
        }).set_index('original_index')

        # Agora, filtramos esses resultados brutos com a máscara de filtros
        # e removemos o próprio atleta de referência
        indices_finais_recomendados = df_similares_brutos.index.intersection(df_atletas_filtrados.index)
        indices_finais_recomendados = indices_finais_recomendados.drop(atleta_id, errors='ignore')

        # Pegar os top_n após a filtragem
        recomendacoes_finais_df = df_similares_brutos.loc[indices_finais_recomendados].sort_values(
            by='similaridade', ascending=False
        ).head(top_n)

        if recomendacoes_finais_df.empty:
            st.info(f"Nenhuma recomendação similar a **{atleta_ref_info['player.name']}** encontrada com os filtros aplicados.")
            # Se não houver similares, mas houver filtros, podemos mostrar jogadores filtrados
            if not df_atletas_filtrados.empty:
                 st.info("Mostrando atletas que atendem apenas aos filtros (sem similaridade).")
                 recomendacoes_df = df_atletas_filtrados.sample(n=min(top_n, len(df_atletas_filtrados)), random_state=42).copy()
                 recomendacoes_df['similaridade'] = np.nan # Indicar que não é por similaridade direta
            else:
                 return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        else:
            recomendacoes_df = df.loc[recomendacoes_finais_df.index].copy()
            recomendacoes_df['similaridade'] = recomendacoes_finais_df['similaridade'].values
            atleta_ref_dados = df_original.loc[[atleta_id]] # Para benchmarking

    else: # Se nenhum atleta de referência, apenas filtrar
        st.info("Mostrando atletas que atendem aos filtros. Para recomendações por similaridade, forneça um atleta de referência.")
        if len(df_atletas_filtrados) < top_n:
            st.info(f"Apenas {len(df_atletas_filtrados)} atletas encontrados com os filtros, mostrando todos.")
        
        recomendacoes_df = df_atletas_filtrados.sample(n=min(top_n, len(df_atletas_filtrados)), random_state=42).copy()
        recomendacoes_df['similaridade'] = np.nan # Indicar que não é por similaridade

    # Preparar DataFrame para download (antes da formatação de exibição)
    recomendacoes_para_download = recomendacoes_df.copy()

    # Formatação para exibição (como antes)
    # ... (idade, valor, similaridade) ...
    # ... (renomear colunas) ...
    
    # Gerar dados de Benchmarking (se aplicável)
    benchmark_results_df = pd.DataFrame()
    if atleta_id is not None and 'metricas_benchmark_selecionadas' in st.session_state and st.session_state.metricas_benchmark_selecionadas:
        # Definir o grupo de comparação para o benchmark (ex: mesma posição do atleta de referência)
        pos_ref = df_original.loc[atleta_id, 'position']
        df_grupo_comparacao = df_original[df_original['position'] == pos_ref]
        
        benchmark_results_df = gerar_benchmark_atleta(atleta_id, df_grupo_comparacao, st.session_state.metricas_benchmark_selecionadas)

    return recomendacoes_exibicao, recomendacoes_para_download, benchmark_results_df


# --- Layout da Aplicação Streamlit ---
# ... (cabeçalho como antes) ...

st.sidebar.header("Opções de Análise")
analise_modo = st.sidebar.radio("Selecione o modo:", ("Busca de Jogadores", "Benchmarking de Jogador"))

if analise_modo == "Busca de Jogadores":
    st.header("🔎 Busca Avançada de Jogadores")
    # ... (inputs de atleta de referência, posição, idade, valor como antes) ...

    with st.expander("Filtros Estatísticos Avançados (Opcional)"):
        st.markdown("Adicione filtros baseados em estatísticas específicas.")
        # Selecionar métricas para filtrar
        metricas_para_filtro = st.multiselect(
            "Selecione métricas para filtrar:",
            options=sorted([col for col in colunas_numericas_disponiveis if col not in ['age', 'player.proposedMarketValue']]), # Exclui as já filtradas
            key="metricas_filtro_avancado"
        )
        
        filtros_estatisticos_input = {}
        if metricas_para_filtro:
            cols_metricas = st.columns(len(metricas_para_filtro))
            for i, metrica in enumerate(metricas_para_filtro):
                with cols_metricas[i]:
                    st.markdown(f"**{metrica}**")
                    # Verificando tipo de dado para melhor input
                    is_percentage = "Percentage" in metrica or "Conversion" in metrica
                    is_rating = "rating" in metrica.lower()

                    if is_percentage:
                        min_val = st.number_input(f"Min {metrica}", value=0.0, min_value=0.0, max_value=100.0, step=1.0, key=f"min_{metrica}", format="%.1f")
                        max_val = st.number_input(f"Max {metrica}", value=100.0, min_value=0.0, max_value=100.0, step=1.0, key=f"max_{metrica}", format="%.1f")
                    elif is_rating:
                        min_val = st.number_input(f"Min {metrica}", value=0.0, min_value=0.0, max_value=10.0, step=0.1, key=f"min_{metrica}", format="%.1f")
                        max_val = st.number_input(f"Max {metrica}", value=10.0, min_value=0.0, max_value=10.0, step=0.1, key=f"max_{metrica}", format="%.1f")
                    else: # Outras métricas numéricas
                        default_min = df_original[metrica].min() if not df_original[metrica].empty else 0.0
                        default_max = df_original[metrica].max() if not df_original[metrica].empty else 100.0
                        step_val = 1.0 if df_original[metrica].dtype == 'int64' else 0.1

                        min_val = st.number_input(f"Min {metrica}", value=default_min, step=step_val, key=f"min_{metrica}")
                        max_val = st.number_input(f"Max {metrica}", value=default_max, step=step_val, key=f"max_{metrica}")
                    
                    # Armazenar apenas se o usuário realmente quer filtrar por isso (ex: se min != default_min ou max != default_max)
                    # Para simplificar, vamos pegar todos os valores definidos
                    filtros_estatisticos_input[metrica] = (min_val if min_val != (df_original[metrica].min() if not df_original[metrica].empty else 0.0) else None, 
                                                           max_val if max_val != (df_original[metrica].max() if not df_original[metrica].empty else 100.0) else None)
                    # Filtrar Nones se ambos forem None
                    if filtros_estatisticos_input[metrica] == (None, None):
                        del filtros_estatisticos_input[metrica]


    if st.button("🔎 Encontrar Jogadores", type="primary"):
        with st.spinner("Analisando dados e buscando jogadores..."):
            recomendacoes_display, recomendacoes_completas, _ = encontrar_atletas(
                nome_ref=nome_atleta if nome_atleta else None,
                clube_ref=clube_atleta if clube_atleta else None,
                posicoes_desejadas=posicao_selecionada,
                idade_min=idade_min_val,
                idade_max=idade_max_val,
                valor_min=valor_min_val,
                valor_max=valor_max_val,
                filtros_estatisticos=filtros_estatisticos_input,
                top_n=15 # Aumentar um pouco o top_n padrão
            )
            # ... (exibição dos resultados e download como antes) ...

elif analise_modo == "Benchmarking de Jogador":
    st.header("📊 Benchmarking de Jogador")
    st.markdown("Compare um jogador com seus pares com base em métricas selecionadas.")

    nome_atleta_bench = st.text_input("Nome do Atleta para Benchmarking", placeholder="Ex: Kevin De Bruyne").strip()
    clube_atleta_bench = st.text_input("Clube do Atleta para Benchmarking", placeholder="Ex: Manchester City").strip()

    if nome_atleta_bench and clube_atleta_bench:
        # Encontrar o atleta
        df_temp_bench = df_original.copy()
        df_temp_bench['temp_sim_nome'] = df_temp_bench['player.name'].apply(lambda x: fuzz.token_set_ratio(nome_atleta_bench, x))
        df_temp_bench['temp_sim_clube'] = df_temp_bench['player.team.name'].apply(lambda x: fuzz.token_set_ratio(clube_atleta_bench, x))
        df_temp_bench['temp_sim_combinada'] = 0.7 * df_temp_bench['temp_sim_nome'] + 0.3 * df_temp_bench['temp_sim_clube']
        
        melhor_match_bench = df_temp_bench.nlargest(1, 'temp_sim_combinada')
        
        atleta_id_bench = None
        if not melhor_match_bench.empty and melhor_match_bench['temp_sim_combinada'].iloc[0] >= 75: # Confiança um pouco menor ok para benchmark
            atleta_id_bench = melhor_match_bench.index[0]
            atleta_ref_bench = df_original.loc[atleta_id_bench]
            st.success(f"Jogador para Benchmarking: **{atleta_ref_bench['player.name']}** ({atleta_ref_bench['player.team.name']})")
            st.info(f"Posição: {atleta_ref_bench['position']} | Idade: {int(atleta_ref_bench['age'])} | Valor: ${atleta_ref_bench['player.proposedMarketValue'] / 1_000_000:.2f}M")
        else:
            st.error(f"Atleta '{nome_atleta_bench}' do clube '{clube_atleta_bench}' não encontrado com confiança suficiente.")
            atleta_id_bench = None

        if atleta_id_bench is not None:
            # Seleção de métricas para o benchmark
            metricas_padrao_benchmark = [
                "rating", "goals", "assists", "accuratePassesPercentage", "keyPasses", 
                "successfulDribblesPercentage", "tackles", "interceptions", "totalDuelsWonPercentage", "minutesPlayed"
            ]
            # Filtrar métricas padrão para garantir que existam no DataFrame
            metricas_padrao_benchmark = [m for m in metricas_padrao_benchmark if m in colunas_numericas_disponiveis]


            metricas_benchmark_selecionadas = st.multiselect(
                "Selecione as métricas para o Benchmarking:",
                options=sorted(colunas_numericas_disponiveis),
                default=metricas_padrao_benchmark,
                key="metricas_benchmark_selecionadas" # Usar st.session_state para persistir
            )
            st.session_state.metricas_benchmark_selecionadas = metricas_benchmark_selecionadas


            # Opção de grupo de comparação
            pos_jogador_ref = df_original.loc[atleta_id_bench, 'position']
            opcoes_grupo = [
                f"Jogadores da Mesma Posição ({pos_jogador_ref})", 
                "Todos os Jogadores no Banco de Dados"
            ]
            # Adicionar mais grupos se tiver dados de liga, etc.
            # opзхes_grupo.append(f"Jogadores da Mesma Liga ({liga_jogador_ref}) e Posição ({pos_jogador_ref})")

            grupo_comparacao_selecionado = st.selectbox(
                "Comparar com:",
                options=opcoes_grupo
            )

            if st.button("📊 Gerar Benchmarking"):
                df_grupo_comp = pd.DataFrame()
                if grupo_comparacao_selecionado == f"Jogadores da Mesma Posição ({pos_jogador_ref})":
                    df_grupo_comp = df_original[df_original['position'] == pos_jogador_ref]
                elif grupo_comparacao_selecionado == "Todos os Jogadores no Banco de Dados":
                    df_grupo_comp = df_original
                # Adicionar lógica para outros grupos
                
                if not df_grupo_comp.empty and st.session_state.metricas_benchmark_selecionadas:
                    with st.spinner("Calculando benchmarking..."):
                        benchmark_df = gerar_benchmark_atleta(
                            atleta_id_bench, 
                            df_grupo_comp, 
                            st.session_state.metricas_benchmark_selecionadas
                        )
                        if not benchmark_df.empty:
                            st.subheader(f"Benchmarking para {atleta_ref_bench['player.name']}")
                            st.markdown(f"Comparado contra: **{grupo_comparacao_selecionado}** (Total de {len(df_grupo_comp)} jogadores no grupo de comparação)")
                            
                            # Formatar floats para melhor visualização
                            for col in benchmark_df.columns:
                                if benchmark_df[col].dtype == 'float64':
                                     benchmark_df[col] = benchmark_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                            
                            st.dataframe(benchmark_df, use_container_width=True)

                            # Poderia adicionar gráficos aqui (ex: st.bar_chart para algumas métricas)
                            # Exemplo simples: Gráfico de barras para 'rating'
                            if 'rating' in st.session_state.metricas_benchmark_selecionadas and not benchmark_df[benchmark_df['Métrica'] == 'rating'].empty:
                                try:
                                    rating_data = benchmark_df[benchmark_df['Métrica'] == 'rating'].iloc[0]
                                    # Converter para numérico antes de plotar, tratando N/A
                                    rating_values = {
                                        'Jogador': pd.to_numeric(rating_data['Jogador'], errors='coerce'),
                                        'Mediana Grupo': pd.to_numeric(rating_data['Mediana Grupo (50%)'], errors='coerce')
                                    }
                                    df_plot = pd.DataFrame([rating_values])
                                    
                                    st.write("Comparativo de Rating:")
                                    st.bar_chart(df_plot.T) # Transpor para ter métricas no eixo X
                                except Exception as e:
                                    st.warning(f"Não foi possível gerar gráfico de rating: {e}")


                        else:
                            st.warning("Não foi possível gerar o benchmarking. Verifique as métricas selecionadas.")
                else:
                    st.warning("Selecione métricas e um grupo de comparação válido.")
    else:
        st.info("Por favor, insira o nome e clube do atleta para iniciar o benchmarking.")


st.markdown("---")
st.write("Desenvolvido no Brasil pela ProFutStat")
