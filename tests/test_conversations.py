"""
test_conversations.py — Tests for conversation and document association.

This file tests:
- Creating conversations
- Listing conversations
- Deleting conversations
- Adding/removing documents to/from conversations
"""

class TestConversationsCRUD:

    def test_create_conversations(self, client, auth_headers):
        """Creates a conversation and checks the endpoint works."""
        res = client.post("/api/v1/conversations/", headers=auth_headers)
        assert res.status_code == 201

        data = res.json()
        assert "conversation_id" in data
        assert "created_at" in data

    def test_create_conversation_unauthorized(self, client):
        """Can't create a conversation without being logged in."""
        response = client.post("/api/v1/conversations/")
        assert response.status_code == 401

    def test_list_conversations(self, client, auth_headers):
        """After creating 2 conversations, listing should return exactly 2."""
        client.post("/api/v1/conversations/", headers=auth_headers)
        client.post("/api/v1/conversations/", headers=auth_headers)

        res = client.get("/api/v1/conversations/", headers=auth_headers)
        assert res.status_code == 200

        data = res.json()
        assert len(data) == 2

    def test_list_conversations_empty(self, client, auth_headers):
        """A new user with no conversations should get an empty list."""
        response = client.get("/api/v1/conversations/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_single_conversation(self, client, auth_headers, created_conversation):
        """Fetching a specific conversation by ID should return its data."""
        conv_id = created_conversation["conversation_id"]

        res = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)

        assert res.status_code == 200
        data = res.json()
        assert data["conversation_id"] == conv_id

    def test_delete_conversation(self, client, auth_headers, created_conversation):
        """
        Delete a conversation and verify it's gone.

        NOTE: Your route decorator has a typo — {comnversation_id}.
        Fix it to {conversation_id} in conversation_logic.py first.
        """
        conv_id = created_conversation["conversation_id"]

        res = client.delete(
            f"/api/v1/conversations/delete/{conv_id}",
            headers=auth_headers
        )
        assert res.status_code == 200

        # Listing should now be empty
        list_response = client.get("/api/v1/conversations/", headers=auth_headers)
        assert len(list_response.json()) == 0

    def test_delete_other_users_conversation(self, client, auth_headers, created_conversation):
        """User B should not be able to delete User A's conversation."""
        conv_id = created_conversation["conversation_id"]

        # Create User B and log in
        client.post("/api/v1/auth/create_user", params={
            "first_name": "Other",
            "last_name": "Person",
            "email": "other@example.com",
            "password": "OtherPassword123!"
        })
        login_resp = client.post("api/v1/auth/login", params={
            "email": "other@example.com",
            "password": "OtherPassword123!"
        })

        print(login_resp)
        print(login_resp.json())

        other_headers = {
            "Authorization": f"Bearer {login_resp.json()["token"]}"
        }
        # User B tries to delete User A's conversation
        client.delete(
            f"/api/v1/conversations/delete/{conv_id}",
            headers=other_headers
        )

        # User A's conversation should still exist
        check = client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers
        )
        assert check.status_code == 200


class TestDocumentAssociation:

    def test_associate_document(self, client, auth_headers, created_conversation, fake_document):
        """Linking a document to a conversation should succeed."""
        conv_id = created_conversation["conversation_id"]

        response = client.post(
            f"/api/v1/conversations/{conv_id}/documents",
            headers=auth_headers,
            json={"documents_to_update": [fake_document.document_id]}
        )

        assert response.status_code == 200

    def test_get_conversation_documents(self, client, auth_headers, created_conversation, fake_document):
        """After associating a document, GET should return it."""
        conv_id = created_conversation["conversation_id"]

        # Associate
        client.post(
            f"/api/v1/conversations/{conv_id}/documents",
            headers=auth_headers,
            json={"documents_to_update": [fake_document.document_id]}
        )

        # Retrieve
        response = client.get(f"/api/v1/conversations/{conv_id}/documents")

        assert response.status_code == 200
        data = response.json()
        assert fake_document.document_id in data["documents_to_update"]

    def test_associate_duplicate_document(self, client, auth_headers, created_conversation, fake_document):
        """
        Adding the same document to a conversation twice should fail
        because of the (conversation_id, document_id) unique constraint.
        """
        conv_id = created_conversation["conversation_id"]

        # First time — should succeed
        client.post(
            f"/api/v1/conversations/{conv_id}/documents",
            headers=auth_headers,
            json={"documents_to_update": [fake_document.document_id]}
        )

        # Second time — duplicate → should fail
        response = client.post(
            f"/api/v1/conversations/{conv_id}/documents",
            headers=auth_headers,
            json={"documents_to_update": [fake_document.document_id]}
        )

        assert response.status_code == 409

    def test_associate_nonexistent_document(self, client, auth_headers, created_conversation):
        """Associating a document_id that doesn't exist should fail."""
        conv_id = created_conversation["conversation_id"]

        response = client.post(
            f"/api/v1/conversations/{conv_id}/documents",
            headers=auth_headers,
            json={"documents_to_update": [99999]}
        )
        data = response.json()
        print(data)
        # Foreign key constraint → IntegrityError → 409
        assert response.status_code in [400, 409, 404]

    def test_delete_document_from_conversation(self, client, auth_headers, created_conversation, fake_document):
        """Removing a document association should succeed."""
        conv_id = created_conversation["conversation_id"]

        # Associate first
        client.post(
            f"/api/v1/conversations/{conv_id}/documents",
            headers=auth_headers,
            json={"documents_to_update": [fake_document.document_id]}
        )

        # Delete the association
        response = client.delete(
            f"/api/v1/conversations/{conv_id}/documents/{fake_document.document_id}"
        )
        assert response.status_code == 200

        # Verify it's gone
        get_resp = client.get(f"/api/v1/conversations/{conv_id}/documents")
        data = get_resp.json()
        if get_resp.status_code == 200:
            if len(data["documents_to_update"]) > 0:
                assert fake_document.document_id not in data["documents_to_update"]
        else:
            assert get_resp.status_code == 404