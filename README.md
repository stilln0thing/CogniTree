# CogniTree — Stateful Tree-Native Autonomous AI Agent Platform

[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph%20StateGraph-blue?logo=python)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%26%20Uvicorn-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/LLM-Local%20Ollama%20(Free)-000000?logo=ollama)](https://ollama.com)
[![pgvector](https://img.shields.io/badge/Vector%20Store-PostgreSQL%20%2B%20pgvector-336791?logo=postgresql)](https://github.com/pgvector/pgvector)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python)](https://www.python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **CogniTree** is a high-performance, local-first autonomous AI agent platform designed for complex multi-turn reasoning, stateful conversational branching, and zero-cost local execution with **Ollama (`qwen2.5:7b`)**. Built with an async **FastAPI** streaming gateway, a multi-node **LangGraph** engine, **pgvector** hybrid RAG, dynamic context pruning, AST security guardrails, and an interactive **Shadcn SVG Decision Tree Canvas**.

---

## 🌟 Why CogniTree?

Traditional AI assistants force users into linear, fragile chat threads where context bloat burns tokens and dead-end tool failures pollute reasoning. **CogniTree solves this with a tree-native architecture:**

- 🌿 **Interactive Decision Tree Canvas**: Explore multiple parallel lines of reasoning on an interactive SVG canvas with smooth cubic Bezier connectors. Time-travel rewind to any previous turn and fork new branches instantaneously.
- 🦙 **100% Free Local Execution**: Native out-of-the-box support for Ollama models (`qwen2.5:7b`, `llama3.2`, `mistral`) running entirely on your local machine with zero API costs.
- ✂️ **Dynamic Context Pruning**: Algorithmic compaction that tombstones failed tool retries, truncates bulky outputs, and hierarchically summarizes historical turns—cutting token costs by over 40%.
- 🔍 **Hybrid pgvector RAG & Reranking**: Enterprise retrieval combining pgvector cosine similarity with keyword search via Reciprocal Rank Fusion (RRF).
- 🛡️ **Zero-Crash Stateful Checkpointing**: Durable persistence powered by `AsyncSqliteSaver` (with zero-configuration local fallback) preserving complete execution histories across application restarts.
- 🔒 **Defense-in-Depth Security**: Cross-platform path jailing (`is_path_safe`), AST static code analysis (`check_python_ast`), and DLP secret masking (`sanitize_output`).

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Web Canvas UI                         │
│  - Vanilla JavaScript (ES6+) + Modern Shadcn CSS            │
│  - Interactive SVG Decision Tree (Cubic Bezier Connectors)  │
│  - Real-time token streaming & Time-travel node brancher    │
└──────────────────────────────▲──────────────────────────────┘
                               │ ws://localhost:8765 / HTTP REST & SSE
┌──────────────────────────────▼──────────────────────────────┐
│                 FastAPI Gateway (python_backend/server)     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ FastAPI Application (main.py, routes/ws.py, rest.py)  │  │
│  │ - Structured Event Schema Validation (Pydantic v2)    │  │
│  │ - Dynamic CORS & 5h/24h Rolling Token Telemetry       │  │
│  │ - REST Endpoints (/health), OpenAPI, & SSE Stream     │  │
│  └───────────────────────────▲───────────────────────────┘  │
│                              │                               │
│  ┌───────────────────────────▼───────────────────────────┐  │
│  │ LangGraph Multi-Node Engine (python_backend/engine)   │  │
│  │ - StateGraph: Planner -> Agent -> Evaluator -> Tools  │  │
│  │ - Async Token Streaming via Ollama qwen2.5:7b         │  │
│  │ - Dynamic Context Pruner (Tombstoning & Truncation)   │  │
│  │ - Centralized Production Logger (Structured Formatting)│  │
│  └───────────▲───────────────────▲───────────────────▲───┘  │
│              │                   │                   │       │
│  ┌───────────▼───────────┐ ┌─────▼───────────┐ ┌─────▼─────┐ │
│  │ Dual Checkpoint Store │ │ pgvector & RAG  │ │ Observ.   │ │
│  │ - AsyncPostgresSaver  │ │ - VectorStore   │ │ - Logger  │ │
│  │ - AsyncSqliteSaver    │ │ - Embeddings    │ │ - Telemetry│ │
│  └───────────────────────┘ └─────────────────┘ └───────────┘ │
│                              ▲                               │
│  ┌───────────────────────────┴───────────────────────────┐  │
│  │ Defense-in-Depth Security & Tool Suite (python_tools) │  │
│  │ - AST analysis, workspace path jail, secret masking   │  │
│  │ - DuckDuckGo web search, Python execution, file tools │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Engineering Highlights

### 1. Multi-Node LangGraph Loop & Model Flexibility
Decomposes complex user requests into discrete, observable steps:
- **`planner`**: Intelligent task decomposition formulating execution plans before actions start.
- **`agent`**: Async token-by-token streaming using free local **Ollama (`qwen2.5:7b`)** or cloud **OpenAI GPT-4o**.
- **`tools`**: Concurrent async tool execution with dynamic dispatch and parameter fallbacks.
- **`evaluator` & `recovery`**: Two-strike self-healing guardrail. On repeated tool failure, routes to `recovery` with reflection guidance before terminating infinite loops.

### 2. Algorithmic Context Pruning & Tombstoning
- **Dead-end Tombstoning**: Verbose tracebacks and failed commands are replaced with single-line tombstones as soon as a retry succeeds, preventing catastrophic hallucination loops.
- **Bulky Output Truncation**: Intelligently samples head/tail snippets of large outputs (>400 tokens) with reduction markers.
- **SHA-256 Block Summarization**: Progressively summarizes historical conversation blocks and caches summaries using deterministic SHA-256 keys.

### 3. Hybrid RAG with Reciprocal Rank Fusion (RRF)
- **Vector Store**: Cosine similarity vector retrieval for document chunking.
- **Reciprocal Rank Fusion (RRF)**: Merges lexical keyword search and vector ranking lists:
  $$RRF(d) = \sum_{m \in M} \frac{1}{60 + \text{rank}_m(d)}$$

### 4. Production-Grade Structured Logging
- Centralized `logging` format: `[TIMESTAMP] [LOG_LEVEL] [MODULE] Message`.
- Clean operational logs tracking graph initialization, node transitions, execution durations, tool outputs, and security checks.

---

## 🛠️ Built-in Tool Suite & Security Guardrails

| Tool | Capabilities |
|---|---|
| `web_search` | Live internet search via DuckDuckGo / ddgs |
| `run_local_python_script` | Subprocess Python execution with AST code checking and subprocess isolation |
| `read_file` / `write_file` | Filesystem operations strictly jailed to `AGENT_WORK_DIR` |
| `SimpleVectorStore` | Cosine similarity vector search combined with keyword retrieval |

### 🔒 Defense-in-Depth Guardrails (`security.py`)
- **Workspace Path Jail (`is_path_safe`)**: Confines all file operations strictly inside `AGENT_WORK_DIR`.
- **System Blocklist**: System folders (`~/.ssh`, `~/.aws`, `~/.bashrc`, `/etc`, `C:\Windows`) are unconditionally blocked.
- **AST Static Code Analysis (`check_python_ast`)**: Pre-execution AST inspection blocks dangerous modules (`ctypes`, `pty`, `winreg`) and dynamic execution primitives (`eval`, `exec`).
- **DLP Secret Masking (`sanitize_output`)**: Automatic redaction of OpenAI, GitHub, and AWS API keys or private keys in tool outputs.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) (for 100% free local model execution)

### 1. Model Setup (Ollama)
```bash
# Pull local model (free execution)
ollama pull qwen2.5:7b
```

### 2. Local Environment Setup & Execution
```bash
# Navigate to project folder
cd ~/Desktop/cognitree

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server & Web UI
python python_backend/server/main.py
```

### 3. Access Web UI Canvas
Open **`http://localhost:8765/ui`** in your browser!

---

## 📋 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | HTML5, Vanilla JavaScript (ES6+), SVG Bezier Canvas, Shadcn Dark Theme |
| **Backend Gateway** | FastAPI, Uvicorn, Pydantic v2, WebSockets, Server-Sent Events (SSE) |
| **Agent Core** | LangGraph, LangChain Core, OpenAI Python SDK |
| **Local LLM Engine** | Ollama (`qwen2.5:7b`), AsyncOpenAI client compatibility |
| **Data & Retrieval** | PostgreSQL 16, pgvector, aiosqlite, AsyncSqliteSaver, RRF Fusion |
| **Security & Utilities** | AST Static Analysis, Subprocess Isolation, DLP Regex Masking, DuckDuckGo Search |

---

## 📄 License

Distributed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for more information.
