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
        "summarization": "📝",
        "knowledge_gap": "🧠",
        "conversational_query": "💬",
        "learning_path": "🛤️"
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
            # Make tags clickable
            tag_buttons = []
            for tag in note["tags"]:
                if st.button(tag, key=f"note_{note.get('id')}_{tag}", help=f"Click to see all notes tagged with '{tag}'"):
                    # This will trigger a search for the tag
                    st.session_state.selected_tag = tag
                    st.rerun()
            
            # Also display as styled tags
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
                    # Make tags clickable
                    for tag in similar["tags"]:
                        if st.button(tag, key=f"similar_{similar.get('id')}_{tag}", help=f"Click to see all notes tagged with '{tag}'"):
                            st.session_state.selected_tag = tag
                            st.rerun()
                    
                    # Also display as styled tags
                    tags_html = "".join([f"<span class='tag'>{t}</span>" for t in similar["tags"]])
                    st.markdown(tags_html, unsafe_allow_html=True)
                st.caption(f"ID: {similar.get('id')} | Similarity: {similar.get('similarity_score', 0):.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
    
    elif agent_type == "query" and "results" in agent_result:
        results = agent_result["results"]
        query = agent_result.get("query", "Unknown query")
        
        st.markdown(f"### 🔍 Search Results for: '{query}'")
        st.caption(f"Found {len(results)} results")
        
        # Display intelligent summary if available
        if "intelligent_summary" in agent_result:
            intelligent_summary = agent_result["intelligent_summary"]
            
            st.markdown("---")
            st.markdown("### 🧠 Intelligent Summary")
            
            if "intelligent_summary" in intelligent_summary:
                st.info(intelligent_summary["intelligent_summary"])
            
            # Display recommendations if available
            if "recommendations" in intelligent_summary and intelligent_summary["recommendations"]:
                st.markdown("#### 💡 Recommendations")
                for i, rec in enumerate(intelligent_summary["recommendations"], 1):
                    st.markdown(f"• {rec}")
            
            # Display key themes if available
            if "key_themes" in intelligent_summary and intelligent_summary["key_themes"]:
                st.markdown("#### 🏷️ Key Themes")
                for theme in intelligent_summary["key_themes"][:5]:  # Show top 5 themes
                    if isinstance(theme, dict):
                        st.markdown(f"• **{theme.get('theme', 'Unknown')}** (appears {theme.get('frequency', 0)} times)")
                    else:
                        st.markdown(f"• {theme}")
            
            st.markdown("---")
            st.markdown("### 📋 Detailed Results")
        
        # Display individual search results
        for result in results:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{result.get('title', 'Untitled')}</h4>", unsafe_allow_html=True)
            if result.get("summary"):
                st.write(result["summary"])
            if result.get("tags"):
                tags_html = "".join([f"<span class='tag'>{t}</span>" for t in result["tags"]])
                st.markdown(tags_html, unsafe_allow_html=True)
            
            # Show relevance score if available (from intelligent summary)
            caption_text = f"ID: {result.get('id')} | Created: {result.get('created_at', 'Unknown')}"
            if "intelligent_summary" in agent_result and "search_results" in agent_result["intelligent_summary"]:
                # Find matching result in intelligent summary to get relevance score
                intelligent_results = agent_result["intelligent_summary"]["search_results"]
                for int_result in intelligent_results:
                    if int_result.get('id') == result.get('id'):
                        if 'relevance_score' in int_result:
                            caption_text += f" | Relevance: {int_result['relevance_score']:.2f}"
                        break
            
            st.caption(caption_text)
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
    
    elif agent_type == "knowledge_gap" and "gap_analysis" in agent_result:
        display_knowledge_gaps(agent_result)
    
    elif agent_type == "conversational_query" and "conversational_response" in agent_result:
        display_conversational_response(agent_result)
    
    elif agent_type == "learning_path" and "path_structure" in agent_result:
        display_learning_path(agent_result)


def display_knowledge_gaps(agent_result: Dict[str, Any]):
    """Display knowledge gap analysis results."""
    try:
        gap_analysis = agent_result.get('gap_analysis', {})
        gaps = gap_analysis.get('gaps', [])
        summary = gap_analysis.get('summary', {})
        
        st.markdown("### 🧠 Knowledge Gap Analysis")
        
        # Display summary
        if summary:
            st.markdown("#### 📊 Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Gaps", summary.get('total_gaps_identified', 0))
            with col2:
                st.metric("High Priority", summary.get('high_priority_gaps', 0))
            with col3:
                st.metric("Medium Priority", summary.get('medium_priority_gaps', 0))
            with col4:
                st.metric("Low Priority", summary.get('low_priority_gaps', 0))
            
            # Overall assessment
            if summary.get('overall_assessment'):
                st.info(f"**Assessment:** {summary['overall_assessment']}")
        
        # Display individual gaps
        if gaps:
            st.markdown("#### 🔍 Identified Knowledge Gaps")
            for i, gap in enumerate(gaps, 1):
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                
                # Gap header
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"<h4>🔍 Gap #{i}: {gap.get('topic', 'Unknown Topic')}</h4>", unsafe_allow_html=True)
                with col2:
                    priority = gap.get('learning_priority', 'medium')
                    priority_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(priority, '🟡')
                    st.markdown(f"<p style='text-align: right;'>{priority_color} {priority.title()}</p>", unsafe_allow_html=True)
                
                # Gap description
                if gap.get('gap_description'):
                    st.write(gap['gap_description'])
                
                # Confidence score
                confidence = gap.get('confidence_score', 0)
                st.progress(confidence)
                st.caption(f"Confidence: {confidence:.2f}")
                
                # Suggested content
                suggested_content = gap.get('suggested_content', [])
                if suggested_content:
                    st.markdown("**💡 Suggested Learning:**")
                    for suggestion in suggested_content[:3]:  # Show top 3 suggestions
                        st.markdown(f"• {suggestion}")
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("🎉 No significant knowledge gaps identified! Your knowledge base looks well-rounded.")
            
    except Exception as e:
        st.error(f"Error displaying knowledge gaps: {str(e)}")


