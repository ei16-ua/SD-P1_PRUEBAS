"""Abstractions over outbound communication channels."""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Dict


class OutboundChannel(ABC):
    """Something capable of sending JSON serialisable payloads."""

    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        raise NotImplementedError


class WriterChannel(OutboundChannel):
    """Wrap an :class:`asyncio.StreamWriter`."""

    def __init__(self, writer: asyncio.StreamWriter):
        self._writer = writer
        self._lock = asyncio.Lock()

    async def send(self, message: Dict[str, Any]) -> None:
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n"
        async with self._lock:
            self._writer.write(payload)
            await self._writer.drain()


class MemoryChannel(OutboundChannel):
    """Utility channel used in tests."""

    def __init__(self) -> None:
        self.messages = []
        self._lock = asyncio.Lock()

    async def send(self, message: Dict[str, Any]) -> None:
        async with self._lock:
            self.messages.append(message)

    def pop_all(self) -> list:
        msgs = list(self.messages)
        self.messages.clear()
        return msgs
