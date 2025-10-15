from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langfuse import Langfuse
from dotenv import load_dotenv
import os
from fastapi import HTTPException

load_dotenv()

# langfuse= Langfuse(
#     public_key= os.getenv("LANGFUSE_PUBLIC_KEY"),
#     secret_key= os.getenv("LANGFUSE_SECRET_KEY")
# )

def semantic_querying(question):
    try: 
        llm= OllamaLLM(model= 'llama3.1:8b')
        embeddings= OllamaEmbeddings(model= "nomic-embed-text:latest")
        vector_index= Neo4jVector(
            embedding= embeddings,
            url= os.getenv("NEO4J_URI"),
            username= os.getenv("NEO4J_USER"),
            password= os.getenv("NEO4J_PASSWORD"),
            node_label= "Chunk",
            text_node_property= "text",
            embedding_node_property= "embedding"
            )
        docs= vector_index.similarity_search(question, k= 3)
        if not docs:
            return "No relevant information found in uploaded files."
        context= "\n".join([d.page_content for d in docs])
        prompt= f"Answer using this context:\n{context}\n\nQ: {question}"
        response= llm.invoke(prompt)
        #log_prompt(prompt, response)
        return response
    except Exception as e:
        print(f"[Query Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# def log_prompt(prompt: str, response: str):
#     langfuse.trace(
#         name= "semantic_query",
#         prompt= prompt,
#         output= response)