from typing import Any

import uvicorn
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

_actor: dict = {}


@router.get("/{path:path}")
async def get__actor(request: Request):
    if str(request.url) == _actor["id"]:
        return JSONResponse(get_actor())
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


def get_actor() -> dict[str, Any]:
    return _actor
