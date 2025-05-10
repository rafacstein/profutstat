import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from PIL import Image
import urllib.request

# Configuração inicial
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=[
        "Evento", "Equipe", "Jogador", "Minuto", "Coordenada_X", "Coordenada_Y"
    ])

# Carrega a imagem do campo do GitHub
def load_field_image():
    url = "https://raw.githubusercontent.com/rafacstein/profutstat/main/vision/campo.jpg"  # Substitua pelo seu link
    urllib.request.urlretrieve(url, "campo.jpg")
    return Image.open("campo.jpg")

field_img = load_field_image()
width, height = field_img.size

# Função para registrar eventos com coordenadas
def registrar_evento(evento, equipe, jogador, minuto, coord_x, coord_y):
    novo_evento = {
        "Evento": evento,
        "Equipe": equipe,
        "Jogador": jogador,
        "Minuto": minuto,
        "Coordenada_X": coord_x,
        "Coordenada_Y": coord_y
    }
    st.session_state.dados = pd.concat(
        [st.session_state.dados, pd.DataFrame([novo_evento])],
        ignore_index=True
    )

# Interface
st.title("⚽ Mapeamento Tático de Ações")

# --- Mapa Interativo ---
st.header("Clique no campo para marcar ações")
st.image("campo.jpg", use_column_width=True)

# Obtém coordenadas do clique
click_coords = st.session_state.get("click_coords", None)
if st.button("Limpar Seleção"):
    click_coords = None

if click_coords:
    st.write(f"📍 Ação marcada em: X={click_coords[0]:.1f}, Y={click_coords[1]:.1f}")

# --- Controles ---
col1, col2 = st.columns(2)
with col1:
    evento = st.selectbox("Tipo de Ação:", [
        "Passe Certo", "Passe Errado", "Cruzamento", 
        "Finalização", "Desarme", "Falta"
    ])
    equipe = st.radio("Equipe:", ["Time A", "Time B"])

with col2:
    jogador = st.text_input("Jogador:", "")
    minuto = st.number_input("Minuto:", 0, 120)

if click_coords and st.button("Registrar Ação"):
    registrar_evento(evento, equipe, jogador, minuto, click_coords[0], click_coords[1])
    st.success("Ação registrada!")

# --- Visualizações ---
st.header("Visualização de Dados")

# Heatmap
if not st.session_state.dados.empty:
    fig = px.density_heatmap(
        st.session_state.dados,
        x="Coordenada_X",
        y="Coordenada_Y",
        nbinsx=10,
        nbinsy=7,
        title="Heatmap de Ações"
    )
    fig.update_layout(images=[dict(
        source=field_img,
        xref="x",
        yref="y",
        x=0,
        y=0,
        sizex=width,
        sizey=height,
        sizing="stretch",
        opacity=0.5,
        layer="below"
    )])
    st.plotly_chart(fig)

# Tabela de dados
st.dataframe(st.session_state.dados)

# Exportar
st.download_button(
    label="📥 Baixar Dados",
    data=st.session_state.dados.to_csv(index=False),
    file_name="dados_mapeamento.csv"
)
