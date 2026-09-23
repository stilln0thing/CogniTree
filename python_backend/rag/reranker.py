"""
reranker.py — Reciprocal Rank Fusion (RRF) for hybrid keyword + vector search.
"""

from typing import List, Dict, Any


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combines vector search rankings and keyword search rankings using RRF formula:
    RRF_score(d) = sum_m ( 1 / (k + rank_m(d)) )
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    # Process vector rankings
    for rank, doc in enumerate(vector_results, 1):
        doc_id = doc.get("id", doc.get("text", ""))
        doc_map[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Process keyword rankings
    for rank, doc in enumerate(keyword_results, 1):
        doc_id = doc.get("id", doc.get("text", ""))
        doc_map[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Sort documents by total RRF score descending
    sorted_doc_ids = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)

    fused_results = []
    for doc_id in sorted_doc_ids:
        entry = dict(doc_map[doc_id])
        entry["rrf_score"] = round(scores[doc_id], 5)
        fused_results.append(entry)

    return fused_results
