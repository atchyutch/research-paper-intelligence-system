from typing import List, Dict, Any

from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
import asyncio
import os
from backend.app.core.config import settings

from dotenv import load_dotenv

load_dotenv()

def embeddings_inititation():
    # This embedding mode, takes text/images ie any data and converts them into vectors that will be stored in the VectorDB.
    embeddings_model = HuggingFaceEmbeddings(
        model_name= settings.EMBEDDINGS_MODEL,  # Model we are using for the embedding
        model_kwargs={"device": "cpu"},
    )

    # Our vector DB initialisation to store the vectors.
    vector_store = PineconeVectorStore(index_name=settings.PINECONE_INDEX_NAME, embedding=embeddings_model)

    return vector_store


def convert_chunks(chunks: List[Dict[str, Any]], document_id, user_id) -> List[Document]:
    langchain_chunk_docs = []
    for idx, chunk in enumerate(chunks):
        curr_doc = Document(page_content=chunk["text"], metadata={
                        "section": chunk.get("section", ""),
                        "page": chunk.get("page", ""),
                        "char_count":len(chunk.get("text", "")),
                        "document_id": document_id,
                        "user_id": user_id,
                        "pinecone_id": f"{user_id}_{document_id}_{idx}",}
        )
        langchain_chunk_docs.append(curr_doc)
    return langchain_chunk_docs


def final_ingestion(langchain_doc_chunks):
    if not langchain_doc_chunks:
        raise HTTPException(status_code=400, detail="No chunks available for ingestion")

    vector_store = embeddings_inititation()
    try:
        vector_store.add_documents(langchain_doc_chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"Status":"Success",
            "Message": "Chunks ingested into Vector DB."}



