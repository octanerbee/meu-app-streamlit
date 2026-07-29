import streamlit as st
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger
from streamlit_sortables import sort_items
import io
import base64
import re
import os
import streamlit.components.v1 as components
import tempfile
from PIL import Image

LAUDOS_PASTA_PADRAO = "laudos"


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

def extrair_patrimonios(pdf_bytes):
    """
    Varre o texto do PDF final procurando os blocos de
    'Instrumento Utilizado' + 'Número de patrimônio' (nos dois
    formatos observados) e retorna uma lista de dicts únicos:
    [{"numero": "0006", "instrumento": "Compano 100"}, ...]
    O número é sempre normalizado para 4 dígitos.
    """

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    numero_regex = re.compile(
        r"N[uú]mero\s+de\s+[Pp]atrim[oô]nio:?\s*\n?\s*(\d{1,6})",
        re.IGNORECASE
    )
    instrumento_regex = re.compile(
        r"Instrumento\s+[Uu]tilizado:?\s*\n?\s*([^\n•]{2,80})",
        re.IGNORECASE
    )

    numeros_todos = []
    instrumentos_todos = []

    for page in doc:
        texto = page.get_text("text")

        for m in numero_regex.finditer(texto):
            numeros_todos.append(m.group(1))

        for m in instrumento_regex.finditer(texto):
            instrumentos_todos.append(m.group(1).strip())

    doc.close()

    resultado = []
    vistos = set()

    for i, numero in enumerate(numeros_todos):
        numero_padded = numero.strip().zfill(4)

        if numero_padded in vistos:
            continue

        vistos.add(numero_padded)

        instrumento = instrumentos_todos[i] if i < len(instrumentos_todos) else "Instrumento não identificado"

        resultado.append({"numero": numero_padded, "instrumento": instrumento})

    return resultado


def buscar_laudos_pasta(pasta):
    """Lê os PDFs de uma pasta local, indexando pelo nome do arquivo (número de patrimônio)."""

    laudos = {}

    if pasta and os.path.isdir(pasta):
        for nome_arquivo in os.listdir(pasta):
            if nome_arquivo.lower().endswith(".pdf"):
                numero = os.path.splitext(nome_arquivo)[0].strip().zfill(4)
                caminho = os.path.join(pasta, nome_arquivo)
                try:
                    with open(caminho, "rb") as f:
                        laudos[numero] = f.read()
                except Exception:
                    pass

    return laudos


