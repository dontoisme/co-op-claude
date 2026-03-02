"""TCP relay server for remote co-op sessions.

The host runs the relay alongside their station. The guest connects
to it from their machine. Messages are bidirectionally forwarded
between the TCP connection and the local SharedBus.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from .models import CoopMessage
from .bus import SharedBus


class CoopRelay:
    """TCP relay bridging remote stations to the shared bus."""

    def __init__(self, bus: SharedBus, host: str = "0.0.0.0", port: int = 7723):
        self.bus = bus
        self.host = host
        self.port = port
        self._clients: list[asyncio.StreamWriter] = []

    async def handle_client(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        self._clients.append(writer)
        print(f"\033[0;90m[relay] Connection from {addr}\033[0m")

        queue = self.bus.subscribe()

        async def forward():
            try:
                while True:
                    msg = await queue.get()
                    writer.write((msg.to_json() + "\n").encode())
                    await writer.drain()
            except (ConnectionError, asyncio.CancelledError):
                pass

        async def receive():
            try:
                while True:
                    data = await reader.readline()
                    if not data:
                        break
                    try:
                        msg = CoopMessage.from_json(data.decode().strip())
                        await self.bus.publish(msg)
                    except (ValueError, KeyError):
                        pass
            except ConnectionError:
                pass

        fwd_task = asyncio.create_task(forward())
        recv_task = asyncio.create_task(receive())
        done, pending = await asyncio.wait(
            [fwd_task, recv_task], return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()

        self.bus.unsubscribe(queue)
        self._clients = [c for c in self._clients if c is not writer]
        writer.close()
        print(f"\033[0;90m[relay] Disconnected: {addr}\033[0m")

    async def start(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port)
        print(f"\033[0;90m[relay] Listening on {self.host}:{self.port}\033[0m")
        async with server:
            await server.serve_forever()


class RelayClient:
    """Connects a remote station's bus to the relay server."""

    def __init__(self, bus: SharedBus, host: str, port: int = 7723):
        self.bus = bus
        self.host = host
        self.port = port

    async def connect(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        queue = self.bus.subscribe()

        async def send_to_relay():
            try:
                while True:
                    msg = await queue.get()
                    writer.write((msg.to_json() + "\n").encode())
                    await writer.drain()
            except (ConnectionError, asyncio.CancelledError):
                pass

        async def receive_from_relay():
            try:
                while True:
                    data = await reader.readline()
                    if not data:
                        break
                    try:
                        msg = CoopMessage.from_json(data.decode().strip())
                        # Inject into local bus without re-publishing to file
                        for q in self.bus._subscribers:
                            if q is not queue:
                                try:
                                    q.put_nowait(msg)
                                except asyncio.QueueFull:
                                    pass
                    except (ValueError, KeyError):
                        pass
            except ConnectionError:
                pass

        await asyncio.gather(
            send_to_relay(), receive_from_relay(),
            return_exceptions=True)

        self.bus.unsubscribe(queue)
        writer.close()
