import pytest
from fastapi.testclient import TestClient

from activitypub_mincore import actor
from tests.support import MockServer


@pytest.fixture
def mock_server(test_client, monkeypatch, mock_actor):
    server = MockServer(test_client, monkeypatch)
    server.add_response(mock_actor["id"], mock_actor)
    return server


@pytest.fixture
def mock_actor():
    mock_actor_uri = "http://server.test/actor"
    profile = {
        "id": mock_actor_uri,
        "type": "Service",
        "inbox": f"{mock_actor_uri}/inbox",
        "outbox": f"{mock_actor_uri}/outbox",
    }
    return profile


@pytest.fixture
def test_client(app):
    app.include_router(actor.router)
    with TestClient(app) as client:
        # actor under test
        actor_uri = f"{client.base_url}/actor"
        actor._actor = {
            "id": actor_uri,
            "type": "Service",
            "inbox": f"{actor_uri}/inbox",
            "outbox": f"{actor_uri}/outbox",
        }
        yield client
