import pytest
from fastapi.testclient import TestClient

from activitypub_mincore.publisher import app as publisher_app
from activitypub_mincore.publisher import publish_once
from tests.support import MockServer


@pytest.fixture
def app():
    return publisher_app


async def test_follow_handling(
    test_client: TestClient, mock_actor: dict, mock_server: MockServer
):
    response = test_client.get(f"{test_client.base_url}/actor")
    assert response.is_success
    # post Follow request
    actor = response.json()
    inbox = actor["inbox"]
    follow_activity_uri = "http://server.test/follow"
    response = test_client.post(
        inbox,
        json={
            "id": follow_activity_uri,
            "type": "Follow",
            "actor": mock_actor["id"],
            "object": actor["id"],
        },
    )
    assert response.is_success
    assert mock_server.received_post({"type": "Accept"}), "No accept"
    # publish
    await publish_once()
    assert mock_server.received_post({"type": "Create"}), "No Create"
    # TODO # unfollow
    # mock_server.requests.clear()
    # response = test_client.post(
    #     inbox,
    #     json={
    #         "id": "http://server.test/unfollow",
    #         "type": "Undo",
    #         "actor": mock_actor["id"],
    #         "object": follow_activity_uri,
    #     },
    # )
    # assert response.is_success
    # # publish again, should not receive this one
    # await publish_once()
    # assert mock_server.received_post({"type": "Create"}) is None, "Unexpected Create"
