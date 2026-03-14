from sqlalchemy import Integer, Column, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime


Base = declarative_base()

class Users(Base):
    __tablename__ = "users"

    user_id: int = Column(Integer, primary_key=True)
    first_name: str = Column(String(100), nullable=False)
    last_name:str = Column(String(100), nullable=False)
    email: str = Column(String(50), unique=True)
    hashed_password:str = Column(String(100), nullable=False)

    documents = relationship("Documents", back_populates="users")
    conversations = relationship("Conversations", back_populates="users")
    messages = relationship("Messages", back_populates="user")

class Documents(Base):
    """
    A table to store all documents and their time of creation.
    """
    __tablename__ = "documents"

    document_id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.user_id"))
    created_at: datetime = Column(DateTime, default=datetime.now)
    file_name:str = Column(String(100), nullable=True)
    document_link:str = Column(String(1024), nullable=False) # R2_key for the document
    page_count:int = Column(Integer, nullable=False)
    size_bytes:int = Column(Integer, nullable=True)


    user = relationship("Users", back_populates="documents")
    chunks = relationship("Chunks", back_populates="documents")

class Conversations(Base):
    """
    A conversations table that keeps track of all conversations.
    """
    __tablename__ = "conversations"
    conversation_id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.user_id"))
    created_at: datetime = Column(DateTime, default=datetime.now)

    user = relationship("Users", back_populates="conversations")
    messages = relationship("Messages", back_populates = "conversations", cascade="all, delete-orphan")


class ConversationDocuments(Base):
    """
    An association table between conversations and documents to keep track of the scope of the documents we will
    have in that conversation.
    """
    __tablename__ = "conversationDocuments"
    conversation_id: int = Column(Integer, ForeignKey("conversations.conversation_id"), primary_key= True)
    document_id: int = Column(Integer, ForeignKey("documents.document_id"), primary_key=True)


class Messages(Base):
    __tablename__ = "messages"
    message_id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey('users.user_id'))
    content: str = Column(Text)
    role = Column(Enum("user", "assistant", "system", name="message_role"), nullable=False)
    created_at:datetime = Column(DateTime, default=datetime.now)
    conversation_id: int = Column(Integer, ForeignKey("conversations.conversation_id"))

    user = relationship("Users", back_populates="messages")
    conversation = relationship("Conversations", back_populates="messages")



class Chunks(Base):

    __tablename__= "chunks"
    chunk_id = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.user_id")) # Made a change need to update in the db
    chunk_content:str = Column(Text)
    document_id:int = Column(Integer, ForeignKey("documents.document_id"))
    chunk_index:int = Column(Integer, nullable=False)
    pinecone_id = Column(String(255), nullable=False, unique=True)
    section = Column(String(255), nullable=True)  # new
    page = Column(Integer, nullable=True)  # new
    char_count = Column(Integer, nullable=True) # new need to update in db

    document = relationship("Documents", back_populates="chunks")





