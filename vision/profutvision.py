import streamlit as st
from supabase import create_client
from datetime import date

# 🔹 Configuração do Supabase (pegando dos secrets no Streamlit Cloud)
supabase_url = st.secrets["supabase"]["supabase_url"]
supabase_key = st.secrets["supabase"]["supabase_key"]

# 🔹 Criando conexão com o Supabase
try:
    supabase = create_client(supabase_url, supabase_key)
    st.success("✅ Conexão com Supabase estabelecida!")
except Exception as e:
    st.error(f"❌ Erro ao conectar no Supabase: {e}")

# 🔹 Pegando o id dos secrets (simulando autenticação)
user_id = st.secrets.get("USER_ID", "anon")  # Se não houver autenticação, assume "anon"
st.write(f"🔍 User ID: {user_id}")

# ==============================
# 📌 Função para tela de atletas
# ==============================
def tela_registro_atletas():
    st.title("Cadastro de Atletas")

    try:
        atletas = supabase.table("api.atletas").select("*").execute().data
        st.write(f"📊 Atletas carregados: {len(atletas)} registros encontrados.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar atletas: {e}")
        atletas = []

    nome = st.text_input("Nome")
    idade = st.number_input("Idade", min_value=10, max_value=50, step=1)
    posicao = st.text_input("Posição")
    nacionalidade = st.text_input("Nacionalidade")
    altura = st.number_input("Altura (cm)", min_value=100, max_value=220, step=1)
    peso = st.number_input("Peso (kg)", min_value=30, max_value=120, step=1)
    pe = st.selectbox("Pé Dominante", ["Destro", "Canhoto", "Ambidestro"])
    observacoes = st.text_area("Observações")

    if st.button("Salvar Atleta"):
        novo_atleta = {
            "nome": nome,
            "idade": idade,
            "posicao": posicao,
            "nacionalidade": nacionalidade,
            "altura": altura,
            "peso": peso,
            "pe": pe,
            "observacoes": observacoes,
            "id": user_id  # Garantindo o id
        }

        try:
            response = supabase.table("api.atletas").insert(novo_atleta).execute()
            st.success("Atleta cadastrado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao cadastrar atleta: {e}")

# ==============================
# 📌 Função para tela de calendário
# ==============================
def tela_calendario():
    st.title("Registro de Calendário")

    data_selecionada = st.date_input("Data da Atividade", value=date.today())
    atividade = st.text_area("Descrição da Atividade")

    if st.button("Salvar Atividade"):
        atividade_data = {
            "data": str(data_selecionada),
            "atividade": atividade,
            "id": user_id  # Garantindo a autenticação do usuário
        }

        try:
            response = supabase.table("api.calendario").upsert(atividade_data).execute()
            st.success("Atividade registrada com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao registrar atividade: {e}")

# ==============================
# 📌 Função para registro de treino
# ==============================
def tela_registro_treino():
    st.title("Registro de Treino")

    data_treino = st.date_input("Data do Treino", value=date.today())
    atleta = st.text_input("Nome do Atleta")
    tipo_treino = st.selectbox("Tipo de Treino", ["Físico", "Tático", "Técnico", "Outro"])
    duracao = st.number_input("Duração (min)", min_value=10, max_value=180, step=5)
    desempenho = st.slider("Desempenho do Atleta", 0, 100, 50)

    if st.button("Salvar Treino"):
        treino_data = {
            "data": str(data_treino),
            "atleta": atleta,
            "tipo_treino": tipo_treino,
            "duracao": duracao,
            "desempenho": desempenho,
            "id": user_id  # Garantindo a autenticação do usuário
        }

        try:
            response = supabase.table("api.registro_treino").insert(treino_data).execute()
            st.success("Treino registrado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao registrar treino: {e}")

# ==============================
# 📌 Navegação entre telas
# ==============================
st.sidebar.title("Menu")
pagina = st.sidebar.radio("Selecione uma página:", ["Atletas", "Calendário", "Treinos"])

if pagina == "Atletas":
    tela_registro_atletas()
elif pagina == "Calendário":
    tela_calendario()
elif pagina == "Treinos":
    tela_registro_treino()
