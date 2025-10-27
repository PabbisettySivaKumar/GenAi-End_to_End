import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_pdf(pdf_path):
    docs= fitz.open(pdf_path)
    chunks= []
    splitter= RecursiveCharacterTextSplitter(
        chunk_size= 3000,
        chunk_overlap= 1000
    )
    for page_number, page in enumerate(docs, start=1):
        text= page.get_text("text").strip()
        if not text:
            continue
    
        page_chunks= splitter.split_text(text)
        for i, chunk_text in enumerate(page_chunks):
            chunks.append({
                "chunk_id": f"{page_number}_{i}",
                    "page": page_number,
                    "text": chunk_text
            })
    print(len(chunks))
    return chunks