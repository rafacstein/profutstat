import streamlit as st
from datetime import date, timedelta
from supabase import create_client
import pandas as pd

# Configuração do Supabase
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Função para verificar se a tabela existe, e criar se necessário
def criar_tabelas():
    # Tabela de Atletas
    atletas_schema = [
        {"nome": "string", "idade": "int", "posicao": "string", "posicao_alt": "string", "nacionalidade": "string", 
         "altura": "int", "peso": "int", "pe": "string", "observacoes": "text"}
    ]
    
    # Tabela de Calendário
    calendario_schema = [
        {"data": "date", "atividade": "text", "observacoes": "text"}
    ]
    
    # Criação das tabelas caso não existam
    for tabela, schema in [("atletas", atletas_schema), ("calendario", calendario_schema)]:
        try:
            # Tentativa de inserir um registro (upsert para garantir que a tabela exista)
            supabase.table(tabela).upsert({"data": "dummy"}).execute()
        except Exception as e:
            print(f"Tabela {tabela} não encontrada. Criando nova tabela...")
            # Criar a tabela manualmente aqui caso não exista
            # No caso do Supabase, use a interface para criar as tabelas, pois não há uma API para criação de tabela direta

# Chame a função ao iniciar a aplicação
criar_tabelas()

# Função de Login
def login():
    st.title("🔐 Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if username == st.secrets["credentials"]["username"] and password == st.secrets["credentials"]["password"]:
            st.session_state["logged_in"] = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos!")

# Tela de Registro de Atletas
def tela_registro_atletas():
    st.title("📋 Registro de Atletas")
    
    nome = st.text_input("Nome")
    idade = st.number_input("Idade", min_value=10, max_value=50, step=1)
    posicao = st.text_input("Posição")
    posicao_alt = st.text_input("Posições Alternativas")
    nacionalidade = st.text_input("Nacionalidade")
    altura = st.number_input("Altura (cm)", min_value=100, max_value=220, step=1)
    peso = st.number_input("Peso (kg)", min_value=30, max_value=120, step=1)
    pe = st.selectbox("Pé Dominante", ["Destro", "Canhoto", "Ambidestro"])
    observacoes = st.text_area("Observações")

    if st.button("Salvar Atleta"):
        atleta = {
            "nome": nome,
            "idade": idade,
            "posicao": posicao,
            "posicao_alt": posicao_alt,
            "nacionalidade": nacionalidade,
            "altura": altura,
            "peso": peso,
            "pe": pe,
            "observacoes": observacoes
        }
        supabase.table("atletas").insert(atleta).execute()
        st.success("Atleta cadastrado com sucesso!")
        st.experimental_rerun()
    
    st.subheader("Lista de Atletas Cadastrados")
    atletas = supabase.table("atletas").select("*").execute().data
    if atletas:
        df = pd.DataFrame(atletas)
        st.dataframe(df)
    else:
        st.write("Nenhum atleta cadastrado.")

# Tela de Calendário
def tela_calendario():
    st.title("📅 Calendário de Atividades")
    hoje = date.today()
    fim_ano = date(hoje.year, 12, 31)
    dias = [(hoje + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((fim_ano - hoje).days + 1)]
    data_selecionada = st.selectbox("Selecione uma data", dias)
    atividade = st.text_area("Atividade do dia")
    if st.button("Salvar Atividade"):
        supabase.table("calendario").upsert({"data": data_selecionada, "atividade": atividade}).execute()
        st.success("Atividade salva!")
    st.subheader("Atividades da Semana")
    atividades = supabase.table("calendario").select("*").execute().data
    if atividades:
        df = pd.DataFrame(atividades)
        st.dataframe(df)
    else:
        st.write("Nenhuma atividade cadastrada.")

# Tela de Registro de Atividade de Treino
def tela_registro_atividade():
    st.title("📋 Registro de Atividades de Treino")
    
    data = st.date_input("Data do Treino")
    registro = st.text_area("Registro do Treino")
    observacoes = st.text_area("Observações")
    
    if st.button("Salvar Atividade de Treino"):
        atividade_treino = {
            "data": str(data),
            "atividade": registro,
            "observacoes": observacoes
        }
        supabase.table("calendario").insert(atividade_treino).execute()
        st.success("Atividade de Treino registrada com sucesso!")
        st.experimental_rerun()
    
    st.subheader("Atividades de Treino Registradas")
    atividades = supabase.table("calendario").select("*").execute().data
    if atividades:
        df = pd.DataFrame(atividades)
        st.dataframe(df)
    else:
        st.write("Nenhuma atividade de treino registrada.")

# Verifica se o usuário está logado
if "logged_in" not in st.session_state:
    login()
else:
    st.sidebar.image("https://github.com/rafacstein/profutstat/blob/main/vision/logo%20profutstat%203.jpeg?raw=true", width=150)
    menu = st.sidebar.radio("Menu", ["🏠 Home", "📋 Registro de Atletas", "📅 Calendário", "📋 Registro de Atividade Treino"])

    if menu == "🏠 Home":
        st.title("🏠 Página Inicial")
        st.write("Bem-vindo ao sistema de gerenciamento de atletas!")
    elif menu == "📋 Registro de Atletas":
        tela_registro_atletas()
    elif menu == "📅 Calendário":
        tela_calendario()
    elif menu == "🏋️‍♀️ Registro de Atividade Treino":
        tela_registro_atividade()
