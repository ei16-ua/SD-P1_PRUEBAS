#!/usr/bin/env python3
"""
Script para limpiar y reinicializar la base de datos con los CPs correctos
"""
import os
import sys

# Añadir path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'EV_Central'))

from database import Database

# Usar la BD de la raíz del proyecto
DB_FILE = 'central.db'
DB_FILE_OLD = os.path.join('src', 'EV_Central', 'central.db')

def reset_database():
    # Eliminar AMBAS bases de datos si existen
    for db_path in [DB_FILE, DB_FILE_OLD]:
        if os.path.exists(db_path):
            print(f"Eliminando base de datos antigua: {db_path}")
            try:
                os.remove(db_path)
            except PermissionError:
                print(f"\n❌ ERROR: La base de datos {db_path} está siendo utilizada")
                print("\nSOLUCIÓN:")
                print("  1. Cierra el CENTRAL (EV_Central.py o EV_Central_Web.py)")
                print("  2. Cierra el CENTRAL GUI si está abierto")
                print("  3. O ejecuta: taskkill /F /IM python.exe")
            print("\nLuego vuelve a ejecutar este script.\n")
            sys.exit(1)
    
    # Crear nueva base de datos
    print("Creando nueva base de datos...")
    db = Database(DB_FILE)
    
    # Eliminar CPs de prueba si existen
    try:
        db.delete_cp("TEST")
        db.delete_cp("TEST_CP")
        db.delete_cp("CP01")
        print("CPs de prueba eliminados")
    except:
        pass
    
    # Añadir CPs reales (como en la imagen) con precio y kW
    cps = [
        {"cp_id": "ALC1", "location": "C/Helios 5", "price": 0.35, "kw_max": 11.0},
        {"cp_id": "ALC3", "location": "Gran Via 2", "price": 0.99, "kw_max": 7.0},
        {"cp_id": "MAD2", "location": "C/Serrano 18", "price": 2.40, "kw_max": 22.0},
        {"cp_id": "MAD3", "location": "C/Fco 23", "price": 0.38, "kw_max": 11.0},
        {"cp_id": "MAD1", "location": "C/Alcalese", "price": 0.50, "kw_max": 11.0},
        {"cp_id": "SEV3", "location": "Gran Via 1", "price": 2.32, "kw_max": 7.0},
        {"cp_id": "SEV2", "location": "Valencia", "price": 0.33, "kw_max": 11.0},
        {"cp_id": "VAL3", "location": "Malaga Aero", "price": 0.45, "kw_max": 50.0},
        {"cp_id": "VAL1", "location": "San Javier", "price": 7.98, "kw_max": 11.0},
        {"cp_id": "COR1", "location": "Menorca", "price": 9.01, "kw_max": 22.0},
    ]
    
    print("\nAñadiendo CPs:")
    for cp in cps:
        db.upsert_cp(
            cp_id=cp["cp_id"],
            location=cp["location"],
            connected=False,  # Inicialmente desconectados (GRIS)
            ok=True,
            charging=False,
            price_eur_kwh=cp["price"],
            kw_max=cp["kw_max"]
        )
        print(f"  ✓ {cp['cp_id']} - {cp['location']} ({cp['price']} €/kWh, {cp['kw_max']} kW)")
    
    # Añadir conductores de ejemplo
    drivers = [
        {"driver_id": "Maria1", "name": "María García"},
        {"driver_id": "Juan2", "name": "Juan Pérez"},
        {"driver_id": "Ana3", "name": "Ana Martínez"},
        {"driver_id": "Carlos4", "name": "Carlos López"},
        {"driver_id": "Laura5", "name": "Laura Sánchez"},
        {"driver_id": "DANTE", "name": "Dante Alighieri"},
    ]
    
    print("\nAñadiendo conductores:")
    for driver in drivers:
        db.upsert_driver(
            driver_id=driver["driver_id"],
            name=driver["name"]
        )
        print(f"  ✓ {driver['driver_id']} - {driver['name']}")
    
    print(f"\n✅ Base de datos reinicializada correctamente")
    print(f"   Total de CPs: {len(cps)}")
    print(f"   Total de conductores: {len(drivers)}")

if __name__ == "__main__":
    reset_database()
