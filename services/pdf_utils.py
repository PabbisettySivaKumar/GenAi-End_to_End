import fitz

from typing import List, Tuple

def highlight_text_on_page(pdf_path: str, page_num: int, snippet: str, out_path: str):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num - 1)  # 0-indexed
    text_instances = page.search_for(snippet)
    for inst in text_instances:
        highlight = page.add_highlight_annot(inst)
        highlight.update()
    pix = page.get_pixmap(dpi=150)
    pix.save(out_path)
    doc.close()