from typing import List, Tuple

from fastapi import Depends
from langchain_core.documents import Document

from backend.app.api.deps import get_db
from backend.app.api.v1.endpoints.auth import get_current_user
from backend.app.db.base import Chunks
from ingestion.embedding import embeddings_inititation
from langchain_community.retrievers import BM25Retriever
from sqlalchemy import select


def retrieve_top_chunks(query, user = Depends(get_current_user), k: int = 6) -> List[Tuple[Document, float]]:
    vector_store = embeddings_inititation()

    results = vector_store.similarity_search_with_score(
        query=query,
        k=k,
        filter={"user_id":user.user_id}
    )
    return results


def lexical_retrieval_top_chunks(query, user = Depends(get_current_user), db = Depends(get_db)):

    stmt = select(Chunks).where(Chunks.user_id == user.user_id)
    documents = []
    for chunk in db.execute(stmt).scalars():
        doc = Document(
            page_content=chunk.chunk_content,
            metadata={
                "document_id": chunk.document_id,
                "pinecone_id": chunk.pinecone_id,
                "chunk_index": chunk.chunk_index,
                "user_id": chunk.user_id,
                "section": chunk.section,
                "page": chunk.page,
                "char_count": chunk.char_count
            }
        )
        documents.append(doc)

    lexical_retriever = BM25Retriever.from_documents(documents)

    lexical_retriever.k = 4
    results = lexical_retriever.invoke(query)

    return results

# Since semantic gives a relevancy score and lexical does not we will normalise them through a ranking score.
def reciprocal_ranking_fusion(semantic_results: List[Tuple[Document,float]], lexical_results: List[Document], k: int = 60):
    final_scores = {}
    for local_rank,(each, semantic_score) in enumerate(semantic_results, start=1):
        rrf_rank_semantic = 1/(k + local_rank)
        pid_semantic = each.metadata["pinecone_id"]
        final_scores[pid_semantic] = {"doc": each, "ranked_score": rrf_rank_semantic}

    for local_rank, each in enumerate(lexical_results):
        rrf_rank_lexical = 1/(k + local_rank)
        pid_lexical = each.metadata["pinecone_id"]

        if pid_lexical in final_scores:
            final_scores[pid_lexical]["ranked_score"] += rrf_rank_lexical
        else:
            final_scores[pid_lexical] = {"doc":each, "ranked_score": rrf_rank_lexical}

    ranked = sorted(final_scores.values(), key=lambda x: x["ranked_score"], reverse=True)

    return ranked










