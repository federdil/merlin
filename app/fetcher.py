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
