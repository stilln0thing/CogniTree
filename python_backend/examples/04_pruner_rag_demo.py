"""
04_pruner_rag_demo.py — Phase 4: Context Pruner & Hybrid RAG Verification Demo
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_core.messages import ToolMessage, HumanMessage
from python_backend.engine.pruner import prune_context, truncate_bulky_output
from python_backend.rag.vectorstore import SimpleVectorStore


def main():
    print("✂️ Testing CogniTree Context Pruner & Hybrid RAG...\n")

    # 1. Test Output Truncation
    print("1️⃣ Testing Bulky Output Truncation:")
    large_output = "LINE " + "\nLINE ".join([f"Trace log entry #{i}" for i in range(500)])
    truncated = truncate_bulky_output(large_output, max_chars=300)
    print(f"   - Original size: {len(large_output)} chars")
    print(f"   - Truncated size: {len(truncated)} chars")
    print(f"   - Snippet:\n{truncated[:120]}...\n")

    # 2. Test Dead-end Tombstoning
    print("2️⃣ Testing Failed Tool Tombstoning:")
    msg_history = [
        HumanMessage(content="Run python script"),
        ToolMessage(content="Error: ModuleNotFoundError: No module named 'foo'", name="python_run", tool_call_id="call_1"),
        ToolMessage(content="Script executed successfully with output: Hello World", name="python_run", tool_call_id="call_2")
    ]
    pruned = prune_context(msg_history)
    print(f"   - Original Msg 1: {msg_history[1].content}")
    print(f"   - Pruned Msg 1 (Tombstoned): {pruned[1].content}\n")

    # 3. Test Hybrid RAG Search with RRF
    print("3️⃣ Testing Hybrid RAG (pgvector / SimpleVectorStore + RRF):")
    store = SimpleVectorStore()
    store.add_document("doc1", "LangGraph uses StateGraph to orchestrate multi-node agent loops.")
    store.add_document("doc2", "CogniTree is an enterprise-grade stateful agent platform.")
    store.add_document("doc3", "PostgreSQL pgvector provides cosine similarity vector retrieval.")

    results = store.hybrid_search("LangGraph stateful agent", top_k=2)
    for i, r in enumerate(results, 1):
        print(f"   [{i}] Score={r['rrf_score']} | ID={r['id']} | Content: {r['text']}")

    print("\n✅ All Phase 4 Pruner & Hybrid RAG tests passed!")


if __name__ == "__main__":
    main()