def display_conversational_response(agent_result: Dict[str, Any]):
    """Display conversational query response."""
    try:
        conversational_response = agent_result.get('conversational_response', {})
        temporal_info = agent_result.get('temporal_info', {})
        intent_analysis = agent_result.get('intent_analysis', {})
        
        st.markdown("### 💬 Conversational Response")
        
        # Direct answer
        if conversational_response.get('direct_answer'):
            st.markdown("#### 🎯 Direct Answer")
            st.write(conversational_response['direct_answer'])
        
        # Context explanation
        if conversational_response.get('context_explanation'):
            st.markdown("#### 📝 Context")
            st.info(conversational_response['context_explanation'])
        
        # Temporal information
        if temporal_info.get('has_temporal'):
            st.markdown("#### ⏰ Time Context")
            st.caption(f"Time period: {temporal_info.get('relative_period', 'unknown')}")
            if temporal_info.get('start_date') and temporal_info.get('end_date'):
                st.caption(f"Date range: {temporal_info['start_date'].strftime('%Y-%m-%d')} to {temporal_info['end_date'].strftime('%Y-%m-%d')}")
        
        # Related insights
        related_insights = conversational_response.get('related_insights', [])
        if related_insights:
            st.markdown("#### 💡 Related Insights")
            for insight in related_insights:
                st.markdown(f"• {insight}")
        
        # Follow-up suggestions
        follow_ups = conversational_response.get('follow_up_suggestions', [])
        if follow_ups:
            st.markdown("#### 🤔 Follow-up Suggestions")
            for suggestion in follow_ups:
                st.markdown(f"• {suggestion}")
        
        # Search results
        search_results = agent_result.get('search_results', {})
        results = search_results.get('results', [])
        if results:
            st.markdown("#### 📚 Related Content")
            for result in results[:3]:  # Show top 3 results
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<h4>{result.get('title', 'Untitled')}</h4>", unsafe_allow_html=True)
                if result.get('summary'):
                    st.write(result['summary'])
                if result.get('tags'):
                    tags_html = "".join([f"<span class='tag'>{t}</span>" for t in result['tags']])
                    st.markdown(tags_html, unsafe_allow_html=True)
                st.caption(f"Created: {result.get('created_at', 'Unknown')}")
                st.markdown("</div>", unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Error displaying conversational response: {str(e)}")


def display_learning_path(agent_result: Dict[str, Any]):
    """Display learning path results."""
    try:
        path_structure = agent_result.get('path_structure', {})
        path_metadata = agent_result.get('path_metadata', {})
        
        st.markdown("### 🛤️ Personalized Learning Path")
        
        # Path overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Level", agent_result.get('current_level', 'Unknown'))
        with col2:
            st.metric("Target Level", agent_result.get('target_level', 'Unknown'))
        with col3:
            st.metric("Estimated Duration", f"{path_metadata.get('estimated_duration', 8)} weeks")
        
        # Learning objectives
        objectives = agent_result.get('learning_objectives', [])
        if objectives:
            st.markdown("#### 🎯 Learning Objectives")
            for i, objective in enumerate(objectives, 1):
                st.markdown(f"{i}. {objective}")
        
        # Learning phases
        phases = path_structure.get('phases', [])
        if phases:
            st.markdown("#### 📚 Learning Phases")
            for i, phase in enumerate(phases, 1):
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                
                # Phase header
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"<h4>Phase {i}: {phase.get('title', 'Untitled Phase')}</h4>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<p style='text-align: center;'>{phase.get('duration', '2 weeks')}</p>", unsafe_allow_html=True)
                with col3:
                    difficulty = phase.get('difficulty', 'medium')
                    difficulty_color = {'easy': '🟢', 'medium': '🟡', 'hard': '🔴', 'expert': '🟣'}.get(difficulty, '🟡')
                    st.markdown(f"<p style='text-align: center;'>{difficulty_color} {difficulty.title()}</p>", unsafe_allow_html=True)
                
                # Phase description
                if phase.get('description'):
                    st.write(phase['description'])
                
                # Learning objectives for this phase
                phase_objectives = phase.get('learning_objectives', [])
                if phase_objectives:
                    st.markdown("**Learning Goals:**")
                    for objective in phase_objectives:
                        st.markdown(f"• {objective}")
                
                # Resources
                resources = phase.get('resources', [])
                if resources:
                    st.markdown("**📚 Resources:**")
                    for resource in resources[:3]:  # Show top 3 resources
                        if isinstance(resource, dict):
                            st.markdown(f"• {resource.get('title', 'Resource')}")
                        else:
                            st.markdown(f"• {resource}")
                
                # Activities
                activities = phase.get('activities', [])
                if activities:
                    st.markdown("**🎯 Activities:**")
                    for activity in activities[:3]:  # Show top 3 activities
                        if isinstance(activity, dict):
                            st.markdown(f"• {activity.get('title', 'Activity')}")
                        else:
                            st.markdown(f"• {activity}")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Key learning outcomes
        outcomes = path_metadata.get('learning_outcomes', [])
        if outcomes:
            st.markdown("#### 🏆 Key Learning Outcomes")
            for outcome in outcomes:
                st.markdown(f"• {outcome}")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start Learning Path", type="primary"):
                st.success("Learning path started! Good luck on your learning journey!")
        with col2:
            if st.button("📋 Save Learning Path"):
                st.success("Learning path saved to your profile!")
                
    except Exception as e:
        st.error(f"Error displaying learning path: {str(e)}")


