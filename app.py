import streamlit as st
from scripts import ultrassomapp, vermelhoapp, planilha, indiceapp


st.image("logo.png", width=600)
st.set_page_config(page_title="Apps", page_icon="🔊")

st.sidebar.title("Menu")

opcao = st.sidebar.selectbox(
    "Escolha uma ferramenta:",
    ["🔊 Ultrassom", "🔴 Destacar PDF", "📊 Planilha", "📘 Índice"]
)

if opcao == "🔊 Ultrassom":
    ultrassomapp.run()

elif opcao == "🔴 Destacar PDF":
    vermelhoapp.run()

elif opcao == "📊 Planilha":
    planilha.run()

elif opcao == "📘 Índice":
    indiceapp.run()
