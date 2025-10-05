from sentence_transformers import SentenceTransformer

# Load a pre-trained embedding model
# 'all-MiniLM-L6-v2' is lightweight and fast, good for MVP
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str):
    """
    Generate a vector embedding for the given text using Hugging Face.
    Returns a list of floats.
    """
    embedding = model.encode([text])[0]  # model.encode returns a list of vectors
    return embedding.tolist()  # convert numpy array to list for pgvector storage
