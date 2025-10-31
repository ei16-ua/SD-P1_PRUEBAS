"""Entry point to launch the CENTRAL server."""

from __future__ import annotations

import asyncio
import signal

from .server import CentralServer


async def amain() -> None:
    server = CentralServer()
    await server.start()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_sigint() -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_sigint)

    waiter = asyncio.create_task(server.run_forever())
    stopper = asyncio.create_task(stop_event.wait())
    done, pending = await asyncio.wait({waiter, stopper}, return_when=asyncio.FIRST_COMPLETED)
    if stopper in done:
        await server.close()
        waiter.cancel()
    await asyncio.gather(*pending, return_exceptions=True)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
