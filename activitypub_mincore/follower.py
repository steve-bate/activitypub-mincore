import asyncio
import logging
import uuid

import fastapi
import httpx

from activitypub_mincore.actor import get_local_actor, get_remote_actor_inbox
from activitypub_mincore.support.validation import (
    MINCORE_ACTIVITY_TYPES,
    create_activity_validator,
    validate_activity,
)

logger = logging.getLogger("follower")

app = fastapi.FastAPI()

EXT_ACTIVITY_VALIDATOR = create_activity_validator(
    types=MINCORE_ACTIVITY_TYPES + ["Create"]
)


@app.post("/{path:path}")
async def post__inbox(request: fastapi.Request):
    instance_actor = get_local_actor()
    if str(request.url) != instance_actor["inbox"]:
        raise fastapi.HTTPException(403, "Forbidden")
    try:
        activity = await request.json()
        logger.info(f"Received activity: {activity}")
    except httpx.HTTPError as httpEx:
        raise httpEx
    except Exception as ex:  # noqa
        logger.exception(ex)
        raise fastapi.HTTPException(500, "Internal Server Error")


async def follow(uri_to_follow: str, *, ntries: int = 1):
    while ntries:
        logger.info(f"Requesting to Follow {uri_to_follow}")
        try:
            remote_inbox = await get_remote_actor_inbox(uri_to_follow)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    remote_inbox,
                    # "Pre-flight" validation
                    json=validate_activity(
                        {
                            # Must have an id for the response
                            "id": f"{get_local_actor()['id']}/{uuid.uuid4()}",
                            "type": "Follow",
                            "actor": get_local_actor()["id"],
                            "object": uri_to_follow,
                        },
                        EXT_ACTIVITY_VALIDATOR,
                    ),
                )
                response.raise_for_status()
        except httpx.ConnectError:
            logging.warning("Connection failed, retrying...")
            ntries -= 1
            if ntries > 0:
                await asyncio.sleep(2)
                continue
        except Exception as ex:
            logger.exception(ex)
        break


async def send_follow(uri_to_follow: str, delay: int = 2):
    logger.info(f"Waiting to send follow for {uri_to_follow}")
    await asyncio.sleep(delay)
    logger.info(f"Sent Follow request for {uri_to_follow}")
    await follow(uri_to_follow, ntries=10000)
