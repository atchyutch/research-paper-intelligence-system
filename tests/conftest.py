"""
conftest.py — Shared fixtures for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# NO backend imports here — they trigger the entire app import chain
# which loads HuggingFace, Pinecone, Ollama etc.

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fresh database for every test."""
    from backend.app.db.base import Base  # moved here
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# @pytest.fixture(scope="function")
# def client(db_session):
#     """FastAPI test client with the test database injected."""
#     from backend.app.main import app  # moved here
#     from backend.app.api.deps import get_db  # moved here
#
#     def override_get_db():
#         try:
#             yield db_session
#         finally:
#             pass
#
#     app.dependency_overrides[get_db] = override_get_db
#
#     with TestClient(app) as c:
#         yield c
#
#     app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with only the needed routers and the test DB injected."""
    from fastapi import FastAPI
    from backend.app.api.deps import get_db
    from backend.app.api.v1.endpoints.auth import auth_router
    from backend.app.api.v1.endpoints.conversation_logic import conversation_router

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(conversation_router, prefix="/api/v1")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def user_data():
    """Valid user registration data matching your create_user endpoint."""
    return {
        "first_name": "Atchyut",
        "last_name": "Chundru",
        "email": "testuser@gmail.com",
        "password": "passwordstrong"
    }


@pytest.fixture
def registered_user(client, user_data):
    """Creates a user via the actual endpoint."""
    response = client.post("/api/v1/auth/create_user", params=user_data)
    assert response.status_code == 201, f"User registration failed: {response.text}"
    return user_data


@pytest.fixture
def auth_headers(client, registered_user):
    """Logs in and returns Authorization headers with a valid JWT."""
    login_data = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }
    response = client.post("/api/v1/auth/login", params=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"

    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def created_conversation(client, auth_headers):
    """Creates a conversation and returns its response data."""
    response = client.post("/api/v1/conversations/", headers=auth_headers)
    assert response.status_code == 201, f"Conversation creation failed: {response.text}"
    return response.json()


@pytest.fixture
def fake_document(db_session, registered_user):
    """Inserts a document row directly into the test DB."""
    from backend.app.db.base import Documents, Users  # already was here

    user = db_session.query(Users).filter(
        Users.email == "testuser@gmail.com"
    ).first()

    doc = Documents(
        user_id=user.user_id,
        file_name="test_paper.pdf",
        document_link="fake/r2/key/test_paper.pdf",
        page_count=10,
        size_bytes=1024,
        file_hash="abc123fakehash"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc