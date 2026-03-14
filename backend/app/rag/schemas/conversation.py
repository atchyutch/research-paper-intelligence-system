from datetime import datetime
from typing import List

import pydantic
from pydantic import BaseModel, Field

class ConversationCreate(BaseModel):
    pass

class ConversationResponse(BaseModel):
    conversation_id:int = Field("The conversation's representation")
    created_at:datetime = Field("The conversation's creation time and date")
    # documents_attached:List = Field("The documents in this conversation")

class AddDocumentRequest(BaseModel):
    document_id: int = Field("The id of the document")


class MessageCreate(BaseModel):
    content:str
    role:str = "user"
    conversation_id: int = Field("The conversation to which this message belongs")
    created_at: datetime = Field("The message's creation time and date")

class MessageResponse(BaseModel):
    conversation_id: int = Field("The conversation's representation")
    message_id:int = Field("Send the id to the frontend")
    content:str = Field("The message's content")
    role:str = "user"
    created_at:datetime = Field("The message's creation time and date")


