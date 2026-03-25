"""
Test_messages.py - Files tests the messaging logic
    - Tests messages being sent into a conversation.
    - Tests messages being added properly into database
    - Tests messages being deleted upon conversation deletion from the database
    - Tsts authorised and unauthorised additions to messages.
    - Tests users' being not being allowed to send messages in others' conversations
    - Tests messages retrieval when needed.
"""
from backend.app.db.base import ConversationDocuments
from unittest.mock import patch


class TestAddMessages:
    def _create_fake_conversation(self, client, db_session, fake_document, auth_headers):
        """
        Create a fake conversation and associate it with the document
        """
        conversation = client.post("/conversations/", headers=auth_headers,)
        conv_id = conversation.json()["conversation_id"]

        doc_id = fake_document.get("document_id")

        db_session.add(ConversationDocuments(
            conversation_id = conv_id,
            document_id = doc_id,
        ))
        db_session.commit()
        return conv_id

    @patch("backend.app.rag.pipeline.generate_rag_response")
    def test_add_message(self, client, db_session,auth_headers, fake_document, mock_rag):
        """
        Create a fake message and agent response mimicking the actual rag response. This is to see if the messages are
        in the right way or not.
        """
        mock_rag.return_value = ("Transformers rely on attention mechanisms [1].",
                                 [{"Citation Number": 1, "Document":
                                     "Transformers Document", "Section": "Sub-section", "Page": 1, "DocumentID": 1}])

        convo_id = self._create_fake_conversation(client, fake_document)

        response = client.post(f"/conversations/{convo_id}/messages", json={
            "content": "How do transformers work",
            "role": "user",
        })
        data = response.json()

        assert response.status_code == 200
        assert "response_content" in data
        assert "sources_list" in data
        assert data["role"] == "assistant"
        assert "message_id" in data


    def test_no_document(self, client, db_session, auth_headers):
        """
        We will send a message to the conversation with no document and we need to see if the system is
        rejecting the message or not
        """
        conv_resp = client.post("/conversations/", headers=auth_headers)
        conv_id = conv_resp.json()["conversation_id"]

        response = client.post(f"/copnversations/{conv_id}/messages", json={
            "content": "How do transformers work"
        })
        data = response.json()
        assert response.status_code == 400
        assert "No documents associated with this conversation. Add documents before chatting." in data["detail"]

    def test_add_message_nonexistent_conversation(self, client, auth_headers):
        """
        Message to a conversation that doesn't exist or has not been created.
        """
        response = client.post(
            "/conversations/99999/messages",
            headers=auth_headers,
            json={
                "content": "Hello?",
                "role": "user"
            }
        )

        assert response.status_code == 404

    def test_add_message_unauthorized(self, client):
        """
        When a message is sent to a conversation without authorisation
        """
        response = client.post(
            "/conversations/1/messages",
            json={
                "content": "Sneaky",
                "role": "user",
            }
        )

        assert response.status_code == 401 or response.status_code == 403

    def test_add_message_to_other_user(self, client, db_session, auth_headers, fake_document, registered_user):
        conversation_id = self._create_fake_conversation( client, fake_document)

        client.post("/auth/create_user", json={
            "first_name": "Other",
            "last_name": "Person",
            "email": "other@example.com",
            "password": "OtherPassword123!"
        })
        login_resp = client.post("/auth/login", json={
            "email": "other@example.com",
            "password": "OtherPassword123!"
        })
        other_headers = {
            "Authorization": f"Bearer {login_resp.json()['access_token']}"
        }

        response = client.post(f"/conversations/{conversation_id}/messages}", headers=other_headers, json={
            "content":"How do transformers work",
            "role":"user",
        })

        assert response.status_code == 404

@patch("backend.app.rag.pipeline.generate_rag_response")
class TestListMessages:
    def TestListMessages(self, mock_rag, client, db_session, auth_headers, fake_document):
        """
        The messages in the conversation need to be returned properly
        """
        mock_rag.return_value = ("Transformers are the ones that always transform.", [{
            "Citation Number": 1, "Document":
            "doc_name","Section":"current_section", "Page": 1 ,"DocumentID":1
        }])

        conversation_id = conv_resp = client.post("/conversations/", headers=auth_headers)
        conv_id = conv_resp.json()["conversation_id"]
        client.post(
            f"/conversations/{conv_id}/documents",
            headers=auth_headers,
            json={"documents_to_update": [fake_document.document_id]}
        )

        client.post(
            f"/conversations/{conv_id}/messages",
            headers=auth_headers,
            json={
                "content": "What is this paper about?",
                "role": "user",
            }
        )

        response = client.get(
            f"/conversations/{conv_id}/messages",
            headers=auth_headers
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 2
        roles = set()
        for m in data:
            roles.add(m["role"])
        assert "user" in roles
        assert "assistant" in roles


    def test_list_messages_empty(self, client, auth_headers, created_conversation):
        """Conversation with no messages → empty list."""
        conv_id = created_conversation["conversation_id"]

        response = client.get(
            f"/conversations/{conv_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []






