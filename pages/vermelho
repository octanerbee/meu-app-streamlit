import fitz  # PyMuPDF
import glob
import os

def destacar_nao_conforme(path_pdf):
    doc = fitz.open(path_pdf)

    for pagina in doc:
        instancias = pagina.search_for("Não conforme")

        for inst in instancias:

            r = fitz.Rect(inst.x0-7, inst.y0-6, inst.x1+7, inst.y1+6) # tamanho da caixa, fonte 12

            # borda, com a cor igual n muda muito
            pagina.draw_rect(
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

    doc.save(path_pdf, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()
    print(f"✔ Editado: {path_pdf}")


def processar_pasta(pasta):
    arquivos = glob.glob(os.path.join(pasta, "*.pdf"))
    if not arquivos:
        print("⚠ Nenhum PDF encontrado na pasta.")
        return

    for arq in arquivos:
        destacar_nao_conforme(arq)


# exemplo de uso
processar_pasta("pdfs_entrada/")
