# 🧙‍♂️ Merlin – Personal Knowledge Curator v2.0

**AI-powered personal knowledge curation system with Strands Agents architecture and Claude AI**


---

### 🧠 The Problem
We are overwhelmed by information — articles, podcasts, videos, newsletters.  
Every day we save links, screenshots, scattered notes… but rarely go back to read them.  

> **The result:** Our digital knowledge is fragmented, dispersed, and mostly forgotten.

---

### 💡 The Solution
**Merlin** is an AI agent system that turns your daily reading into structured knowledge.  

Just paste a link, ask a question, or submit text, and Merlin's intelligent agents will:

- 🤖 **Automatically route** your input to the right specialist agent
- 📖 **Read and understand** content with AI-powered analysis  
- ✍️ **Generate personalized summaries** with contextual insights
- 🏷 **Extract intelligent tags** using semantic understanding
- 🔗 **Connect related concepts** from your existing archive  
- 🔍 **Answer questions** about your knowledge base

Over time, it builds a **true semantic map of your personal knowledge**.

---

### ⚙️ How It Works
1. **User Input:** Paste a link, ask a question, or submit text  
2. **Intelligent Routing:** Merlin classifies input and routes to appropriate specialist
3. **AI Processing:** Agents process content with specialized capabilities
4. **Semantic Storage:** Summaries, metadata, and embeddings 
5. **Discovery:** Browse, search, and rediscover ideas 

---

### 🚀 What Makes It Unique
Unlike Obsidian or Notion, Merlin is **proactive and intelligent**:

- 🧠 **Intelligent Agent Routing:** Automatically determines the best processing approach
- 🤖 **Specialized AI Agents:** Each agent has specific expertise (ingestion, query, summarization)
- 📚 **Context-Aware Processing:** Understands content type and user intent
- 🔄 **Automatic Connections:** Builds semantic links between sources  
- 🎯 **Unified Interface:** Single input box handles all interaction types

> **It's like having a team of AI specialists working for your knowledge curation.**

---

### 🌟 Key Features
- **🧠 Strands + Claude Integration**: Advanced AI reasoning using official Strands framework
- **🤖 Intelligent Agent Routing**: Claude-powered input classification and routing
- **📥 Smart Ingestion Agent**: AI-powered content analysis with insights extraction
- **🔍 Query Agent**: Semantic search and information retrieval
- **📝 Summarization Agent**: Advanced content analysis and summarization
- **🎯 Unified API**: Single endpoint for all interactions
- **💻 Modern UI**: Streamlined Streamlit interface with single input box
- **🔧 Structured Output**: Reliable AI responses using Pydantic models

---

### 💻 Technical Stack

| Layer                  | Technology / Library       | Purpose                                                   |
|------------------------|---------------------------|-----------------------------------------------------------|
| **Frontend (UI)**      | Streamlit                 | Unified interface for all interactions                   |
| **Backend API**        | FastAPI                   | RESTful API with unified processing endpoint             |
| **Agent Framework**    | Strands Agents            | Intelligent agent orchestration and routing              |
| **LLM**                | Claude 3.5 Haiku          | AI reasoning, summarization, and content analysis        |
| **Database**           | PostgreSQL + pgvector     | Store notes, embeddings, enable semantic search          |
| **Embeddings**         | sentence-transformers     | Semantic similarity & vector operations                   |
| **Content Extraction** | trafilatura               | URL content extraction and processing                     |
| **Environment**        | Python venv, dotenv       | Isolated dev environment, API keys management            |
| **Testing**            | pytest, httpx            | Comprehensive test suite for all components              |
| **Configuration**      | YAML                      | Agent configuration and routing rules                     |

---

