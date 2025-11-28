import streamlit as st
from scripts import ultrassomapp, vermelhoapp, planilha, indiceapp, condicoesapp, juntarpdfsapp, completoapp


st.image("logo.png", width=600)
st.set_page_config(page_title="Apps", page_icon="⚡")

st.sidebar.title("Menu")

opcao = st.sidebar.selectbox(
    "Escolha uma ferramenta:",
    ["🔊 Ultrassom", "🔴 Destacar PDF", "📊 Planilha", "📘 Índice", "🎨 Condições", "🖇️ Juntar PDF's", "📄 Processador Completo de PDF"]
)

if opcao == "🔊 Ultrassom":
    ultrassomapp.run()

elif opcao == "🔴 Destacar PDF":
    vermelhoapp.run()

elif opcao == "📊 Planilha":
    planilha.run()

elif opcao == "📘 Índice":
    indiceapp.run()

elif opcao == "🎨 Condições":
    condicoesapp.run()

elif opcao == "🖇️ Juntar PDF's":
    juntarpdfsapp.run()

elif opcao == "📄 Processador Completo de PDF":
    completoapp.run()
