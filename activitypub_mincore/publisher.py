import asyncio
import logging
from datetime import datetime
from typing import Any

import fastapi
import httpx
from bidict import bidict

from activitypub_mincore.actor import get_actor

logger = logging.getLogger("publisher")

app = fastapi.FastAPI()

_followers = bidict()


async def handle_follow(local_actor: dict[str, Any], payload: dict[str, Any]) -> None:
    async def send_response(type_: str):
        response = await client.post(
            follower_inbox,
            json={
                # transient, so no id
                "type": type_,
                "actor": local_actor["id"],
                "object": payload.get("id"),
            },
        )
        response.raise_for_status()

    follower_uri = payload.get("actor")
    if isinstance(follower_uri, str):
        async with httpx.AsyncClient() as client:
            follower_response = await client.get(follower_uri)
            follower_response.raise_for_status()
            follower = follower_response.json()
            follower_inbox = follower.get("inbox")
            if follower_inbox:
                if follower_inbox in _followers:
                    await send_response("Reject")
                    logger.info(
                        f"Rejected Follow from {follower_uri}, already following"
                    )
                else:
                    await send_response("Accept")
                    logger.info(f"Accepted Follow from {follower_uri}")
                _followers[follower_inbox] = payload.get("id")
            else:
                logger.warn(f"No inbox for actor: {follower_uri}")
    else:
        logger.warn(f"Follower URI must be a string: {follower_uri}")


def handle_undo_follow(payload: dict[str, Any]) -> None:
    follow_activity_uri = payload.get("object")
    if isinstance(follow_activity_uri, str):
        follower_inbox = _followers.inverse.get(follow_activity_uri)
        if follower_inbox:
            del _followers[follower_inbox]
            logger.info(f"Follower inbox removed: {follower_inbox}")
        else:
            logger.warn(f"Uknown follow activity: {follow_activity_uri}")
    else:
        logger.warn(f"Follow activity must be a string (URI): {payload}")


@app.post("/{path:path}")
async def post__inbox(request: fastapi.Request):
    instance_actor = get_actor()
    if str(request.url) != instance_actor["inbox"]:
        raise fastapi.HTTPException(403, "Forbidden")
    try:
        payload = await request.json()
        match payload.get("type"):
            case "Follow":
                await handle_follow(instance_actor, payload)
            case "Undo":
                handle_undo_follow(payload)
            case _:
                raise fastapi.HTTPException(400, "Bad request")
    except httpx.HTTPError as httpEx:
        raise httpEx
    except Exception as ex:  # noqa
        logger.exception(ex)
        raise fastapi.HTTPException(500, "Internal Server Error")


async def publish_once():
    if _followers:
        inboxes = list(_followers)  # copy, to allow mutation
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
                _followers.remove(inbox_uri)


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
