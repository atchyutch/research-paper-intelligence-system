"""
conftest.py — Shared fixtures for all tests.

"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.api.deps import get_db
from backend.app.db.base import Base



SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fresh database for every test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with the test database injected."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # NO parentheses — assign the function, don't call it
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

# AUTH FIXTURES
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
    # user_data is already a dict — don't call it as a function
    response = client.post("/auth/create_user", json=user_data)
    assert response.status_code == 201, f"User registration failed: {response.text}"
    return user_data


@pytest.fixture
def auth_headers(client, registered_user):
    """Logs in and returns Authorization headers with a valid JWT."""
    login_data = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



# CONVERSATION & DOCUMENT FIXTURES
@pytest.fixture
def created_conversation(client, auth_headers):
    """Creates a conversation and returns its response data."""
    response = client.post("/conversations/", headers=auth_headers)
    assert response.status_code == 201, f"Conversation creation failed: {response.text}"
    return response.json()


@pytest.fixture
def fake_document(db_session, registered_user):
    """
    Inserts a document row directly into the test DB.
    Skips the upload endpoint — no R2, no PDF parsing.
    """
    from backend.app.db.base import Documents, Users

    # Look up the actual user_id from the test database
    # Email must match what's in user_data fixture
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

