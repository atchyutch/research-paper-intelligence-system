from datetime import datetime
from typing import List

import pydantic
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    document_id: int
    user_id: int
    created_at: datetime
    file_name: str
    page_count: int

class DocumentIDs(BaseModel):
    #Will use this to delete a list of  documents for that conversation and add a list of documents to that conversation
    documents_to_update: List[int]
