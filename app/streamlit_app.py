import os
import requests
import streamlit as st
from typing import List, Dict, Any
import json

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
      <h1>🧙‍♂️ Merlin – Personal Knowledge Curator</h1>
      <p class="sub">AI-powered knowledge curation with intelligent agents. Paste a link, text, or ask a question.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def process_input_with_agents(input_text: str) -> Dict[str, Any]:
    """Process input using the new Strands Agents architecture."""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/process",
            json={"input_text": input_text},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API Error {response.status_code}: {response.text}",
                "agent_type": "error",
                "action": "error",
                "message": "Failed to process input"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "agent_type": "error",
            "action": "error",
            "message": "Failed to connect to API"
        }


def display_agent_result(result: Dict[str, Any]):
    """Display the result from an agent in a formatted way."""
    if not result.get("success", False):
        st.error(f"❌ {result.get('error', 'Unknown error')}")
        return
    
    agent_type = result.get("agent_type", "unknown")
    action = result.get("action", "unknown")
    message = result.get("message", "")
    agent_result = result.get("result", {})
    
    # Display success message
    st.success(f"✅ {message}")
    
    # Display agent info
    agent_emoji = {
        "ingestion": "📥",
        "query": "🔍", 
        "summarization": "📝"
    }.get(agent_type, "🤖")
    
    st.info(f"{agent_emoji} **Agent:** {agent_type.title()} | **Action:** {action}")
    
    # Display results based on agent type
    if agent_type == "ingestion" and "note" in agent_result:
        note = agent_result["note"]
        
        # Display the created note
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>📄 {note.get('title', 'Untitled')}</h4>", unsafe_allow_html=True)
        
        if note.get("summary"):
            st.write(note["summary"])
        
        if note.get("tags"):
            tags_html = "".join([f"<span class='tag'>{t}</span>" for t in note["tags"]])
            st.markdown(tags_html, unsafe_allow_html=True)
        
        st.caption(f"Note ID: {note.get('id')} | Created: {note.get('created_at', 'Unknown')}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display similar notes if available
        similar_notes = agent_result.get("similar_notes", [])
        if similar_notes:
            st.markdown("### 🔗 Similar Notes")
            for similar in similar_notes:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<h4>{similar.get('title', 'Untitled')}</h4>", unsafe_allow_html=True)
                if similar.get("summary"):
                    st.write(similar["summary"])
                if similar.get("tags"):
                    tags_html = "".join([f"<span class='tag'>{t}</span>" for t in similar["tags"]])
                    st.markdown(tags_html, unsafe_allow_html=True)
                st.caption(f"ID: {similar.get('id')} | Similarity: {similar.get('similarity_score', 0):.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
    
    elif agent_type == "query" and "results" in agent_result:
        results = agent_result["results"]
        query = agent_result.get("query", "Unknown query")
        
        st.markdown(f"### 🔍 Search Results for: '{query}'")
        st.caption(f"Found {len(results)} results")
        
        for result in results:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{result.get('title', 'Untitled')}</h4>", unsafe_allow_html=True)
            if result.get("summary"):
                st.write(result["summary"])
            if result.get("tags"):
                tags_html = "".join([f"<span class='tag'>{t}</span>" for t in result["tags"]])
                st.markdown(tags_html, unsafe_allow_html=True)
            st.caption(f"ID: {result.get('id')} | Created: {result.get('created_at', 'Unknown')}")
            st.markdown("</div>", unsafe_allow_html=True)
    
    elif agent_type == "summarization" and "generated_summary" in agent_result:
        st.markdown("### 📝 Generated Summary")
        st.write(agent_result["generated_summary"])
        
        if agent_result.get("generated_tags"):
            st.markdown("**Tags:**")
            tags_html = "".join([f"<span class='tag'>{t}</span>" for t in agent_result["generated_tags"]])
            st.markdown(tags_html, unsafe_allow_html=True)
        
        if agent_result.get("related_content"):
            st.markdown("### 🔗 Related Content")
            for related in agent_result["related_content"]:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<h4>{related.get('title', 'Untitled')}</h4>", unsafe_allow_html=True)
                if related.get("summary"):
                    st.write(related["summary"])
                st.caption(f"ID: {related.get('id')} | Relevance: {related.get('relevance_score', 0):.2f}")
                st.markdown("</div>", unsafe_allow_html=True)


# Main interface - Single input box
st.markdown("### 💬 What would you like to do?")

input_text = st.text_area(
    "Paste a URL, text content, or ask a question...",
    height=150,
    placeholder="Examples:\n• https://example.com/article\n• What are the main topics in my notes?\n• Summarize the key points about AI\n• Any text content you want to save"
)

process_button = st.button("🚀 Process with Merlin", type="primary")

if process_button:
    if not input_text or not input_text.strip():
        st.warning("Please enter some text, URL, or question.")
    else:
        with st.spinner("🧠 Merlin is thinking..."):
            result = process_input_with_agents(input_text.strip())
            display_agent_result(result)

# Additional tabs for advanced features
advanced_tab, settings_tab = st.tabs(["Advanced", "Settings"]) 

with advanced_tab:
    st.subheader("🤖 Agent Information")
    
    # Display available agents
    try:
        agents_resp = requests.get(f"{API_URL}/api/v1/agents/info", timeout=10)
        if agents_resp.status_code == 200:
            agents_info = agents_resp.json()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Available Agents:**")
                for agent_name, agent_info in agents_info.items():
                    if agent_name != 'router_agent':
                        st.write(f"• **{agent_info.get('name', agent_name)}**: {agent_info.get('description', 'No description')}")
            
            with col2:
                st.markdown("**Supported Actions:**")
                for agent_name, agent_info in agents_info.items():
                    if agent_name != 'router_agent' and 'supported_actions' in agent_info:
                        actions = ', '.join(agent_info['supported_actions'])
                        st.write(f"**{agent_info.get('name', agent_name)}**: {actions}")
        else:
            st.warning("Could not fetch agent information")
    except Exception as e:
        st.warning(f"Could not connect to API: {e}")
    
    st.markdown("---")
    
    # Agent testing section
    st.subheader("🧪 Test Specific Agent")
    
    test_input = st.text_area("Test Input", placeholder="Enter text to test routing...")
    if st.button("Test Routing"):
        if test_input:
            with st.spinner("Testing..."):
                result = process_input_with_agents(test_input)
                st.json(result)
        else:
            st.warning("Please enter test input")

with settings_tab:
    st.subheader("⚙️ Settings")
    
    # API Configuration
    st.markdown("**API Configuration**")
    api_val = st.text_input("API URL", value=API_URL)
    if st.button("Apply API URL"):
        os.environ["API_URL"] = api_val
        st.rerun()
    
    # Display current configuration
    st.markdown("**Current Configuration**")
    st.code(f"API URL: {API_URL}")
    
    # Health check
    st.markdown("**System Status**")
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=5)
        if health_resp.status_code == 200:
            st.success("✅ API is healthy")
        else:
            st.error(f"❌ API returned status {health_resp.status_code}")
    except Exception as e:
        st.error(f"❌ Cannot connect to API: {e}")
    
    # Instructions
    st.markdown("---")
    st.markdown("**📖 Usage Instructions**")
    st.markdown("""
    **Merlin v2.0** uses intelligent agents to process your input:
    
    • **📥 Ingestion Agent**: Automatically saves URLs and text content with AI-generated summaries and tags
    • **🔍 Query Agent**: Handles search queries and finds relevant information
    • **📝 Summarization Agent**: Creates summaries and analyzes content
    
    **Examples:**
    - Paste a URL → Ingestion Agent processes it
    - Ask "What are my notes about AI?" → Query Agent searches
    - Type "Summarize this: [content]" → Summarization Agent creates summary
    """)
