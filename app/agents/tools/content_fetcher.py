"""
Content fetcher tool for agents.
Refactored from app/fetcher.py to be used by Strands agents.
"""

import trafilatura
from typing import Optional, Tuple


def fetch_url_content(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch and extract main content and (optionally) title from a URL using trafilatura.
    Returns (title, content) or (None, None) if extraction fails.
    """
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None, None

    # trafilatura v2: extract returns plain text; 'output' param is not supported
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
    )
    if not text:
        return None, None

    text = text.strip()

    # Title extraction: trafilatura doesn't return title in plain-text mode; leave None
    title = None
    return title, text


def is_url(text: str) -> bool:
    """Check if the input text is a URL."""
    if text is None:
        return False
    return text.startswith(('http://', 'https://'))


def extract_content_from_input(input_text: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extract content from user input. Returns (title, content, input_type).
    input_type can be 'url', 'text', or 'empty'
    """
    if not input_text or not input_text.strip():
        return None, None, 'empty'
    
    input_text = input_text.strip()
    
    if is_url(input_text):
        title, content = fetch_url_content(input_text)
        return title, content, 'url'
    else:
        return None, input_text, 'text'
