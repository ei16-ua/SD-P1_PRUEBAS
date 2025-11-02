#!/usr/bin/env python3
"""
Script para crear 9 conductores en la base de datos
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "src" / "EV_Central" / "central.db"

def create_drivers():
    """Crea 9 conductores en la tabla drivers"""
    drivers = [
        ("DRIVER01", "Carlos Martinez", "carlos@email.com"),
        ("DRIVER02", "Ana Lopez", "ana@email.com"),
        ("DRIVER03", "Miguel Garcia", "miguel@email.com"),
        ("DRIVER04", "Laura Sanchez", "laura@email.com"),
        ("DRIVER05", "David Rodriguez", "david@email.com"),
        ("DRIVER06", "Sara Fernandez", "sara@email.com"),
        ("DRIVER07", "Pedro Jimenez", "pedro@email.com"),
        ("DRIVER08", "Elena Ruiz", "elena@email.com"),
        ("DRIVER09", "Javier Moreno", "javier@email.com"),
    ]
    
    print(f"Conectando a la base de datos: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Limpiar drivers existentes
    print("Limpiando drivers existentes...")
    cursor.execute("DELETE FROM drivers")
    
    # Insertar nuevos drivers
    print("Insertando 9 conductores...")
    for driver_id, name, email in drivers:
        cursor.execute(
            "INSERT INTO drivers (driver_id, name, email) VALUES (?, ?, ?)",
            (driver_id, name, email)
        )
        print(f"  ✓ {driver_id}: {name} ({email})")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 9 conductores creados correctamente!")

if __name__ == "__main__":
    try:
        create_drivers()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
