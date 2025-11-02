#!/usr/bin/env python3
"""
Agregar un nuevo CP a la base de datos
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'EV_Central'))
from database import Database

DB_FILE = os.path.join('src', 'EV_Central', 'central.db')

def add_cp(cp_id: str, location: str):
    """Agregar un nuevo CP a la base de datos"""
    db = Database(DB_FILE)
    
    # Verificar si ya existe
    existing = db.get_cp(cp_id)
    if existing:
        print(f"⚠️  El CP {cp_id} ya existe:")
        print(f"   Ubicación: {existing['location']}")
        print(f"   Conectado: {'Sí' if existing['connected'] else 'No'}")
        return False
    
    # Agregar nuevo CP
    db.upsert_cp(
        cp_id=cp_id,
        location=location,
        connected=False,
        ok=True,
        charging=False
    )
    
    print(f"✅ CP agregado exitosamente:")
    print(f"   ID: {cp_id}")
    print(f"   Ubicación: {location}")
    print(f"   Estado: Desconectado (inicialmente)")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python add_cp.py <CP_ID> <UBICACION>")
        print("Ejemplo: python add_cp.py ALC2 'Alicante Centro'")
        sys.exit(1)
    
    cp_id = sys.argv[1]
    location = ' '.join(sys.argv[2:])
    
    add_cp(cp_id, location)
