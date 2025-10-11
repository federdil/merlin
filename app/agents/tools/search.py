"""
Search utilities for agents.
Refactored from app/search.py and db/crud.py to be used by Strands agents.
"""

from db.crud import semantic_search_pgvector
from app.agents.tools.embedding import generate_embedding
from app.agents.tools.database_ops import get_all_notes, get_note_by_id
from typing import List, Optional
import numpy as np


def semantic_search(query: str, top_k: int = 5) -> List:
    """Perform semantic search using embeddings."""
    query_vec = generate_embedding(query)
    results = semantic_search_pgvector(query_vec, top_k)
    return results


def find_similar_notes(note_id: int, top_k: int = 3) -> List:
    """Find notes similar to a given note."""
    note = get_note_by_id(note_id)
    if not note:
        return []
    
    # Use the note's existing embedding for similarity search
    results = semantic_search_pgvector(note.embedding, top_k + 1)
    
    # Filter out the note itself
    similar_notes = [n for n in results if n.id != note.id]
    
    return similar_notes[:top_k]


def search_by_tags(tags: List[str], top_k: int = 10) -> List:
    """Search notes by tags."""
    from app.agents.tools.database_ops import get_notes_by_tags
    return get_notes_by_tags(tags)[:top_k]


def search_by_content(query: str, top_k: int = 10) -> List:
    """Search notes by content using text search."""
    from app.agents.tools.database_ops import search_notes_by_content
    return search_notes_by_content(query, top_k)


def hybrid_search(query: str, semantic_weight: float = 0.7, top_k: int = 10) -> List:
    """
    Perform hybrid search combining semantic and text search.
    
    Args:
        query: Search query
        semantic_weight: Weight for semantic search (0-1)
        top_k: Number of results to return
    """
    # Get semantic search results
    semantic_results = semantic_search(query, top_k * 2)
    semantic_scores = {note.id: 1.0 - (i / len(semantic_results)) for i, note in enumerate(semantic_results)}
    
    # Get text search results
    text_results = search_by_content(query, top_k * 2)
    text_scores = {note.id: 1.0 - (i / len(text_results)) for i, note in enumerate(text_results)}
    
    # Combine scores
    all_note_ids = set(semantic_scores.keys()) | set(text_scores.keys())
    combined_scores = {}
    
    for note_id in all_note_ids:
        semantic_score = semantic_scores.get(note_id, 0.0)
        text_score = text_scores.get(note_id, 0.0)
        combined_scores[note_id] = (semantic_weight * semantic_score + 
                                  (1 - semantic_weight) * text_score)
    
    # Sort by combined score and get note objects
    sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
    
    # Get note objects
    notes_dict = {note.id: note for note in semantic_results + text_results}
    final_results = [notes_dict[note_id] for note_id in sorted_ids if note_id in notes_dict]
    
    return final_results[:top_k]


def get_recent_notes(limit: int = 10) -> List:
    """Get recent notes."""
    from app.agents.tools.database_ops import get_recent_notes
    return get_recent_notes(limit)


def search_notes(query: str, search_type: str = "semantic", top_k: int = 5) -> List:
    """
    Unified search interface for different search types.
    
    Args:
        query: Search query
        search_type: Type of search ('semantic', 'text', 'hybrid', 'tags')
        top_k: Number of results to return
    """
    if search_type == "semantic":
        return semantic_search(query, top_k)
    elif search_type == "text":
        return search_by_content(query, top_k)
    elif search_type == "hybrid":
        return hybrid_search(query, top_k=top_k)
    elif search_type == "tags":
        # Assume query contains comma-separated tags
        tags = [tag.strip() for tag in query.split(',')]
        return search_by_tags(tags, top_k)
    else:
        raise ValueError(f"Unknown search type: {search_type}")
