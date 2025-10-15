from langchain_ollama import OllamaEmbeddings

embedder= OllamaEmbeddings(
    model= "nomic-embed-text:latest"
)
#print(embedder)
def get_embeddings(text):
    try:
        embedding= embedder.embed_query(text)
        return embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return []