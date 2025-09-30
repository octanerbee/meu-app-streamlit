import fitz  #PyMuPDF
import streamlit as st
import io


def destacar_nao_conforme(path_pdf):
    doc = fitz.open("pdf", path_pdf)
    for pagina in doc:
        instancias = pagina.search_for("Não conforme")
        for inst in instancias:
            r = fitz.Rect(inst.x0-7, inst.y0-6, inst.x1+7, inst.y1+6) # tamanho da caixa, fonte 12
            pagina.draw_rect( # borda, com a cor igual n muda muito
                r,
                color=(1, 0, 0),      # padrao rgb
                fill=(1, 0, 0),
                overlay=True
            )
            # texto um pouco mais pra baixo, eixo y
            r = fitz.Rect(inst.x0-7, inst.y0-3, inst.x1+7, inst.y1+6)
            # texto
            pagina.insert_textbox(
                r,
                "Não conforme",
                fontname="times-bold",
                fontsize=12,
                color=(0, 0, 0),
                align=1,
                overlay=True

            )

    saida = io.BytesIO()
    doc.save(saida)
    doc.close()
    return saida.getvalue()

def run():
    st.write(" ## 🔴 Destacar 'Não conforme' em PDFs ")
    uploaded_files = st.file_uploader("Escolha arquivos pdf", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"Processando: {uploaded_file.name}")
            pdf_processado = destacar_nao_conforme(uploaded_file.read())

            st.download_button(
                label="Baixar PDF Editado",
                data=pdf_processado,
                file_name=f"{uploaded_file.name.replace('.pdf', '')}_editado.pdf",
                mime="application/pdf"
            )
