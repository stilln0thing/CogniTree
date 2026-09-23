# 🌿 CogniTree — Stateful Tree-Native Autonomous AI Agent Platform

CogniTree is a high-performance, stateful autonomous AI agent platform designed for multi-turn reasoning, decision tree branching, and local execution.

---

## 🏛️ System Architecture

- 🌿 **Interactive Decision Tree Canvas**: Explore parallel lines of reasoning on an interactive SVG canvas with time-travel state rewind.
- ⚡ **Multi-Node LangGraph Engine**: Planner -> Agent -> Evaluator -> Tools cycle.
- ✂️ **Context Pruning**: Algorithmic tombstoning of resolved retries, output truncation, and SHA-256 block summarization.
- 🔒 **Defense-in-Depth Security**: Workspace path jailing, AST inspection, Linux bubblewrap isolation, and secret masking (DLP).
- 🚀 **FastAPI Streaming Gateway**: Real-time token streaming via WebSockets and Server-Sent Events (SSE).

---

## 🛠️ Quickstart

### Prerequisites
- Python 3.11+

### Installation & Execution
```bash
# Install dependencies
pip install -r requirements.txt

# Copy config template
cp config.template.json config.json

# Run FastAPI backend
python python_backend/server/main.py
```

---

## 📄 License
Apache 2.0
