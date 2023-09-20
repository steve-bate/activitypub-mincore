import asyncio
import logging
import uuid

import fastapi
import httpx

from activitypub_mincore.actor import get_actor

logger = logging.getLogger("follower")

app = fastapi.FastAPI()


@app.post("/{path:path}")
async def post__inbox(request: fastapi.Request):
    instance_actor = get_actor()
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
            async with httpx.AsyncClient() as client:
                actor_response = await client.get(uri_to_follow)
                remote_actor = actor_response.json()
                remote_inbox = remote_actor.get("inbox")
                if remote_inbox:
                    response = await client.post(
                        remote_inbox,
                        json={
                            "id": f"{get_actor()['id']}/{uuid.uuid4()}",
                            "type": "Follow",
                            "actor": get_actor()["id"],
                            "object": uri_to_follow,
                        },
                    )
                    response.raise_for_status()
                else:
                    logger.error(f"No inbox: {remote_actor}")
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
