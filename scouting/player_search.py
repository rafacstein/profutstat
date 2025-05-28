import streamlit as st
import pandas as pd
import numpy as np
import faiss
from sklearn.preprocessing import StandardScaler
from fuzzywuzzy import fuzz

@st.cache_data
def carregar_dados():
    df = pd.read_parquet('https://github.com/rafacstein/profutstat/raw/main/scouting/final_merged_data.parquet')
    return df

@st.cache_data
def carregar_features():
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

# Salvar os vetores
    np.save("df_features.npy", X_scaled.astype('float32'))
    return np.load("df_features.npy")

@st.cache_resource
def criar_index(features):
    faiss.normalize_L2(features)
    index = faiss.IndexFlatIP(features.shape[1])
    index.add(features)
    return index

def recomendar_faiss(nome, clube=None, posicao=None, idade_min=None, idade_max=None,
                     valor_min=None, valor_max=None, top_n=5):
    
    df['sim_nome'] = df['player.name'].apply(lambda x: fuzz.token_set_ratio(nome, x))
    
    if clube:
        df['sim_clube'] = df['player.team.name.1'].apply(lambda x: fuzz.token_set_ratio(clube, x))
        df['sim_total'] = 0.7 * df['sim_nome'] + 0.3 * df['sim_clube']
    else:
        df['sim_total'] = df['sim_nome']

    if df['sim_total'].isnull().all():
        st.error("Nenhuma correspondência encontrada para o nome/clube fornecido.")
        return pd.DataFrame()

    idx_ref = df['sim_total'].idxmax()
    jogador_ref = df.loc[idx_ref]
    vetor_ref = features[idx_ref].reshape(1, -1)

    D, I = index.search(vetor_ref, 100)
    similares = df.iloc[I[0]].copy()
    similares['similaridade'] = D[0]

    if posicao:
        similares = similares[similares['position'].str.split(',').str[0].str.strip() == posicao]
    if idade_min:
        similares = similares[similares['age'] >= idade_min]
    if idade_max:
        similares = similares[similares['age'] <= idade_max]
    if valor_min:
        similares = similares[similares['player.proposedMarketValue'] >= valor_min]
    if valor_max:
        similares = similares[similares['player.proposedMarketValue'] <= valor_max]

    similares = similares[similares.index != idx_ref]

    return similares.nlargest(top_n, 'similaridade')[[
        'player.name', 'player.team.name.1', 'position', 'player.country.name','age','minutesPlayed',
        'player.proposedMarketValue', 'similaridade'
    ]]

st.title("Recomendação de Jogadores com FAISS")

df = carregar_dados()
features = carregar_features()
index = criar_index(features)

nome_input = st.text_input("Nome do jogador")
clube_input = st.text_input("Clube (opcional)")
posicao_input = st.text_input("Posição (opcional)")
idade_min_input = st.number_input("Idade mínima", min_value=0, max_value=100, value=20)
idade_max_input = st.number_input("Idade máxima", min_value=0, max_value=100, value=30)
valor_max_input = st.number_input("Valor máximo", min_value=0, value=2000000)
top_n_input = st.number_input("Número de resultados", min_value=1, max_value=20, value=5)

if st.button("Buscar recomendação"):
    resultado = recomendar_faiss(nome_input, clube_input or None, posicao_input or None,
                                idade_min_input, idade_max_input, None, valor_max_input, top_n_input)
    if resultado.empty:
        st.warning("Nenhum jogador encontrado com os critérios informados.")
    else:
        st.dataframe(resultado)
