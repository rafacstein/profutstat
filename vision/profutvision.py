import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# 🔒 Recuperando credenciais do Supabase via Streamlit Secrets
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Função para registrar atletas
def tela_registro_atletas():
    st.title("Cadastro de Atletas")

    # Buscar atletas cadastrados
    atletas = supabase.table("api.atletas").select("*").execute().data

    if atletas:
        st.subheader("Atletas Cadastrados")
        for atleta in atletas:
            st.write(f"**Nome:** {atleta['nome']} - **Posição:** {atleta['posicao']}")

    with st.form("cadastro_atletas"):
        nome = st.text_input("Nome")
        idade = st.number_input("Idade", min_value=10, max_value=50, step=1)
        posicao = st.text_input("Posição")
        posicao_alt = st.text_input("Posições Alternativas")
        nacionalidade = st.text_input("Nacionalidade")
        altura = st.number_input("Altura (cm)", min_value=100, max_value=220, step=1)
        peso = st.number_input("Peso (kg)", min_value=30, max_value=120, step=1)
        pe = st.selectbox("Pé Dominante", ["Destro", "Canhoto", "Ambidestro"])
        observacoes = st.text_area("Observações")

        if st.form_submit_button("Salvar Atleta"):
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
            supabase.table("api.atletas").insert(atleta).execute()
            st.success("Atleta cadastrado com sucesso!")
            st.experimental_rerun()

# Função para registrar atividades no calendário
def tela_calendario():
    st.title("Calendário de Atividades")

    with st.form("cadastro_calendario"):
        data_atividade = st.date_input("Data da Atividade")
        atividade = st.text_area("Descrição da Atividade")

        if st.form_submit_button("Registrar Atividade"):
            atividade_data = {"data": str(data_atividade), "atividade": atividade}
            supabase.table("api.calendario").upsert(atividade_data).execute()
            st.success("Atividade registrada com sucesso!")
            st.experimental_rerun()

    # Exibir atividades registradas
    atividades = supabase.table("api.calendario").select("*").execute().data
    if atividades:
        st.subheader("Atividades Registradas")
        for atv in atividades:
            st.write(f"📅 **{atv['data']}** - {atv['atividade']}")

# Função para registrar treinos
def tela_registro_treinos():
    st.title("Registro de Treinos")

    with st.form("cadastro_treinos"):
        data_treino = st.date_input("Data do Treino")
        tipo_treino = st.text_input("Tipo de Treino")
        duracao = st.number_input("Duração (minutos)", min_value=10, max_value=180, step=5)
        intensidade = st.selectbox("Intensidade", ["Leve", "Moderado", "Intenso"])
        observacoes = st.text_area("Observações")

        if st.form_submit_button("Salvar Treino"):
            treino_data = {
                "data": str(data_treino),
                "tipo_treino": tipo_treino,
                "duracao": duracao,
                "intensidade": intensidade,
                "observacoes": observacoes
            }
            supabase.table("api.registro_treinos").insert(treino_data).execute()
            st.success("Treino registrado com sucesso!")
            st.experimental_rerun()

    # Exibir treinos já registrados
    treinos = supabase.table("api.registro_treinos").select("*").execute().data
    if treinos:
        st.subheader("Treinos Registrados")
        for treino in treinos:
            st.write(f"🏋️‍♂️ **{treino['data']}** - {treino['tipo_treino']} ({treino['duracao']} min, {treino['intensidade']})")

# Menu de navegação
menu = st.sidebar.radio("Navegação", ["Cadastro de Atletas", "Calendário", "Registro de Treinos"])

if menu == "Cadastro de Atletas":
    tela_registro_atletas()
elif menu == "Calendário":
    tela_calendario()
elif menu == "Registro de Treinos":
    tela_registro_treinos()
