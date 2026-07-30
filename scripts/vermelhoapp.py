import fitz  # PyMuPDF
import streamlit as st
import io


TEXTOS_E_CORES = {
    "Não conforme": (1, 0, 0),     
    "Não se aplica": (0.29, 0.51, 0.83),
}


def _destacar_texto(pagina, texto, cor):
    instancias = pagina.search_for(texto)
    if not instancias:
        return

    caixas_redacao = [fitz.Rect(inst) for inst in instancias]

    caixas_visuais = [
        fitz.Rect(inst.x0 - 7, inst.y0 - 6, inst.x1 + 7, inst.y1 + 6)
        for inst in instancias
    ]

    for r in caixas_redacao:
        pagina.add_redact_annot(r, fill=cor)

    pagina.apply_redactions()

    for r in caixas_visuais:
        pagina.draw_rect(r, color=cor, fill=cor, overlay=True)

    for r in caixas_visuais:
        r_texto = fitz.Rect(r.x0, r.y0 + 3, r.x1, r.y1)  
        pagina.insert_textbox(
            r_texto,
            texto,
            fontname="times-bold",
            fontsize=12,
            color=(0, 0, 0),
            align=1,
            overlay=True
        )


def destacar_nao_conforme(path_pdf):
    doc = fitz.open("pdf", path_pdf)

    for pagina in doc:
        for texto, cor in TEXTOS_E_CORES.items():
            _destacar_texto(pagina, texto, cor)

    saida = io.BytesIO()
    doc.save(saida, garbage=4, deflate=True)
    doc.close()
    return saida.getvalue()


def run():
    st.write(" ## Destacar não conforme e não se aplica em RTI")
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
