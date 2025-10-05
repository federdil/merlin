from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from db.crud import add_note, get_all_notes, get_note_by_id, semantic_search_pgvector
from embeddings.embed_articles import generate_embedding
from app.search import semantic_search
from app.fetcher import fetch_url_content
from app.llm import summarize_and_tag
from app.utils import normalize_tags
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Personal Knowledge Curator")

# Enable CORS for local development (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoteInput(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []


@app.post("/add_note")
def create_note(note: NoteInput):
    # Resolve content and title from either raw input or URL
    resolved_title = note.title
    resolved_content = note.content

    if not resolved_content and note.url:
        title, content = fetch_url_content(note.url)
        if not content:
            raise HTTPException(status_code=400, detail="Failed to extract content from URL")
        resolved_content = content
        if not resolved_title and title:
            resolved_title = title

    if not resolved_content:
        raise HTTPException(status_code=400, detail="content or url is required")

    if not resolved_title:
        resolved_title = resolved_content[:80]

    # Generate summary and tags if missing
    summary = note.summary
    tags = note.tags or []
    if summary is None or not tags:
        gen_summary, gen_tags = summarize_and_tag(resolved_content)
        summary = summary or gen_summary
        if not tags:
            tags = gen_tags

    embedding = generate_embedding(resolved_content)
    db_note = add_note(resolved_title, resolved_content, summary, tags, embedding)
    return {"id": db_note.id, "title": db_note.title, "summary": db_note.summary, "tags": normalize_tags(db_note.tags)}


@app.get("/search")
def search_notes(query: str, top_k: int = 5):
    results = semantic_search(query, top_k=top_k)
    return [{"id": n.id, "title": n.title, "summary": n.summary, "tags": normalize_tags(n.tags)} for n in results]


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    note = get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": note.id,
        "title": note.title,
        "summary": note.summary,
        "tags": normalize_tags(note.tags),
        "content": note.content,
        "created_at": str(note.created_at),
    }


@app.get("/similar/{note_id}")
def similar_notes(note_id: int, top_k: int = 3):
    note = get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    # Reuse existing embedding as query
    results = semantic_search_pgvector(note.embedding, top_k)
    # Exclude the note itself if present
    filtered = [n for n in results if n.id != note.id]
    payload = []
    for n in filtered[:top_k]:
        payload.append({"id": n.id, "title": n.title, "summary": n.summary, "tags": normalize_tags(n.tags)})
    return payload
