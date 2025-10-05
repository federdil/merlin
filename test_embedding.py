from embeddings.embed_articles import generate_embedding

text = "This is a test for Hugging Face embeddings."
embedding = generate_embedding(text)

print("Embedding length:", len(embedding))
print("First 5 values:", embedding[:5])
