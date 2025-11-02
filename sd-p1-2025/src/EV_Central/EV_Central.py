#!/usr/bin/env python3
"""CENTRAL

Simple implementation of the CENTRAL module required by the assignment.

Features implemented:
- Loads a small local DB (cp_db.json) with known CPs (optional).
- TCP server that accepts lines from clients (MONITORs and DRIVERs):
  * AUTH#<CP_ID>             -> register CP as connected, reply ACK
  * FAULT#<CP_ID>#<REASON>   -> mark CP as in fault, reply ACK
  * REQ#<DRIVER_ID>#<CP_ID>  -> driver requests authorization; CENTRAL checks state and
                                if possible sends a start_charge command to the CP via Kafka
                                and replies AUTH_GRANTED or AUTH_DENIED#<reason>
  * FINISH#<CP_ID>#<DRIVER_ID> -> driver notifies end of charging; CENTRAL sends stop_charge

+- Optional Kafka integration: if --kafka-bootstrap provided, CENTRAL will produce commands
  to cp.commands.<CP_ID> and consume cp.telemetry to update consumption shown in console.

This is a compact, single-file implementation intended to be readable and extendable.
"""

from __future__ import annotations
import argparse
import json
import os
import socket
import threading
import time
from dataclasses import dataclass, asdict, field
from threading import Lock
from typing import Dict, Optional

try:
    from loguru import logger
except Exception:
    class _L:
        def info(self, *a, **k): print("[INFO]", *a)
        def warning(self, *a, **k): print("[WARN]", *a)
        def error(self, *a, **k): print("[ERROR]", *a)
        def debug(self, *a, **k): print("[DEBUG]", *a)
    logger = _L()

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # Para importar database.py
from UTILS import kafka as bus
from UTILS.protocol import ProtocolMessage
from database import Database


# Usar la BD de la raíz del proyecto (2 niveles arriba)
DB_FILENAME = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "central.db")


@dataclass
class CPRecord:
    cp_id: str
    location: Optional[str] = None
    connected: bool = False
    ok: bool = True
    charging: bool = False
    driver_id: Optional[str] = None
    last_kw: float = 0.0
    euros_accum: float = 0.0
    last_ts: float = 0.0
    stopped_by_central: bool = False  # True = Parado (Out of Order) por CENTRAL
    kw_max: float = 11.0  # Potencia máxima del CP
    price_eur_kwh: float = 0.35  # Precio por kWh
    _lock: Lock = field(default_factory=Lock, repr=False)

    def to_dict(self):
        """Convert to dict manually to avoid Lock serialization issues"""
        return {
            'cp_id': self.cp_id,
            'location': self.location,
            'connected': self.connected,
            'ok': self.ok,
            'charging': self.charging,
            'driver_id': self.driver_id,
            'last_kw': self.last_kw,
            'euros_accum': self.euros_accum,
            'last_ts': self.last_ts,
            'stopped_by_central': self.stopped_by_central,
            'kw_max': self.kw_max,
            'price_eur_kwh': self.price_eur_kwh
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k != "_lock"})

    def start_charge(self, driver_id: str):
        with self._lock:
            self.charging = True
            self.driver_id = driver_id
            self.last_kw = 0.0
            self.euros_accum = 0.0

    def stop_charge(self):
        with self._lock:
            self.charging = False
            self.driver_id = None
            self.last_kw = 0.0
            self.euros_accum = 0.0  # Resetear valores para el próximo usuario

    def update_telemetry(self, kw: float, eur: float, ts: float):
        with self._lock:
            self.last_kw = kw
            self.euros_accum = eur
            self.last_ts = ts


