import streamlit as st
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger
from streamlit_sortables import sort_items
import io
import base64
import re
import streamlit.components.v1 as components
import tempfile
from PIL import Image


def mostrar_preview_pdf(pdf_bytes):

    try:

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        total_paginas = len(doc)

        st.info(f"📄 Preview do PDF ({total_paginas} páginas)")

        mat = fitz.Matrix(1.2, 1.2)

        colunas_por_linha = 3

        for i in range(0, total_paginas, colunas_por_linha):

            cols = st.columns(colunas_por_linha)

            for j in range(colunas_por_linha):

                pagina_idx = i + j

                if pagina_idx >= total_paginas:
                    break

                page = doc[pagina_idx]

                pix = page.get_pixmap(matrix=mat)

                img_bytes = pix.tobytes("png")

                with cols[j]:

                    st.image(
                        img_bytes,
                        caption=f"Página {pagina_idx + 1}",
                        use_container_width=True
                    )

        doc.close()

    except Exception as e:

        st.error(f"Erro ao gerar preview: {e}")

def gerar_nome_automatico(pdf_bytes):

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        texto = doc[0].get_text("text")

        doc.close()

        linhas = [l.strip() for l in texto.split("\n") if l.strip()]

        codigo_servico = "OU"

        servicos = {
            "MANUTENÇÃO PREVENTIVA": "MP",
            "MANUTENÇÃO CORRETIVA": "MC",
            "TERMOGRAFIA": "TM",
            "ULTRASSOM": "US",
            "COMISSIONAMENTO": "CO",
            "SPDA": "SP",
            "ANÁLISE DE ÓLEO": "OL",
        }

        texto_upper = texto.upper()

        for nome, sigla in servicos.items():
            if nome in texto_upper:
                codigo_servico = sigla
                break

        bee = "BEE0000-00"


        bee_match = re.search(r"BEE\s*(\d+)\s*/\s*(\d+)", texto_upper)

        if bee_match:
            numero = bee_match.group(1).zfill(4)
            ano = bee_match.group(2)

            bee = f"BEE{numero}-{ano}"

        cliente_unidade = "CLIENTE"

        for linha in linhas:

            if "BEE" in linha.upper():
                continue

            if "-" in linha or "–" in linha:
                cliente_unidade = linha.replace("/", "-")
                break

        cidade = "CIDADE"

        for linha in linhas:

            estados = [
                "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
                "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
                "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
            ]

            for linha in linhas:

                linha_upper = linha.upper()

                for uf in estados:

                    if f"- {uf}" in linha_upper:
                        cidade = linha.split("-")[0].strip()
                        break

        cliente_unidade = cliente_unidade.replace("/", "-")
        cliente_unidade = cliente_unidade.replace(":", "")
        cidade = cidade.replace(":", "")

        nome_final = f"{bee}-{cliente_unidade}-{cidade}-{codigo_servico}.pdf"

        return nome_final

    except Exception as e:
        print(e)
        return "BEE0000-CLIENTE-CIDADE-OU.pdf"

