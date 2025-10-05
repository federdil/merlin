# 🧙‍♂️ Merlin – Personal Knowledge Curator (Phase 1 MVP)

---

## 🎯 Pitch

### 🧠 The Problem
We are overwhelmed by information — articles, podcasts, videos, newsletters.  
Every day we save links, screenshots, scattered notes… but rarely go back to read them.  

> **The result:** Our digital knowledge is fragmented, dispersed, and mostly forgotten.

---

### 💡 The Solution
**Merlin** is an AI agent that turns your daily reading into structured knowledge.  

Just paste a link or the text of an article, and Merlin will:

- 📖 Read and understand the content  
- ✍️ Generate a personalized summary  
- 🏷 Extract intelligent thematic tags  
- 🔗 Connect related concepts from your existing archive  

Over time, it builds a **true semantic map of your personal knowledge**.

---

### ⚙️ How It Works
1. **User Input:** Paste a link or text.  
2. **AI Processing:** Claude + Strands process the content.  
3. **Semantic Storage:** Summaries, metadata, and links are stored in **PostgreSQL + pgvector**.  
4. **Discovery:** Browse, filter, and rediscover ideas via **Streamlit UI**.

---

### 🚀 What Makes It Unique
Unlike Obsidian or Notion, Merlin is **proactive and intelligent**:

- 🧠 Understands what you read  
- 📚 Enriches notes with context and references  
- 🔄 Builds automatic connections between sources  

> **It’s like having a second brain that grows with you.**

---

### 📈 Initial MVP
- **Input:** Pasted link or text  
- **Output:** Summary + tags + 3 similar articles already read  
- **Tech Stack:** Claude (LLM), Strands (agent), FastAPI + Streamlit, PostgreSQL/pgvector  

---

### 🌍 Long-Term Vision
Merlin aims to be the **personal cognitive assistant** for information-driven people:

- Read what you read  
- Understand your interests  
- Suggest new connections & insights from past knowledge  

> **In one sentence:**  
> “Merlin: your AI archivist that turns forgotten readings into living knowledge.”

---

## 🛠 Technical Description (Phase 1 MVP)
Merlin allows users to paste full content or submit a URL. The AI then:

- ✍️ Summarizes content  
- 🏷 Generates semantic tags  
- 💾 Stores notes in **PostgreSQL** with embeddings  
- 🔍 Suggests related notes via semantic search  
- 🪞 Optionally provides mini-reflections on knowledge growth  

### 🌟 Key Features
- **Autonomous AI Agent:** Decides actions on new inputs  
- **Curator Personality:** Friendly, reflective, thoughtful summaries  
- **Semantic Organization:** Notes linked by meaning, not folders  
- **Flexible Input:** Paste text or provide URL  
- **Mini Reflection:** Summarizes trends in user notes  

---

### 💻 Technical Stack

| Layer                  | Technology / Library       | Purpose                                                   |
|------------------------|---------------------------|-----------------------------------------------------------|
| Frontend (UI)          | Streamlit                 | Quick interface for input & visualization               |
| Backend                | FastAPI                   | API for note ingestion & agent communication            |
| Agent Framework        | Strands                   | Orchestrates summarization, tagging, embedding, reasoning|
| LLM                    | Claude                    | Summarization, tagging, reflective insights             |
| Database               | PostgreSQL + pgvector     | Store notes, embeddings, enable semantic search          |
| Embeddings             | pgvector / custom embeddings | Semantic similarity & linking                           |
| Environment Management | Python venv, dotenv       | Isolated dev environment, API keys management           |
