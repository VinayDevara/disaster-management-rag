# DisasterRAG Project Overview

## 📂 Folder Structure
```text
DisasterRAG/
├── agents/                     # LLM Agent definitions
│   ├── consensus_agent.py
│   ├── disaster_agent.py
│   ├── flight_agent.py
│   ├── orchestrator_agent.py
│   └── weather_agent.py
├── config/                     # Configuration management
│   └── config.py
├── data/                       # Data storage
│   ├── chromadb/               # Vector database storage
│   ├── disaster_rag.db         # SQLite database
│   └── adsb_sample.xlsx
├── disaster-app-frontend/      # Frontend application codebase
├── disaster-dashboard/         # Dashboard application codebase
├── models/                     # Data models / Prompts
├── tools/                      # Agent tools
│   ├── api_tool.py
│   └── sql_tool.py
├── utils/                      # Core backend utilities
│   ├── context_window.py
│   ├── database.py
│   ├── llm_client.py
│   ├── metrics.py
│   ├── toon_converter.py
│   └── vector_db.py
├── .env                        # Environment variables
├── data_loader.py              # Data initialization
├── main.py                     # Main application entry point
└── requirements.txt            # Python dependencies
```

## 📄 Key Files
- **`main.py`**: The central entry point for the backend, initializing the FastAPI server and assembling the RAG agents.
- **`config/config.py`**: Central configuration class that loads environment variables (API keys for Groq, OpenWeather, NASA; DB paths; and tunable LLM parameters).
- **`agents/*`**: Contains the logic for specific domain agents (`flight_agent.py`, `weather_agent.py`, `disaster_agent.py`) and orchestrating/consensus agents (`orchestrator_agent.py`, `consensus_agent.py`).
- **`tools/*`**: Contains the fetchers and interface tools (`api_tool.py` for external API requests, `sql_tool.py` for database queries) used by agents.
- **`utils/database.py` & `utils/vector_db.py`**: Manage the connections to both the relational database and the vector store.

## 🛠️ Project Stack
- **Framework**: **FastAPI** (served via **Uvicorn**) orchestrating the backend API for the application.
- **LLM/AI Stack**: **DSPy** / **LangChain** usage for agentic workflows powered primarily by **Groq** (`llama3-70b-8192`) and local embeddings (`all-MiniLM-L6-v2`).
- **Databases**:
  - **Relational**: **SQLite** (`disaster_rag.db`) for structured data storage.
  - **Vector**: **ChromaDB** for document embeddings and semantic search.
- **Scheduler**: No heavy-duty task scheduler (like Celery or APScheduler) is explicitly defined. Execution is mostly driven by FastAPI async request handling.
