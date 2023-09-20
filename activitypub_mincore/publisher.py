import asyncio
import logging
from datetime import datetime

import fastapi
import httpx

from activitypub_mincore.actor import get_actor

logger = logging.getLogger("publisher")

app = fastapi.FastAPI()

_follower_inboxes = set()


@app.post("/{path:path}")
async def post__inbox(request: fastapi.Request):
    instance_actor = get_actor()
    if str(request.url) != instance_actor["inbox"]:
        raise fastapi.HTTPException(403, "Forbidden")
    try:
        payload = await request.json()
        match payload.get("type"):
            case "Follow":
                follower_uri = payload.get("actor")
                if isinstance(follower_uri, str):
                    async with httpx.AsyncClient() as client:
                        follower_response = await client.get(follower_uri)
                        follower_response.raise_for_status()
                        follower = follower_response.json()
                        follower_inbox = follower.get("inbox")
                        if follower_inbox:
                            accept_response = await client.post(
                                follower_inbox,
                                json={
                                    # transient, so no id
                                    "type": "Accept",
                                    "actor": instance_actor["id"],
                                    "object": payload.get("id"),
                                },
                            )
                            accept_response.raise_for_status()
                            logger.info(f"Accepted Follow from {follower_uri}")
                    _follower_inboxes.add(follower_inbox)
            case _:
                raise fastapi.HTTPException(400, "Bad request")
    except httpx.HTTPError as httpEx:
        raise httpEx
    except Exception as ex:  # noqa
        logger.exception(ex)
        raise fastapi.HTTPException(500, "Internal Server Error")


async def publish_once():
    if _follower_inboxes:
        inboxes = list(_follower_inboxes)
        logger.info(f"publishing to {inboxes}")
        activity = {
            # transient objects, no ids
            "type": "Create",
            "actor": get_actor()["id"],
            "object": {
                "type": "Note",
                "content": f"The time is {datetime.now().isoformat()}",
                "to": inboxes,
            },
        }
        for inbox_uri in inboxes:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(inbox_uri, json=activity)
                    response.raise_for_status()
            except Exception as ex:
                # Remove follower if there is an error
                if not isinstance(ex, httpx.ConnectError):
                    logger.exception(ex)
                else:
                    logger.error(ex)
                logger.warning(f"Removing {inbox_uri} from followers")
                _follower_inboxes.remove(inbox_uri)


async def publish():
    try:
        while True:
            await publish_once()
            await asyncio.sleep(5)
    except OSError as ex:
        logging.warning(ex)
    except Exception as ex:
        logging.exception(ex)
    finally:
        logger.warning("publish task exiting")
