from .crud import add_note, get_all_notes
from ..embeddings.embed_articles import generate_embedding

embedding = generate_embedding("This is a test note content.")

note = add_note(
    title="Test Note",
    content="This is a test note content.",
    summary="Short summary",
    tags=["test", "mvp"],
    embedding=embedding
)

print("Inserted Note ID:", note.id)

notes = get_all_notes()
print("Total notes in DB:", len(notes))
