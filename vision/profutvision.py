import streamlit as st
from supabase import create_client, Client
import os

# Recuperando as credenciais do Supabase via Streamlit Secrets
url = st.secrets["supabase"]["supabase_url"]
key = st.secrets["supabase"]["supabase_key"]

# Inicializando o cliente do Supabase
supabase: Client = create_client(url, key)

# Função para salvar atleta
def salvar_atleta(nome, idade, time):
    try:
        # Inserção de dados na tabela 'atletas' no esquema 'api'
        atleta_data = {
            "nome": nome,
            "idade": idade,
            "time": time
        }
        response = supabase.table("api.atletas").insert(atleta_data).execute()  # Esquema 'api'
        
        if response.status_code == 201:
            st.success("Atleta registrado com sucesso!")
        else:
            st.error(f"Erro ao registrar atleta: {response.json()}")
    except Exception as e:
        st.error(f"Erro ao salvar atleta: {e}")

# Função para registrar atividades no calendário
def registrar_atividade(data_selecionada, atividade):
    try:
        # Inserção de dados na tabela 'calendario' no esquema 'api'
        atividade_data = {
            "data": data_selecionada,
            "atividade": atividade
        }
        response = supabase.table("api.calendario").upsert(atividade_data).execute()  # Esquema 'api'
        
        if response.status_code == 200:
            st.success("Atividade registrada com sucesso!")
        else:
            st.error(f"Erro ao registrar atividade: {response.json()}")
    except Exception as e:
        st.error(f"Erro ao registrar atividade: {e}")

# Função principal de registro de atletas
def tela_registro_atletas():
    st.title("Cadastro de Atletas")
    
    nome = st.text_input("Nome do Atleta")
    idade = st.number_input("Idade", min_value=0)
    time = st.text_input("Nome do Time")
    
    if st.button("Salvar Atleta"):
        if nome and time:
            salvar_atleta(nome, idade, time)
        else:
            st.warning("Preencha todos os campos obrigatórios!")

# Função principal de registro de calendário
def tela_calendario():
    st.title("Calendário de Atividades")
    
    data_selecionada = st.date_input("Selecione a Data")
    atividade = st.text_input("Descrição da Atividade")
    
    if st.button("Registrar Atividade"):
        if data_selecionada and atividade:
            registrar_atividade(data_selecionada, atividade)
        else:
            st.warning("Preencha todos os campos obrigatórios!")

# Layout do Streamlit para navegação entre telas
menu = ["Cadastro de Atletas", "Calendário de Atividades"]
opcao = st.sidebar.selectbox("Escolha uma opção", menu)

if opcao == "Cadastro de Atletas":
    tela_registro_atletas()
elif opcao == "Calendário de Atividades":
    tela_calendario()
