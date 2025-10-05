import faiss
import numpy as np

class VectorStore:
    def __init__(self, dim):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.notes = []

    def add(self, embedding, note_id):
        vec = np.array([embedding], dtype='float32')
        self.index.add(vec)
        self.notes.append(note_id)

    def search(self, query_embedding, top_k=5):
        vec = np.array([query_embedding], dtype='float32')
        distances, indices = self.index.search(vec, top_k)
        results = [self.notes[i] for i in indices[0]]
        return results
