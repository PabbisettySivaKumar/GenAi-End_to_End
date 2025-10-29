"""
services/chunking.py

DocumentChunker: PDF reading and text chunkking and logging support.
"""

import fitz
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict


#configure Logging
logger= logging.getLogger(__name__)

class DocumentChunker:
    """
    A utility class for chunking PDF Documents into smaller text segments/chunks
    which is good for embedding and retrival
    """

    def __init__(self, chunk_size: int= 3000, chunk_overlap: int= 1000):
        """
        Initializing DocumentChunker.

        Arguments:
                    chunk_size---> int: The Maximum size of each text chunk.
                    chunk_overlap---> int: The Overlap between consecutive chunks.
        
        """
        self.chunk_size= chunk_size
        self.chunk_overlap= chunk_overlap
        self.splitter= RecursiveCharacterTextSplitter(
            chunk_size= self.chunk_size,
            chunk_overlap= self.chunk_overlap
        )
        logger.info(
            f"DocumentChunker Initialized with chunk_size= {self.chunk_size},"
            f"chunk_overlap= {self.chunk_overlap}"
        )

    def chunk_pdf(self, pdf_path: str):
        """
        Read a PDF from Disk and return a list of chunk dictionaries:
            {"chunk_id": "page_index", "page": int, "text": str, "pdf_path": str}
        Arguments:
            pdf_path ---> str: Path to input for PDF File
        Returns:
            List ---> Dict: List of Chunk metadata and text. 
        """
        logger.info(f"starting PDF Chunking for file: {pdf_path}")
        chunks= []
        
        try:
            docs= fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"Failed to open PDF File {pdf_path}: {e}")
            return chunks

        for page_number, page in enumerate(docs, start=1):
            try:
                text= page.get_text("text").strip()
                if not text:
                    logger.warning(f"Page {page_number} is empty. Skipping")
                    continue
                page_chunks= self.splitter.split_text(text)
                for i, chunk_text in enumerate(page_chunks):
                    chunks.append({
                        "chunk_id": f"{page_number}_{i}",
                            "page_num": page_number, #did changes
                            "text": chunk_text,
                            "pdf_path": pdf_path #added this line
                    })
                
                logger.info(
                    f"Processed Page {page_number}>>>{len(page_chunks)} chunks created."
                )
            except Exception as e:
                logger.error(f"Error Reading Page {page_number}: {e}")
        logger.info(f"Total Chunks Created from PDF: {len(chunks)}")
        return chunks