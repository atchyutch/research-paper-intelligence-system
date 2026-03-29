import json
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.api.deps import get_db
from backend.app.api.v1.endpoints.auth import get_current_user
from backend.app.db.base import Conversations, ConversationDocuments, Messages, Documents
from backend.app.rag.pipeline import generate_rag_response, generate_rag_responseStream, call_llm_with_stream, \
    parse_citations
from backend.app.rag.schemas.conversation import ConversationResponse, ConversationCreate, MessageResponse, \
    MessageCreate, AddDocumentRequest, AgentResponse
from backend.app.rag.schemas.document_schemas import DocumentIDs

conversation_router = APIRouter(prefix="/conversations", tags=["conversations"])

# Retrieves the token from the url header and gives to us
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@conversation_router.post("/", status_code=201)
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
        db.refresh(conversation_object)
    return ConversationResponse(
        conversation_id = conversation_object.conversation_id,
        created_at = conversation_object.created_at,
    )



@conversation_router.get("/", status_code=200)
def get_user_conversations(user = Depends(get_current_user), db=Depends(get_db)) -> List[ConversationResponse]:
    """
    Retrieve all the conversation of the current user.
    :return: List of Conversation Responses
    """
    result_conversation = []
    try:
        conversations = db.query(Conversations).filter(Conversations.user_id == user.user_id)
        for each in conversations:
            result_conversation.append(ConversationResponse(
                conversation_id = each.conversation_id,
                created_at = each.created_at,
            ))
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


@conversation_router.delete("/delete/{conversation_id}")
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
            doc = db.query(Documents).filter(Documents.document_id == id).first()
            if not doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = "Document does not exist to associate")
            Conversation_Document = ConversationDocuments(
            conversation_id = conversation_id,
            document_id = id
            )
            db.add(Conversation_Document)
            db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@conversation_router.get("/{conversation_id}/documents")
def get_documents(conversation_id, db=Depends(get_db)):
    try:
        conversation_docs = db.query(ConversationDocuments).filter(
            ConversationDocuments.conversation_id == conversation_id,
        ).all()
        if not conversation_docs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No conversation created in that table")
        document_ids = []
        for row in conversation_docs:
            con_id = row.conversation_id
            doc_id = row.document_id
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
        db.commit()
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

    conversation = db.query(Conversations).filter(
        Conversations.conversation_id == conversation_id,
        Conversations.user_id == user.user_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    docs = db.query(ConversationDocuments).filter(
        ConversationDocuments.conversation_id == conversation_id
    ).first()
    if not docs:
        raise HTTPException(status_code=400,
                            detail="No documents associated with this conversation. Add documents before chatting.")
    try:
        Message_Obj = Messages(
            user_id = user.user_id,
            content = payload.content,
            conversation_id = conversation_id,
            role = "user",
            created_at = datetime.now(timezone.utc)
        )
        db.add(Message_Obj)
        db.commit()
        db.refresh(Message_Obj)
        msg_front = MessageResponse(
            conversation_id = Message_Obj.conversation_id,
            message_id = Message_Obj.message_id,
            content = Message_Obj.content,
            created_at = Message_Obj.created_at,
            role = Message_Obj.role,
        )
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
    try:
        agent_response, citations_list = generate_rag_response(conversation_id=conversation_id, query=payload.content,db=db, user_id=user.user_id)
        assistant_obj = Messages(
            user_id=user.user_id,
            content=agent_response,
            conversation_id=conversation_id,
            role="assistant",
            created_at=datetime.now(timezone.utc)
        )
        db.add(assistant_obj)
        db.commit()
        db.refresh(assistant_obj)

        final_response = AgentResponse(
            conversation_id=assistant_obj.conversation_id,
            message_id=assistant_obj.message_id,
            response_content=agent_response,
            sources_list = citations_list,
            created_at=assistant_obj.created_at,
            role=assistant_obj.role,
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Response generated but failed to save")

    return final_response


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


@conversation_router.get("/{conversation_id}/messages/stream")
def add_messages_stream(conversation_id, payload:MessageCreate, db = Depends(get_db), user = Depends(get_current_user)):

    conversation = db.query(Conversations).filter(Conversations.conversation_id == conversation_id,
                                                  Conversations.user_id == user.user_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail=f"Conversation with this id: {conversation_id} for that user: {user.user_id} is not found")


    docs = db.query(ConversationDocuments).filter(
        ConversationDocuments.conversation_id == conversation_id
    ).first()
    if not docs:
        raise HTTPException(status_code=400,
                            detail="No documents associated with this conversation. Add documents before chatting.")

    try:
        user_message = Messages(
            conversation_id = conversation_id,
            content = payload.content,
            created_at = datetime.now(timezone.utc),
            role = "user",
            user_id= user.user_id
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Addition of message in stream endpoint failed from backend."
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error in adding a user message instream endpoint for that conversation"
        )

    full_response = []
    final_context_message, result_rrf, document_names = generate_rag_responseStream(
        conversation_id, payload.content, db, user.user_id
    )
    try:
        for token in call_llm_with_stream(final_context_message):
            full_response.append(token)
            yield f"data: {token}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': 'LLM call failed to return the tokens for the response'})}\n\n"
        return

    complete_response = "".join(full_response)

    try:
        agent_obj = Messages(
            conversation_id=conversation_id,
            content=complete_response,
            created_at=datetime.now(timezone.utc),
            role="user",
            user_id=user.user_id
        )

        db.add(agent_obj)
        db.commit()
        db.refresh(agent_obj)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error in adding a assistant message instream endpoint for that conversation"
        )
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Addition of assistant message in stream endpoint failed from backend."
        )

    response_citations = parse_citations(complete_response, result_rrf, document_names)
    yield f"data: {json.dumps({'type': 'citations', 'data': response_citations})}\n\n"


