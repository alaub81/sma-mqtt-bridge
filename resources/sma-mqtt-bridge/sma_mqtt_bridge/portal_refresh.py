"""Wake the existing portal supervisor without enabling preference writes."""

import asyncio


class PortalRefresh:
    def __init__(self, state):
        self.state = state
        self.event = asyncio.Event()
        self.reading = False
        self.blocked = False

    def result(self, status):
        self.state.update({"portal/refresh": status})

    async def handle(self, key, data, retained=False):
        if retained:
            self.result("rejected-retained")
        elif key != "refresh" or data != b"refresh":
            self.result("rejected")
        elif self.blocked:
            self.result("auth-blocked")
        elif self.reading:
            self.result("reading")
        else:
            self.result("queued")
            self.event.set()

    def begin(self):
        self.event.clear()
        self.reading = True
        self.result("reading")

    def finish(self, status):
        self.reading = False
        self.result(status)

    async def wait(self, stop, seconds=None):
        tasks = [asyncio.create_task(stop.wait()), asyncio.create_task(self.event.wait())]
        try:
            await asyncio.wait(tasks, timeout=seconds, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def close(self):
        pass
