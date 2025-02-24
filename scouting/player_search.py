import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Carregar credenciais do secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

# Criar conexão com Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Título do app
st.title("📊 Análise de Jogadores")

# Carregar dados do Supabase com as colunas selecionadas
@st.cache_data
def carregar_dados():
    response = supabase.table("footdataset").select("fullname, age, position, league, Current Club, season, nationality, country").execute()
    return pd.DataFrame(response.data)

df = carregar_dados()

# Sidebar para filtros
st.sidebar.header("🎯 Filtros")

# Filtrar por nome
nome_filtro = st.sidebar.text_input("Nome do Jogador")

# Filtrar por idade
idade_min, idade_max = st.sidebar.slider("Idade", int(df["age"].min()), int(df["age"].max()), (int(df["age"].min()), int(df["age"].max())))

# Filtrar por posição
posicoes = df["position"].unique().tolist()
posicao_filtro = st.sidebar.multiselect("Posição", posicoes, default=posicoes)

# Filtrar por liga
ligas = df["league"].unique().tolist()
liga_filtro = st.sidebar.multiselect("Liga", ligas, default=ligas)

# Filtrar por posição
posicoes = df["Current Club"].unique().tolist()
posicao_filtro = st.sidebar.multiselect("Posição", posicoes, default=posicoes)

# Filtrar por nacionalidade
nacionalidades = df["nationality"].unique().tolist()
nacionalidade_filtro = st.sidebar.multiselect("Nacionalidade", nacionalidades, default=nacionalidades)

# Aplicar filtros
df_filtrado = df[
    (df["idade"] >= idade_min) & (df["idade"] <= idade_max) &
    (df["posicao"].isin(posicao_filtro)) &
    (df["liga"].isin(liga_filtro)) &
    (df["nacionalidade"].isin(nacionalidade_filtro))
]

# Filtrar por nome se algo for digitado
if nome_filtro:
    df_filtrado = df_filtrado[df_filtrado["nome"].str.contains(nome_filtro, case=False, na=False)]

# Exibir tabela
st.write(f"🔍 **Total de jogadores encontrados:** {len(df_filtrado)}")
st.dataframe(df_filtrado)
