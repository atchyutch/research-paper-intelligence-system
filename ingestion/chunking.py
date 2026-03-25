import re
from typing import Dict, List, Any

from fastapi import Depends, HTTPException, status
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from sqlalchemy import Boolean
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db

from backend.app.api.v1.endpoints.auth import get_current_user
from backend.app.core.r2_client import get_r2_client
from backend.app.core.config import settings
from backend.app.db.base import Documents, Users
import fitz

from backend.app.db.base import Chunks
from ingestion.embedding import convert_chunks, final_ingestion

heading_words = {
    "abstract",
    "introduction",
    "related work",
    "background",
    "methods",
    "methodology",
    "experiments",
    "results",
    "discussion",
    "conclusion",
    "references",
    "acknowledgements"
}


def get_pdf_r2(current_user = Depends(get_current_user), client = Depends(get_r2_client)):
    obj = client.get_object(Bucket=settings.R2_BUCKET_NAME, Key=f"document/{current_user.user_id}/{current_user.document_link}")
    return obj["Body"].read()


###################
## Pdf Extraction
###################
def pdf_text(pdf_bytes: bytes) -> List[Dict[str,Any]]:
    """
    Collects the pdf as bytes and returns a dictionary with the text in that page.
    :param pdf_bytes:
    :return:
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages =[]
    page_count = doc.page_count
    for i in range(page_count):
        current_page = doc.load_page(i)
        page_text = current_page.get_text("text") or ""
        pages.append({
            "page": i + 1, "text": page_text
        })
    doc.close()
    return pages

################
## Text Cleaning
################
def text_cleaner(pages:List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    cleaned_pages = []
    for page in pages:
        curr_text = page["text"]
        # Fix the hyphenated line break words
        curr_text = re.sub(r"(\w)-\n(\w)", r"\1\2", curr_text)

        # Remove trailing spaces before newline
        curr_text = re.sub(r"[ \t]+\n", "\n", curr_text)

        # Protect paragraph breaks (one or more blank lines)
        curr_text = re.sub(r"\n\s*\n", "<<PARA>>", curr_text)

        # Convert remaining single newlines to spaces
        curr_text = curr_text.replace("\n", " ")

        # Restore paragraph breaks
        curr_text = curr_text.replace("<<PARA>>", "\n\n")

        # Collapse extra spaces
        curr_text = re.sub(r"[ \t]{2,}", " ", curr_text)

        # Collapse too many paragraph breaks
        curr_text = re.sub(r"(\n\s*){3,}", "\n\n", curr_text)

        cleaned_pages.append({
            "page": page["page"],
            "text": curr_text.strip()
        })

    return cleaned_pages


def identify_heading(text: str):
    capital_words_count = 0
    if text.isupper() and len(text) < 12:
        return True
    if len(text) > 100:
        return False
    if text.endswith((".", "?", "!")) and len(text)<50:
        return True
    if text.lower() in heading_words:
        return True
    if re.match(r"^\d+\.\d+", text):
        return True
    if re.match(r"^\d+(\.\d+)*\s+\S+", text):
        return True

    words =  text.split(" ")
    for word in words:
        if word.isupper() and len(word)<10:
            return True
        if word in heading_words:
            return True
        if word[:1].isupper():
            capital_words_count += 1
    if capital_words_count > len(words)//2:
        return True
    return False

def classify_block(cleaned_pages: List[Dict[str,Any]]):
    blocks = []
    buffer = []
    buffer_start_page = None  # stores the page where the current paragraph started

    for page in cleaned_pages:
        page_num = page["page"]  # use the actual page number from the dict
        lines = page.get("text", "").split("\n")

        for each in lines:
            cleaned_each = each.strip()

            # If we find a heading, first save any paragraph currently in buffer
            if identify_heading(cleaned_each):
                if len(buffer) > 0:
                    blocks.append({
                        "page_num": buffer_start_page,  # paragraph may have started on an earlier page
                        "type": "Paragraph",
                        "text": " ".join(buffer)
                    })
                    buffer = []
                    buffer_start_page = None

                # Then store the heading as its own block
                blocks.append({
                    "page_num": page_num,
                    "type": "Heading",
                    "text": cleaned_each
                })
                continue

            # Blank line means paragraph boundary, so save buffer if it has content
            elif cleaned_each == "":
                if len(buffer) > 0:
                    blocks.append({
                        "page_num": buffer_start_page,
                        "type": "Paragraph",
                        "text": " ".join(buffer)
                    })
                    buffer = []
                    buffer_start_page = None
                continue

            # Otherwise this is a normal content line, so keep collecting it
            else:
                if len(buffer) == 0:
                    buffer_start_page = page_num  # mark where this paragraph began
                buffer.append(cleaned_each)

    # After all pages are done, save any leftover paragraph still in buffer
    if len(buffer) > 0:
        blocks.append({
            "page_num": buffer_start_page,
            "type": "Paragraph",
            "text": " ".join(buffer)
        })

    return blocks



def recursive_splitter(paragraph: str) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1200, overlap = 200 )
    pieces = text_splitter.split_text(paragraph)

    return pieces


def structure_aware_chunking(retrieved_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    current_chunk = ""
    current_section = None
    max_chunk_size = 1200

    for each in retrieved_blocks:
        if each.get("type", "") == "Heading":
            current_section = each["text"]
            current_chunk += each["text"]
        elif each.get("type", "") == "Paragraph":
            if len(each["text"]) > max_chunk_size:
                #Call recursive character splitter
                collected_pieces = recursive_splitter(each["text"])
                for piece in collected_pieces:
                    chunks.append({
                        "text": piece,
                        "section": current_section,
                        "page": each["page_num"],
                        "char_count": len(piece)
                    })
                continue
            elif len(current_chunk) + len(each["text"]) < max_chunk_size:
                current_chunk += " " + each["text"]
                continue
            elif len(current_chunk) + len(each["text"]) > max_chunk_size:
                chunks.append(
                    {
                        "text": current_chunk,
                        "section": current_section,
                        "page": each["page_num"],
                        "char_count": len(current_chunk)
                    })
                current_chunk = ""
                current_chunk += " " + each["text"]
                continue
    if current_chunk:
        chunks.append({
            "text": current_chunk,
            "section": current_section,
            "char_count": len(current_chunk)
        })
    return chunks


def process_documents(document_id, client, db:Session, user):
    document = (
        db.query(Documents)
        .filter(
            Documents.document_id == document_id,
            Documents.user_id == user.user_id
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404,detail = "Document not found")

    obj = client.get_object(Bucket=settings.R2_BUCKET_NAME,
                            Key=f"document/{user.user_id}/{document.document_link}")

    pdf_bytes = obj["Body"].read()
    pages_pdf = pdf_text(pdf_bytes)
    cleaned_pages = text_cleaner(pages_pdf)
    blocks = classify_block(cleaned_pages)
    chunks = structure_aware_chunking(blocks)

    #send document id and user id to the ingesting thing
    langchain_docs = convert_chunks(chunks, document.document_id, user.user_id)

    final_ingestion(langchain_docs)

    # Send them into the sql table amigo
    for i, doc in enumerate(langchain_docs):
        chunk_object = Chunks(
            chunk_content=doc.page_content,
            chunk_index=i,
            document_id=doc.metadata["document_id"],
            pinecone_id=doc.metadata["pinecone_id"],
            user_id=user.user_id,
            section=doc.metadata.get("section"),
            page=doc.metadata.get("page"),
            char_count=doc.metadata.get("char_count")
        )

        try:
            db.add(chunk_object)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        finally:
            db.commit()
    return {"Status":"Success",
            "Message": "Chunks Created and added to both Vector DB and Backend DB"}













