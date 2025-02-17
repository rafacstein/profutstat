import streamlit as st
from supabase import create_client, Client
import os
from datetime import datetime

# Recuperando as credenciais do Supabase via Streamlit Secrets
url = st.secrets["supabase"]["supabase_url"]
key = st.secrets["supabase"]["supabase_key"]

# Inicializando o cliente do Supabase
supabase: Client = create_client(url, key)

# Função para salvar atleta
def salvar_atleta(nome, idade, posicao, posicao_alt, nacionalidade, altura, peso, pe, observacoes):
    try:
        # Inserção de dados na tabela 'atletas' no esquema 'api'
        atleta_data = {
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
        response = supabase.table("api.atletas").insert(atleta_data).execute()  # Esquema 'api'
        
        if response.status_code == 201:
            st.success("Atleta registrado com sucesso!")
        else:
            st.error(f"Erro ao registrar atleta: {response.json()}")
    except Exception as e:
        st.error(f"Erro ao salvar atleta: {e}")

# Função para registrar/atualizar atividade
def registrar_atividade(data_atividade, atividade_atualizada, observacoes_atualizadas):
    try:
        # Convertendo data para string no formato YYYY-MM-DD
        data_str = data_atividade.strftime("%Y-%m-%d")
        
        # Atualizando dados na tabela 'calendario' no esquema 'api'
        atividade_data = {
            "data": data_str,
            "atividade": atividade_atualizada,
            "observacoes": observacoes_atualizadas
        }
        
        response = supabase.table("api.calendario").upsert(atividade_data).execute()  # Esquema 'api'
        
        if response.status_code == 200:
            st.success("Atividade registrada/atualizada com sucesso!")
        else:
            st.error(f"Erro ao registrar atividade: {response.json()}")
    except Exception as e:
        st.error(f"Erro ao registrar atividade: {e}")

# Interface de entrada de dados do atleta
def tela_registro_atletas():
    st.header("Registro de Atleta")

    # Campos para entrada de dados do atleta
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
        salvar_atleta(nome, idade, posicao, posicao_alt, nacionalidade, altura, peso, pe, observacoes)

# Interface de correção de atividade
def tela_correção_atividade():
    st.header("Correção de Atividade")

    # Entrada de data para buscar atividade
    data_atividade = st.date_input("Data da Atividade para Correção")
    
    if data_atividade:
        atividade = supabase.table("api.calendario").select("*").eq("data", str(data_atividade)).execute().data
        
        if atividade:
            atividade = atividade[0]
            st.write("Atividade encontrada:", atividade)
            
            # Campos para atualização de atividade
            atividade_atualizada = st.text_area("Registro de Atividade", value=atividade["atividade"])
            observacoes_atualizadas = st.text_area("Observações", value=atividade["observacoes"])
            
            if st.button("Atualizar Atividade"):
                registrar_atividade(data_atividade, atividade_atualizada, observacoes_atualizadas)

# Função principal para exibir as telas
def main():
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Escolha a opção", ("Registrar Atleta", "Corrigir Atividade"))
    
    if menu == "Registrar Atleta":
        tela_registro_atletas()
    elif menu == "Corrigir Atividade":
        tela_correção_atividade()

if __name__ == "__main__":
    main()
