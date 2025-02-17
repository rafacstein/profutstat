import streamlit as st
from datetime import date, timedelta
from supabase import create_client
import pandas as pd

# Configuração do Supabase
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Função de Login
def login():
    st.title("🔐 Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username == st.secrets["credentials"]["username"] and password == st.secrets["credentials"]["password"]:
            st.session_state["logged_in"] = True
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

    # Exibe lista de atletas cadastrados
    st.subheader("Lista de Atletas Cadastrados")
    try:
        atletas = supabase.table("atletas").select("*").execute()
        if atletas.data:
            df = pd.DataFrame(atletas.data)
            st.dataframe(df)
        else:
            st.write("Nenhum atleta cadastrado.")
    except Exception as e:
        st.warning("Erro ao carregar atletas. Talvez a tabela ainda não exista.")

# Tela de Registro de Atividades de Treino
# Tela de Registro de Atividades de Treino
def tela_registro_atividades():
    st.title("🏋️‍♂️ Registro de Atividades de Treino")

    # Formulário para registrar uma nova atividade
    with st.form("registro_treino_form"):
        data = st.date_input("Data", value=date.today())
        registro = st.text_area("Registro do Treino")
        observacoes = st.text_area("Observações")
        submit_button = st.form_submit_button("Salvar Registro")

        if submit_button:
            atividade = {
                "data": str(data),
                "registro": registro,
                "observacoes": observacoes
            }
            try:
                supabase.table("registro_treino").insert(atividade).execute()
                st.success("Atividade registrada com sucesso!")
                st.experimental_rerun()  # Recarrega a página para exibir os dados atualizados
            except Exception as e:
                st.error(f"Erro ao salvar atividade: {e}")

    # Exibe os registros de atividades cadastrados
    st.subheader("📋 Atividades Registradas")
    try:
        response = supabase.table("registro_treino").select("*").execute()
        atividades = response.data

        if atividades:
            df = pd.DataFrame(atividades)
            df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")  # Formata a data
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma atividade registrada ainda.")
    except Exception as e:
        st.warning("Erro ao carregar atividades. Talvez a tabela ainda não exista.")


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
    try:
        atividades = supabase.table("calendario").select("*").execute()
        if atividades.data:
            df = pd.DataFrame(atividades.data)
            st.dataframe(df)
        else:
            st.write("Nenhuma atividade cadastrada.")
    except Exception as e:
        st.warning("Erro ao carregar atividades. Talvez a tabela ainda não exista.")

# Verifica se o usuário está logado
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    st.sidebar.image("https://github.com/rafacstein/profutstat/blob/main/vision/logo%20profutstat%203.jpeg?raw=true", width=150)
    menu = st.sidebar.radio("Menu", ["🏠 Home", "📋 Registro de Atletas", "📅 Calendário", "📋 Registro de Atividades de Treino"])

    if menu == "🏠 Home":
        st.title("🏠 Página Inicial")
        st.write("Bem-vindo ao sistema de gerenciamento de atletas!")

    elif menu == "📋 Registro de Atletas":
        tela_registro_atletas()

    elif menu == "📅 Calendário":
        tela_calendario()

    elif menu == "🏋️‍♂️ Registro de Atividades de Treino":
        tela_registro_atividades()
