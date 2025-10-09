from langchain_ollama import OllamaEmbeddings

def get_embeddings(text):
    embedder= OllamaEmbeddings(model= "nomic-embed-text:latest")
    return embedder.embed_query(text)