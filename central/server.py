"""AsyncIO TCP server that exposes the CENTRAL core."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .channel import WriterChannel
from .constants import HealthStatus
from .core import CentralCore
from .database import CentralDatabase


class CentralServer:
    """Combine networking, storage and UI for the practice."""

    def __init__(
        self,
        *,
        cp_host: str = "0.0.0.0",
        cp_port: int = 9000,
        driver_host: str = "0.0.0.0",
        driver_port: int = 9001,
        storage_path: Optional[Path] = None,
    ) -> None:
        if storage_path is None:
            storage_path = Path("data/central_db.json")
        self._storage_path = Path(storage_path)
        self._core = CentralCore(CentralDatabase(self._storage_path))
        self._cp_host = cp_host
        self._cp_port = cp_port
        self._driver_host = driver_host
        self._driver_port = driver_port

        self._cp_server: Optional[asyncio.base_events.Server] = None
        self._driver_server: Optional[asyncio.base_events.Server] = None
        self._printer_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    async def start(self) -> None:
        self._cp_server = await asyncio.start_server(self._handle_cp_connection, self._cp_host, self._cp_port)
        self._driver_server = await asyncio.start_server(
            self._handle_driver_connection, self._driver_host, self._driver_port
        )
        await self._print_startup_banner()

    async def run_forever(self) -> None:
        if not self._cp_server or not self._driver_server:
            raise RuntimeError("El servidor no está inicializado, llama a start() primero")
        await asyncio.gather(
            self._cp_server.serve_forever(),
            self._driver_server.serve_forever(),
            self._cli_loop(),
        )

    async def close(self) -> None:
        if self._cp_server:
            self._cp_server.close()
            await self._cp_server.wait_closed()
        if self._driver_server:
            self._driver_server.close()
            await self._driver_server.wait_closed()

    # ------------------------------------------------------------------
    async def _handle_cp_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        address = writer.get_extra_info("peername")
        try:
            hello = await self._read_message(reader)
            if hello.get("role") != "cp":
                raise ValueError("La conexión no pertenece a un punto de recarga")
            cp_id = str(hello.get("cp_id"))
            location = str(hello.get("location", ""))
            await self._core.register_cp(cp_id, location)
            await self._core.attach_cp_channel(cp_id, WriterChannel(writer))
            await self._send(writer, {"type": "welcome", "cp_id": cp_id})
            await self._print(f"CP {cp_id} conectado desde {address}")
            while not reader.at_eof():
                message = await self._read_message(reader)
                await self._dispatch_cp_message(cp_id, message)
        except asyncio.IncompleteReadError:
            pass
        except Exception as exc:  # pragma: no cover - debug aid
            await self._print(f"Error en conexión CP {address}: {exc}")
        finally:
            await self._core.detach_cp(cp_id)
            writer.close()
            await writer.wait_closed()
            await self._print(f"CP {cp_id} desconectado")

    async def _dispatch_cp_message(self, cp_id: str, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")
        if msg_type == "authorization_response":
            await self._core.cp_authorization_response(
                session_id=message["session_id"],
                accepted=bool(message.get("accepted")),
                reason=message.get("reason"),
            )
        elif msg_type == "supply_started":
            await self._core.supply_started(message["session_id"])
        elif msg_type == "supply_update":
            await self._core.supply_progress(
                session_id=message["session_id"],
                energy=float(message.get("energy", 0.0)),
                amount=message.get("amount"),
            )
        elif msg_type == "supply_finished":
            await self._core.finalize_session(
                session_id=message["session_id"],
                success=bool(message.get("success", True)),
                message=message.get("message"),
            )
        elif msg_type == "health":
            status = HealthStatus(message.get("status", HealthStatus.OK.value))
            await self._core.update_health(cp_id, status, message.get("message"))
        else:
            await self._print(f"Mensaje desconocido de {cp_id}: {message}")

    async def _handle_driver_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        address = writer.get_extra_info("peername")
        driver_id: Optional[str] = None
        try:
            hello = await self._read_message(reader)
            if hello.get("role") != "driver":
                raise ValueError("La conexión no pertenece a un conductor")
            driver_id = str(hello.get("driver_id"))
            await self._core.attach_driver_channel(driver_id, WriterChannel(writer))
            await self._send(writer, {"type": "welcome", "driver_id": driver_id})
            await self._print(f"Driver {driver_id} conectado desde {address}")
            while not reader.at_eof():
                message = await self._read_message(reader)
                await self._dispatch_driver_message(driver_id, message)
        except asyncio.IncompleteReadError:
            pass
        except Exception as exc:  # pragma: no cover - debug aid
            await self._print(f"Error en conexión driver {address}: {exc}")
        finally:
            if driver_id:
                await self._core.detach_driver(driver_id)
            writer.close()
            await writer.wait_closed()
            await self._print(f"Driver {driver_id or 'desconocido'} desconectado")

    async def _dispatch_driver_message(self, driver_id: str, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")
        if msg_type == "request_supply":
            await self._core.request_supply(
                driver_id=driver_id,
                cp_id=str(message.get("cp_id")),
                requested_kwh=message.get("requested_kwh"),
            )
        elif msg_type == "remote_command":
            await self._core.remote_command(message.get("command"), message.get("cp_id"))
        elif msg_type == "list_cps":
            await self._core._send_driver_snapshot(driver_id)  # pylint: disable=protected-access
        else:
            await self._print(f"Mensaje desconocido de driver {driver_id}: {message}")

    # ------------------------------------------------------------------
    async def _cli_loop(self) -> None:
        while True:
            cmd = await asyncio.to_thread(input, "CENTRAL> ")
            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd in {"quit", "exit"}:
                await self._print("Saliendo...")
                await self.close()
                raise SystemExit(0)
            if cmd == "list":
                await self._print(self._render_cp_table())
                continue
            if cmd.startswith("stop "):
                _, _, cp_id = cmd.partition(" ")
                await self._core.remote_command("stop", cp_id.strip() or None)
                continue
            if cmd.startswith("resume "):
                _, _, cp_id = cmd.partition(" ")
                await self._core.remote_command("resume", cp_id.strip() or None)
                continue
            await self._print(f"Comando desconocido: {cmd}")

    def _render_cp_table(self) -> str:
        cps = sorted(self._core.charging_points(), key=lambda cp: cp.cp_id)
        if not cps:
            return "No hay puntos registrados"
        lines = ["ID        | Ubicación                 | Estado              | Salud"]
        lines.append("-" * len(lines[0]))
        for cp in cps:
            lines.append(
                f"{cp.cp_id:<9}| {cp.location:<24}| {cp.status.value:<19}| {cp.health.value}"
            )
        return "\n".join(lines)

    async def _print_startup_banner(self) -> None:
        lines = [
            "CENTRAL iniciado",
            f"Puerto CP: {self._cp_port}",
            f"Puerto conductores: {self._driver_port}",
            "Puntos conocidos:",
            self._render_cp_table(),
        ]
        await self._print("\n".join(lines))

    async def _print(self, message: str) -> None:
        async with self._printer_lock:
            print(message)

    async def _read_message(self, reader: asyncio.StreamReader) -> Dict[str, Any]:
        raw = await reader.readline()
        if not raw:
            raise asyncio.IncompleteReadError(partial=b"", expected=1)
        return json.loads(raw.decode("utf-8"))

    async def _send(self, writer: asyncio.StreamWriter, message: Dict[str, Any]) -> None:
        writer.write(json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n")
        await writer.drain()
