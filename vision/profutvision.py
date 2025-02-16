import streamlit as st
import pandas as pd
import os
from streamlit_dnd import dnd_grid  # Biblioteca para drag and drop (pip install streamlit-dnd)
from PIL import Image

# Carregar credenciais do secrets.toml
username = st.secrets["credentials"]["username"]
password = st.secrets["credentials"]["password"]

# Função para autenticação
def login():
    st.title("🔑 Login")
    user_input = st.text_input("Usuário")
    pass_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user_input == username and pass_input == password:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos! ❌")

# Caminho do banco de dados (Excel temporário)
DATA_PATH = "dados_treino.xlsx"

def carregar_dados():
    if os.path.exists(DATA_PATH):
        return pd.read_excel(DATA_PATH)
    else:
        return pd.DataFrame(columns=["Atleta", "Treino", "Notas"])

def salvar_dados(df):
    df.to_excel(DATA_PATH, index=False)

def tela_principal():
    st.sidebar.image("logo.png", width=150)  # Logo no topo
    st.title("⚽ Gestão de Treinos e Táticas")
    aba = st.sidebar.radio("Menu", ["Cadastro de Atletas", "Registro de Treinos", "Lousa Tática"])

    if aba == "Cadastro de Atletas":
        st.header("📋 Cadastro de Atletas")
        df = carregar_dados()
        nome = st.text_input("Nome do Atleta")
        if st.button("Adicionar"):
            if nome:
                df = df.append({"Atleta": nome, "Treino": "", "Notas": ""}, ignore_index=True)
                salvar_dados(df)
                st.success("Atleta cadastrado!")
        st.dataframe(df["Atleta"].dropna())

    elif aba == "Registro de Treinos":
        st.header("🥅 Registro de Treinos")
        df = carregar_dados()
        atleta = st.selectbox("Selecione o Atleta", df["Atleta"].dropna().unique())
        treino = st.text_area("Descrição do Treino")
        notas = st.text_area("Notas Adicionais")
        if st.button("Salvar Treino"):
            df.loc[df["Atleta"] == atleta, ["Treino", "Notas"]] = [treino, notas]
            salvar_dados(df)
            st.success("Treino registrado!")
        st.dataframe(df)

    elif aba == "Lousa Tática":
        st.header("📋 Lousa Tática Interativa")
        tipo = st.radio("Escolha o tipo de lousa", ["Livre", "Campo de Futebol"])

        if tipo == "Livre":
            st.write("Arraste os pontos para simular movimentações.")
            positions = [(i*50, i*50) for i in range(5)]
            positions = dnd_grid(positions, grid_size=(400, 400))

        elif tipo == "Campo de Futebol":
            st.image("campo.png", width=600)
            positions = [(100, 50), (200, 50), (300, 50), (400, 50), (500, 50), (150, 200), (250, 200), (350, 200), (450, 200), (275, 350), (275, 500)]
            positions = dnd_grid(positions, grid_size=(600, 800))

if "logged_in" not in st.session_state:
    login()
else:
    tela_principal()
