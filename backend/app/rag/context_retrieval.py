from typing import List, Tuple

from fastapi import Depends, HTTPException, status
from langchain_core.documents import Document
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.db.base import Chunks, Messages, ConversationDocuments, Documents
from sqlalchemy import select
from backend.app.rag.schemas.conversation import MessageResponse


def retrieve_top_chunks(query, document_ids: List[int], user_id, k: int = 6) -> List[Tuple[Document, float]]:
    from ingestion.embedding import embeddings_inititation
    vector_store = embeddings_inititation()

    results = vector_store.similarity_search_with_score(
        query=query,
        k=k,
        filter={"user_id":user_id,
                "document_id": {"$in": document_ids}}
    )
    return results


def lexical_retrieval_top_chunks(query,document_ids:List[int], user_id, db:Session):
    from langchain_community.retrievers import BM25Retriever
    stmt = select(Chunks).where(Chunks.user_id == user_id,
                                Chunks.document_id.in_(document_ids))
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

    if not documents:
        return []
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

    if len(ranked) < 5:
        return ranked
    else:
        return ranked[:5]

def conversational_history(db:Session, conversation_id):
    try:
        query = select(Messages).where(Messages.conversation_id == conversation_id).order_by(Messages.created_at.desc()).limit(15)
        messages_received = db.execute(query).scalars().all()
        messages_received = messages_received[::-1]
        message_response = []
        for every in messages_received:
            message_response.append(MessageResponse(
                conversation_id = every.conversation_id,
                message_id = every.message_id,
                content = every.content,
                role = every.role,
                created_at = every.created_at,
            ))
        return message_response

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Getting the last 15 messages in the context for the agent in their conversation has failed."
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error in retrieving the last 15 messages from the table for that conversation  has failed."
        )


def get_conversation_document_ids(conversation_id, db:Session):
    try:
        query = select(ConversationDocuments).where(ConversationDocuments.conversation_id == conversation_id)
        results = db.execute(query).scalars().all()
        conversation_document_ids = []
        for each in results:
            conversation_document_ids.append(each.document_id)
        return conversation_document_ids

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Getting the document ids in that conversation has failed."
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error in getting the document ids for that conversation has failed."
        )

def get_document_names(document_ids: List[int], db: Session):
    try:
        query = select(Documents).where(Documents.document_id.in_(document_ids))
        results = db.execute(query).scalars().all()
        document_names = {}
        for each in results:
            document_names[each.document_id] = each.file_name
        return document_names
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Getting the document names from the ids in that conversation has failed."
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error in getting the document names from their ids for that conversation has failed."
        )
