import os
import requests
import streamlit as st
from typing import List

API_URL = os.getenv("API_URL", "http://127.0.0.1:8002")

st.set_page_config(page_title="Merlin – Personal Knowledge Curator", layout="wide")

# --- Styles ---
st.markdown(
    """
    <style>
    .hero {
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        color: #fff;
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0 0 .35rem 0;
        font-size: 1.6rem;
        line-height: 1.2;
    }
    .sub { color: #cbd5e1; font-size: .95rem; margin: 0; }

    .card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 0.6rem 1rem 0.9rem 1rem; /* tighten top padding to remove white bar */
        margin-bottom: 0.75rem;
        background: #ffffff;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .card *:first-child { margin-top: 0; } /* ensure no top margin from first child */
    .card h4 { margin: 0 0 .35rem 0; font-size: 1.02rem; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #f3f4f6; color: #111827; border: 1px solid #e5e7eb; margin-right: 6px; margin-bottom: 6px; font-size: .8rem; }
    .muted { color: #6b7280; }
    .small { font-size: .85rem; }
    .divider { height: 1px; background: #e5e7eb; margin: 8px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Merlin – Personal Knowledge Curator</h1>
      <p class="sub">Paste a link or text to generate a summary, tags, and discover related notes. Search semantically across your knowledge.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# Tabs: Ingest, Search, Settings
ingest_tab, search_tab, settings_tab = st.tabs(["Ingest", "Search", "Settings"]) 

with ingest_tab:
    st.subheader("Add a new note")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        url = st.text_input("Article URL", placeholder="https://...")
        content = st.text_area("Or paste text", height=200, placeholder="Paste article or note text here…")
        title = st.text_input("Optional title override")
    with col_right:
        generate_llm = st.checkbox("Generate summary & tags (LLM)", value=True)
        top_k_sim = st.number_input("Similar notes to show", min_value=0, max_value=12, value=3, step=1)
        st.caption("Tip: Disable LLM to see local fallback summarization.")

    curate_clicked = st.button("Curate", type="primary")
    if curate_clicked:
        if not url and not content:
            st.warning("Provide either a URL or some content.")
        else:
            payload = {"url": url or None, "content": content or None}
            if title:
                payload["title"] = title
            if not generate_llm:
                payload["summary"] = None
                payload["tags"] = []

            with st.spinner("Curating note…"):
                try:
                    resp = requests.post(f"{API_URL}/add_note", json=payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success("Note added successfully")
                        # Pretty card for created note
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown(f"<h4>{data.get('title','(untitled)')}</h4>", unsafe_allow_html=True)
                        if data.get("summary"):
                            st.write(data["summary"])
                        created_tags: List[str] = data.get("tags") or []
                        if created_tags:
                            st.markdown("".join([f"<span class='tag'>{t}</span>" for t in created_tags]), unsafe_allow_html=True)
                        st.caption(f"Note ID: {data.get('id')}")
                        st.markdown("</div>", unsafe_allow_html=True)

                        note_id = data.get("id")
                        if note_id and top_k_sim > 0:
                            sim = requests.get(f"{API_URL}/similar/{note_id}", params={"top_k": top_k_sim}, timeout=20)
                            if sim.ok:
                                sim_items = sim.json() or []
                                if sim_items:
                                    st.markdown("### Similar notes")
                                    # Grid of cards
                                    ncols = 3 if len(sim_items) >= 3 else max(1, len(sim_items))
                                    rows = [sim_items[i:i+ncols] for i in range(0, len(sim_items), ncols)]
                                    for row in rows:
                                        cols = st.columns(ncols)
                                        for i, item in enumerate(row):
                                            with cols[i]:
                                                # Fetch tags for each similar note
                                                tags_html = ""
                                                try:
                                                    detail = requests.get(f"{API_URL}/notes/{item['id']}", timeout=15)
                                                    if detail.ok:
                                                        d = detail.json()
                                                        t = d.get("tags") or []
                                                        if t:
                                                            tags_html = "".join([f"<span class='tag'>{x}</span>" for x in t])
                                                except Exception:
                                                    pass
                                                st.markdown("<div class='card'>", unsafe_allow_html=True)
                                                # Title without id
                                                st.markdown(f"<h4>{item['title']}</h4>", unsafe_allow_html=True)
                                                if item.get("summary"):
                                                    st.write(item["summary"])
                                                if tags_html:
                                                    st.markdown(tags_html, unsafe_allow_html=True)
                                                st.caption(f"note_id: {item['id']}")
                                                st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

with search_tab:
    st.subheader("Search notes")
    query_col, k_col = st.columns([3,1])
    with query_col:
        query = st.text_input("Query", placeholder="Type your search… e.g., 'Leclerc'")
    with k_col:
        top_k = st.slider("Results", min_value=1, max_value=20, value=5)

    if st.button("Search", type="secondary"):
        if not query:
            st.warning("Enter a query")
        else:
            with st.spinner("Searching…"):
                try:
                    resp = requests.get(f"{API_URL}/search", params={"query": query, "top_k": top_k}, timeout=30)
                    if resp.ok:
                        results = resp.json() or []
                        if not results:
                            st.info("No results.")
                        for r in results:
                            st.markdown("<div class='card'>", unsafe_allow_html=True)
                            st.markdown(f"<h4>{r['title']}</h4>", unsafe_allow_html=True)
                            st.write(r.get("summary") or "(No summary)")
                            # Fetch tags for preview
                            detail = requests.get(f"{API_URL}/notes/{r['id']}", timeout=15)
                            if detail.ok:
                                d = detail.json()
                                tags = d.get("tags") or []
                                if tags:
                                    st.markdown("".join([f"<span class='tag'>{t}</span>" for t in tags]), unsafe_allow_html=True)
                            st.caption(f"note_id: {r['id']}")
                            st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

with settings_tab:
    st.subheader("Settings")
    st.caption("Configure the backend API URL used for requests.")
    api_val = st.text_input("API URL", value=API_URL)
    if st.button("Apply API URL"):
        os.environ["API_URL"] = api_val
        st.rerun()