def run():

    st.set_page_config(page_title="PDF Automático Completo", page_icon="📄", layout="wide")

    st.title("📄 Processador Completo de PDF")
    st.markdown("### Fluxo: Juntar PDFs → Colorir Condições → Criar Índice Navegável")

    st.header("1️⃣ Juntar e organizar PDFs")

    uploaded_files = st.file_uploader(
        "Envie os arquivos PDF:",
        type=["pdf"],
        accept_multiple_files=True
    )
    incluir_pagina_final = st.checkbox(
        "📄 Incluir última página padrão",
        value=True
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

                if incluir_pagina_final:
                    merger.append("ultima_pagina_padrao.pdf")

                output = io.BytesIO()
                merger.write(output)
                merger.close()
                output.seek(0)

                st.session_state["pdf_unido"] = output.getvalue()
                st.success("✅ PDFs unidos com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao juntar PDFs: {e}")

    st.header("2️⃣ Colorir condições automaticamente")

    TEXTOS_CORES = {
        "Equipamento em boas condições para operação": (0, 0.8, 0),
        "Resultados indicam que o equipamento está em boas condições de operação.": (0, 0.8, 0),
        "Equipamento requer intervenção.": (1, 0, 0),
        "Resultados indicam que o equipamento está apto a operar, salvo seguintes observações.": (0.8, 0.8, 0),
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
                                    fontname="helvetica-bold",
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
                            # mantém o link clicável
                            index_page.insert_link({
                                "kind": fitz.LINK_GOTO,
                                "from": bbox,
                                "page": pagina_destino,
                                "zoom": 0
                            })

                        for xxx_rect in index_page.search_for("XXX"):

                            if abs(xxx_rect.y0 - bbox.y0) < 3:
                                index_page.add_redact_annot(
                                    xxx_rect,
                                    fill=(1, 1, 1)
                                )

                                index_page.apply_redactions()

                                index_page.insert_text(
                                    (xxx_rect.x0, xxx_rect.y1 - 2),
                                    str(pagina_destino + 1),
                                    fontsize=14,
                                    fontname = "helv",
                                    color=(0, 0, 0)
                                )

                                break
                    
                    total_paginas = len(pdf_temp)

                    for page_num in range(1, len(pdf_temp)):
                        page = pdf_temp[page_num]

                        rect = page.rect

                        pagina_atual = page_num + 1

                        texto = f"Página {pagina_atual} de {total_paginas}"

                        x = rect.width - 120
                        y = rect.height - 24

                        page.insert_text(
                            (x, y),
                            texto,
                            fontsize=10,
                            fontname="helv",
                            color=(1, 1, 1)
                        )

                    pdf_final_buf = io.BytesIO()

                    pdf_temp.save(
                        pdf_final_buf,
                        garbage=4,
                        deflate=True,
                        clean=True
                    )

                    pdf_temp.close()

                    pdf_final_buf.seek(0)

                    doc_final = fitz.open(
                        stream=pdf_final_buf.getvalue(),
                        filetype="pdf"
                    )

                    pdf_limpo = io.BytesIO()

                    doc_final.save(
                        pdf_limpo,
                        garbage=4,
                        deflate=True,
                        clean=True
                    )

                    doc_final.close()

                    pdf_limpo.seek(0)

                    st.session_state["pdf_final"] = pdf_limpo.getvalue()

                    st.success("✅ PDF final gerado com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro ao criar índice navegável: {e}")

    if st.session_state.get("pdf_final"):
        st.markdown("---")
        st.subheader("📥 Baixar PDF final")

        nome_arquivo = st.text_input(
            "📝 Nome do arquivo final (sem .pdf):",
            value=gerar_nome_automatico(st.session_state["pdf_final"]),
            key="nome_arquivo_input"
        ).strip()

        if nome_arquivo == "":
            nome_arquivo = "BEE0000-26-Cliente-Unidade-Cidade-Código do Serviço"
        if not nome_arquivo.lower().endswith(".pdf"):
            nome_arquivo = nome_arquivo + ".pdf"
        st.write("""Exemplos:    
1.	BEE0010-MBRF-Ração-Videira-MP
2.  BEE0015-KRONA-Tubos-Joinville-MC
3.	BEE0128-CISER-Araquari-OL
4.	BEE0130-WEG-Laboratório-Jaraguá-MP
5.	BEE0135-WEG-Trafos-Itajaí-SPDA
6.	BEE0150-WEG-Trafos-Blumenau-MP
7.	BEE1026-MBRF-Frigorífico-Francisco Beltrão-MP

Código dos serviços padronizados:

    MP – Manutenção Preventiva
    MC – Manutenção Corretiva
    TM – Termografia 
    US – Ultrassom 
    CO – Comissionamento
    SP – SPDA
    TE – Malha de Terra
    OL – Análise de Óleo
    CS – Consultoria
    EE – Estudos Elétricos
    BK – BEEKit
    AU – Automação (pode ser PME, EPO, ou qualquer outro software de controle)
    TR – Troca de equipamentos (pode ser relé, disjuntor, medidor ou qualquer outro)
    MD – Medição de grandezas
    OU – Qualquer atividade que não se enquadra nos critérios acima
""")
        st.markdown("---")
        st.subheader("👁 Preview do PDF final")


        st.download_button(
            "📥 Baixar PDF FINAL",
            data=st.session_state["pdf_final"],
            file_name=nome_arquivo,
            mime="application/pdf",
            key="download_final"
        )


        mostrar_preview_pdf(st.session_state["pdf_final"])

    st.markdown("---")
    if st.button("🔄 Reiniciar / Limpar sessão", key="btn_clear"):
        for k in ["pdf_unido", "pdf_colorido", "pdf_final"]:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()

        mostrar_preview_pdf(st.session_state["pdf_final"])

if __name__ == "__main__":
    run()
