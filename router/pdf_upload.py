from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from services.chunking import chunk_pdf
from utils.embeddings import get_embeddings
from services.storage import store_project_graph, store_metadata
import tempfile
import fitz
from datetime import datetime
import pytz
import os
from typing import List

router= APIRouter()

ist= pytz.timezone('Asia/Kolkata')

@router.post('/upload')
async def upload_pdfs(
    files: List[UploadFile] = File(..., description= "Upload upto 2 Files"),
    project_name: str = Form("default_project")):

    if not files or len(files)==0:
        raise HTTPException(status_code= 400, detail= "Atleast One pdf must be added.")
    if len(files) > 2:
        raise HTTPException(status_code=400, detail="Limit: 2 PDFs only.")

    uploaded_files = []
    all_chunks = []
    pdf_metadata = []

    for f in files:
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_pdf.write(await f.read())
        temp_pdf.close()
        try:
            doc = fitz.open(temp_pdf.name)
            pages = len(doc)
        except Exception as e:
            os.remove(temp_pdf.name)
            raise HTTPException(status_code=500, detail=f"Error reading PDF: {e}")

        chunks = chunk_pdf(temp_pdf.name)
        for c in chunks:
            #print(c["text"])
            c["embedding"]= get_embeddings(c["text"])
            c["pdf_name"]= f.filename
        all_chunks.extend(chunks)
        os.remove(temp_pdf.name)
        

        pdf_info = {
            "name": f.filename,
            "pages": pages,
            "uploaded_at": datetime.now(ist).isoformat(),
        }
        pdf_metadata.append(pdf_info)
        #uploaded_files.append(f.filename)

        store_metadata({
            "project": project_name,
            "pdf_name": f.filename,
            "num_pages": pages,
            "upload_time": datetime.now(ist).isoformat()
        })

        uploaded_files.append(f.filename)

    store_project_graph(project_name, pdf_metadata, all_chunks)

    return {
        "project": project_name,
        "uploaded_files": uploaded_files,
        "total_chunks": len(all_chunks),
        "status": "Successfully processed and stored in Neo4j + MongoDB."
    }
