import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_pdf(pdf_path):
    docs= fitz.open(pdf_path)
    text= ''
    for page in docs:
        text= text+page.get_text()
    
    splitter= RecursiveCharacterTextSplitter(
        chunk_size= 1000,
        chunk_overlap= 200
    )

    chunks= splitter.split_text(text)
    print(chunks)
    return [
        {'chunk_id':i, 'text': chunk}
        for i, chunks in enumerate(chunks)
    ]
