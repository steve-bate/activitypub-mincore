import asyncio

import click
import uvicorn

from activitypub_mincore import follower, publisher
from activitypub_mincore.actor import initialize_actor
from activitypub_mincore.support.server import Server


@click.group
def cli():
    """ActivityPub Minimal Core"""


@cli.command("publisher")
@click.option("--port", help="server port", default=8000)
def publisher_instance(port: int):
    """Publish-only, single-actor instance"""
    config = uvicorn.Config(app=publisher.app, port=port, log_config=None)
    server = Server(config, [publisher.publish()])
    initialize_actor(server)
    asyncio.run(server.run())


@cli.command("follower")
@click.argument("tofollow", nargs=-1, metavar="ACTOR_URIS...")
@click.option("--port", metavar="PORT", type=int, help="server port", default=8001)
def follower_instance(tofollow: list[str], port: int):
    """Follow-only, single actor instance"""
    if not tofollow:
        tofollow = ["http://127.0.0.1:8000/actor"]
    config = uvicorn.Config(app=follower.app, port=port, log_config=None)
    server = Server(config, [follower.send_follow(uri) for uri in tofollow])
    initialize_actor(server)
    asyncio.run(server.run())


#
