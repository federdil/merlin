from db.crud import semantic_search_pgvector
from embeddings.embed_articles import generate_embedding

def semantic_search(query, top_k=5):
    query_vec = generate_embedding(query)
    results = semantic_search_pgvector(query_vec, top_k)
    return results
