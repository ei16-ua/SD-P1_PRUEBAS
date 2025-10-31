"""Persistence utilities for CENTRAL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .datamodel import ChargingPoint


class CentralDatabase:
    """Tiny JSON backed storage for charging point metadata."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_charging_points(self) -> List[ChargingPoint]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

        cps = []
        for item in payload.get("charging_points", []):
            cps.append(ChargingPoint(cp_id=item["cp_id"], location=item.get("location", "")))
        return cps

    def save_charging_points(self, cps: Iterable[ChargingPoint]) -> None:
        payload = {"charging_points": [cp.to_storage() for cp in cps]}
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
