import streamlit as st
from PyPDF2 import PdfMerger
import io
from streamlit_sortables import sort_items

def run():

    st.set_page_config(page_title="Juntar PDFs", page_icon="🖇️", layout="centered")

    st.title("🖇️ Juntar e Organizar PDFs")

    uploaded_files = st.file_uploader(
        "Envie os arquivos PDF que deseja juntar:",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        nomes = [f.name for f in uploaded_files]
        st.write("### 🗂️ Arraste os arquivos para definir a ordem:")

        sorted_items = sort_items(nomes, direction="vertical", key="sortable_list")

        st.write("#### ✅ Ordem final escolhida:")
        for i, nome in enumerate(sorted_items, start=1):
            st.write(f"{i}. {nome}")

        if st.button("📎 Juntar PDFs"):
            try:
                merger = PdfMerger()

                arquivos_ordenados = [next(f for f in uploaded_files if f.name == nome) for nome in sorted_items]

                for pdf in arquivos_ordenados:
                    merger.append(io.BytesIO(pdf.read()))

                output = io.BytesIO()
                merger.write(output)
                merger.close()

                st.success("✅ PDFs unidos com sucesso!")
                st.download_button(
                    label="⬇️ Baixar PDF unificado",
                    data=output.getvalue(),
                    file_name="pdf_unido.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"❌ Erro ao juntar PDFs: {e}")
