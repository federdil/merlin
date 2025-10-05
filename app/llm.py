import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv
import re

load_dotenv()

try:
    from anthropic import Anthropic
except Exception:  # optional dependency at runtime
    Anthropic = None  # type: ignore


SYSTEM_PROMPT = (
    "You are Merlin, a friendly, reflective curator. "
    "Summarize the user's content succinctly (120-180 words) and extract 5-10 semantic tags. "
    "Tags should be concise noun phrases, lowercase, no punctuation."
)

# Use models you have access to
PRIMARY_MODEL = "claude-3-5-haiku-20241022"
FALLBACK_MODEL = "claude-3-haiku-20240307"


def _get_client() -> Optional["Anthropic"]:
    if Anthropic is None:
        return None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def _local_fallback(content: str) -> Tuple[str, List[str]]:
    # Simple extractive summary: first 3 sentences (or ~180 words max)
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())
    summary = " ".join(sentences[:3])
    if len(summary.split()) > 180:
        summary = " ".join(summary.split()[:180])

    # Naive tag extraction: frequent keywords (lowercased), filter short/stop words
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", content.lower())
    tokens = [t for t in text.split() if len(t) > 2]
    stop = set(
        [
            "the","and","for","that","with","from","this","have","has","had","was","were","are","you","your","his","her","its","but","not","out","about","into","they","their","them","who","what","when","where","why","how","will","would","can","could","should","between","after","before","over","under","into","onto","more","most","some","any","each","other","than",
        ]
    )
    filtered = [t for t in tokens if t not in stop]
    freq: dict[str, int] = {}
    for t in filtered:
        freq[t] = freq.get(t, 0) + 1
    # pick top 8 unique tokens as tags
    top = sorted(freq.items(), key=lambda x: (-x[1], x[0]))[:8]
    tags = [w for w, _ in top]
    return summary or content[:200], tags


def is_llm_available() -> bool:
    return _get_client() is not None


def llm_ping() -> Tuple[bool, str]:
    client = _get_client()
    if client is None:
        return False, "no_client"
    try:
        msg = client.messages.create(
            model=PRIMARY_MODEL,
            max_tokens=20,
            temperature=0,
            system="Return JSON {\"ok\": true} only.",
            messages=[{"role": "user", "content": "ping"}],
        )
        # Coalesce text
        text_out = ""
        blocks = getattr(msg, "content", []) or []
        for block in blocks:
            val = getattr(block, "text", None) if not isinstance(block, dict) else block.get("text")
            if val:
                text_out += val
        return True, text_out.strip()
    except Exception as e:
        return False, f"error:{e}"


def summarize_and_tag(content: str) -> Tuple[Optional[str], List[str]]:
    """
    Returns (summary, tags). If API not configured or fails, uses a local fallback.
    """
    client = _get_client()
    if client is None:
        print("[LLM] No client available; using fallback")
        summary, tags = _local_fallback(content)
        return summary, tags

    prompt = (
        f"Content:\n\n{content[:6000]}\n\n"
        "Return STRICT JSON with keys 'summary' (string) and 'tags' (array of strings)."
    )

    def _call_model(model_name: str) -> Tuple[bool, str]:
        try:
            msg = client.messages.create(
                model=model_name,
                max_tokens=600,
                temperature=0.2,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            blocks = getattr(msg, "content", []) or []
            parts: List[str] = []
            for block in blocks:
                text_val = None
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_val = block.get("text")
                else:
                    text_val = getattr(block, "text", None)
                if text_val:
                    parts.append(text_val)
            combined = "\n".join(parts)
            return True, combined
        except Exception as e:
            print(f"[LLM] Exception calling {model_name}; will try fallback or local: {e}")
            return False, ""

    ok, combined = _call_model(PRIMARY_MODEL)
    if not ok:
        ok, combined = _call_model(FALLBACK_MODEL)

    if not ok:
        print("[LLM] Both model calls failed; using local fallback")
        return _local_fallback(content)

    print(f"[LLM] Raw output (first 200 chars): {combined[:200]!r}")

    import json
    data = None
    try:
        data = json.loads(combined)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", combined)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception as e:
                print(f"[LLM] JSON extract parse error: {e}")
                data = None
    if not isinstance(data, dict):
        print("[LLM] Could not parse JSON; using fallback")
        return _local_fallback(content)

    summary = data.get("summary")
    tags_raw = data.get("tags") or []
    tags = [str(t).strip().lower() for t in tags_raw if str(t).strip()] if isinstance(tags_raw, list) else []

    if not summary or not tags:
        print("[LLM] Empty fields from LLM; supplementing with fallback")
        fsum, ftags = _local_fallback(content)
        summary = summary or fsum
        if not tags:
            tags = ftags
    return summary, tags
