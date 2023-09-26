import asyncio
import logging
from datetime import datetime
from typing import Any

import fastapi
import httpx
from bidict import bidict

from activitypub_mincore.actor import get_local_actor, get_remote_actor_inbox
from activitypub_mincore.support.validation import (
    MINCORE_ACTIVITY_TYPES,
    create_activity_validator,
    validate_activity,
)

logger = logging.getLogger("publisher")

app = fastapi.FastAPI()

_followers = bidict()

EXT_ACTIVITY_VALIDATOR = create_activity_validator(
    types=MINCORE_ACTIVITY_TYPES + ["Create"]
)


async def handle_follow(local_actor: dict[str, Any], activity: dict[str, Any]) -> None:
    async def send_follow_response(type_: str):
        response = await client.post(
            follower_inbox,
            json=validate_activity(
                {
                    # transient, so no id
                    "type": type_,
                    "actor": local_actor["id"],
                    "object": activity.get("id"),
                },
                EXT_ACTIVITY_VALIDATOR,
            ),
        )
        response.raise_for_status()

    follower_uri = activity.get("actor")
    if isinstance(follower_uri, str):
        async with httpx.AsyncClient() as client:
            follower_inbox = await get_remote_actor_inbox(follower_uri)
            if follower_inbox in _followers:
                await send_follow_response("Reject")
                logger.info(f"Rejected: already following {follower_uri}")
            else:
                await send_follow_response("Accept")
                logger.info(f"Accepted Follow from {follower_uri}")
            _followers[follower_inbox] = activity.get("id")
    else:
        logger.warn(f"Follower URI must be a string: {follower_uri}")


def handle_undo_follow(activity: dict[str, Any]) -> None:
    follow_activity_uri = activity.get("object")
    if isinstance(follow_activity_uri, str):
        follower_inbox = _followers.inverse.get(follow_activity_uri)
        if follower_inbox:
            del _followers[follower_inbox]
            logger.info(f"Follower inbox removed: {follower_inbox}")
        else:
            logger.warn(f"Uknown follow activity: {follow_activity_uri}")
    else:
        logger.warn(f"Follow activity must be a string (URI): {activity}")


@app.post("/{path:path}")
async def post__inbox(request: fastapi.Request):
    instance_actor = get_local_actor()
    if str(request.url) != instance_actor["inbox"]:
        raise fastapi.HTTPException(403, "Forbidden")
    try:
        activity = await request.json()
        match activity.get("type"):
            case "Follow":
                await handle_follow(instance_actor, activity)
            case "Undo":
                handle_undo_follow(activity)
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
        activity = validate_activity(
            {
                # transient objects, no ids
                "type": "Create",
                "actor": get_local_actor()["id"],
                "object": {
                    "type": "Note",
                    "content": f"The time is {datetime.now().isoformat()}",
                    "to": inboxes,
                },
            },
            EXT_ACTIVITY_VALIDATOR,
        )
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
                _followers.pop(inbox_uri)


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
