"""
utils/embeddings.py

Base embedder and concrete Ollama Embedder wrapper with logging.
"""
import logging
from typing import List
from langchain_ollama import OllamaEmbeddings

#logging Configuration
logger= logging.getLogger(__name__)

#Base Class for Embedding
class BaseEmbedder:
    """
    Abstract Base class for all embedding Implementaions.

    Methods:
        embed_query(text: str)-> List[float]:
        Should return a list of floats representing the text embedding
    """
    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError("SubClass Must Implement this method.")

#Ollama Embedding
class OllamaEmbedder(BaseEmbedder):
    def __init__(self, model: str= "nomic-embed-text:latest"):
        """
        Initialize the Ollama embedding model.

        Arguments:
            model ---> str: Name of emnedding model to use.
        """
        self.model= model
        logger.info(f"Initializing OllamaEbedder with model '{self.model}'.")
        try:
            self._client= OllamaEmbeddings(model= self.model)
            logger.info("OllamaEmbeddings succesfully initialized.")
        except Exception as e:
            logger.exception(f"Failed to initialize OllamaEmbeddings: {e}")
            raise

    def embed_query(self, text: str)-> List[float]:
        """
        Generate embeddings for a given text using Ollama

        Arguments:
            text---> str: The input text to embed
        Returns:
            List[float]: The Embedding Vector.
        """
        try:
            logger.debug(f"Generating embedding for text: {text[:60]}...")
            embedding= self._client.embed_query(text)
            logger.info("Embedding generated successfully.")
            return embedding
        except Exception as e:
            logger.exception(f"Error generating embeddings: {e}")
            return []