def laudos_de_uploads(arquivos):
    """Indexa arquivos enviados via st.file_uploader pelo nome (número de patrimônio)."""

    laudos = {}

    if arquivos:
        for arq in arquivos:
            numero = os.path.splitext(arq.name)[0].strip().zfill(4)
            laudos[numero] = arq.read()

    return laudos


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
                        elif "Transformador Média Tensão a Seco" in text and "TRANSFORMADOR DE MÉDIA TENSÃO" not in targets:
                            targets["TRANSFORMADOR DE MÉDIA TENSÃO"] = page_num
                        elif "Transformador Média Tensão a Óleo" in text and "TRANSFORMADOR DE MÉDIA TENSÃO" not in targets:
                            targets["TRANSFORMADOR DE MÉDIA TENSÃO"] = page_num
                        elif "Disjuntor Baixa Tensão" in text and "DISJUNTOR DE BAIXA TENSÃO" not in targets:
                            targets["DISJUNTOR DE BAIXA TENSÃO"] = page_num
                        elif "Retificador/Baterias" in text and "RETIFICADOR/BATERIAS" not in targets:
                            targets["RETIFICADOR/BATERIAS"] = page_num
                        elif "Banco de baterias" in text and "BANCO DE BATERIAS" not in targets:
                            targets["BANCO DE BATERIAS"] = page_num
                        elif "Relé diferencial" in text and "RELÉ DIFERENCIAL" not in targets:
                            targets["RELÉ DIFERENCIAL"] = page_num
                        elif "Transformadores de Corrente Alta Tensão" in text and "TRANFORMADOR ED CORRENTE" not in targets:
                            targets["TRANSFORMADOR DE CORRENTE"] = page_num
                        elif "Transformadores de Potencial Alta Tensão" in text and "TRANSFORMADOR DE POTENCIAL" not in targets:
                            targets["TRANSFORMADOR DE POTENCIAL"] = page_num
                        elif "Transformador Alta Tensão a Óleo" in text and "TRANSFORMADOR DE ALTA TENSÃO" not in targets:
                            targets["TRANSFORMADOR DE ALTA TENSÃO"] = page_num
                        elif "Disjuntor Alta Tensão" in text and "DISJUNTOR DE ALTA TENSÃO" not in targets:
                            targets["DISJUNTOR DE ALTA TENSÃO"] = page_num
                        elif "Resistor de Aterramento" in text and "RESISTOR DE ATERRAMENTO" not in targets:
                            targets["RESISTOR DE ATERRAMENTO"] = page_num
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

    st.header("4️⃣ Anexar laudos de aferição dos instrumentos")

    if "laudos_manuais" not in st.session_state:
        st.session_state["laudos_manuais"] = {}
    if "patrimonios_detectados" not in st.session_state:
        st.session_state["patrimonios_detectados"] = None
    if "pdf_com_laudos" not in st.session_state:
        st.session_state["pdf_com_laudos"] = None

    if not st.session_state.get("pdf_final"):
        st.info("Gere o PDF final (etapas 1 a 3) antes de anexar os laudos.")
    else:
        pasta_laudos = LAUDOS_PASTA_PADRAO

        arquivos_laudos = st.file_uploader(
            "📤 Envie os laudos (PDF, nome = número de patrimônio, ex: 0034.pdf):",
            type=["pdf"],
            accept_multiple_files=True,
            key="upload_laudos"
        )

        if st.button("🔍 Buscar laudos no relatório", key="btn_buscar_laudos"):
            st.session_state["patrimonios_detectados"] = extrair_patrimonios(st.session_state["pdf_final"])

        patrimonios = st.session_state.get("patrimonios_detectados")

        if patrimonios:
            laudos_disponiveis = {}
            laudos_disponiveis.update(buscar_laudos_pasta(pasta_laudos))
            laudos_disponiveis.update(laudos_de_uploads(arquivos_laudos))
            laudos_disponiveis.update(st.session_state["laudos_manuais"])

            faltando_itens = []

            st.write("#### 📋 Instrumentos detectados no relatório:")

            for item in patrimonios:
                numero = item["numero"]
                instrumento = item["instrumento"]

                if numero in laudos_disponiveis:
                    st.write(f"✅ **{numero}** — {instrumento} — laudo encontrado")
                else:
                    faltando_itens.append(item)
                    st.write(f"❌ **{numero}** — {instrumento} — laudo **NÃO** encontrado")

            if faltando_itens:
                st.warning(
                    f"⚠️ {len(faltando_itens)} laudo(s) não encontrado(s). "
                    "Você pode enviá-los individualmente abaixo (isso não bloqueia o download do PDF)."
                )

                for item in faltando_itens:
                    numero = item["numero"]
                    instrumento = item["instrumento"]

                    arquivo_manual = st.file_uploader(
                        f"Enviar laudo do patrimônio {numero} ({instrumento}):",
                        type=["pdf"],
                        key=f"laudo_manual_{numero}"
                    )

                    if arquivo_manual is not None:
                        st.session_state["laudos_manuais"][numero] = arquivo_manual.read()
                        st.success(f"Laudo do patrimônio {numero} recebido. Clique em '🔍 Buscar laudos' de novo ou anexe abaixo.")

            if st.button("📎 Anexar laudos ao PDF final", key="btn_anexar_laudos"):
                try:
                    laudos_disponiveis.update(st.session_state["laudos_manuais"])

                    doc_final = fitz.open(stream=st.session_state["pdf_final"], filetype="pdf")

                    anexados = []
                    ainda_faltando = []

                    for item in patrimonios:
                        numero = item["numero"]
                        dados_laudo = laudos_disponiveis.get(numero)

                        if dados_laudo:
                            try:
                                laudo_doc = fitz.open(stream=dados_laudo, filetype="pdf")
                                doc_final.insert_pdf(laudo_doc)
                                laudo_doc.close()
                                anexados.append(numero)
                            except Exception:
                                ainda_faltando.append(numero)
                        else:
                            ainda_faltando.append(numero)

                    buf_com_laudos = io.BytesIO()
                    doc_final.save(buf_com_laudos, garbage=4, deflate=True, clean=True)
                    doc_final.close()
                    buf_com_laudos.seek(0)

                    st.session_state["pdf_com_laudos"] = buf_com_laudos.getvalue()

                    if anexados:
                        st.success(f"✅ {len(anexados)} laudo(s) anexado(s): {', '.join(anexados)}")
                    if ainda_faltando:
                        st.warning(
                            f"⚠️ Ainda faltam laudos para: {', '.join(ainda_faltando)}. "
                            "O PDF foi gerado mesmo assim, sem esses laudos."
                        )
                except Exception as e:
                    st.error(f"❌ Erro ao anexar laudos: {e}")
        else:
            st.info("Clique em '🔍 Buscar laudos no relatório' para identificar os instrumentos utilizados.")

    if st.session_state.get("pdf_final"):
        st.markdown("---")
        st.subheader("📥 Baixar PDF final")

        pdf_para_baixar = st.session_state.get("pdf_com_laudos") or st.session_state["pdf_final"]

        if st.session_state.get("pdf_com_laudos"):
            st.caption("ℹ️ Baixando a versão com os laudos de aferição anexados.")

        nome_arquivo = st.text_input(
            "📝 Nome do arquivo final (sem .pdf):",
            value=gerar_nome_automatico(pdf_para_baixar),
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
            data=pdf_para_baixar,
            file_name=nome_arquivo,
            mime="application/pdf",
            key="download_final"
        )


        mostrar_preview_pdf(pdf_para_baixar)

    st.markdown("---")
    if st.button("🔄 Reiniciar / Limpar sessão", key="btn_clear"):
        for k in ["pdf_unido", "pdf_colorido", "pdf_final", "pdf_com_laudos", "patrimonios_detectados", "laudos_manuais"]:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()

        mostrar_preview_pdf(st.session_state["pdf_final"])

if __name__ == "__main__":
    run()
