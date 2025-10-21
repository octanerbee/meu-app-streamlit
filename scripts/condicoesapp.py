import streamlit as st
import fitz  # PyMuPDF
import io

def run():
    st.set_page_config(page_title="Colorir PDF automático", page_icon="🖍️", layout="centered")

    st.write("## Colorir as condições dos equipamentos")

    TEXTOS_CORES = {
        "Equipamento em boas condições para operação": (0, 0.8, 0),
        "Equipamento requer intervenção": (1, 0, 0),
        "EM ANÁLISE": (1, 1, 0),
    }

    FONTE = "times-bold"
    TAMANHO_FONTE = 12

    uploaded_file = st.file_uploader("📄 Envie o arquivo PDF", type=["pdf"])

    if uploaded_file and st.button("🎨 Processar PDF"):
        try:

            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page in doc:
                for texto_alvo, cor in TEXTOS_CORES.items():
                    areas = page.search_for(texto_alvo)
                    for rect in areas:
                        trecho = page.get_text("text", clip=rect).strip()
                        if trecho == texto_alvo:
                            page.draw_rect(rect, color=None, fill=(1, 1, 1))

                            x = rect.x0
                            y = rect.y1 - 1  # ligeiro ajuste

                            page.insert_text(
                                (x, y),
                                texto_alvo,
                                fontsize=TAMANHO_FONTE,
                                fontname=FONTE,
                                color=cor,
                            )

            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            doc.close()

            st.success("✅ PDF processado com sucesso!")
            st.download_button(
                label="⬇️ Baixar PDF colorido",
                data=output_buffer.getvalue(),
                file_name="pdf_colorido.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")