merlin/
│
├── app/
│   ├── main.py                           # FastAPI entrypoint
│   ├── routes/
│   │   └── process_input.py              # Unified input endpoint
│   ├── agents/
│   │   ├── strands_router_agent.py       # 🆕 Strands + Claude routing
│   │   ├── strands_ingestion_agent.py    # 🆕 Strands + Claude analysis
│   │   ├── strands_conversational_query_agent.py  # Conversational queries
│   │   ├── strands_knowledge_gap_agent.py         # Knowledge gap analysis
│   │   ├── strands_learning_path_agent.py         # Learning path generation
│   │   ├── summarization_agent.py        # Summarization & analysis
│   │   ├── query_agent.py                # Search & retrieval
│   │   └── tools/
│   │       ├── content_fetcher.py
│   │       ├── summarize.py
│   │       ├── tagging.py
│   │       ├── embedding.py
│   │       ├── database_ops.py
│   │       ├── search.py
│   │       ├── external_knowledge.py
│   │       ├── knowledge_analyzer.py
│   │       ├── knowledge_assessor.py
│   │       ├── path_builder.py
│   │       ├── tag_utils.py
│   │       └── temporal_parser.py
│   └── streamlit_app.py                  # Modern UI interface
│
├── db/
│   ├── crud.py                   # Database operations
│   ├── models.py                 # Database models
│   └── create_tables.py          # Database initialization
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── test_runner.py            # Test runner
├── strands_config.yaml           # Agent configuration
├── start_merlin.py               # Startup script
├── test_agents.py                # Test suite
├── pytest.ini                   # Test configuration
└── requirements.txt              # Dependencies
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to the repository
cd personal_knowledge_curator

# Install dependencies
pip install -r requirements.txt


### 2. Start the System

```bash
# Start the API server
python start_merlin.py

# In another terminal, start the Streamlit UI
streamlit run app/streamlit_app.py
```

### 3. Use Merlin

Open http://localhost:8501 and simply paste:
- **URLs** → Automatically processed by Ingestion Agent
- **Questions** → Handled by Query Agent  
- **Text content** → Processed by Ingestion Agent
- **Summary requests** → Handled by Summarization Agent

## 🤖 Agent System

### Router Agent
- **Purpose**: Classifies user input and routes to appropriate agents
- **Technology**: Strands + Claude 3.5 Haiku
- **Input**: Any text, URL, or question
- **Output**: Routing decision with confidence score

### Ingestion Agent
- **Purpose**: Processes and stores new content
- **Technology**: Strands + Claude 3.5 Haiku
- **Capabilities**:
  - URL content extraction
  - AI-powered summarization
  - Intelligent tagging
  - Vector embedding generation
  - Similar note discovery

### Query Agent
- **Purpose**: Handles search and information retrieval
- **Capabilities**:
  - Semantic search
  - Text-based search
  - Hybrid search
  - Similarity search
  - Recent notes retrieval

### Summarization Agent
- **Purpose**: Creates summaries and analyzes content
- **Capabilities**:
  - Content summarization
  - Tag extraction
  - Trend analysis
  - Insight generation

## 🔧 API Endpoints

### Unified Processing
```http
POST /api/v1/process
Content-Type: application/json

{
  "input_text": "Your input here"
}
```

### Agent Information
```http
GET /api/v1/agents/info
GET /api/v1/agents/{agent_type}/capabilities
```

### Health Check
```http
GET /health
```

## 📝 Usage Examples

### URL Ingestion
```bash
curl -X POST "http://localhost:8002/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "https://example.com/article"}'
```

### Search Query
```bash
curl -X POST "http://localhost:8002/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "What are my notes about machine learning?"}'
```

### Text Summarization
```bash
curl -X POST "http://localhost:8002/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Summarize this: [your content here]"}'
```

## 🛠️ Configuration

The system is configured via `strands_config.yaml`:

```yaml
# Agent definitions
agents:
  router:
    name: "StrandsRouterAgent"
    type: "routing"
    class: "app.agents.strands_router_agent.StrandsRouterAgent"
    framework: "strands"
    model: "claude-3-5-haiku-20241022"
  
  ingestion:
    name: "StrandsIngestionAgent"
    type: "processing"
    class: "app.agents.strands_ingestion_agent.StrandsIngestionAgent"
    framework: "strands"
    model: "claude-3-5-haiku-20241022"
    tools:
      - "content_fetcher"
      - "summarize"
      - "tagging"
      - "embedding"
      - "database_ops"
```

## 🧪 Testing

Test the agent routing system:

```bash
# Test URL routing
curl -X POST "http://localhost:8002/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "https://news.ycombinator.com"}'

# Test query routing  
curl -X POST "http://localhost:8002/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Find notes about AI"}'

# Test summarization routing
curl -X POST "http://localhost:8002/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Summarize this article: [content]"}'

# Run test suite
python test_agents.py
```

---

**Merlin** - Your AI archivist that turns forgotten readings into living knowledge, powered by intelligent agents.
