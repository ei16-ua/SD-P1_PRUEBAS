"""Unit tests for the CENTRAL core logic."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from central.channel import MemoryChannel
from central.constants import CPStatus, SessionState
from central.core import CentralCore
from central.database import CentralDatabase


@pytest.fixture()
def core(tmp_path: Path) -> CentralCore:
    db = CentralDatabase(tmp_path / "db.json")
    return CentralCore(db)


@pytest.mark.asyncio()
async def test_register_and_attach_cp(core: CentralCore) -> None:
    cp = await core.register_cp("CP-01", "Campus Norte")
    assert cp.location == "Campus Norte"
    channel = MemoryChannel()
    await core.attach_cp_channel("CP-01", channel)
    assert next(iter(core.charging_points())).status == CPStatus.AVAILABLE
    await core.detach_cp("CP-01")
    assert next(iter(core.charging_points())).status == CPStatus.DISCONNECTED


@pytest.mark.asyncio()
async def test_request_supply_happy_path(core: CentralCore) -> None:
    await core.register_cp("CP-02", "Campus Sur")
    cp_channel = MemoryChannel()
    driver_channel = MemoryChannel()
    await core.attach_cp_channel("CP-02", cp_channel)
    await core.attach_driver_channel("DRV-1", driver_channel)

    await core.request_supply(driver_id="DRV-1", cp_id="CP-02", requested_kwh=15)

    assert cp_channel.messages[-1]["type"] == "authorize_supply"
    session_id = cp_channel.messages[-1]["session_id"]

    await core.cp_authorization_response(session_id=session_id, accepted=True)
    await core.supply_started(session_id)
    await core.supply_progress(session_id=session_id, energy=4.2, amount=None)
    await core.finalize_session(session_id=session_id, success=True, message="Completado")

    supply_messages = [m for m in driver_channel.messages if m.get("type").startswith("supply")]
    assert supply_messages[0]["state"] == SessionState.PENDING.value
    assert supply_messages[-1]["state"] == SessionState.FINISHED.value


@pytest.mark.asyncio()
async def test_request_supply_denied_when_cp_unavailable(core: CentralCore) -> None:
    await core.register_cp("CP-03", "Campus Oeste")
    driver_channel = MemoryChannel()
    await core.attach_driver_channel("DRV-2", driver_channel)

    await core.request_supply(driver_id="DRV-2", cp_id="CP-03", requested_kwh=None)
    assert driver_channel.messages[-1]["state"] == SessionState.DENIED.value
