from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_neo4j import Neo4jVector
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler as LfHandler
from dotenv import load_dotenv
import os, time
from fastapi import HTTPException

load_dotenv()

langfuse= Langfuse(
    public_key= os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key= os.getenv("LANGFUSE_SECRET_KEY"),
    host= os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

lf= get_client()
lf_handler= LfHandler()

def semantic_querying(question):

    start_time= time.time()
    try:
        #llm
        llm= OllamaLLM(model= 'llama3.1:8b', callbacks= [lf_handler])
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
        prompt_template= None
        try:
            prompt_template= langfuse.get_prompt(prompt_name, label= "production")
            #print(f"Langfuse Loaded Prompt: '{prompt_name}'(version {prompt_template.version})")
        except Exception as e:
            print(f"Langfuse could not fetch '{prompt_name}': {e}")
            #langfuse not available


        #prompt variable
        chat_input= None
        
        if prompt_template:
            compiled= prompt_template.compile(context= context, question= question)

            if isinstance(compiled, dict) and "messages" in compiled:
                messages= compiled["messages"]
                chat_input= "\n".join([m["content"] for m in messages])
            elif isinstance(compiled, dict) and "prompt" in compiled:
                chat_input= compiled["prompt"]
            else:
                chat_input= str(compiled)
            #print(f"prmpt from langfuse")
        else:
            chat_input = f"Use the following context to answer accurately:\n{context}\n\nQuestion: {question}"

        if not chat_input:
            raise ValueError("Prompt could not be compiles or generated")
        #print("Retrived COntext", context[:1000])
        response= llm.invoke(chat_input)
        elapsed= round(time.time()- start_time, 2)

        #log trace
        # try:
        #     trace= langfuse.client().trace(
        #         name= "semantic_query_prompt",
        #         metadata= {
        #             "prompt_name": prompt_name,
        #             "retrived_chunks": [d.page_content[:200] for d in docs],
        #             "latency_seconds": elapsed
        #         }
        #     )
        #     generation= trace.generation(
        #         name= "ollama_generation",
        #         model= "llama3.1:8b",
        #         input= chat_input,
        #         output= response
        #     )
        #     generation.end()
        #     trace.end()
        #     print(f"Logged trace: ({elapsed}s).")
        # except Exception as e:
        #     print(f"Langfuse tracing failed: {e}")
        
        return response

    except Exception as e:
        print(f"[Query Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))