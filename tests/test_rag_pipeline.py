"""
test_rag_pipeline.py — Unit tests for core RAG functions.

6 tests covering the two most important functions:
    - reciprocal_ranking_fusion (context_retrieval.py)
    - parse_citations (pipeline.py)
"""

from langchain_core.documents import Document


def _make_doc(chunk_id, text="some text", doc_id=1):
    """Helper — creates a langchain Document matching your metadata structure."""
    return Document(
        page_content=text,
        metadata={
            "pinecone_id": chunk_id,
            "document_id": doc_id,
            "section": "Test",
            "page": 1,
            "char_count": len(text),
            "user_id": 1,
        }
    )


def _make_rrf_entry(doc_id=1, section="Intro", page=3):
    """Helper — creates an RRF result dict matching what reciprocal_ranking_fusion returns."""
    doc = Document(
        page_content="chunk text",
        metadata={"document_id": doc_id, "section": section, "page": page}
    )
    return {"doc": doc, "ranked_score": 0.5}


def test_rrf_overlap_ranks_higher():
    """Chunk in both lists gets a higher score than chunks in only one list."""
    from backend.app.rag.context_retrieval import reciprocal_ranking_fusion

    shared = _make_doc("c1", "Attention is all you need.")
    only_semantic = _make_doc("c2", "BERT uses transformers.")
    only_lexical = _make_doc("c3", "GPT is autoregressive.")

    semantic = [(shared, 0.95), (only_semantic, 0.85)]
    lexical = [shared, only_lexical]

    result = reciprocal_ranking_fusion(semantic, lexical)

    assert result[0]["doc"].metadata["pinecone_id"] == "c1"
    pids = [r["doc"].metadata["pinecone_id"] for r in result]
    assert set(pids) == {"c1", "c2", "c3"}


def test_rrf_empty_inputs():
    """Both lists empty → empty result."""
    from backend.app.rag.context_retrieval import reciprocal_ranking_fusion

    result = reciprocal_ranking_fusion([], [])
    assert result == []


def test_rrf_one_list_empty():
    """Semantic has results, lexical is empty → still works."""
    from backend.app.rag.context_retrieval import reciprocal_ranking_fusion

    doc = _make_doc("c1", "Something relevant.")
    result = reciprocal_ranking_fusion([(doc, 0.9)], [])

    assert len(result) == 1
    assert result[0]["doc"].metadata["pinecone_id"] == "c1"

def test_parse_single_citation():
    """Response with [1] → one citation dict with correct data."""
    from backend.app.rag.pipeline import parse_citations

    rrf = [_make_rrf_entry(doc_id=1, section="Intro", page=3)]
    doc_names = {1: "attention.pdf"}

    result = parse_citations("The model uses attention [1].", rrf, doc_names)

    assert len(result) == 1
    assert result[0]["Document"] == "attention.pdf"
    assert result[0]["Citation Number"] == 1


def test_parse_no_citations():
    """No [N] in response → empty list."""
    from backend.app.rag.pipeline import parse_citations

    rrf = [_make_rrf_entry()]
    doc_names = {1: "paper.pdf"}

    result = parse_citations("The model is interesting.", rrf, doc_names)
    assert result == []


def test_parse_duplicate_and_out_of_range():
    """[1] repeated 3 times → one entry. [99] with 1 chunk → skipped."""
    from backend.app.rag.pipeline import parse_citations

    rrf = [_make_rrf_entry()]
    doc_names = {1: "paper.pdf"}

    # Duplicates
    result = parse_citations("Great [1] and powerful [1] attention [1].", rrf, doc_names)
    assert len(result) == 1

    # Out of range
    result = parse_citations("See [99] for details.", rrf, doc_names)
    assert result == []