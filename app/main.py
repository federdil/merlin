from fastapi import FastAPI
from pydantic import BaseModel
from db.crud import add_note, get_all_notes
from embeddings.embed_articles import generate_embedding
from app.search import semantic_search

app = FastAPI(title="Personal Knowledge Curator")

class NoteInput(BaseModel):
    title: str
    content: str
    summary: str = None
    tags: list[str] = []

@app.post("/add_note")
def create_note(note: NoteInput):
    embedding = generate_embedding(note.content)
    db_note = add_note(note.title, note.content, note.summary, note.tags, embedding)
    return {"id": db_note.id, "title": db_note.title}

@app.get("/search")
def search_notes(query: str):
    results = semantic_search(query)
    return [{"id": n.id, "title": n.title, "summary": n.summary} for n in results]
