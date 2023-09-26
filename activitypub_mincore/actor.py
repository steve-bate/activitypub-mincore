from typing import Any

import httpx
import uvicorn
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator

from activitypub_mincore.support.validation import MINCORE_REGISTRY, schema_retriever

router = APIRouter()

_actor: dict = {}


@router.get("/{path:path}")
async def get__actor(request: Request):
    if str(request.url) == _actor["id"]:
        return JSONResponse(get_local_actor())
    raise HTTPException(404, "Not found")


def initialize_actor(server: uvicorn.Server):
    global _actor
    url_prefix = f"http://{server.config.host}:{server.config.port}"
    _actor = {
        "id": f"{url_prefix}/actor",
        "type": "Service",
        "inbox": f"{url_prefix}/inbox",
        "outbox": f"{url_prefix}/outbox",
    }
    server.config.app.include_router(router)


def get_local_actor() -> dict[str, Any]:
    return _actor


ACTOR_VALIDATOR = Draft202012Validator(
    schema_retriever("schema:actor").contents,
    registry=MINCORE_REGISTRY,
    format_checker=Draft202012Validator.FORMAT_CHECKER,
)


async def get_remote_actor(actor_uri: str):
    # NOTE No authn/authz
    async with httpx.AsyncClient() as client:
        response = await client.get(actor_uri)
        response.raise_for_status()
        # TODO Validate actor with JSON Schema
        actor = response.json()
        ACTOR_VALIDATOR.validate(actor)
        return actor


async def get_remote_actor_inbox(actor_uri: str):
    return (await get_remote_actor(actor_uri))["inbox"]
