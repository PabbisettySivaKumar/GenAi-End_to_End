from langchain_ollama import OllamaEmbeddings

embedder = OllamaEmbeddings(model="nomic-embed-text:latest")
vec = embedder.embed_query("Testing Ollama embeddings")
print(len(vec))
