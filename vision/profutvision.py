import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
from PIL import Image
import json

# Configuração inicial
st.set_page_config(page_title="ProFutStat", layout="wide")

# Carregar logo
logo_path = "https://github.com/rafacstein/profutstat/blob/main/vision/logo%20profutstat%203.jpeg"  # Substitua pelo caminho real do seu logo
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=200)

# Autenticação
users = {"admin": "1234"}  # Usuário e senha fixos (melhor usar um sistema seguro)
username = st.sidebar.text_input("Usuário")
password = st.sidebar.text_input("Senha", type="password")
login_button = st.sidebar.button("Login")

if username in users and password == users[username]:
    st.sidebar.success("Login realizado com sucesso!")
    autenticado = True
else:
    autenticado = False
    st.sidebar.warning("Usuário ou senha incorretos.")

if autenticado:
    # Criar abas
    aba = st.sidebar.radio("Navegação", ["Cadastro de Atletas", "Registro de Treinos", "Lousa Tática"])
    
    # --- Cadastro de Atletas ---
    if aba == "Cadastro de Atletas":
        st.title("Cadastro de Atletas")
        data_path = "atletas.xlsx"
        
        if os.path.exists(data_path):
            df = pd.read_excel(data_path)
        else:
            df = pd.DataFrame(columns=["Nome", "Idade", "Posição", "Altura", "Peso"])
        
        with st.form("Cadastro de Atletas"):
            nome = st.text_input("Nome")
            idade = st.number_input("Idade", min_value=10, max_value=40)
            posicao = st.selectbox("Posição", ["Goleiro", "Zagueiro", "Lateral", "Meia", "Atacante"])
            altura = st.number_input("Altura (cm)", min_value=140, max_value=210)
            peso = st.number_input("Peso (kg)", min_value=40, max_value=120)
            submit = st.form_submit_button("Salvar")
            
            if submit:
                novo_atleta = pd.DataFrame([[nome, idade, posicao, altura, peso]], columns=df.columns)
                df = pd.concat([df, novo_atleta], ignore_index=True)
                df.to_excel(data_path, index=False)
                st.success("Atleta cadastrado!")
        
        st.write(df)
    
    # --- Registro de Treinos ---
    elif aba == "Registro de Treinos":
        st.title("Registro de Treinos")
        treino_path = "treinos.xlsx"
        
        if os.path.exists(treino_path):
            df_treinos = pd.read_excel(treino_path)
        else:
            df_treinos = pd.DataFrame(columns=["Data", "Atletas", "Treino", "Observações"])
        
        with st.form("Cadastro de Treino"):
            data = st.date_input("Data do treino")
            atletas = st.text_area("Atletas presentes")
            treino = st.text_area("Descrição do treino")
            observacoes = st.text_area("Observações")
            submit = st.form_submit_button("Salvar")
            
            if submit:
                novo_treino = pd.DataFrame([[data, atletas, treino, observacoes]], columns=df_treinos.columns)
                df_treinos = pd.concat([df_treinos, novo_treino], ignore_index=True)
                df_treinos.to_excel(treino_path, index=False)
                st.success("Treino registrado!")
        
        st.write(df_treinos)
    
    # --- Lousa Tática ---
    elif aba == "Lousa Tática":
        st.title("Lousa Tática")
        
        col1, col2 = st.columns(2)
        
        # Lousa Livre
        with col1:
            st.subheader("Lousa Livre")
            st.write("Arraste os pontos para montar sua estratégia.")
            canvas_result = st.canvas(
                fill_color="rgba(255, 165, 0, 0.5)",
                stroke_width=3,
                stroke_color="#000000",
                background_color="#FFFFFF",
                height=400,
                width=400,
                key="canvas_livre"
            )
        
        # Lousa com Campo e 11 Atletas
        with col2:
            st.subheader("Lousa com Campo e 11 Atletas")
            st.write("Clique e arraste os jogadores para posicioná-los.")
            
            jogadores = [f"Jogador {i+1}" for i in range(11)]
            posicoes = {j: [200 + i * 50, 200] for i, j in enumerate(jogadores)}
            
            for jogador in jogadores:
                x, y = st.slider(f"{jogador} - Posição X", 0, 400, posicoes[jogador][0]), \
                       st.slider(f"{jogador} - Posição Y", 0, 400, posicoes[jogador][1])
                posicoes[jogador] = [x, y]
            
            campo = st.image("campo.jpg")  # Substitua pelo caminho real do fundo do campo
            st.write("Posicione os jogadores conforme sua estratégia.")
    
else:
    st.warning("Por favor, faça login para acessar o sistema.")
