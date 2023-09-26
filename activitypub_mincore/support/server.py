import asyncio
import logging
import sys
from typing import Awaitable

import uvicorn

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


class Server(uvicorn.Server):
    def __init__(
        self, config: uvicorn.Config, background_tasks: list[Awaitable] | None = None
    ):
        logging.getLogger("uvicorn.error").name = "uvicorn"
        super().__init__(config)
        self.background_tasks = background_tasks or []
        self.tasks: list[asyncio.Task] = []

    def handle_exit(self, sig: int, frame) -> None:
        if self.tasks:
            for task in self.tasks:
                if task != self.server_task:
                    task.cancel()
        return super().handle_exit(sig, frame)

    async def run(self):
        self.server_task = asyncio.create_task(self.serve())
        self.tasks = [self.server_task] + [
            asyncio.create_task(t) for t in self.background_tasks
        ]
        await asyncio.wait(self.tasks)