# Sidebar for navigation and tag selection
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    st.markdown("---")
    
    # Check if a tag was selected
    if hasattr(st.session_state, 'selected_tag') and st.session_state.selected_tag:
        st.success(f"🏷️ Selected tag: {st.session_state.selected_tag}")
        if st.button("🔍 Search this tag", type="primary"):
            # Clear the selected tag and trigger search
            selected_tag = st.session_state.selected_tag
            delattr(st.session_state, 'selected_tag')
            # Switch to tag explorer tab
            st.session_state.active_tab = "Tag Explorer"
            st.rerun()
    
    st.markdown("### 📋 Quick Access")
    st.markdown("- **Home**: Main interface")
    st.markdown("- **Tag Explorer**: Browse by tags")
    st.markdown("- **Advanced**: Agent testing")
    st.markdown("- **Settings**: Configuration")
    
    st.markdown("---")
    st.markdown("### 🔥 Popular Tags")
    
    # Quick tag buttons in sidebar - fetch dynamically
    try:
        response = requests.get(f"{API_URL}/api/v1/tags")
        if response.status_code == 200:
            tags_data = response.json()
            if tags_data.get("success") and tags_data.get("tags"):
                # Get top 5 most popular tags
                quick_tags = [tag_info["tag"] for tag_info in tags_data["tags"][:5]]
                for tag in quick_tags:
                    if st.button(tag, key=f"sidebar_{tag}", help=f"Click to search for '{tag}'"):
                        st.session_state.selected_tag = tag
                        st.rerun()
            else:
                st.info("No tags found in your knowledge base yet.")
        else:
            st.error("Failed to load tags from API")
    except Exception as e:
        st.error(f"Error loading tags: {str(e)}")
        # Fallback to default tags
        quick_tags = ["AI", "Movies", "Philosophy", "Technology", "Recipes"]
        for tag in quick_tags:
            if st.button(tag, key=f"sidebar_{tag}", help=f"Click to search for '{tag}'"):
                st.session_state.selected_tag = tag
                st.rerun()

# Main interface - Single input box
st.markdown("### 💬 What would you like to do?")

