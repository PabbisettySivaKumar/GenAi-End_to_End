"""
router/pdf_upload.py

Handles PDF upload, chunking, embedding, and storage in Neo4j + MongoDB.
Implements an OOP-based class (PDFUploader) with FastAPI route defined here itself.
"""

import os
import fitz
import tempfile
import logging
import pytz
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from services.chunking import DocumentChunker
from utils.embeddings import OllamaEmbedder
from services.storage import Neo4jStorage, MongoMetadata


# Logging Configuration
logger = logging.getLogger(__name__)


# FastAPI Router
router = APIRouter()
IST = pytz.timezone("Asia/Kolkata")

UPLOAD_DIR= Path("uploaded_pdfs")
UPLOAD_DIR.mkdir(exist_ok=True)

# PDFUploader Class
class PDFUploader:
    """
    A class that encapsulates the end-to-end PDF upload and processing flow:
    1. Save uploaded PDFs permanently.
    2. Extract text chunks using DocumentChunker.
    3. Generate embeddings using OllamaEmbedder.
    4. Store metadata + graph structure in Neo4j & MongoDB.
    """

    def __init__(self, timezone: str = "Asia/Kolkata"):
        """Initialize core services and timezone."""
        self.chunker = DocumentChunker()
        self.embedder = OllamaEmbedder()
        self.storage = Neo4jStorage()
        self.mongo= MongoMetadata()
        self.ist = pytz.timezone(timezone)
        logger.info("PDFUploader initialized with timezone: %s", timezone)

    # Helper Methods
    def _save_pdf_permanent(self, file: UploadFile, project_name: str) -> str:
        """Save uploaded PDF to a permanet filefolder and return its path."""
        try:
            project_dir= UPLOAD_DIR/project_name
            project_dir.mkdir(exist_ok= True)

            pdf_path= project_dir/file.filename
            with open(pdf_path, "wb") as f:
                f.write(file.file.read())
            logger.info(f"Saved uploaded PDF Permanently at: {pdf_path}")
            return str(pdf_path)
        except Exception as e:
            logger.error("Failed to save Permanent PDF: %s", e)
            raise

    def _get_pdf_page_count(self, pdf_path: str) -> int:
        """Return the number of pages in the given PDF."""
        try:
            doc = fitz.open(pdf_path)
            pages = len(doc)
            logger.info("PDF '%s' has %d pages", pdf_path, pages)
            return pages
        except Exception as e:
            logger.error("Error reading PDF '%s': %s", pdf_path, e)
            raise

    def _chunk_and_embed(self, pdf_path: str, pdf_name: str) -> List[Dict]:
        """Chunk PDF text and generate embeddings for each chunk."""
        try:
            chunks = self.chunker.chunk_pdf(pdf_path)
            if not chunks:
                raise ValueError("No text chunks extracted from PDF.")
            logger.info("Extracted %d chunks from %s", len(chunks), pdf_name)

            for c in chunks:
                try:
                    c["embedding"]= self.embedder.embed_query(c["text"])
                    c["pdf_name"]= pdf_name
                    c["pdf_path"]= pdf_path 
                except Exception as e:
                    logger.warning("Embedding failed for chunk in %s: %s", pdf_name, e)
                    c["embedding"] = []
            return chunks
        except Exception as e:
            logger.error("Chunking/embedding failed for %s: %s", pdf_name, e)
            raise

    def _store_metadata(self, project_name: str, pdf_name: str, pages: int):
        """Store PDF metadata into MongoDB via storage helper."""
        try:
            metadata = {
                "project": project_name,
                "pdf_name": pdf_name,
                "num_pages": pages,
                "upload_time": datetime.now(self.ist).isoformat(),
            }
            self.mongo.store_metadata(metadata)
            logger.info("Stored metadata for %s", pdf_name)
        except Exception as e:
            logger.error("MongoDB metadata insertion failed: %s", e)
            raise

    # Main Processing Logic
    def process_pdfs(self, files: List[UploadFile], project_name: str = "default_project") -> dict:
        """
        Orchestrate the full PDF upload + processing flow.

        Args:
            files (List[UploadFile]): Uploaded PDF files.
            project_name (str): Name of the project.

        Returns:
            dict: Summary of processing result.
        """
        uploaded_files = []
        all_chunks = []
        pdf_metadata = []

        for f in files:
            logger.info("Processing PDF: %s", f.filename)
            perm_path = self._save_pdf_permanent(f, project_name)

            try:
                pages = self._get_pdf_page_count(perm_path)
                chunks = self._chunk_and_embed(perm_path, f.filename)

                uploaded_files.append(f.filename)
                pdf_metadata.append({
                    "pdf_name": f.filename,
                    "pages": pages,
                    "uploaded_at": datetime.now(self.ist).isoformat(),
                })
                all_chunks.extend(chunks)

                self._store_metadata(project_name, f.filename, pages)

            except Exception as e:
                logger.error(f"Failed to process PDF {f.filename}: {e}")

        try:
            self.storage.ensure_index()
            self.storage.store_project(project_name, pdf_metadata, all_chunks)
            logger.info("Stored project '%s' successfully in Neo4j.", project_name)
        except Exception as e:
            logger.error("Neo4j storage failed for project '%s': %s", project_name, e)
            raise

        return {
            "project": project_name,
            "uploaded_files": uploaded_files,
            "total_chunks": len(all_chunks),
            "status": "Successfully processed and stored in Neo4j + MongoDB.",
        }

# FastAPI Endpoint
pdf_uploader = PDFUploader()

@router.post("/upload", tags= ["PDF Uploader"])
async def upload_pdfs(
    files: List[UploadFile] = File(..., description="Upload up to 5 PDF files"),
    project_name: str = Form("default_project")
):
    """
    FastAPI endpoint to handle PDF uploads and trigger processing.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="At least one PDF must be added.")
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Limit: 5 PDFs only.")

        result = pdf_uploader.process_pdfs(files, project_name)
        return result

    except HTTPException as e:
        logger.error("HTTP error during upload: %s", e.detail)
        raise
    except Exception as e:
        logger.exception("Unexpected error during PDF upload: %s", e)
        raise HTTPException(status_code=500, detail=str(e))