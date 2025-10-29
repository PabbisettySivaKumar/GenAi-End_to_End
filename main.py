"""
main.py

Fast API endpoints that includes simple query endpoint.
Uses the RAGPipeline class for semantic querying.
"""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from router.pdf_upload import router as pdf_router
from services.querying import RAGPipeline

#logging configuration
logging.basicConfig(
    level= logging.INFO,
    format= "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger= logging.getLogger(__name__)

#FastAPI
app= FastAPI(title= "Generative AI RAG System")

#request schema
class QueryRequest(BaseModel):
    query: str= Field(..., example="what is transformers?")

@app.get("/", tags= ["Health Check"])
def home():
    """Healthcheck Endpoint."""
    logger.info("Home Endpoint is Called.")
    return {"message": "Generative AI Backend is Running"}

app.include_router(pdf_router, prefix="/api")

try:
    rag_pipeline = RAGPipeline()
    logger.info("RAGPipeline initialized successfully.")
except Exception as e:
    logger.exception("Failed to initialize RAGPipeline: %s", e)
    raise

@app.post("/query", tags= ['Querying'])
def query_endpoint(request: QueryRequest):
    question= request.query.strip()
    if not question:
        logger.warning("Empty Query Received.")
        raise HTTPException(status_code=400, detail= "Query Text is required")
    try:
        logger.info(f"Received Query: {question}")
        answer= rag_pipeline.query(question)
        logger.info("Query Processed Successfully.")
        return {"answer": answer}
    except Exception as e:
        logger.exception("Error while processing Query: %s", e)
        raise HTTPException(status_code= 500, detail="Internal Server Error")