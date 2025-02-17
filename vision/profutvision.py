import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# Configuração do Supabase
SUPABASE_URL = "https://SEU_PROJETO.supabase.co"
SUPABASE_KEY = "SUA_CHAVE_ANON"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Função para carregar dados de atletas
def carregar_atletas():
    response = supabase.table("atletas").select("*").execute()
    return pd.DataFrame(response.data)

# Função para adicionar um atleta
def adicionar_atleta(nome, idade, posicao, pos_alt, nacionalidade, altura, peso, pe, obs):
    supabase.table("atletas").insert({
        "nome": nome, "idade": idade, "posicao": posicao, 
        "posicoes_alternativas": pos_alt, "nacionalidade": nacionalidade,
        "altura": altura, "peso": peso, "pe": pe, "observacoes": obs
    }).execute()

# Função para carregar treinos
def carregar_treinos():
    response = supabase.table("treinos").select("*").execute()
    return pd.DataFrame(response.data)

# Função para salvar um treino
def salvar_treino(atleta, data, atividade, obs):
    supabase.table("treinos").insert({
        "atleta": atleta, "data": data, "atividade": atividade, "observacoes": obs
    }).execute()

# Função para carregar calendário
def carregar_calendario():
    response = supabase.table("calendario").select("*").execute()
    return pd.DataFrame(response.data)

# Função para salvar no calendário
def salvar_calendario(data, atividade):
    supabase.table("calendario").upsert({
        "data": data, "atividade": atividade
    }).execute()

# Interface no Streamlit
st.title("⚽ Gestão de Atletas e Treinos")

aba = st.sidebar.radio("Menu", ["Cadastro de Atletas", "Registro de Treinos", "Calendário de Atividades"])

# 📋 Cadastro de Atletas
if aba == "Cadastro de Atletas":
    st.header("📋 Cadastro de Atletas")
    
    nome = st.text_input("Nome")
    idade = st.number_input("Idade", min_value=10, max_value=40, step=1)
    posicao = st.selectbox("Posição", ["Goleiro", "Zagueiro", "Lateral", "Volante", "Meia", "Atacante"])
    pos_alt = st.text_input("Posições Alternativas")
    nacionalidade = st.text_input("Nacionalidade")
    altura = st.number_input("Altura (m)", format="%.2f")
    peso = st.number_input("Peso (kg)", format="%.1f")
    pe = st.selectbox("Pé Dominante", ["Destro", "Canhoto", "Ambidestro"])
    obs = st.text_area("Observações")

    if st.button("Adicionar Atleta"):
        adicionar_atleta(nome, idade, posicao, pos_alt, nacionalidade, altura, peso, pe, obs)
        st.success("Atleta cadastrado!")

    df = carregar_atletas()
    st.dataframe(df)

# 🏋️‍♂️ Registro de Treinos
elif aba == "Registro de Treinos":
    st.header("🏋️‍♂️ Registro de Treinos")
    
    df = carregar_atletas()
    atleta = st.selectbox("Selecione o Atleta", df["nome"].dropna().unique())
    data = st.date_input("Data do Treino", datetime.date.today())
    atividade = st.text_area("Descrição da Atividade")
    obs = st.text_area("Observações")

    if st.button("Salvar Treino"):
        salvar_treino(atleta, data, atividade, obs)
        st.success("Treino registrado!")

    df_treinos = carregar_treinos()
    st.dataframe(df_treinos)

# 📅 Calendário de Atividades
elif aba == "Calendário de Atividades":
    st.header("📅 Calendário de Atividades")

    hoje = datetime.date.today()
    fim_ano = datetime.date(hoje.year, 12, 31)

    data = st.date_input("Selecione a Data", min_value=hoje, max_value=fim_ano)
    atividade = st.text_area("Atividade do Dia")

    if st.button("Salvar Atividade"):
        salvar_calendario(data, atividade)
        st.success("Atividade salva no calendário!")

    df_calendario = carregar_calendario()
    st.dataframe(df_calendario)
