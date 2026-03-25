"""
test_auth.py — Tests for authentication endpoints.

HOW PYTEST DISCOVERS TESTS:
- File names must start with "test_" (test_auth.py ✓, auth_test.py ✗)
- Function names must start with "test_" (test_register_success ✓, register_test ✗)
- pytest finds them automatically — no need to register them anywhere.

HOW TO RUN:
    pytest tests/test_auth.py -v          # run just this file, verbose output
    pytest tests/test_auth.py::test_register_success  # run one specific test
    pytest tests/ -v                       # run ALL tests

WHAT -v DOES:
    Without -v:  "3 passed"
    With -v:     "test_auth.py::test_register_success PASSED"
                 "test_auth.py::test_register_duplicate_email PASSED"
    It shows you each test name and its result individually.

THE PATTERN:
    Every test follows the same structure — Arrange, Act, Assert (AAA):

    1. ARRANGE — set up the data/state you need
    2. ACT     — call the function or endpoint you're testing
    3. ASSERT  — check that the result matches your expectation
"""


##User Registration tests
def test_register_success(client, user_data):
    response = client.post("/auth/create_user", json=user_data)
    assert response.status_code == 201
    result = response.json()
    assert "message" in result


def test_duplicate_email(client, user_data):
    response = client.post("/auth/create_user", json=user_data)
    assert response.status_code == 201

    try_again = client.post("/auth/create_user", json=user_data)
    assert try_again.status_code == 400


def test_missing_email(client, user_data):
    user_data["email"] = ""
    response = client.post("/auth/create_user", json=user_data)
    assert response.status_code == 400


## User login tests
def test_check_password(client, registered_user):
    """
    Check with both right and wrong passwords
    """
    res = client.post("/auth/login", json={"email": registered_user["email"],
                                           "password": registered_user["password"]})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert len(data["token"]) > 0

    res = client.post("/auth/login", json={"email": registered_user["email"], "password": "Wrongbclwedb"})
    assert res.status_code == 401


def test_non_existent_user(client):
    res = client.post("/auth/login", json={
        "email": "noone@gmail.com",
        "password": "nonexistent"
    })
    assert res.status_code == 401
