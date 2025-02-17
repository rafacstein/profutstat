import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import pandas as pd

# Conectando ao Supabase
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# Função para login
def login():
    st.title("🔐 Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        try:
            # Fazendo login com o Supabase Auth
            user = supabase.auth.sign_in_with_password(username=username, password=password)
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user['user']['id']  # Armazenando user_id na sessão
            st.success("Login bem-sucedido!")
        except Exception as e:
            st.error(f"Erro ao fazer login: {e}")

# Função para exibir e registrar dados de atletas
def tela_registro_atletas():
    if not st.session_state.get("logged_in"):
        st.warning("Por favor, faça login primeiro.")
        return
    
    st.title("📋 Registro de Atletas")
    
    # Inputs para o cadastro do atleta
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
        # Coletando os dados do atleta junto com o user_id
        atleta = {
            "nome": nome,
            "idade": idade,
            "posicao": posicao,
            "posicao_alt": posicao_alt,
            "nacionalidade": nacionalidade,
            "altura": altura,
            "peso": peso,
            "pe": pe,
            "observacoes": observacoes,
            "user_id": st.session_state["user_id"]  # Incluindo o user_id
        }
        
        # Inserindo o atleta na tabela "atletas"
        try:
            supabase.table("atletas").insert(atleta).execute()
            st.success("Atleta cadastrado com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao salvar atleta: {e}")
    
    # Exibindo a lista de atletas cadastrados
    st.subheader("Lista de Atletas Cadastrados")
    atletas = supabase.table("atletas").select("*").execute().data
    if atletas:
        df = pd.DataFrame(atletas)
        st.dataframe(df)
    else:
        st.write("Nenhum atleta cadastrado.")

# Função para exibir e registrar dados no calendário
def tela_calendario():
    if not st.session_state.get("logged_in"):
        st.warning("Por favor, faça login primeiro.")
        return

    st.title("📅 Calendário de Atividades")
    hoje = date.today()
    fim_ano = date(hoje.year, 12, 31)
    dias = [(hoje + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((fim_ano - hoje).days + 1)]
    
    data_selecionada = st.selectbox("Selecione uma data", dias)
    atividade = st.text_input("Atividade")

    if st.button("Salvar Atividade"):
        # Salvando a atividade junto com o user_id
        atividade_data = {
            "data": data_selecionada,
            "atividade": atividade,
            "user_id": st.session_state["user_id"]  # Incluindo o user_id
        }
        
        # Inserindo ou atualizando a atividade no calendário
        try:
            supabase.table("calendario").upsert(atividade_data).execute()
            st.success("Atividade registrada com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao salvar atividade: {e}")

# Função principal para controle das abas
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    menu = ["Login", "Registro de Atletas", "Calendário"]
    escolha = st.sidebar.selectbox("Selecione a opção", menu)
    
    if escolha == "Login":
        login()
    elif escolha == "Registro de Atletas":
        tela_registro_atletas()
    elif escolha == "Calendário":
        tela_calendario()

if __name__ == "__main__":
    main()
