"""
Embedding utilities for agents.
Refactored from embeddings/embed_articles.py to be used by Strands agents.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np


# Load a pre-trained embedding model
# 'all-MiniLM-L6-v2' is lightweight and fast, good for MVP
model = SentenceTransformer('all-MiniLM-L6-v2')


def generate_embedding(text: str) -> List[float]:
    """
    Generate a vector embedding for the given text using Hugging Face.
    Returns a list of floats.
    """
    embedding = model.encode([text])[0]  # model.encode returns a list of vectors
    return embedding.tolist()  # convert numpy array to list for pgvector storage


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.
    """
    embeddings = model.encode(texts)
    return [embedding.tolist() for embedding in embeddings]


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Compute cosine similarity between two embeddings.
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Handle different dimensions by padding with zeros
    if len(vec1) != len(vec2):
        max_len = max(len(vec1), len(vec2))
        if len(vec1) < max_len:
            vec1 = np.pad(vec1, (0, max_len - len(vec1)), mode='constant')
        if len(vec2) < max_len:
            vec2 = np.pad(vec2, (0, max_len - len(vec2)), mode='constant')
    
    # Compute cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Convert numpy float to Python float for JSON serialization
    return float(dot_product / (norm1 * norm2))


def get_embedding_dimension() -> int:
    """Get the dimension of the embedding model."""
    return 384  # all-MiniLM-L6-v2 dimension
