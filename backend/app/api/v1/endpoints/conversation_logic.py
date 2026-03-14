from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.api.deps import get_db
from backend.app.api.v1.endpoints.auth import get_current_user
from backend.app.db.base import Conversations, ConversationDocuments, Messages
from backend.app.rag.schemas.conversation import ConversationResponse, ConversationCreate, MessageResponse,\
    MessageCreate, AddDocumentRequest
from backend.app.rag.schemas.document_schemas import DocumentIDs

conversation_router = APIRouter(prefix="/conversations", tags=["conversations"])

# Retrieves the token from the url header and gives to us
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@conversation_router.post("/")
def create_new_conversation(user = Depends(get_current_user), db=Depends(get_db)):
    """
    Create a new conversation
    :return: Return the conversation response which has the id, datetime.
    """
    curr_datetime = datetime.now()
    conversation_object = Conversations(
        user_id = user.user_id,
        created_at = curr_datetime,
    )
    try:
        db.add(conversation_object)
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    finally:
        db.commit()



@conversation_router.get("/")
def get_user_conversations(user = Depends(get_current_user), db=Depends(get_db)) -> List[ConversationResponse]:
    """
    Retrieve all the conversation of the current user.
    :return: List of Conversation Responses
    """
    result_conversation = []
    try:
        conversations = db.query(Conversations).filter(user_id = user.user_id)
        for each in conversations:
            ConversationResponse(
                conversation_id = each.conversation_id,
                created_at = each.created_at,
            )
            result_conversation.append(ConversationResponse())
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT  , detail = str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = str(e))
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "HTTP error from get user's all conversations")
    return result_conversation

@conversation_router.get("/{conversation_id}")
def get_single_conversation(conversation_id, user = Depends(get_current_user), db=Depends(get_db)) -> ConversationResponse:
    """
    Retrieve a single conversation
    :param user: Verified user, also makes sure the token is not tamopered with
    :param db: Connection to the database with a session object
    :return: Single conversation response
    """
    try:
        conversation = db.query(Conversations).filter(
            Conversations.user_id == user.user_id,
            Conversations.conversation_id == conversation_id,
        ).first()
        response = ConversationResponse(
            conversation_id = conversation.conversation_id,
            created_at = conversation.created_at,
        )
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT  , detail = str(e))

    return response


@conversation_router.delete("/delete/{comnversation_id")
def delete_conversation(conversation_id, user = Depends(get_current_user), db=Depends(get_db)):
    try:
        db.query(Conversations).filter(Conversations.user_id == user.user_id,
                                       Conversations.conversation_id == conversation_id).delete()
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT  , detail = str(e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = str(e))
    except HTTPException as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "HTTP error for deleting the conversations")


@conversation_router.post("/{conversation_id}/documents")
def associate_docs(conversation_id, payload: DocumentIDs, user = Depends(get_current_user), db=Depends(get_db)):
    try:
        for id in payload.documents_to_update:
            Conversation_Document = ConversationDocuments(
            conversation_id = conversation_id,
            document_id = id
            )
            db.add(Conversation_Document)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HTTP error to make change to the conversation's document scope")


@conversation_router.get("/{conversation_id}/documents")
def get_documents(conversation_id, db=Depends(get_db)):
    try:
        conversation_docs = db.query(ConversationDocuments).filter(
            ConversationDocuments.conversation_id == conversation_id,
        ).all()
        document_ids = []
        for (con_id,doc_id) in conversation_docs:
            document_ids.append(doc_id)
        return DocumentIDs(documents_to_update=document_ids)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate association"
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@conversation_router.delete("/{conversation_id}/documents/{document_id}")
def delete_document(conversation_id, document_id, db = Depends(get_db)):
    try:
        db.query(ConversationDocuments).filter(
            ConversationDocuments.conversation_id == conversation_id,
            ConversationDocuments.document_id == document_id,
        ).delete()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deletion failed from backend"
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error from delete a document from a conversation"
        )

@conversation_router.post("/{conversation_id}/messages")
def add_message(conversation_id, payload:MessageCreate, db = Depends(get_db), user = Depends(get_current_user)):
    try:
        for each in payload:
            Message_Obj = Messages(
                user_id = user.user_id,
                content = each.content,
                conversation_id = conversation_id,
                role = "user",
                created_at = datetime.now(timezone.utc)
            )
            db.add(Message_Obj)
            db.refresh(Message_Obj)
            msg_front = MessageResponse(
                conversation_id = Message_Obj.conversation_id,
                message_id = Message_Obj.message_id,
                content = Message_Obj.content,
                created_at = Message_Obj.created_at,
            )
            return msg_front
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Addition of message failed from backend."
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error in adding a message for that conversation"
        )



@conversation_router.get("/{conversation_id}/messages")
def list_all_messages(conversation_id, db = Depends(get_db), user = Depends(get_current_user)):
    try:
        messages_db = db.query(Messages).filter(
            Messages.conversation_id == conversation_id,
            Messages.user_id == user.user_id
        ).all()
        messages = []
        for each in  messages_db:
            messages.append(MessageResponse(
                conversation_id = each.conversation_id,
                message_id = each.message_id,
                content = each.content,
                created_at = each.created_at,
                role = each.role
            ))
        return messages

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Getting all of the message failed from backend."
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error in retrieving all messages from the table for that conversation"
        )



