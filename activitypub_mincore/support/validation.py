from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import referencing
import referencing.retrieval
from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator
from referencing.jsonschema import DRAFT202012

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"


@referencing.retrieval.to_cached_resource()
def schema_retriever(uri):
    url = urlparse(uri)
    filepath = SCHEMA_DIR / f"{url.path}-schema.json"
    with open(filepath) as fp:
        return fp.read()


MINCORE_REGISTRY = referencing.Registry(retrieve=schema_retriever)

MINCORE_ACTIVITY_TYPES = ["Follow", "Accept", "Reject"]


def create_activity_validator(
    *, root_schema: str = "schema:activity", types=None
) -> Validator:
    types = set(types or MINCORE_ACTIVITY_TYPES)
    return Draft202012Validator(
        schema_retriever(root_schema).contents,
        registry=MINCORE_REGISTRY.with_resource(
            uri="schema:known-activity-types",
            resource=referencing.Resource(
                contents={
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": "schema:known-activities",
                    "oneOf": [{"const": a} for a in types],
                },
                specification=DRAFT202012,
            ),
        ),
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


MINCORE_ACTIVITY_VALIDATOR = create_activity_validator()


def validate_activity(activity: dict[str, Any], validator: Validator) -> dict[str, Any]:
    """Validates an activity and returns it, if valid."""
    validator.validate(activity)
    return activity
