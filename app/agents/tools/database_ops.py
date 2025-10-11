"""
Database operations for agents.
Refactored from db/crud.py to be used by Strands agents.
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from db.models import Note
import os
from dotenv import load_dotenv
from typing import List, Optional, Tuple
import datetime

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def add_note(title: str, content: str, summary: str, tags: List[str], embedding: List[float]) -> Note:
    """Add a new note to the database."""
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


def get_all_notes() -> List[Note]:
    """Get all notes from the database."""
    session = SessionLocal()
    notes = session.query(Note).all()
    session.close()
    return notes


def get_note_by_id(note_id: int) -> Optional[Note]:
    """Get a note by its ID."""
    session = SessionLocal()
    note = session.query(Note).filter(Note.id == note_id).first()
    session.close()
    return note


def get_notes_by_ids(note_ids: List[int]) -> List[Note]:
    """Get multiple notes by their IDs."""
    session = SessionLocal()
    notes = session.query(Note).filter(Note.id.in_(note_ids)).all()
    session.close()
    return notes


def get_notes_by_tags(tags: List[str]) -> List[Note]:
    """Get notes that contain any of the specified tags."""
    session = SessionLocal()
    notes = session.query(Note).filter(Note.tags.overlap(tags)).all()
    session.close()
    return notes


def get_recent_notes(limit: int = 10) -> List[Note]:
    """Get the most recent notes."""
    session = SessionLocal()
    notes = session.query(Note).order_by(Note.created_at.desc()).limit(limit).all()
    session.close()
    return notes


def update_note(note_id: int, **kwargs) -> Optional[Note]:
    """Update a note with new values."""
    session = SessionLocal()
    note = session.query(Note).filter(Note.id == note_id).first()
    if note:
        for key, value in kwargs.items():
            if hasattr(note, key):
                setattr(note, key, value)
        session.commit()
        session.refresh(note)
    session.close()
    return note


def delete_note(note_id: int) -> bool:
    """Delete a note by ID."""
    session = SessionLocal()
    note = session.query(Note).filter(Note.id == note_id).first()
    if note:
        session.delete(note)
        session.commit()
        session.close()
        return True
    session.close()
    return False


def search_notes_by_content(query: str, limit: int = 10) -> List[Note]:
    """Search notes by content using basic text search."""
    session = SessionLocal()
    notes = session.query(Note).filter(
        Note.content.ilike(f"%{query}%") | 
        Note.title.ilike(f"%{query}%") |
        Note.summary.ilike(f"%{query}%")
    ).limit(limit).all()
    session.close()
    return notes


def get_note_statistics() -> dict:
    """Get basic statistics about notes."""
    session = SessionLocal()
    total_notes = session.query(Note).count()
    
    # Get unique tags
    all_notes = session.query(Note).all()
    all_tags = set()
    for note in all_notes:
        if note.tags:
            all_tags.update(note.tags)
    
    session.close()
    
    return {
        "total_notes": total_notes,
        "unique_tags": len(all_tags),
        "total_tags": sum(len(note.tags or []) for note in all_notes)
    }
