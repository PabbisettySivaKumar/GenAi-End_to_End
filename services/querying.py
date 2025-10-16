from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langfuse import Langfuse
from dotenv import load_dotenv
import os, time
from fastapi import HTTPException

load_dotenv()

langfuse= Langfuse(
    public_key= os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key= os.getenv("LANGFUSE_SECRET_KEY"),
    host= os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

def semantic_querying(question):

    start_time= time.time()
    try:
        #llm
        llm= OllamaLLM(model= 'llama3.1:8b')
        embeddings= OllamaEmbeddings(model= "nomic-embed-text:latest")

        #Neo4j
        vector_index= Neo4jVector(
            embedding= embeddings,
            url= os.getenv("NEO4J_URI"),
            username= os.getenv("NEO4J_USER"),
            password= os.getenv("NEO4J_PASSWORD"),
            node_label= "Chunk",
            text_node_property= "text",
            embedding_node_property= "embedding",
            index_name= "vector"
        )

        #chunks
        docs= vector_index.similarity_search(question, k= 3)
        if not docs:
            return "No relevant information found in uploaded files."
        context= "\n".join([d.page_content for d in docs])

        #fromlangfuse get prompt
        prompt_name= os.getenv("LANGFUSE_PROMPT_NAME", "semantic_query_prompt")
        try:
            prompt_template= langfuse.get_prompt(prompt_name)
            print(f"Langfuse Loaded Prompt: '{prompt_name}'(version {prompt_template.version})")
        except Exception as e:
            print(f"Langfuse could not fetch '{prompt_name}': {e}")
            #langfuse not available
            prompt_template= None

        #prompt variable
        if prompt_template:
            prompt= prompt_template.compile(context= context, question= question)
            print(f"prmpt from langfuse")
        else:
            prompt= f"Use the following context to answer:\n{context}\n\nQ: {question}"        
        response= llm.invoke(prompt)
        elapsed= round(time.time()- start_time, 2)

        #log trace
        try:
            trace= langfuse.client().trace(
                name= "semantic_query_prompt",
                metadata= {
                    "project": project,
                    "retrived_chunks": [d.page_content[:200] for d in docs],
                    "latency_seconds": elapsed
                }
            )
            generation= trace.generation(
                name= "ollama_generation",
                model= "llama3.1:8b",
                input= prompt,
                output= response
            )
            generation.end()
            trace.end()
            print(f"Logged trace: ({elapsed}s).")
        except Exception as e:
            print(f"Langfuse tracing failed: {e}")
        
        return response

    except Exception as e:
        print(f"[Query Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# def log_prompt(prompt: str, response: str):
#     langfuse.trace(
#         name= "semantic_query",
#         prompt= prompt,
#         output= response)