from typing import List, Tuple, Any

from fastapi import Depends
import ollama
from sqlalchemy.orm import Session
from ollama import Client

from backend.app.api.deps import get_db
from backend.app.api.v1.endpoints.auth import get_current_user
# from backend.app.api.v1.endpoints.conversation_logic import conversation_router
from backend.app.core.config import settings

import re

from backend.app.rag.context_retrieval import get_conversation_document_ids, retrieve_top_chunks, \
    lexical_retrieval_top_chunks, reciprocal_ranking_fusion, get_document_names, conversational_history
from backend.app.rag.schemas.conversation import AgentResponse


def build_context(ranked_rrf, conversation_history, document_names, query):
    """
    Build the context for the agent
    :param ranked_rrf: Ranked final chunks
    :param conversation_history: Previous conversation upto last 15 messages
    :param document_names: Document names associated in the conversation
    :param query: The latest query sent by the user
    :return: The final prompt and the context blocks constructed.
    """
    context_blocks = []

    for i, chunk in enumerate(ranked_rrf, start=1):

        doc = chunk["doc"]
        doc_id = doc.metadata.get("document_id")
        page = doc.metadata.get("page", "Unknown")
        section = doc.metadata.get("section", "Unknown")
        content = doc.page_content

        doc_name = document_names.get(doc_id, "Unknown document")

        curr_source = (
            f"[{i}] Document: {doc_name} | Section: {section} | Page: {page}\n"
            f"{content}"
        )

        context_blocks.append(curr_source)

    context_chunks = "\n\n".join(context_blocks)

    system_message = (
        "You are a research paper assistant. Your job is to answer questions using ONLY the context provided below. "
        "Do not use any outside knowledge.\n\n"
        "Rules:\n"
        "- Cite your sources using [1], [2], etc. matching the chunk numbers below\n"
        "- Never fabricate citations\n"
        "- Prefer citing multiple sources when relevant\n"
        "- If the context does not contain enough information to answer, say "
        "\"I don't have enough information in the provided documents to answer this.\"\n"
        "- Be concise and direct\n"
        "- Reference the document name, section, and page when relevant\n\n"
        f"Context:\n{context_chunks}"
    )

    final_message = [{"role": "system", "content": system_message}]

    for message in conversation_history:
        final_message.append({
            "role": message.role,
            "content": message.content,
        })

    final_message.append({
        "role": "user",
        "content": query
    })

    return final_message, context_blocks


def call_llm(messages_list) -> Any:
    """
    Call the llm with the context
    :param messages_list:
    :return: The agent's response that is not parsed
    """
    try:
        client = Client(host=settings.OLLAMA_HOST)
        response = client.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages_list,
            options={
                "temperature": 0.4
            }
        )
    except Exception as e:
        raise RuntimeError("Error calling in the Ollama model, check"
                           "if the ollama model is downloaded locally and running.")
    return response["message"]["content"]

def call_llm_with_stream(messages_list):
    try:
        client = Client(host=settings.OLLAMA_HOST)
        response = client.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages_list,
            options={
                "temperature": 0.4
            },
            stream = True
        )

        for token in response["message"]["content"]:
            yield token

    except Exception as e:
        raise RuntimeError("Error calling in the Ollama model, check"
                       "if the ollama model is downloaded locally and running.")

def parse_citations(response, ranked_rrf, document_names) -> List[Any]:
    final_list = []
    seen = set()
    citation_list = re.findall(r'\[(\d+)\]', response)
    for every in citation_list:
        every = int(every)
        if every in seen or every < 1 or every > len(ranked_rrf):
            continue
        seen.add(every)
        curr_chunk = ranked_rrf[every - 1]
        doc = curr_chunk["doc"]
        doc_id = doc.metadata.get("document_id")
        doc_name = document_names.get(doc_id, "Unknown Document")
        section = doc.metadata.get("section", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        final_list.append({"Citation Number": every, "Document":
            doc_name,"Section":section, "Page": page ,"DocumentID":doc_id})
    return final_list


def generate_rag_response(conversation_id, query, db:Session, user_id):
    document_ids = get_conversation_document_ids(conversation_id, db)
    document_names = get_document_names(document_ids, db)
    semantic_results = retrieve_top_chunks(query, document_ids, user_id)
    lexical_results = lexical_retrieval_top_chunks(query, document_ids, user_id, db)
    result_rrf = reciprocal_ranking_fusion(semantic_results, lexical_results)
    history = conversational_history(db, conversation_id)
    final_context_message, context_blocks = build_context(result_rrf, history, document_names, query)
    response_llm = call_llm(final_context_message)
    parsed_citations = parse_citations(response_llm, result_rrf, document_names)

    return response_llm, parsed_citations


def generate_rag_responseStream(conversation_id, query, db:Session, user_id):
    document_ids = get_conversation_document_ids(conversation_id, db)
    document_names = get_document_names(document_ids, db)
    semantic_results = retrieve_top_chunks(query, document_ids, user_id)
    lexical_results = lexical_retrieval_top_chunks(query, document_ids, user_id, db)
    result_rrf = reciprocal_ranking_fusion(semantic_results, lexical_results)
    history = conversational_history(db, conversation_id)
    final_context_message, context_blocks = build_context(result_rrf, history, document_names, query)

    return final_context_message, context_blocks, result_rrf















