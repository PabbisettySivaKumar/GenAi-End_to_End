"""
services/querying.py

RAG Pipeline retrival+generation
Integrates Ollama, neo4j and langfuse prompt management.
"""

import os
import time
import logging
from typing import List, Optional

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_neo4j import Neo4jVector
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler as LfHandler
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.documents import Document
from services.storage import Neo4jStorage

#logging configuration

logger= logging.getLogger(__name__)

#Environment Set-up
load_dotenv()

#RAG Pipeline

class RAGPipeline:
    """
    RAG Pipeline combining
    -- Ollama LLM for generation
    -- Neo4j Vector index for retrival
    -- Langfuse for prompt and montoring.
    """

    def __init__(self,
                llm: Optional[str]= None,
                embedding_model: Optional[str]= None,
                neo4j_uri: Optional[str]= None,
                neo4j_user: Optional[str]= None,
                neo4j_password: Optional[str]= None,
                neo4j_index_name: str= "vector"):
        """
        Initialize RAG Pipeline components using environmental variable
        """
        logger.info("Initializing RAG Pipeline")

        #laoding model from .env or fallback defaults.
        self.llm= llm or os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
        self.embedding_model= embedding_model or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")

        #Neo4j credentials
        self.neo4j_uri= neo4j_uri or os.getenv("NEO4J_URI")
        self.neo4j_user= neo4j_user or os.getenv("NEO4J_USER")
        self.neo4j_password= neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.neo4j_index_name= neo4j_index_name

        #langfuse initialization
        try:
            self.langfuse= Langfuse(
                    public_key= os.getenv("LANGFUSE_PUBLIC_KEY"),
                    secret_key= os.getenv("LANGFUSE_SECRET_KEY"),
                    host= os.getenv("LANGFUSE_HOST", "http://localhost:3000")

            )
            self.lf_handler= LfHandler()
            logger.info("Langfuse Initialized successfully")
        except Exception as e:
            logger.warning(f"Langfuse initialization failed: {e}")
            self.langfuse= None
            self.lf_handler= None

        # LLM and Embeddings Initialization
        try:
            self.llm = OllamaLLM(model=self.llm, callbacks=[self.lf_handler] if self.lf_handler else None)
            self.embeddings = OllamaEmbeddings(model=self.embedding_model)
            logger.info(f"Ollama models loaded from .env: LLM={self.llm}, Embeddings={self.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama models: {e}")
            raise

        # Neo4j Connection Setup
        try:
            self.vector_index = Neo4jVector(
                embedding=self.embeddings,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                node_label="Chunk",
                text_node_property="text",
                embedding_node_property="embedding",
                index_name=self.neo4j_index_name,
                #metadata_properties= ["pdf_name", "pdf_num", "pdf_path"]
            )
            try:
                self.vector_index.metdata_keys= ["pdf_name", "page_num", "pdf_path"]
                logger.info("Metadata properties added manually for Neo4j vector.")
            except Exception:
                logger.warning("Neo4jVector metadata patch not applied — using default properties.")
            logger.info("Connected to Neo4jVector index successfully.")
        except Exception as e:
            logger.error(f"Neo4jVector initialization failed: {e}")
            self.vector_index = None
            self.storage = Neo4jStorage(uri=self.neo4j_uri, user=self.neo4j_user, password=self.neo4j_password)

    #langfuse prompt loader
    def get_langfuse_prompt(self, context: str, question: str):
        """
        Retrives and compiles a  prompt from langfuse.
        """
        prompt_name= os.getenv("LANGFUSE_PROMPT_NAME", "semantic_query_prompt")
        logger.info(f"Fetching Lnagfuse Prompt '{prompt_name}'...")

        if not self.langfuse:
            logger.warning("Langfuse not initialized. Using default prompt.")
            return f"Use the following context to answer accurately:\n{context}\n\nQuestion: {question}"

        try:
            prompt_template= self.langfuse.get_prompt(prompt_name, label= "production")
            compiled= prompt_template.compile(context= context, question= question)

            if isinstance(compiled, dict) and "messages" in compiled:
                messages= compiled["messages"]
                chat_input= "\n".join([m["content"] for m in messages])
            elif isinstance(compiled, dict) and "prompt" in compiled:
                chat_input= compiled["prompt"]
            else:
                chat_input= str(compiled)

            logger.info("Langfuse Prompt Compiled Successfully.")
            return chat_input
        except Exception as e:
            logger.error(f"LangFuse Prompt fetching failed: {e}")
            return f"Use the following context to answer accurately:\n{context}\n\nQuestion: {question}"

    #retrival
    def retrival_documents(self, question: str, k: int= 3)-> List[Document]:
        """
        retrive top-k similar chunks from neo4j using similarity search.
        """
        logger.info(f"Retrieving top-{k} chunks from query: {question}")
        try:
            if self.vector_index:
                return self.vector_index.similarity_search(question, k= k)
            else:
                logger.warning("Falling back to Neo4j storage similarity search.")
                raw= self.storage.similarity_search(question, k= k)
                return [Document(page_content= r.get("text", "")) for r in raw]
        except Exception as e:
            logger.error(f"Document Retrival failed: {e}")
            raise HTTPException(status_code= 500, detail= str(e))

    #generation from context
    def generation_from_context(self, question: str, docs: List[Document])-> str:
        """
        Generate an answer using context and langfuse prompt.
        """
        context= "\n".join([d.page_content for d in docs]) if docs else ""

        #checking whether content from document or not
        if context:
            logger.info(f"---Retireved Context Preview (first 100 characters) ---\n{context[:100]}\n--- End of Preview ---")

        prompt= self.get_langfuse_prompt(context, question)

        if isinstance(prompt, dict):
            if "messages" in prompt:
                prompt= "\n".join([m["context"] for m in prompt["messages"]])
            elif "prompt" in prompt:
                prompt= prompt["prompt"]
            else:
                prompt= str(prompt)

        try:
            response= self.llm.invoke(prompt)
            logger.info("Response generated Successfully.")
            return response
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            raise HTTPException(status_code= 500, detail= str(e))

    #end to end query
    def query(self, question: str, top_k: int= 3)-> dict:
        """
        Perform full retrival+generation Pipeline for a given user question.
        Retirves both the final answer and retrieved chunk metadata.
        """
        start_time= time.time()
        logger.info(f"Processing query: {question}")

        try:
            docs= self.retrival_documents(question, k= top_k)
            if not docs:
                logger.warning("No relevant Documents Found")
                return {
                    "answer": "No Relevant context found in database.",
                    "chunks": []
                }
            retrieved_chunks= []
            for d in docs:
                meta= getattr(d, "metadata", {})
                retrieved_chunks.append({
                    "text": d.page_content,
                    "page_num": meta.get("page_num"),
                    "pdf_path": meta.get("pdf_path")
                })
            answer= self.generation_from_context(question, docs)
            elapsed= round(time.time()-start_time,2)
            logger.info(f"Query Processed Successfully in {elapsed}s.")
            return {
                "answer": answer,
                "chunks": retrieved_chunks
                }
        except Exception as e:
            logger.error(f"Query pipeline failed: {e}")
            raise HTTPException(status_code= 500, detail= str(e))