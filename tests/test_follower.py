import pytest
from fastapi.testclient import TestClient

from activitypub_mincore.follower import app as follower_app
from activitypub_mincore.follower import follow
from tests.support import MockServer


@pytest.fixture
def app():
    return follower_app


async def test_following(
    test_client: TestClient, mock_actor: dict, mock_server: MockServer
):
    await follow(mock_actor["id"])
    assert mock_server.received_post({"type": "Follow", "object": mock_actor["id"]})
    # simulate publication (smoke test)
    response = test_client.get(f"{test_client.base_url}/actor")
    assert response.is_success
    actor = response.json()
    inbox = actor["inbox"]
    response = test_client.post(
        inbox,
        json={
            "id": "http://server.test/create",
            "type": "Create",
            "actor": mock_actor["id"],
            "to": actor["id"],
            "object": {"type": "Note", "content": "Hello"},
        },
    )
    assert response.is_success
