"""Station routing tests."""

import pytest
from src.models import Role, CoopMessage, MessageType
from src.bus import SharedBus
from src.station import Station


@pytest.fixture
def bus(tmp_path):
    return SharedBus(tmp_path / "test-bus")


def test_station_creation(bus):
    """Test station initializes correctly."""
    station = Station(
        human_name="Don",
        role=Role.ARCHITECT,
        partner_name="West",
        project_path="/tmp/test-project",
        bus=bus,
    )
    assert station.human_name == "Don"
    assert station.role == Role.ARCHITECT
    assert station.partner_name == "West"
    assert station.claude.claude_name == "Claude-Architect"
    assert station.is_running is False


def test_station_claude_bridge_config(bus):
    """Test that station configures its Claude bridge correctly."""
    station = Station(
        human_name="West",
        role=Role.UX,
        partner_name="Don",
        project_path="/tmp/test-project",
        bus=bus,
    )
    assert station.claude.role == Role.UX
    assert station.claude.human_name == "West"
    assert station.claude.partner_name == "Don"
    assert station.claude.claude_name == "Claude-Ux"
