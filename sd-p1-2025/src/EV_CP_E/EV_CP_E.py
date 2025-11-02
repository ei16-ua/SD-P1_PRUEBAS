#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENGINE (EV_CP_E)
- Socket de salud (Monitor hace PING -> OK/KO)
- Kafka:
    * Produce telemetría en topic_telemetry()
    * Consume comandos en topic_commands_for(CP_ID)
- Alterna OK/KO con Enter
"""

from __future__ import annotations
import argparse
import socket
import sys
import os
import threading
import time
import random
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

# Logs
try:
    from loguru import logger
except Exception:
    class _L:
        def info(self, *a, **k): print("[INFO]", *a)
        def warning(self, *a, **k): print("[WARN]", *a)
        def error(self, *a, **k): print("[ERROR]", *a)
        def debug(self, *a, **k): print("[DEBUG]", *a)
    logger = _L()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import kafka as bus

# ----- Estado CP -----
@dataclass
class CPState:
    cp_id: str
    ok: bool = True
    charging: bool = False
    driver_id: Optional[str] = None
    price_eur_kwh: float = 0.35
    kw_max: float = 11.0
    kw_current: float = 0.0
    euros_accum: float = 0.0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def toggle_ok(self):
        with self._lock:
            self.ok = not self.ok
            return self.ok

    def start_charge(self, driver_id: str):
        with self._lock:
            self.charging = True
            self.driver_id = driver_id
            self.kw_current = 0.0
            self.euros_accum = 0.0

    def stop_charge(self):
        with self._lock:
            self.charging = False
            self.driver_id = None
            self.kw_current = 0.0
            self.euros_accum = 0.0  # Resetear también los euros acumulados

    def tick_telemetry(self):
        with self._lock:
            if not self.charging:
                return None
            # kW simulado con variación ±5% respecto a kw_max
            variation = self.kw_max * 0.05
            self.kw_current = round(self.kw_max + random.uniform(-variation, variation), 2)
            self.euros_accum = round(self.euros_accum + (self.kw_current/3600.0)*self.price_eur_kwh, 4)
            return {
                "cp_id": self.cp_id,
                "driver_id": self.driver_id,
                "kw": self.kw_current,
                "eur": self.euros_accum,
                "ts": time.time(),
            }


# ----- Socket salud -----
class HealthServer:
    def __init__(self, host: str, port: int, state: CPState):
        self._addr = (host, port)
        self._state = state

    def start(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(self._addr)
        srv.listen(5)
        logger.info("Health server on {}:{}", *self._addr)

        def _accept_loop():
            while True:
                conn, addr = srv.accept()
                threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()

        threading.Thread(target=_accept_loop, daemon=True).start()

    def _handle(self, conn: socket.socket, addr):
        with conn:
            try:
                data = conn.recv(1024).decode().strip()
                if data == "PING":
                    conn.sendall(b"OK\n" if self._state.ok else b"KO\n")
                else:
                    conn.sendall(b"NACK\n")
            except Exception as e:
                logger.warning("HealthServer error with {}: {}", addr, e)


# ----- Engine main -----
def _on_command(state: CPState):
    def _handler(payload: dict, _raw_msg):
        if payload.get("cp_id") not in (None, state.cp_id, "all"):
            return  # ignora si no es para este CP (o si no es broadcast)
        op = payload.get("op")
        if op == "start_charge":
            state.start_charge(driver_id=payload.get("driver_id", "unknown"))
            logger.info("[CMD] start_charge({})", state.driver_id)
        elif op == "stop_charge":
            state.stop_charge()
            logger.info("[CMD] stop_charge")
        elif op == "toggle_ko":
            new_ok = state.toggle_ok()
            logger.warning("[CMD] toggle_ko -> ok={}", new_ok)
        else:
            logger.warning("[CMD] unknown op: {}", op)
    return _handler

def _keyboard_toggle(state: CPState):
    print("Pulsa Enter para alternar OK/KO… (Ctrl+C para salir)")
    try:
        for _ in sys.stdin:
            new_ok = state.toggle_ok()
            print(f"[ENGINE] Salud ahora ok={new_ok}")
    except:
        pass

def main():
    ap = argparse.ArgumentParser(prog="EV_CP_E")
    ap.add_argument("--cp-id", required=True)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=7001, help="puerto socket salud para monitor")
    ap.add_argument("--kafka-bootstrap", help="host:port (OPCIONAL - si no se proporciona, solo socket)")
    ap.add_argument("--topic-telemetry", default=bus.topic_telemetry())
    ap.add_argument("--topic-commands", help="por defecto: cp.commands.<CP_ID>")
    ap.add_argument("--price", type=float, help="Precio por kWh (si no se especifica, se lee de la DB o usa 0.35)")
    ap.add_argument("--kw-max", type=float, help="Potencia máxima en kW (si no se especifica, se lee de la DB o usa 11.0)")
    ap.add_argument("--db-path", default=None, help="Ruta a central.db para leer configuración")
    args = ap.parse_args()

    # Intentar leer precio y kW de la base de datos
    price_eur_kwh = args.price if args.price else 0.35
    kw_max = args.kw_max if args.kw_max else 11.0
    
    if not args.price or not args.kw_max:
        db_path = args.db_path
        if not db_path:
            # Intentar encontrar central.db en ubicación estándar
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "EV_Central", "central.db"),
                "central.db",
                os.path.join(os.path.dirname(__file__), "..", "EV_Central", "central.db"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
        
        if db_path and os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT price_eur_kwh, kw_max FROM charging_points WHERE cp_id = ?", (args.cp_id,))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    if not args.price and row[0]:
                        price_eur_kwh = row[0]
                        logger.info("Precio leído de la DB: {} €/kWh", price_eur_kwh)
                    if not args.kw_max and row[1]:
                        kw_max = row[1]
                        logger.info("Potencia máxima leída de la DB: {} kW", kw_max)
            except Exception as e:
                logger.warning("No se pudo leer configuración de la DB: {}", e)
    
    logger.info("Configuración del CP: Precio={} €/kWh, Potencia={} kW", price_eur_kwh, kw_max)
    
    state = CPState(cp_id=args.cp_id, price_eur_kwh=price_eur_kwh, kw_max=kw_max)

    # Socket para Monitor
    HealthServer(args.host, args.port, state).start()

    # Kafka (producer + consumer) - OPCIONAL
    producer = None
    consumer = None
    
    if args.kafka_bootstrap:
        try:
            # Solo usar el topic broadcast (todos los comandos van ahí)
            cmd_topic = bus.topic_broadcast_commands()
            
            producer = bus.BusProducer(bootstrap=args.kafka_bootstrap, client_id=f"cp-{args.cp_id}")
            consumer = bus.BusConsumer(
                bootstrap=args.kafka_bootstrap,
                group_id=f"cp-{args.cp_id}-grp",
                topics=[cmd_topic],  # Solo un topic para todos
            )
            consumer.start(on_message=_on_command(state))
            logger.info("Kafka conectado exitosamente (usando topic compartido: {})", cmd_topic)
        except Exception as e:
            logger.warning("No se pudo conectar a Kafka (continuando sin Kafka): {}", e)
            producer = None
            consumer = None
    else:
        logger.info("Kafka deshabilitado (sin --kafka-bootstrap)")

    # Hilo de teclado
    threading.Thread(target=_keyboard_toggle, args=(state,), daemon=True).start()

    # Loop telemetría (solo si hay producer y está cargando)
    try:
        while True:
            if producer:
                payload = state.tick_telemetry()
                if payload:
                    producer.send(topic=args.topic_telemetry, value=payload, key=args.cp_id)
                    logger.debug("[TELEMETRY] Sent: {:.2f} kW, {:.4f} €", payload["kw"], payload["eur"])
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping ENGINE…")
        if producer:
            producer.flush()

if __name__ == "__main__":
    main()