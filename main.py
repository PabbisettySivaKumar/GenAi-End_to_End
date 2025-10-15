from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from router.pdf_upload import router as pdf_router
from services.querying import semantic_querying

app= FastAPI()

class QueryRequest(BaseModel):
    query: str= Field(..., example="what is transformers?")

@app.get("/")
def home():
    return {"message": "Generative AI Backend is Running"}

app.include_router(pdf_router, prefix="/api")

@app.post("/query")
def query_endpoint(request: QueryRequest):
    question= request.query.strip()
    if not question:
        raise HTTPException(status_code=400, detail= "Query Text is required")
    answer= semantic_querying(question)
    return {"answer": answer}