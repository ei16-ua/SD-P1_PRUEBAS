#!/usr/bin/env python3
"""Crear topics necesarios en Kafka para este proyecto.

Usage examples:
  python scripts/create_kafka_topics.py --bootstrap 192.168.1.17:9092
  python scripts/create_kafka_topics.py --bootstrap localhost:29092 --from-db

This script will create:
  - cp.telemetry
  - cp.commands.all
  - cp.commands.<CP_ID> for CPs discovered in the SQLite DB (if --from-db) or provided via --cps

Requires: confluent-kafka (AdminClient)
"""
from __future__ import annotations
import argparse
import sys
import time
from typing import List

try:
    from confluent_kafka.admin import AdminClient, NewTopic
except Exception as e:
    print("ERROR: confluent_kafka is required. Install with: pip install confluent-kafka")
    raise

import os


def ensure_topics(admin: AdminClient, topics: List[str], num_partitions: int = 1, replication: int = 1, timeout: float = 10.0):
    md = admin.list_topics(timeout=5)
    existing = set(md.topics.keys())
    to_create = [t for t in topics if t not in existing]
    if not to_create:
        print("No topics to create. All topics already exist on the broker.")
        return

    new_topics = [NewTopic(topic=t, num_partitions=num_partitions, replication_factor=replication) for t in to_create]
    fs = admin.create_topics(new_topics)
    # Wait for results
    for topic, f in fs.items():
        try:
            f.result(timeout=timeout)
            print(f"Created topic: {topic}")
        except Exception as e:
            print(f"Failed to create topic {topic}: {e}")


def read_cps_from_db(db_path: str) -> List[str]:
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT cp_id FROM charging_points")
        rows = cur.fetchall()
        cps = [r[0] for r in rows]
        conn.close()
        return cps
    except Exception as e:
        print(f"Warning: could not read DB {db_path}: {e}")
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", required=True, help="Kafka bootstrap server host:port")
    ap.add_argument("--cps", help="Comma-separated list of CP ids to create topics for (DEPRECATED - no longer needed)")
    ap.add_argument("--cp-id", help="Single CP id to create topic for (DEPRECATED - no longer needed)")
    ap.add_argument("--from-db", action="store_true", help="Read CP ids from src/EV_Central/central.db (DEPRECATED - no longer needed)")
    ap.add_argument("--partitions", type=int, default=1)
    ap.add_argument("--replication", type=int, default=1)
    args = ap.parse_args()

    admin = AdminClient({"bootstrap.servers": args.bootstrap})

    # Crear los 3 topics necesarios (compartidos por todos los CPs)
    topics = ["cp.telemetry", "cp.commands.all", "cp.invoices"]
    
    print("Creating topics on bootstrap=", args.bootstrap)
    print("Topics to ensure:")
    for t in topics:
        print(" -", t)
    print("\nNOTA: Ya NO se crean topics individuales por CP.")
    print("      Todos los CPs usan 'cp.commands.all' (filtrado por cp_id)")
    print("      Las facturas se envian por 'cp.invoices'")

    ensure_topics(admin, topics, num_partitions=args.partitions, replication=args.replication)


if __name__ == "__main__":
    main()
