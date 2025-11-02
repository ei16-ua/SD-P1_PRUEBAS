#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONITOR (EV_CP_M)
- AUTH con CENTRAL: AUTH#<CP_ID> -> ACK/NACK
- Heartbeats a ENGINE: PING -> OK/KO
- Si KO/TIMEOUT/NACK => FAULT#<CP_ID>#<MOTIVO> a CENTRAL
"""

from __future__ import annotations
import argparse
import socket
import time
import sys
import os

# Add UTILS to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS.protocol import ProtocolMessage

try:
    from loguru import logger
except Exception:
    class _L:
        def info(self, *a, **k): print("[INFO]", *a)
        def warning(self, *a, **k): print("[WARN]", *a)
        def error(self, *a, **k): print("[ERROR]", *a)
        def debug(self, *a, **k): print("[DEBUG]", *a)
    logger = _L()


class EngineClient:
    def __init__(self, host: str, port: int, timeout: float = 1.5):
        self._addr = (host, port)
        self._timeout = timeout

    def ping(self) -> str:
        try:
            with socket.create_connection(self._addr, timeout=self._timeout) as s:
                s.sendall(b"PING\n")
                resp = s.recv(1024).decode().strip()
                return resp
        except Exception:
            return "TIMEOUT"


class CentralClient:
    def __init__(self, host: str, port: int, timeout: float = 2.0):
        self._addr = (host, port)
        self._timeout = timeout
        self._sock: socket.socket | None = None

    def connect(self):
        self._sock = socket.create_connection(self._addr, timeout=self._timeout)

    def send_line(self, line: str) -> str:
        if not self._sock:
            raise RuntimeError("CentralClient not connected")
        
        # Enviar mensaje con protocolo y esperar ACK
        success = ProtocolMessage.send_with_protocol(self._sock, line, wait_ack=True, timeout=5.0)
        if not success:
            raise RuntimeError("Failed to send message (no ACK)")
        
        # Recibir respuesta con protocolo y enviar ACK
        response, valid = ProtocolMessage.receive_with_protocol(self._sock, send_ack=True, timeout=5.0)
        if not valid or response is None:
            raise RuntimeError("Failed to receive valid response")
        
        return response.strip()
    
    def send_auth(self, cp_id: str) -> str:
        """Envía AUTH y espera ACK (el protocolo maneja automáticamente)"""
        if not self._sock:
            raise RuntimeError("CentralClient not connected")
        
        # Enviar AUTH con protocolo y esperar ACK crudo (0x06)
        success = ProtocolMessage.send_with_protocol(self._sock, f"AUTH#{cp_id}", wait_ack=True, timeout=5.0)
        if not success:
            raise RuntimeError("Failed to send AUTH (no ACK or NACK received)")
        
        return "ACK"
    
    def send_fault(self, cp_id: str, reason: str) -> str:
        """Envía FAULT y espera ACK (el protocolo maneja automáticamente)"""
        if not self._sock:
            raise RuntimeError("CentralClient not connected")
        
        # Enviar FAULT con protocolo y esperar ACK crudo (0x06)
        success = ProtocolMessage.send_with_protocol(self._sock, f"FAULT#{cp_id}#{reason}", wait_ack=True, timeout=5.0)
        if not success:
            raise RuntimeError("Failed to send FAULT (no ACK or NACK received)")
        
        return "ACK"

    def close(self):
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(prog="EV_CP_M")
    ap.add_argument("--cp-id", required=True)
    ap.add_argument("--engine-host", required=True)
    ap.add_argument("--engine-port", type=int, required=True)
    ap.add_argument("--central-host", required=True)
    ap.add_argument("--central-port", type=int, required=True)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--engine-timeout", type=float, default=1.5)
    ap.add_argument("--central-timeout", type=float, default=2.0)
    args = ap.parse_args()

    eng = EngineClient(args.engine_host, args.engine_port, timeout=args.engine_timeout if hasattr(args, 'engine-timeout') else args.engine_timeout)
    cen = CentralClient(args.central_host, args.central_port, timeout=args.central_timeout if hasattr(args, 'central-timeout') else args.central_timeout)

    try:
        cen.connect()
    except Exception as e:
        logger.error("No se pudo conectar a CENTRAL {}:{} -> {}", args.central_host, args.central_port, e)
        sys.exit(1)

    # Enviar AUTH usando método específico (solo espera ACK)
    try:
        auth_resp = cen.send_auth(args.cp_id)
        logger.info("Central AUTH response: {}", auth_resp)
    except Exception as e:
        logger.error("AUTH failed: {}", e)
        sys.exit(1)

    try:
        while True:
            status = eng.ping()
            logger.info("Heartbeat -> Engine: {}", status)

            if status != "OK":
                reason = "NO_RESPONSE" if status == "TIMEOUT" else status
                try:
                    r = cen.send_fault(args.cp_id, reason)
                    logger.warning("FAULT sent to CENTRAL: {} ({})", r, reason)
                except Exception as e:
                    logger.error("Failed to send FAULT: {}", e)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Stopping MONITOR…")
    finally:
        cen.close()

if __name__ == "__main__":
    main()