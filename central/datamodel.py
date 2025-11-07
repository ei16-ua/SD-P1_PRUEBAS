"""Data model definitions for the CENTRAL module."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional

from .constants import CPStatus, HealthStatus, SessionState


@dataclass
class ChargingPoint:
    """Model a charging point registered in CENTRAL."""

    cp_id: str
    location: str
    status: CPStatus = CPStatus.DISCONNECTED
    health: HealthStatus = HealthStatus.OK
    current_session_id: Optional[str] = None
    last_seen: Optional[_dt.datetime] = None

    def to_storage(self) -> dict:
        """Serialize the charging point for persistence."""

        return {
            "cp_id": self.cp_id,
            "location": self.location,
        }


@dataclass
class SupplySession:
    """Represent a supply request being orchestrated by CENTRAL."""

    session_id: str
    cp_id: str
    driver_id: str
    requested_kwh: Optional[float]
    state: SessionState = SessionState.PENDING
    energy_delivered: float = 0.0
    amount_due: float = 0.0
    created_at: _dt.datetime = field(default_factory=_dt.datetime.utcnow)
    started_at: Optional[_dt.datetime] = None
    finished_at: Optional[_dt.datetime] = None
    reason: Optional[str] = None

    def to_public_dict(self) -> dict:
        """Return a sanitized representation for UI updates."""

        return {
            "session_id": self.session_id,
            "cp_id": self.cp_id,
            "driver_id": self.driver_id,
            "requested_kwh": self.requested_kwh,
            "state": self.state.value,
            "energy_delivered": self.energy_delivered,
            "amount_due": self.amount_due,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "reason": self.reason,
        }
