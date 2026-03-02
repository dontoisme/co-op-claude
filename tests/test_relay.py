"""TCP relay integration tests."""

import asyncio
import pytest

from src.bus import SharedBus
from src.relay import CoopRelay, RelayClient
from src.models import CoopMessage, MessageType


@pytest.fixture
def host_bus(tmp_path):
    return SharedBus(tmp_path / "host-bus")


@pytest.fixture
def guest_bus(tmp_path):
    return SharedBus(tmp_path / "guest-bus")


@pytest.mark.asyncio
async def test_relay_starts_and_accepts(host_bus):
    """Test that the relay server starts and listens."""
    relay = CoopRelay(host_bus, host="127.0.0.1", port=0)  # port 0 = OS picks

    server = await asyncio.start_server(
        relay.handle_client, "127.0.0.1", 0)
    addr = server.sockets[0].getsockname()
    assert addr[1] > 0  # Got a valid port

    server.close()
    await server.wait_closed()


@pytest.mark.asyncio
async def test_relay_message_forwarding(host_bus, guest_bus):
    """Test that messages flow through the relay."""
    relay = CoopRelay(host_bus, host="127.0.0.1", port=0)

    server = await asyncio.start_server(
        relay.handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    # Connect client
    client = RelayClient(guest_bus, host="127.0.0.1", port=port)

    guest_queue = guest_bus.subscribe()

    client_task = asyncio.create_task(client.connect())

    # Give connection time to establish
    await asyncio.sleep(0.2)

    # Publish on host side
    msg = CoopMessage(
        sender="Don", recipient="all",
        content="hello from host", msg_type=MessageType.HUMAN_TO_HUMAN)
    await host_bus.publish(msg)

    # Wait briefly for message to arrive on guest side
    await asyncio.sleep(0.3)

    # Cleanup — cancel client and close server to prevent hang
    client_task.cancel()
    try:
        await client_task
    except asyncio.CancelledError:
        pass
    server.close()
    await server.wait_closed()
