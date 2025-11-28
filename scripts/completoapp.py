import streamlit as st
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger
from streamlit_sortables import sort_items
import io

def run():

    st.set_page_config(page_title="PDF Automático Completo", page_icon="📄", layout="wide")

    st.title("📄 Processador Completo de PDF")
    st.markdown("### Fluxo: Juntar PDFs → Colorir Condições → Criar Índice Navegável")

    # ============================
    # 1. UPLOAD E ORDENAÇÃO
    # ============================
    st.header("1️⃣ Juntar e organizar PDFs")

    uploaded_files = st.file_uploader(
        "Envie os arquivos PDF:",
        type=["pdf"],
        accept_multiple_files=True
    )

    if "pdf_unido" not in st.session_state:
        st.session_state["pdf_unido"] = None
    if "pdf_colorido" not in st.session_state:
        st.session_state["pdf_colorido"] = None
    if "pdf_final" not in st.session_state:
        st.session_state["pdf_final"] = None

    if uploaded_files:
        nomes = [f.name for f in uploaded_files]
        st.write("🗂️ Arraste para definir a ordem:")
        sorted_items = sort_items(nomes, direction="vertical", key="sortable_list")

        st.write("#### ✅ Ordem final escolhida:")
        for i, nome in enumerate(sorted_items, start=1):
            st.write(f"{i}. {nome}")

        if st.button("📎 Juntar PDFs", key="btn_juntar"):
            try:
                merger = PdfMerger()
                arquivos_ordenados = [next(f for f in uploaded_files if f.name == nome) for nome in sorted_items]

                for pdf in arquivos_ordenados:
                    pdf_bytes = pdf.read()
                    merger.append(io.BytesIO(pdf_bytes))

                output = io.BytesIO()
                merger.write(output)
                merger.close()
                output.seek(0)

                st.session_state["pdf_unido"] = output.getvalue()
                st.success("✅ PDFs unidos com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao juntar PDFs: {e}")

    if st.session_state.get("pdf_unido"):
        st.markdown("**PDF unido disponível.**")
        st.download_button(
            label="⬇️ Baixar PDF unificado (intermediário)",
            data=st.session_state["pdf_unido"],
            file_name="pdf_unido.pdf",
            mime="application/pdf",
            key="download_unido"
        )

    # ============================
    # 2. COLORIR CONDIÇÕES
    # ============================
    st.header("2️⃣ Colorir condições automaticamente")

    TEXTOS_CORES = {
        "Equipamento em boas condições para operação": (0, 0.8, 0),
        "Equipamento requer intervenção": (1, 0, 0),
        "EM ANÁLISE": (1, 1, 0),
    }

    if st.session_state.get("pdf_unido"):
        if st.button("🎨 Aplicar coloração", key="btn_colorir"):
            try:
                doc = fitz.open(stream=st.session_state["pdf_unido"], filetype="pdf")

                for page in doc:
                    for texto_alvo, cor in TEXTOS_CORES.items():
                        areas = page.search_for(texto_alvo)
                        for rect in areas:
                            trecho = page.get_text("text", clip=rect).strip()
                            if trecho == texto_alvo:
                                page.draw_rect(rect, color=(1,1,1), fill=(1, 1, 1))
                                x = rect.x0
                                y = rect.y1 - 1
                                page.insert_text(
                                    (x, y),
                                    texto_alvo,
                                    fontsize=12,
                                    fontname="times-bold",
                                    color=cor,
                                )

                pdf_colorido_buf = io.BytesIO()
                doc.save(pdf_colorido_buf)
                doc.close()
                pdf_colorido_buf.seek(0)

                st.session_state["pdf_colorido"] = pdf_colorido_buf.getvalue()
                st.success("✅ Condições coloridas aplicadas")
            except Exception as e:
                st.error(f"❌ Erro ao aplicar coloração: {e}")
    else:
        st.info("Faça a junção de PDFs primeiro (etapa 1) para aplicar a coloração.")

    if st.session_state.get("pdf_colorido"):
        st.download_button(
            label="⬇️ Baixar PDF colorido (intermediário)",
            data=st.session_state["pdf_colorido"],
            file_name="pdf_colorido.pdf",
            mime="application/pdf",
            key="download_colorido"
        )

    # ============================
    # 3. ÍNDICE NAVEGÁVEL
    # ============================
    st.header("3️⃣ Criar índice navegável")

    pdf_bytes_for_index = st.session_state.get("pdf_colorido") or st.session_state.get("pdf_unido")

    if not pdf_bytes_for_index:
        st.info("PDF final ainda não está disponível. Faça as etapas 1 e 2 primeiro.")
    else:
        try:
            pdf_temp = fitz.open(stream=pdf_bytes_for_index, filetype="pdf")
        except Exception as e:
            st.error(f"❌ Não foi possível abrir o PDF para criar índice: {e}")
            pdf_temp = None

        if pdf_temp:
            pagina_indice = st.number_input(
                "Página do índice (começa em 1):",
                min_value=1,
                max_value=len(pdf_temp),
                value=3,
                key="pagina_indice_input"
            ) - 1

            if st.button("📘 Criar índice", key="btn_indice"):
                try:
                    targets = {}

                    for page_num in range(len(pdf_temp)):
                        text = pdf_temp[page_num].get_text("text")

                        if "Teste Em Painel e Cabos de Média Tensão" in text and "PAINEL DE MÉDIA TENSÃO" not in targets:
                            targets["PAINEL DE MÉDIA TENSÃO"] = page_num
                        elif "Relé de sobrecorrente" in text and "RELÉ DE SOBRECORRENTE" not in targets:
                            targets["RELÉ DE SOBRECORRENTE"] = page_num
                        elif "Disjuntor Média Tensão" in text and "DISJUNTOR DE MÉDIA TENSÃO" not in targets:
                            targets["DISJUNTOR DE MÉDIA TENSÃO"] = page_num
                        elif "Para-raios" in text and "PARA-RAIOS" not in targets:
                            targets["PARA-RAIOS"] = page_num
                        elif "Chave Seccionadora" in text and "CHAVE-SECCIONADORA" not in targets:
                            targets["CHAVE-SECCIONADORA"] = page_num
                        elif "Transformadores de Corrente" in text and "TRANSFORMADOR DE CORRENTE" not in targets:
                            targets["TRANSFORMADOR DE CORRENTE"] = page_num
                        elif "Transformadores de Potencial" in text and "TRANSFORMADOR DE POTENCIAL" not in targets:
                            targets["TRANSFORMADOR DE POTENCIAL"] = page_num
                        elif "Transformadores Média Tensão a Seco" in text and "TRANSFORMADOR DE MÉDIA TENSÃO" not in targets:
                            targets["TRANSFORMADOR DE MÉDIA TENSÃO"] = page_num
                        elif "Transformadores Média Tensão a Óleo" in text and "TRANSFORMADOR DE MÉDIA TENSÃO" not in targets:
                            targets["TRANSFORMADOR DE MÉDIA TENSÃO"] = page_num
                        elif "Disjuntor Baixa Tensão" in text and "DISJUNTOR DE BAIXA TENSÃO" not in targets:
                            targets["DISJUNTOR DE BAIXA TENSÃO"] = page_num

                    st.subheader("📄 Mapeamento encontrado:")
                    for k, v in targets.items():
                        st.write(f"**{k}** → página {v + 1}")

                    index_page = pdf_temp[pagina_indice]

                    for titulo, pagina_destino in targets.items():
                        for bbox in index_page.search_for(titulo):
                            index_page.insert_link({
                                "kind": fitz.LINK_GOTO,
                                "from": bbox,
                                "page": pagina_destino,
                                "zoom": 0
                            })

                    pdf_final_buf = io.BytesIO()
                    pdf_temp.save(pdf_final_buf)
                    pdf_temp.close()
                    pdf_final_buf.seek(0)

                    st.session_state["pdf_final"] = pdf_final_buf.getvalue()

                    st.success("✅ PDF final gerado com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro ao criar índice navegável: {e}")

    # Se o PDF final existe, mostrar campo de nome e botão de download
    if st.session_state.get("pdf_final"):
        st.markdown("---")
        st.subheader("📥 Baixar PDF final")

        nome_arquivo = st.text_input(
            "📝 Nome do arquivo final (sem .pdf):",
            value="BEE ___-25 M.P. SE CLIENTE",
            key="nome_arquivo_input"
        ).strip()

        # Normaliza o nome e garante extensão .pdf
        if nome_arquivo == "":
            nome_arquivo = "BEE ___-25 M.P. SE CLIENTE"
        if not nome_arquivo.lower().endswith(".pdf"):
            nome_arquivo = nome_arquivo + ".pdf"

        st.download_button(
            "📥 Baixar PDF FINAL",
            data=st.session_state["pdf_final"],
            file_name=nome_arquivo,
            mime="application/pdf",
            key="download_final"
        )

    # ============================
    # Opcional: limpar sessão
    # ============================
    st.markdown("---")
    if st.button("🔄 Reiniciar / Limpar sessão", key="btn_clear"):
        for k in ["pdf_unido", "pdf_colorido", "pdf_final"]:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()

if __name__ == "__main__":
    run()
