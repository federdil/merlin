"""
Utility functions for handling tags in the database.
"""

import json
import re
from typing import List, Any


def fix_tags_format(tags: List[Any]) -> List[str]:
    """
    Fix tags that might be stored as individual characters instead of proper strings.
    
    Args:
        tags: List of tags (might be individual characters)
        
    Returns:
        List of properly formatted tag strings
    """
    if not tags:
        return []
    
    # Check if tags are stored as individual characters
    if len(tags) > 10 and all(len(str(tag)) == 1 for tag in tags[:5]):
        # Tags are stored as individual characters, try to reconstruct
        try:
            tags_str = ''.join(tags)
            parsed_tags = json.loads(tags_str)
            if isinstance(parsed_tags, list):
                return [str(tag) for tag in parsed_tags]
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, try to extract meaningful tags
        try:
            quoted_tags = re.findall(r'"([^"]+)"', ''.join(tags))
            if quoted_tags:
                return quoted_tags
        except:
            pass
    
    # Return tags as strings if they're already properly formatted
    return [str(tag) for tag in tags]


def format_note_for_display(note: Any) -> dict:
    """
    Format a note object for display, fixing any tag formatting issues.
    
    Args:
        note: Note object from database
        
    Returns:
        Dictionary with properly formatted note data
    """
    return {
        'id': note.id,
        'title': note.title,
        'summary': note.summary,
        'tags': fix_tags_format(note.tags or []),
        'created_at': note.created_at.isoformat() if note.created_at else None,
        'content_preview': note.content[:200] + '...' if len(note.content) > 200 else note.content
    }
