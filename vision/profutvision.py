import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# 🔑 Carregar credenciais do Streamlit Secrets
USERNAME = st.secrets["credentials"]["username"]
PASSWORD = st.secrets["credentials"]["password"]

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

# Conectar ao Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔐 Função de Login
def login():
    st.title("🔑 Login")
    user_input = st.text_input("Usuário")
    pass_input = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user_input == USERNAME and pass_input == PASSWORD:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos! ❌")

# 📌 Tela de Registro de Atletas
def tela_registro_atletas():
    st.title("Registro de Atletas")
    
    nome = st.text_input("Nome")
    idade = st.number_input("Idade", min_value=10, max_value=50, step=1)
    posicao = st.text_input("Posição")
    posicoes_alt = st.text_input("Posições Alternativas")
    nacionalidade = st.text_input("Nacionalidade")
    altura = st.number_input("Altura (cm)", min_value=100, max_value=220, step=1)
    peso = st.number_input("Peso (kg)", min_value=30, max_value=120, step=1)
    pe = st.selectbox("Pé dominante", ["Direito", "Esquerdo", "Ambidestro"])
    observacoes = st.text_area("Observações")

    if st.button("Salvar Atleta"):
        data = {
            "nome": nome,
            "idade": idade,
            "posicao": posicao,
            "posicoes_alt": posicoes_alt,
            "nacionalidade": nacionalidade,
            "altura": altura,
            "peso": peso,
            "pe": pe,
            "observacoes": observacoes,
        }
        supabase.table("atletas").insert(data).execute()
        st.success(f"✅ Atleta {nome} registrado com sucesso!")

# 📌 Tela de Registro de Treinos
def tela_registro_treinos():
    st.title("📋 Registro de Treinos")

    data = st.date_input("Data do treino", datetime.date.today())
    atividade = st.text_area("Descrição da Atividade")
    observacoes = st.text_area("Observações")

    if st.button("Salvar Treino"):
        treino_data = {
            "data": str(data),
            "atividade": atividade,
            "observacoes": observacoes,
        }
        supabase.table("treinos").insert(treino_data).execute()
        st.success(f"✅ Treino registrado para {data}!")

# 📆 Tela do Calendário de Atividades
def tela_calendario():
    st.title("📅 Calendário de Atividades")

    hoje = datetime.date.today()
    fim_ano = datetime.date(hoje.year, 12, 31)

    data = st.date_input("Selecionar data", min_value=hoje, max_value=fim_ano)
    atividade = st.text_area("Atividade planejada para este dia")

    if st.button("Salvar Atividade"):
        supabase.table("calendario").insert({"data": str(data), "atividade": atividade}).execute()
        st.success(f"✅ Atividade salva para {data}!")

    # Exibir atividades já cadastradas
    atividades_existentes = supabase.table("calendario").select("*").execute()
    if atividades_existentes.data:
        df = pd.DataFrame(atividades_existentes.data)
        df["data"] = pd.to_datetime(df["data"])
        df = df.sort_values(by="data")
        st.write("📅 **Atividades Cadastradas**")
        st.dataframe(df)

# 🚀 Tela Principal
def tela_principal():
    st.sidebar.image("https://github.com/rafacstein/profutstat/blob/main/vision/logo%20profutstat%203.jpeg?raw=true", width=150)
    st.sidebar.title("Menu")

    opcao = st.sidebar.radio("Escolha uma opção:", ["📋 Registro de Atletas", "📋 Registro de Treinos", "📅 Calendário de Atividades"])

    if opcao == "🏃‍♂️ Registro de Atletas":
        tela_registro_atletas()
    elif opcao == "📋 Registro de Treinos":
        tela_registro_treinos()
    elif opcao == "📅 Calendário de Atividades":
        tela_calendario()

# 🔑 Controle de Acesso
if "logged_in" not in st.session_state:
    login()
else:
    tela_principal()
