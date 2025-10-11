"""
Tagging utilities for agents.
Extracted from existing LLM functionality.
"""

from typing import List
import re


def normalize_tags(tags) -> List[str]:
    """Normalize tags to consistent format."""
    if not tags:
        return []
    
    # Handle different input types
    if isinstance(tags, str):
        # Handle comma-separated string
        if ',' in tags:
            tags = [tag.strip() for tag in tags.split(',')]
        # Handle JSON array string
        elif tags.startswith('[') and tags.endswith(']'):
            try:
                import json
                tags = json.loads(tags)
            except:
                tags = []
        # Handle PostgreSQL array string
        elif tags.startswith('{') and tags.endswith('}'):
            # Remove braces and split by comma
            tags = tags[1:-1].split(',')
            tags = [tag.strip().strip('"') for tag in tags]
        else:
            # Single tag
            tags = [tags]
    
    # If tags is already a list but contains character-by-character split strings,
    # try to reconstruct the original string and parse it properly
    elif isinstance(tags, list) and len(tags) > 0:
        # Check if this looks like a character-by-character split of a string
        if len(tags) > 10 and tags[0] in ['{', '['] and tags[-1] in ['}', ']']:
            try:
                # Reconstruct the original string
                original_string = ''.join(tags)
                
                # Try to parse as JSON first
                import json
                try:
                    parsed_tags = json.loads(original_string)
                    if isinstance(parsed_tags, list):
                        tags = parsed_tags
                    else:
                        tags = []
                except:
                    # If JSON parsing fails, try PostgreSQL array format
                    if original_string.startswith('{') and original_string.endswith('}'):
                        # Remove braces and split by comma, handling quoted strings
                        content = original_string[1:-1]
                        tags = []
                        current_tag = ''
                        in_quotes = False
                        for char in content:
                            if char == '"' and (not current_tag or current_tag[-1] != '\\'):
                                in_quotes = not in_quotes
                                current_tag += char
                            elif char == ',' and not in_quotes:
                                if current_tag.strip():
                                    tags.append(current_tag.strip().strip('"'))
                                current_tag = ''
                            else:
                                current_tag += char
                        if current_tag.strip():
                            tags.append(current_tag.strip().strip('"'))
                    else:
                        tags = []
            except:
                # If all parsing fails, continue with the original list
                pass
    
    if not isinstance(tags, (list, tuple)):
        return []
    
    normalized = []
    for tag in tags:
        if isinstance(tag, str) and tag.strip():
            # Convert to lowercase, remove extra whitespace
            clean_tag = tag.strip().lower()
            # Replace multiple spaces with single space
            clean_tag = re.sub(r'\s+', ' ', clean_tag)
            # Keep forward slashes and hyphens but remove other punctuation
            clean_tag = re.sub(r'[^\w\s/-]', '', clean_tag)
            if clean_tag and len(clean_tag) > 1:
                normalized.append(clean_tag)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in normalized:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    
    return unique_tags


def extract_keywords_from_content(content: str, max_tags: int = 10) -> List[str]:
    """Extract keywords from content as fallback tags."""
    # Remove punctuation and convert to lowercase
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", content.lower())
    tokens = [t for t in text.split() if len(t) > 2]
    
    # Common stop words to filter out
    stop_words = set([
        "the", "and", "for", "that", "with", "from", "this", "have", "has", "had",
        "was", "were", "are", "you", "your", "his", "her", "its", "but", "not",
        "out", "about", "into", "they", "their", "them", "who", "what", "when",
        "where", "why", "how", "will", "would", "can", "could", "should",
        "between", "after", "before", "over", "under", "into", "onto", "more",
        "most", "some", "any", "each", "other", "than", "also", "may", "might",
        "must", "shall", "should", "could", "would", "will", "been", "being"
    ])
    
    # Filter out stop words and count frequency (case-insensitive)
    filtered_tokens = [t for t in tokens if t not in stop_words]
    freq = {}
    for token in filtered_tokens:
        # Use lowercase for frequency counting to ensure case-insensitive deduplication
        token_lower = token.lower()
        freq[token_lower] = freq.get(token_lower, 0) + 1
    
    # Get top keywords by frequency
    sorted_tokens = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [token for token, _ in sorted_tokens[:max_tags]]


def merge_tags(existing_tags: List[str], new_tags: List[str], max_total: int = 15) -> List[str]:
    """Merge existing and new tags, removing duplicates and limiting total."""
    all_tags = existing_tags + new_tags
    normalized = normalize_tags(all_tags)
    
    # Limit total tags
    return normalized[:max_total]
