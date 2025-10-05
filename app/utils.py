from typing import Any, List
import json
import re


def normalize_tags(raw: Any) -> List[str]:
    # Handle degenerate case: list of single-character strings -> join and re-parse
    if isinstance(raw, list) and raw and all(isinstance(t, str) and len(t) == 1 for t in raw):
        joined = "".join(raw)
        return normalize_tags(joined)

    # Already a list of strings (normal case)
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]

    if raw is None:
        return []

    # If it's a string, try JSON first
    if isinstance(raw, str):
        s = raw.strip()
        # Try JSON array
        if (s.startswith("[") and s.endswith("]")):
            try:
                data = json.loads(s)
                if isinstance(data, list):
                    return [str(t).strip() for t in data if str(t).strip()]
            except Exception:
                pass
        # Try Postgres array literal like {"foo","bar"}
        if s.startswith("{") and s.endswith("}"):
            inner = s[1:-1]
            # split on commas not inside quotes
            parts = re.findall(r'"(.*?)"|([^,]+)', inner)
            cleaned: List[str] = []
            for a, b in parts:
                token = a or b
                token = token.strip().strip('"')
                if token:
                    cleaned.append(token)
            return cleaned
        # Fallback: split by comma
        return [t.strip() for t in s.split(",") if t.strip()]

    # Fallback: best-effort string cast
    return [str(raw)]
