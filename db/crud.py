from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Note  # <-- relative import
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def add_note(title, content, summary, tags, embedding):
    session = SessionLocal()
    note = Note(
        title=title,
        content=content,
        summary=summary,
        tags=tags,
        embedding=embedding
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    session.close()
    return note

def get_all_notes():
    session = SessionLocal()
    notes = session.query(Note).all()
    session.close()
    return notes

def get_note_by_id(note_id):
    session = SessionLocal()
    note = session.query(Note).filter(Note.id == note_id).first()
    session.close()
    return note

def semantic_search_pgvector(query_embedding, top_k=5):
    session = SessionLocal()
    results = (
        session.query(Note)
        .order_by(Note.embedding.op("<->")(query_embedding))
        .limit(top_k)
        .all()
    )
    session.close()
    return results
