"""
vectorstore.py — Lightweight in-memory/sqlite hybrid vector & keyword store.
"""

import math
from typing import List, Dict, Any
from python_backend.rag.reranker import reciprocal_rank_fusion


def _naive_vector(text: str) -> List[float]:
    """Generates a simple normalized frequency vector for demonstration search."""
    words = [w.lower() for w in text.split() if len(w) > 2]
    vocab = ["ai", "agent", "state", "langgraph", "python", "model", "vector", "search", "tree", "prune"]
    vec = [words.count(v) for v in vocab]
    norm = math.sqrt(sum(x*x for x in vec)) or 1.0
    return [x / norm for x in vec]


class SimpleVectorStore:
    """
    Lightweight document store supporting hybrid keyword search, cosine vector search,
    and Reciprocal Rank Fusion (RRF).
    """

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """Adds a document chunk to the vector store."""
        vec = _naive_vector(content)
        self.documents.append({
            "id": doc_id,
            "text": content,
            "metadata": metadata or {},
            "vector": vec
        })

    def vector_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Cosine similarity vector search."""
        q_vec = _naive_vector(query)
        scored = []
        for doc in self.documents:
            d_vec = doc["vector"]
            dot = sum(a * b for a, b in zip(q_vec, d_vec))
            scored.append((dot, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k]]

    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Exact keyword matching search."""
        q_terms = set(query.lower().split())
        scored = []
        for doc in self.documents:
            d_terms = set(doc["text"].lower().split())
            overlap = len(q_terms.intersection(d_terms))
            scored.append((overlap, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k]]

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes vector search + keyword search and merges using Reciprocal Rank Fusion (RRF).
        """
        v_res = self.vector_search(query, top_k=top_k)
        k_res = self.keyword_search(query, top_k=top_k)
        return reciprocal_rank_fusion(v_res, k_res)[:top_k]