input_text = st.text_area(
    "Paste a URL, text content, or ask a question...",
    height=150,
    placeholder="Examples:\n• https://example.com/article\n• What are the main topics in my notes?\n• Summarize the key points about AI\n• What knowledge gaps do I have?\n• What did I learn about AI last month?\n• Create a learning path for Python\n• Any text content you want to save"
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
advanced_tab, tags_tab, settings_tab = st.tabs(["Advanced", "Tag Explorer", "Settings"]) 

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

with tags_tab:
    st.subheader("🏷️ Tag Explorer")
    st.markdown("Explore your knowledge base by clicking on tags to see related notes.")
    
    # Get all notes to extract tags
    try:
        import requests
        # We'll need to add an endpoint to get all tags, for now let's use a workaround
        st.info("Loading tags from your knowledge base...")
        
        # Create a simple tag explorer using the existing search functionality
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🔥 Popular Tags")
            selected_tag = None
            
            # Fetch tags dynamically from API
            try:
                response = requests.get(f"{API_URL}/api/v1/tags")
                if response.status_code == 200:
                    tags_data = response.json()
                    if tags_data.get("success") and tags_data.get("tags"):
                        popular_tags = tags_data["tags"]
                        
                        # Display tags as clickable buttons with counts
                        tag_cols = st.columns(4)
                        for i, tag_info in enumerate(popular_tags):
                            tag = tag_info["tag"]
                            count = tag_info["count"]
                            with tag_cols[i % 4]:
                                if st.button(f"{tag} ({count})", key=f"tag_{tag}", help=f"Click to see {count} notes tagged with '{tag}'"):
                                    selected_tag = tag
                    else:
                        st.info("No tags found in your knowledge base yet.")
                        popular_tags = []
                else:
                    st.error("Failed to load tags from API")
                    popular_tags = []
            except Exception as e:
                st.error(f"Error loading tags: {str(e)}")
                # Fallback to some default tags
                popular_tags = [
                    {"tag": "AI", "count": 0}, {"tag": "Movies", "count": 0}, 
                    {"tag": "Philosophy", "count": 0}, {"tag": "Technology", "count": 0}
                ]
                tag_cols = st.columns(4)
                for i, tag_info in enumerate(popular_tags):
                    tag = tag_info["tag"]
                    with tag_cols[i % 4]:
                        if st.button(tag, key=f"tag_{tag}", help=f"Click to see notes tagged with '{tag}'"):
                            selected_tag = tag
        
        with col2:
            st.markdown("### 🔍 Search by Tag")
            custom_tag = st.text_input("Enter a custom tag:", placeholder="e.g., 'Transformers', 'Carbonara'")
            if custom_tag:
                selected_tag = custom_tag
        
        # Display results for selected tag
        if selected_tag:
            st.markdown(f"### 📚 Notes tagged with '{selected_tag}'")
            
            # Use the existing search functionality to find notes with this tag
            with st.spinner(f"Searching for notes with tag '{selected_tag}'..."):
                try:
                    # Create a search query for the tag
                    search_query = f"notes about {selected_tag}"
                    result = process_input_with_agents(search_query)
                    
                    if result.get("success") and result.get("result"):
                        # Display the results
                        display_agent_result(result)
                    else:
                        st.warning(f"No notes found with the tag '{selected_tag}'. Try a different tag or add some content first.")
                        
                except Exception as e:
                    st.error(f"Error searching for tag '{selected_tag}': {str(e)}")
        
        # Tag statistics
        st.markdown("---")
        st.markdown("### 📊 Tag Statistics")
        
        # Use real tag data from API
        try:
            response = requests.get(f"{API_URL}/api/v1/tags")
            if response.status_code == 200:
                tags_data = response.json()
                if tags_data.get("success") and tags_data.get("tags"):
                    popular_tags = tags_data["tags"][:9]  # Top 9 tags for display
                    
                    col1, col2, col3 = st.columns(3)
                    for i, tag_info in enumerate(popular_tags):
                        tag = tag_info["tag"]
                        count = tag_info["count"]
                        with [col1, col2, col3][i % 3]:
                            st.metric(tag, count)
                    
                    # Show total unique tags
                    total_tags = tags_data.get("total_unique_tags", 0)
                    st.info(f"📈 **Total unique tags in your knowledge base: {total_tags}**")
                else:
                    st.info("No tags found in your knowledge base yet.")
            else:
                st.error("Failed to load tag statistics from API")
        except Exception as e:
            st.error(f"Error loading tag statistics: {str(e)}")
        
        # Instructions
        st.markdown("---")
        st.markdown("### 💡 How to Use Tag Explorer")
        st.markdown("""
        - **Click on any popular tag** to see all notes related to that topic
        - **Enter a custom tag** in the search box to find specific content
        - **Browse by topic** to discover connections in your knowledge base
        - **Use this to find** similar content and explore related ideas
        """)
        
    except Exception as e:
        st.error(f"Error loading tag explorer: {str(e)}")

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
