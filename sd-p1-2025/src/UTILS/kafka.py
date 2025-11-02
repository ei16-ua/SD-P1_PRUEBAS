#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kafka_bus.py
Capa común de Kafka (Confluent) con JSON producer/consumer y utilidades de topics.
Reutilizable por Engine, Central y AppUser.
"""

from __future__ import annotations
import json
import threading
from typing import Callable, Iterable, Optional

# pip install confluent-kafka
from confluent_kafka import Producer, Consumer, KafkaException, KafkaError, Message


# --------- Helpers de topics (convención) ---------
def topic_telemetry() -> str:
    return "cp.telemetry"

def topic_commands_for(cp_id: str) -> str:
    # Comandos dirigidos a un punto de carga concreto
    return f"cp.commands.{cp_id}"

def topic_broadcast_commands() -> str:
    # (Opcional) Comandos broadcast para todos los CPs
    return "cp.commands.all"

def topic_invoices() -> str:
    # Topic para facturas/tickets de pago
    return "cp.invoices"


# --------- Serialización JSON ---------
def _to_bytes(value) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _from_bytes(raw: bytes):
    return json.loads(raw.decode("utf-8"))


# --------- Producer ---------
class BusProducer:
    def __init__(
        self,
        bootstrap: str,
        client_id: str,
        acks: str = "all",
        enable_idempotence: bool = True,
        linger_ms: int = 0,
        batch_size: int = 0,
    ):
        conf = {
            "bootstrap.servers": bootstrap,
            "client.id": client_id,
            "enable.idempotence": enable_idempotence,
            "acks": acks,
        }
        if linger_ms:
            conf["linger.ms"] = linger_ms
        if batch_size:
            conf["batch.num.messages"] = batch_size

        self._p = Producer(conf)

    def send(self, topic: str, value: dict, key: Optional[str] = None):
        self._p.produce(topic=topic, value=_to_bytes(value), key=key)
        # poll(0) procesa callbacks internos y evita que el buffer crezca indefinidamente
        self._p.poll(0)

    def flush(self, timeout: float = 5.0):
        self._p.flush(timeout)


# --------- Consumer ---------
class BusConsumer:
    def __init__(
        self,
        bootstrap: str,
        group_id: str,
        topics: Iterable[str],
        auto_offset_reset: str = "earliest",
    ):
        self._conf = {
            "bootstrap.servers": bootstrap,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
        }
        self._topics = list(topics)
        self._consumer = Consumer(self._conf)
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self, on_message: Callable[[dict, Message], None]):
        """Lanza un hilo que llama on_message(payload_dict, raw_msg) por cada mensaje."""
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._consumer.subscribe(self._topics)

        def _loop():
            try:
                while self._running:
                    msg = self._consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        # Puedes mejorar el logging aquí
                        if msg.error().code() != KafkaError._PARTITION_EOF:
                            print("[kafka_bus] Consumer error:", msg.error())
                        continue
                    try:
                        payload = _from_bytes(msg.value())
                        on_message(payload, msg)
                    except Exception as e:
                        print("[kafka_bus] Bad payload:", e)
            except KafkaException as e:
                print("[kafka_bus] Kafka exception:", e)
            finally:
                try:
                    self._consumer.close()
                except Exception:
                    pass

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