class Central:
    def __init__(self, host: str, port: int, kafka_bootstrap: Optional[str] = None, gui_callback=None):
        self._addr = (host, port)
        self._sock = None
        self._db: Dict[str, CPRecord] = {}
        self._db_lock = Lock()
        self.kafka_bootstrap = kafka_bootstrap
        self.producer = None
        self.telemetry_consumer = None
        self.gui_callback = gui_callback
        
        # SQLite Database
        self.database = Database(DB_FILENAME)

        if kafka_bootstrap:
            try:
                self.producer = bus.BusProducer(bootstrap=kafka_bootstrap, client_id="central-producer")
            except Exception as e:
                logger.warning("Kafka producer initialization failed: {}", e)
                self.producer = None

    # DB helpers
    def load_db(self):
        """Cargar CPs desde SQLite a memoria"""
        try:
            cps_data = self.database.get_all_cps()
            for cp_data in cps_data:
                rec = CPRecord(
                    cp_id=cp_data['cp_id'],
                    location=cp_data.get('location', 'Calle'),
                    connected=bool(cp_data['connected']),
                    ok=bool(cp_data['ok']),
                    charging=bool(cp_data['charging']),
                    stopped_by_central=bool(cp_data.get('stopped_by_central', False)),
                    driver_id=cp_data['driver_id'],
                    last_kw=cp_data['last_kw'],
                    euros_accum=cp_data['euros_accum'],
                    last_ts=cp_data['last_ts'],
                    kw_max=cp_data.get('kw_max', 11.0),
                    price_eur_kwh=cp_data.get('price_eur_kwh', 0.35)
                )
                self._db[rec.cp_id] = rec
            logger.info("Loaded {} CP records from SQLite", len(self._db))
        except Exception as e:
            logger.error("Failed to load DB: {}", e)

    def persist_db(self):
        """Persistir CPs a SQLite (solo los campos cambiados)"""
        try:
            with self._db_lock:
                for cp in self._db.values():
                    self.database.upsert_cp(
                        cp_id=cp.cp_id,
                        location=cp.location,
                        connected=cp.connected,
                        ok=cp.ok,
                        charging=cp.charging,
                        stopped_by_central=cp.stopped_by_central,
                        driver_id=cp.driver_id,
                        last_kw=cp.last_kw,
                        euros_accum=cp.euros_accum,
                        last_ts=cp.last_ts,
                        price_eur_kwh=cp.price_eur_kwh,
                        kw_max=cp.kw_max
                    )
            logger.debug("DB persisted to SQLite")
        except Exception as e:
            logger.error("Failed to persist DB: {}", e)

    def ensure_cp(self, cp_id: str) -> CPRecord:
        """
        SOLO para AUTH/FAULT de Monitors conectados.
        Crea el CP si no existe (caso de Monitor nuevo conectándose).
        """
        with self._db_lock:
            if cp_id not in self._db:
                logger.info("New CP discovered: {} (added to DB as Calle)", cp_id)
                rec = CPRecord(cp_id=cp_id, location="Calle")
                self._db[cp_id] = rec
                # NO llamar persist_db aquí porque ya tenemos el lock
                # Lo haremos después en el handler
            return self._db[cp_id]
    
    def cp_exists(self, cp_id: str) -> bool:
        """Verificar si un CP existe en la base de datos"""
        with self._db_lock:
            return cp_id in self._db

    # Network handlers
    def start(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(self._addr)
        srv.listen(8)
        logger.info("CENTRAL listening on {}:{}", *self._addr)

        # optional kafka telemetry
        if self.kafka_bootstrap:
            try:
                self.telemetry_consumer = bus.BusConsumer(
                    bootstrap=self.kafka_bootstrap,
                    group_id="central-telemetry-grp",
                    topics=[bus.topic_telemetry()],
                )
                self.telemetry_consumer.start(on_message=self._on_telemetry)
                logger.info("Telemetry consumer started (topic={})", bus.topic_telemetry())
                
                # Mensaje de Kafka conectado
                if self.gui_callback:
                    try:
                        threading.Thread(target=self.gui_callback, args=('message',), 
                                       kwargs={'message': f"Kafka connected ({self.kafka_bootstrap})"}, daemon=True).start()
                    except Exception as e:
                        logger.warning("GUI callback error: {}", e)
            except Exception as e:
                logger.warning("Failed to start telemetry consumer: {}", e)
                # Mensaje de Kafka caído
                if self.gui_callback:
                    try:
                        threading.Thread(target=self.gui_callback, args=('message',), 
                                       kwargs={'message': f"Kafka connection failed"}, daemon=True).start()
                    except Exception as e:
                        logger.warning("GUI callback error: {}", e)

        def _accept_loop():
            while True:
                conn, addr = srv.accept()
                threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()

        # Server thread should NOT be daemon - we want it to keep the program alive
        self.server_thread = threading.Thread(target=_accept_loop, daemon=False)
        self.server_thread.start()

        # CLI thread can be daemon - it's just for commands
        threading.Thread(target=self._cli_loop, daemon=True).start()

    def _handle_conn(self, conn: socket.socket, addr):
        """Maneja conexión persistente del Monitor (y conexiones one-shot del Driver)"""
        current_cp_id = None  # Track which CP this connection belongs to
        
        with conn:
            logger.info("[CENTRAL] New connection from {}", addr)
            try:
                while True:
                    # Recibir mensaje con protocolo (valida LRC y envía ACK/NACK automáticamente)
                    message, valid = ProtocolMessage.receive_with_protocol(conn, send_ack=True, timeout=300.0)
                    
                    if message is None:
                        # Connection closed or timeout
                        logger.info("[CENTRAL] Connection closed or timeout from {}", addr)
                        break
                    
                    if not valid:
                        # LRC corruption detected
                        logger.error("[CENTRAL] Corrupted message from {}, sent NACK", addr)
                        continue
                    
                    line = message.strip()
                    logger.info("[CENTRAL] recv: {} from {}", line, addr)
                    parts = line.split("#")

                    if parts[0] == "AUTH" and len(parts) >= 2:
                        cp_id = parts[1]
                        current_cp_id = cp_id  # TRACKEAR el CP de esta conexión
                        rec = self.ensure_cp(cp_id)
                        rec.connected = True
                        rec.ok = True
                        rec.charging = False
                        logger.info("CP {} authenticated and now CONNECTED", cp_id)
                        # AUTH no necesita respuesta adicional, el ACK ya se envió automáticamente
                        try:
                            if self.gui_callback:
                                threading.Thread(target=self.gui_callback, args=('message',), 
                                               kwargs={'message': f"{cp_id} connected"}, daemon=True).start()
                        except Exception as e:
                            logger.warning("GUI callback error: {}", e)
                        try:
                            threading.Thread(target=self.persist_db, daemon=True).start()
                        except Exception as e:
                            logger.warning("Persist DB error: {}", e)

                    elif parts[0] == "FAULT" and len(parts) >= 3:
                        cp_id = parts[1]
                        current_cp_id = cp_id  # TRACKEAR el CP de esta conexión
                        reason = parts[2]
                        rec = self.ensure_cp(cp_id)
                        rec.connected = True
                        rec.ok = False
                        rec.charging = False
                        logger.warning("CP {} reported FAULT: {}", cp_id, reason)
                        # FAULT no necesita respuesta adicional, el ACK ya se envió automáticamente
                        try:
                            if self.gui_callback:
                                threading.Thread(target=self.gui_callback, args=('message',), 
                                               kwargs={'message': f"{cp_id} FAULT: {reason}"}, daemon=True).start()
                        except Exception as e:
                            logger.warning("GUI callback error: {}", e)
                        try:
                            threading.Thread(target=self.persist_db, daemon=True).start()
                        except Exception as e:
                            logger.warning("Persist DB error: {}", e)

                    elif parts[0] == "REQ" and len(parts) >= 3:
                        driver_id = parts[1]
                        cp_id = parts[2]
                        
                        # PRIMERO verificar si el CP existe
                        if not self.cp_exists(cp_id):
                            resp = "AUTH_DENIED#CP_NOT_FOUND"
                            ProtocolMessage.send_with_protocol(conn, resp, wait_ack=True, timeout=5.0)
                            logger.warning("Authorization denied for driver {} on {}: CP does not exist", driver_id, cp_id)
                            if self.gui_callback:
                                try:
                                    threading.Thread(target=self.gui_callback, args=('message',), 
                                                   kwargs={'message': f"DENIED {driver_id}: CP {cp_id} not found"}, daemon=True).start()
                                except Exception as e:
                                    logger.warning("GUI callback error: {}", e)
                            continue
                        
                        rec = self.ensure_cp(cp_id)
                        
                        if self.gui_callback:
                            try:
                                self.gui_callback('request', driver_id=driver_id, cp_id=cp_id)
                            except Exception as e:
                                logger.warning("GUI callback error: {}", e)
                        
                        # SOLUCIÓN AL BUG: Si el CP está ocupado PERO es el mismo driver, permitir reconexión
                        if rec.charging and rec.driver_id == driver_id:
                            # El mismo driver está reconectándose a su carga activa
                            resp = f"AUTH_GRANTED#{cp_id}#{driver_id}#RECONNECT"
                            ProtocolMessage.send_with_protocol(conn, resp, wait_ack=True, timeout=5.0)
                            logger.info("Driver {} RECONNECTED to active charge on {}", driver_id, cp_id)
                            if self.gui_callback:
                                try:
                                    threading.Thread(target=self.gui_callback, args=('message',), 
                                                   kwargs={'message': f"{driver_id} reconnected to {cp_id}"}, daemon=True).start()
                                except Exception as e:
                                    logger.warning("GUI callback error: {}", e)
                            # No reiniciar la carga, solo reconectar
                            continue
                        
                        # Authorization checks (para drivers nuevos o diferentes)
                        reason = None
                        if not rec.connected:
                            reason = "DISCONNECTED"
                        elif rec.stopped_by_central:
                            reason = "OUT_OF_ORDER"
                        elif not rec.ok:
                            reason = "FAULT"
                        elif rec.charging:
                            # Ya verificamos arriba si es el mismo driver, aquí es otro driver
                            reason = "BUSY"

                        if reason:
                            resp = f"AUTH_DENIED#{reason}"
                            ProtocolMessage.send_with_protocol(conn, resp, wait_ack=True, timeout=5.0)
                            logger.info("Authorization denied for driver {} on {}: {}", driver_id, cp_id, reason)
                            if self.gui_callback:
                                try:
                                    threading.Thread(target=self.gui_callback, args=('message',), 
                                                   kwargs={'message': f"{cp_id} denied to {driver_id}: {reason}"}, daemon=True).start()
                                except Exception as e:
                                    logger.warning("GUI callback error: {}", e)
                        else:
                            # grant and send kafka command to start
                            resp = f"AUTH_GRANTED#{cp_id}#{driver_id}"
                            ProtocolMessage.send_with_protocol(conn, resp, wait_ack=True, timeout=5.0)
                            logger.info("Authorization GRANTED for driver {} on {}", driver_id, cp_id)
                            if self.gui_callback:
                                try:
                                    threading.Thread(target=self.gui_callback, args=('message',), 
                                                   kwargs={'message': f"{cp_id} authorized for {driver_id}"}, daemon=True).start()
                                except Exception as e:
                                    logger.warning("GUI callback error: {}", e)
                            rec.start_charge(driver_id)
                            try:
                                threading.Thread(target=self.persist_db, daemon=True).start()
                            except Exception as e:
                                logger.warning("Persist DB error: {}", e)
                            if self.producer:
                                payload = {"cp_id": cp_id, "op": "start_charge", "driver_id": driver_id}
                                try:
                                    self.producer.send(topic=bus.topic_broadcast_commands(), value=payload, key=cp_id)
                                    logger.info("Sent start_charge command to topic {}", bus.topic_broadcast_commands())
                                except Exception as e:
                                    logger.error("Failed to send start command via Kafka: {}", e)

                    elif parts[0] == "FINISH" and len(parts) >= 3:
                        cp_id = parts[1]
                        driver_id = parts[2]
                        rec = self.ensure_cp(cp_id)
                        
                        # Guardar valores antes de parar la carga
                        final_kw = rec.last_kw
                        final_eur = rec.euros_accum
                        
                        rec.stop_charge()
                        logger.info("Driver {} finished charging on {}", driver_id, cp_id)
                        # FINISH no necesita respuesta adicional, el ACK ya se envió automáticamente
                        
                        # Mensaje de desconexión del driver
                        if self.gui_callback:
                            try:
                                threading.Thread(target=self.gui_callback, args=('message',), 
                                               kwargs={'message': f"Driver {driver_id} finished on {cp_id}"}, daemon=True).start()
                            except Exception as e:
                                logger.warning("GUI callback error: {}", e)
                        
                        try:
                            threading.Thread(target=self.persist_db, daemon=True).start()
                        except Exception as e:
                            logger.warning("Persist DB error: {}", e)
                        
                        # Enviar comando stop al ENGINE
                        if self.producer:
                            payload = {"cp_id": cp_id, "op": "stop_charge", "driver_id": driver_id}
                            try:
                                self.producer.send(topic=bus.topic_broadcast_commands(), value=payload, key=cp_id)
                                logger.info("Sent stop_charge command to topic {}", bus.topic_broadcast_commands())
                            except Exception as e:
                                logger.error("Failed to send stop command via Kafka: {}", e)
                        
                        # IMPORTANTE: Enviar factura/ticket al Driver via Kafka
                        if self.producer:
                            invoice_payload = {
                                "driver_id": driver_id,
                                "cp_id": cp_id,
                                "total_kw": final_kw,
                                "total_eur": final_eur,
                                "timestamp": time.time()
                            }
                            try:
                                self.producer.send(topic=bus.topic_invoices(), value=invoice_payload, key=driver_id)
                                logger.info("Sent invoice to driver {} via Kafka: {:.2f} kW, {:.4f} €", driver_id, final_kw, final_eur)
                            except Exception as e:
                                logger.error("Failed to send invoice via Kafka: {}", e)

                    else:
                        ProtocolMessage.send_with_protocol(conn, "NACK", wait_ack=True, timeout=5.0)
                        
            except Exception as e:
                logger.error("Connection handler error for {}: {}", addr, e)
            finally:
                # MARCAR COMO DESCONECTADO al salir del loop
                if current_cp_id:
                    logger.warning("[CENTRAL] Connection lost for CP {}, marking as DISCONNECTED", current_cp_id)
                    with self._db_lock:
                        if current_cp_id in self._db:
                            self._db[current_cp_id].connected = False
                            self._db[current_cp_id].charging = False
                            logger.info("CP {} marked as DISCONNECTED", current_cp_id)
                    try:
                        threading.Thread(target=self.persist_db, daemon=True).start()
                    except Exception as e:
                        logger.warning("Persist DB error in finally: {}", e)
                    try:
                        if self.gui_callback:
                            threading.Thread(target=self.gui_callback, args=('message',), 
                                           kwargs={'message': f"{current_cp_id} disconnected"}, daemon=True).start()
                    except Exception as e:
                        logger.warning("GUI callback error in finally: {}", e)

    def _on_telemetry(self, payload: dict, _raw_msg):
        try:
            cp_id = payload.get("cp_id")
            kw = payload.get("kw", 0.0)
            eur = payload.get("eur", 0.0)
            ts = payload.get("ts", time.time())
            rec = self.ensure_cp(cp_id)
            rec.update_telemetry(kw=kw, eur=eur, ts=ts)
            # If telemetry arrives, consider the CP connected and charging True
            rec.connected = True
            rec.charging = True
            # Print a concise status line
            print(f"[TELEMETRY] {cp_id} kw={kw} eur={eur} at {time.strftime('%H:%M:%S', time.localtime(ts))}")
        except Exception as e:
            logger.warning("Bad telemetry payload: {} -> {}", e, payload)

    # Simple CLI for operator actions
    def _cli_loop(self):
        print("CENTRAL CLI: commands: list | stop <CP_ID> | resume <CP_ID> | quit")
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                break
            if not line:
                continue
            parts = line.split()
            cmd = parts[0].lower()
            if cmd == "list":
                self._print_status()
            elif cmd == "stop" and len(parts) >= 2:
                cp_id = parts[1]
                # VALIDAR que el CP existe
                if not self.cp_exists(cp_id):
                    print(f"❌ Error: El CP '{cp_id}' NO EXISTE en el sistema")
                    logger.warning("STOP command failed: CP {} does not exist", cp_id)
                    continue
                
                rec = self.ensure_cp(cp_id)
                rec.stopped_by_central = True  # Marcado como parado por CENTRAL
                rec.charging = False
                self.persist_db()
                logger.info("CP {} stopped by CENTRAL (Out of Order)", cp_id)
                print(f"✅ CP {cp_id} marcado como Out of Order")
                # optionally send stop command via kafka
                if self.producer:
                    try:
                        self.producer.send(topic=bus.topic_broadcast_commands(), value={"cp_id": cp_id, "op": "stop_charge", "reason": "CENTRAL_STOP"}, key=cp_id)
                        logger.info("Sent stop (CENTRAL) to {}", cp_id)
                    except Exception as e:
                        logger.warning("Failed sending stop to {}: {}", cp_id, e)
            elif cmd == "resume" and len(parts) >= 2:
                cp_id = parts[1]
                # VALIDAR que el CP existe
                if not self.cp_exists(cp_id):
                    print(f"❌ Error: El CP '{cp_id}' NO EXISTE en el sistema")
                    logger.warning("RESUME command failed: CP {} does not exist", cp_id)
                    continue
                
                rec = self.ensure_cp(cp_id)
                rec.stopped_by_central = False  # Reanudar
                rec.ok = True
                self.persist_db()
                logger.info("CP {} resumed (available again)", cp_id)
                print(f"✅ CP {cp_id} reanudado (disponible)")
            elif cmd == "quit":
                print("Shutting down CENTRAL CLI")
                os._exit(0)
            else:
                print("Unknown command")

    def _print_status(self):
        with self._db_lock:
            if not self._db:
                print("No CPs registered")
                return
            print("CP_ID | LOC | CONNECTED | OK | CHARGING | DRIVER | KW | EUR | LAST_TS")
            for cp in self._db.values():
                ts = time.strftime('%H:%M:%S', time.localtime(cp.last_ts)) if cp.last_ts else "-"
                print(f"{cp.cp_id} | {cp.location} | {cp.connected} | {cp.ok} | {cp.charging} | {cp.driver_id or '-'} | {cp.last_kw} | {cp.euros_accum} | {ts}")


def main():
    ap = argparse.ArgumentParser(prog="EV_Central")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=9099)
    ap.add_argument("--kafka-bootstrap", help="host:port for Kafka (optional)")
    args = ap.parse_args()

    cen = Central(host=args.host, port=args.port, kafka_bootstrap=args.kafka_bootstrap)
    cen.load_db()
    cen.start()

    # keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("CENTRAL stopping…")


if __name__ == "__main__":
    main()

