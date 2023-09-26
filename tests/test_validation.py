from pathlib import Path

import pytest
from jsonschema import ValidationError

from activitypub_mincore.support.validation import MINCORE_ACTIVITY_VALIDATOR

SCHEMA_DIR = Path(__file__).parent.parent / "activitypub_mincore" / "schemas"


VALIDATION_TEST_CASES = [
    # Wrong type type
    ({"type": 123}, "fail"),
    # Wrong type type
    ({"type": ["Follow"]}, "fail"),
    # Invalid type
    ({"type": "Bogus"}, "fail"),
    # No object
    ({"type": "Follow"}, "fail"),
    # Accepts objects for "object"
    ({"type": "Follow", "object": {"id": "http://server.test"}}, "pass"),
    # Invalid URI
    ({"type": "Follow", "object": "@foo@bar.test"}, "fail"),
    # Valid URI
    ({"type": "Follow", "object": "https://server.test/"}, "pass"),
    ({"type": "Accept", "object": "https://server.test/"}, "pass"),
    ({"type": "Reject", "object": "https://server.test/"}, "pass"),
    # Extra properties
    ({"type": "Follow", "object": "https://server.test/", "EXTRA": "extra"}, "pass"),
    # Mispelled "actor"... passes as extra property
    (
        {"type": "Follow", "object": "https://server.test/", "acter": "Mel Brooks"},
        "pass",
    ),
]


@pytest.mark.parametrize(["activity", "outcome"], VALIDATION_TEST_CASES)
def test_activity_validation(activity: dict, outcome: str):
    try:
        MINCORE_ACTIVITY_VALIDATOR.validate(activity)
        assert outcome == "pass", lambda: f"Unexpected pass: {activity}"
    except ValidationError as ex:
        assert outcome == "fail", ex.message
