import fitz  # PyMuPDF
import streamlit as st
import io

def run():

    st.set_page_config(page_title="Criar Índice Navegável em PDF", layout="centered")

    st.title("📘 Criar Índice Navegável em PDF")
    st.write("Envie o relatório PDF e o app criará automaticamente links internos no índice.")

    uploaded_file = st.file_uploader("📎 Envie o arquivo PDF", type=["pdf"])

    if uploaded_file:
        pdf_bytes = uploaded_file.read()
        pdf = fitz.open(stream=pdf_bytes, filetype="pdf")

        pagina_indice = st.number_input(
            "Informe o número da página onde está o índice (começa em 1):",
            min_value=1,
            max_value=len(pdf),
            value=3,
            step=1
        )
        pagina_indice -= 1

        if st.button("🚀 Criar Índice Navegável"):
            targets = {}

            for page_num in range(len(pdf)):
                page = pdf[page_num]
                text = page.get_text("text")

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

            index_page = pdf[pagina_indice]

            for titulo, pagina_destino in targets.items():
                for bbox in index_page.search_for(titulo):
                    index_page.insert_link({
                        "kind": fitz.LINK_GOTO,
                        "from": bbox,
                        "page": pagina_destino,
                        "zoom": 0
                    })

            output_pdf = io.BytesIO()
            pdf.save(output_pdf)
            pdf.close()
            output_pdf.seek(0)

            st.success("✅ Índice navegável criado com sucesso!")

            st.download_button(
                label="📥 Baixar PDF com Índice Navegável",
                data=output_pdf,
                file_name="relatorio_com_links.pdf",
                mime="application/pdf"
            )
