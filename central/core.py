"""Core orchestration logic for CENTRAL."""

from __future__ import annotations

import asyncio
import datetime as dt
import secrets
from typing import Dict, Iterable, Optional

from .channel import OutboundChannel
from .constants import CPStatus, HealthStatus, SessionState
from .datamodel import ChargingPoint, SupplySession
from .database import CentralDatabase


class CentralCore:
    """Central business logic, independent of transport details."""

    def __init__(
        self,
        database: CentralDatabase,
        *,
        price_per_kwh: float = 0.25,
    ) -> None:
        self._db = database
        self._price_per_kwh = price_per_kwh
        self._lock = asyncio.Lock()

        self._cps: Dict[str, ChargingPoint] = {}
        self._cp_channels: Dict[str, OutboundChannel] = {}
        self._driver_channels: Dict[str, OutboundChannel] = {}
        self._sessions: Dict[str, SupplySession] = {}

        for cp in database.load_charging_points():
            self._cps[cp.cp_id] = cp

    # ------------------------------------------------------------------
    # Read model helpers
    def charging_points(self) -> Iterable[ChargingPoint]:
        return list(self._cps.values())

    def sessions(self) -> Iterable[SupplySession]:
        return list(self._sessions.values())

    # ------------------------------------------------------------------
    async def register_cp(self, cp_id: str, location: str) -> ChargingPoint:
        """Create the charging point if it does not exist."""

        async with self._lock:
            cp = self._cps.get(cp_id)
            if cp is None:
                cp = ChargingPoint(cp_id=cp_id, location=location)
                self._cps[cp_id] = cp
                self._persist()
            else:
                if location and location != cp.location:
                    cp.location = location
                    self._persist()
            return cp

    async def attach_cp_channel(self, cp_id: str, channel: OutboundChannel) -> ChargingPoint:
        async with self._lock:
            cp = self._cps.setdefault(cp_id, ChargingPoint(cp_id=cp_id, location=""))
            cp.status = CPStatus.AVAILABLE if cp.health == HealthStatus.OK else CPStatus.FAULT
            cp.last_seen = dt.datetime.utcnow()
            self._cp_channels[cp_id] = channel
        await self._broadcast_cp_state(cp)
        return cp

    async def detach_cp(self, cp_id: str) -> None:
        async with self._lock:
            cp = self._cps.get(cp_id)
            if not cp:
                return
            self._cp_channels.pop(cp_id, None)
            cp.status = CPStatus.DISCONNECTED
            cp.current_session_id = None
            cp.last_seen = dt.datetime.utcnow()
        await self._broadcast_cp_state(cp)

    async def attach_driver_channel(self, driver_id: str, channel: OutboundChannel) -> None:
        async with self._lock:
            self._driver_channels[driver_id] = channel
        await self._send_driver_snapshot(driver_id)

    async def detach_driver(self, driver_id: str) -> None:
        async with self._lock:
            self._driver_channels.pop(driver_id, None)

    async def update_health(self, cp_id: str, status: HealthStatus, message: Optional[str]) -> None:
        async with self._lock:
            cp = self._cps.get(cp_id)
            if not cp:
                return
            cp.health = status
            cp.last_seen = dt.datetime.utcnow()
            if status == HealthStatus.FAULT:
                cp.status = CPStatus.FAULT
            elif cp.status == CPStatus.FAULT:
                cp.status = CPStatus.AVAILABLE
        await self._broadcast_cp_state(cp, extra={"health_message": message})
        if status == HealthStatus.FAULT and cp.current_session_id:
            await self._abort_session(cp.current_session_id, reason=message or "Avería en el punto")

    async def request_supply(
        self,
        *,
        driver_id: str,
        cp_id: str,
        requested_kwh: Optional[float],
    ) -> None:
        async with self._lock:
            driver_channel = self._driver_channels.get(driver_id)
            if driver_channel is None:
                raise RuntimeError(f"driver {driver_id} no conectado")

            cp = self._cps.get(cp_id)
            if cp is None:
                await driver_channel.send(
                    {
                        "type": "supply_status",
                        "state": SessionState.DENIED.value,
                        "message": f"El punto {cp_id} no existe",
                    }
                )
                return
            cp.last_seen = dt.datetime.utcnow()

            if cp.status not in {CPStatus.AVAILABLE}:
                await driver_channel.send(
                    {
                        "type": "supply_status",
                        "state": SessionState.DENIED.value,
                        "message": f"El punto {cp_id} no está disponible ({cp.status.value})",
                    }
                )
                return

            cp_channel = self._cp_channels.get(cp_id)
            if cp_channel is None:
                cp.status = CPStatus.DISCONNECTED
                await driver_channel.send(
                    {
                        "type": "supply_status",
                        "state": SessionState.DENIED.value,
                        "message": f"El punto {cp_id} no está conectado a CENTRAL",
                    }
                )
                await self._broadcast_cp_state(cp)
                return

            session_id = secrets.token_urlsafe(8)
            session = SupplySession(
                session_id=session_id,
                cp_id=cp_id,
                driver_id=driver_id,
                requested_kwh=requested_kwh,
            )
            cp.status = CPStatus.PENDING_AUTH
            cp.current_session_id = session_id
            self._sessions[session_id] = session

        await driver_channel.send(
            {
                "type": "supply_status",
                "session": session.to_public_dict(),
                "state": SessionState.PENDING.value,
                "message": "Solicitud enviada a CENTRAL",
            }
        )
        await cp_channel.send(
            {
                "type": "authorize_supply",
                "session_id": session.session_id,
                "driver_id": driver_id,
                "requested_kwh": requested_kwh,
            }
        )
        await self._broadcast_cp_state(cp)

    async def cp_authorization_response(
        self,
        *,
        session_id: str,
        accepted: bool,
        reason: Optional[str] = None,
    ) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return
            cp = self._cps.get(session.cp_id)
            driver_channel = self._driver_channels.get(session.driver_id)
            if not cp or not driver_channel:
                return

            if not accepted:
                session.state = SessionState.DENIED
                session.reason = reason or "Denegado por el punto"
                cp.status = CPStatus.AVAILABLE
                cp.current_session_id = None
                await driver_channel.send(
                    {
                        "type": "supply_status",
                        "session": session.to_public_dict(),
                        "state": session.state.value,
                        "message": session.reason,
                    }
                )
                await self._broadcast_cp_state(cp)
                self._sessions.pop(session_id, None)
                return

            session.state = SessionState.AUTHORIZED
            session.reason = "Autorizado"
            session.started_at = dt.datetime.utcnow()
            cp.status = CPStatus.SUPPLYING
        await driver_channel.send(
            {
                "type": "supply_status",
                "session": session.to_public_dict(),
                "state": SessionState.AUTHORIZED.value,
                "message": "Conecta el vehículo al punto",
            }
        )
        await self._broadcast_cp_state(cp)

    async def supply_started(self, session_id: str) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return
            session.state = SessionState.IN_PROGRESS
            session.started_at = session.started_at or dt.datetime.utcnow()
            cp = self._cps.get(session.cp_id)
            driver_channel = self._driver_channels.get(session.driver_id)
        if driver_channel and session:
            await driver_channel.send(
                {
                    "type": "supply_status",
                    "session": session.to_public_dict(),
                    "state": SessionState.IN_PROGRESS.value,
                    "message": "Suministro en curso",
                }
            )
        if cp:
            await self._broadcast_cp_state(cp)

    async def supply_progress(
        self,
        *,
        session_id: str,
        energy: float,
        amount: Optional[float],
    ) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return
            session.energy_delivered = energy
            session.amount_due = amount if amount is not None else energy * self._price_per_kwh
            cp = self._cps.get(session.cp_id)
            driver_channel = self._driver_channels.get(session.driver_id)
        if driver_channel:
            await driver_channel.send(
                {
                    "type": "supply_update",
                    "session": session.to_public_dict(),
                }
            )
        if cp:
            await self._broadcast_cp_state(cp)

    async def finalize_session(
        self,
        *,
        session_id: str,
        success: bool,
        message: Optional[str],
    ) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return
            cp = self._cps.get(session.cp_id)
            driver_channel = self._driver_channels.get(session.driver_id)
            session.finished_at = dt.datetime.utcnow()
            session.state = SessionState.FINISHED if success else SessionState.ABORTED
            session.reason = message
            if cp:
                cp.current_session_id = None
                cp.status = CPStatus.AVAILABLE if cp.health == HealthStatus.OK else CPStatus.FAULT
            self._sessions.pop(session_id, None)

        if driver_channel:
            await driver_channel.send(
                {
                    "type": "supply_status",
                    "session": session.to_public_dict(),
                    "state": session.state.value,
                    "message": message,
                }
            )
        if cp:
            await self._broadcast_cp_state(cp)

    async def remote_command(self, command: str, cp_id: Optional[str] = None) -> None:
        targets: Dict[str, OutboundChannel]
        async with self._lock:
            if cp_id is None:
                targets = dict(self._cp_channels)
            else:
                channel = self._cp_channels.get(cp_id)
                if channel is None:
                    return
                targets = {cp_id: channel}
        coros = [channel.send({"type": "remote_command", "command": command}) for channel in targets.values()]
        if coros:
            await asyncio.gather(*coros)

    async def _abort_session(self, session_id: str, *, reason: str) -> None:
        await self.finalize_session(session_id=session_id, success=False, message=reason)

    async def _broadcast_cp_state(self, cp: ChargingPoint, extra: Optional[dict] = None) -> None:
        async with self._lock:
            payload = {
                "type": "cp_state",
                "cp": {
                    "cp_id": cp.cp_id,
                    "location": cp.location,
                    "status": cp.status.value,
                    "health": cp.health.value,
                    "current_session_id": cp.current_session_id,
                },
            }
            if extra:
                payload.update(extra)
            targets = list(self._driver_channels.values())
        if targets:
            await asyncio.gather(*(channel.send(payload) for channel in targets))

    async def _send_driver_snapshot(self, driver_id: str) -> None:
        async with self._lock:
            channel = self._driver_channels.get(driver_id)
            if channel is None:
                return
            cps = [
                {
                    "cp_id": cp.cp_id,
                    "location": cp.location,
                    "status": cp.status.value,
                    "health": cp.health.value,
                    "current_session_id": cp.current_session_id,
                }
                for cp in self._cps.values()
            ]
        await channel.send({"type": "snapshot", "charging_points": cps})

    def _persist(self) -> None:
        self._db.save_charging_points(self._cps.values())
