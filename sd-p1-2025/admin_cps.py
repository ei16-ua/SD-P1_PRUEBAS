#!/usr/bin/env python3
"""
Script de administración de Puntos de Carga (CPs)
Permite añadir y eliminar CPs de la base de datos con validación de duplicados
"""

import sqlite3
import sys
import argparse
from pathlib import Path

DB_PATH = Path(__file__).parent / 'central.db'

def init_db():
    """Inicializar la base de datos si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS charging_points (
            cp_id TEXT PRIMARY KEY,
            location TEXT NOT NULL UNIQUE,
            connected INTEGER DEFAULT 0,
            ok INTEGER DEFAULT 1,
            charging INTEGER DEFAULT 0,
            stopped_by_central INTEGER DEFAULT 0,
            driver_id TEXT,
            last_kw REAL DEFAULT 0.0,
            euros_accum REAL DEFAULT 0.0,
            last_ts REAL DEFAULT 0.0,
            price_eur_kwh REAL DEFAULT 0.35,
            kw_max REAL DEFAULT 11.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def list_cps():
    """Listar todos los puntos de carga"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT cp_id, location, price_eur_kwh, kw_max, connected FROM charging_points ORDER BY cp_id')
    cps = cursor.fetchall()
    conn.close()
    
    if not cps:
        print("\n❌ No hay puntos de carga registrados en la base de datos.\n")
        return
    
    print("\n" + "="*90)
    print("  PUNTOS DE CARGA REGISTRADOS")
    print("="*90)
    print(f"{'ID':<12} {'UBICACIÓN':<30} {'PRECIO':<12} {'kW MAX':<10} {'ESTADO':<10}")
    print("-"*90)
    for cp_id, location, price, kw, connected in cps:
        status = "🟢 Online" if connected else "⚫ Offline"
        print(f"{cp_id:<12} {location:<30} {price:.2f} €/kWh  {kw:.1f} kW    {status:<10}")
    print("="*90)
    print(f"\nTotal: {len(cps)} punto(s) de carga\n")

def check_duplicate(cp_id, location):
    """Verificar si ya existe un CP con ese ID o ubicación"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar ID duplicado
    cursor.execute('SELECT cp_id FROM charging_points WHERE cp_id = ?', (cp_id,))
    if cursor.fetchone():
        conn.close()
        return 'id', cp_id
    
    # Verificar ubicación duplicada
    cursor.execute('SELECT cp_id FROM charging_points WHERE location = ?', (location,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return 'location', existing[0]
    
    conn.close()
    return None, None

def add_cp(cp_id, location, price=0.35, kw_max=11.0, force=False):
    """Añadir un nuevo punto de carga"""
    cp_id = cp_id.upper()
    
    # Verificar duplicados
    dup_type, dup_value = check_duplicate(cp_id, location)
    if dup_type == 'id':
        print(f"\n❌ ERROR: Ya existe un punto de carga con el ID '{cp_id}'")
        if not force:
            print("   Usa --force para sobrescribir o elige otro ID.\n")
            return False
        print("   [--force] Sobrescribiendo el registro existente...\n")
    elif dup_type == 'location':
        print(f"\n❌ ERROR: Ya existe un punto de carga en '{location}' (ID: {dup_value})")
        if not force:
            print("   Usa --force para sobrescribir o elige otra ubicación.\n")
            return False
        print("   [--force] Sobrescribiendo el registro existente...\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if force and dup_type:
            # Actualizar registro existente
            cursor.execute('''
                INSERT OR REPLACE INTO charging_points 
                (cp_id, location, connected, ok, charging, stopped_by_central, driver_id, 
                 last_kw, euros_accum, last_ts, price_eur_kwh, kw_max)
                VALUES (?, ?, 0, 1, 0, 0, NULL, 0.0, 0.0, 0.0, ?, ?)
            ''', (cp_id, location, price, kw_max))
        else:
            # Insertar nuevo registro
            cursor.execute('''
                INSERT INTO charging_points 
                (cp_id, location, connected, ok, charging, stopped_by_central, driver_id, 
                 last_kw, euros_accum, last_ts, price_eur_kwh, kw_max)
                VALUES (?, ?, 0, 1, 0, 0, NULL, 0.0, 0.0, 0.0, ?, ?)
            ''', (cp_id, location, price, kw_max))
        
        conn.commit()
        print(f"✅ Punto de carga añadido exitosamente:")
        print(f"   ID: {cp_id}")
        print(f"   Ubicación: {location}")
        print(f"   Precio: {price} €/kWh")
        print(f"   Potencia máxima: {kw_max} kW")
        print(f"\nℹ️  No necesitas crear topics de Kafka")
        print(f"   Todos los CPs usan 'cp.commands.all' (topic compartido)")
        print()
        return True
        
    except sqlite3.IntegrityError as e:
        print(f"\n❌ ERROR al añadir el punto de carga: {e}\n")
        return False
    finally:
        conn.close()

def remove_cp(cp_id):
    """Eliminar un punto de carga"""
    cp_id = cp_id.upper()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute('SELECT location FROM charging_points WHERE cp_id = ?', (cp_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"\n❌ ERROR: No existe un punto de carga con el ID '{cp_id}'\n")
        conn.close()
        return False
    
    location = result[0]
    
    # Confirmar eliminación
    print(f"\n⚠️  ¿Estás seguro de eliminar el punto de carga?")
    print(f"   ID: {cp_id}")
    print(f"   Ubicación: {location}")
    response = input("\n   Escribe 'SI' para confirmar: ").strip().upper()
    
    if response != 'SI':
        print("\n❌ Operación cancelada.\n")
        conn.close()
        return False
    
    try:
        cursor.execute('DELETE FROM charging_points WHERE cp_id = ?', (cp_id,))
        conn.commit()
        print(f"\n✅ Punto de carga '{cp_id}' eliminado exitosamente.")
        print(f"\n💡 Recuerda eliminar el topic de Kafka si ya no se usa:")
        print(f"   docker exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic cp.commands.{cp_id}\n")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR al eliminar el punto de carga: {e}\n")
        return False
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description='Administración de Puntos de Carga (CPs)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos de uso:

  # Listar todos los puntos de carga
  python admin_cps.py --list

  # Añadir un nuevo punto de carga
  python admin_cps.py --add --id FRANCIA --location "Rue de Paris, Paris"

  # Añadir forzando sobrescritura si existe duplicado
  python admin_cps.py --add --id FRANCIA --location "Nueva dirección" --force

  # Eliminar un punto de carga
  python admin_cps.py --remove --id FRANCIA

        '''
    )
    
    parser.add_argument('--list', action='store_true', help='Listar todos los puntos de carga')
    parser.add_argument('--add', action='store_true', help='Añadir un nuevo punto de carga')
    parser.add_argument('--remove', action='store_true', help='Eliminar un punto de carga')
    parser.add_argument('--id', type=str, help='ID del punto de carga (ej: ALC1, SEV1, FRANCIA)')
    parser.add_argument('--location', type=str, help='Ubicación/dirección del punto de carga')
    parser.add_argument('--price', type=float, default=0.35, help='Precio por kWh (default: 0.35 €/kWh)')
    parser.add_argument('--kw-max', type=float, default=11.0, help='Potencia máxima (default: 11.0 kW)')
    parser.add_argument('--force', action='store_true', help='Forzar sobrescritura si existe duplicado')
    
    args = parser.parse_args()
    
    # Inicializar DB si no existe
    init_db()
    
    # Validar argumentos
    if args.list:
        list_cps()
        return 0
    
    if args.add:
        if not args.id or not args.location:
            print("\n❌ ERROR: Para añadir un CP necesitas especificar --id y --location\n")
            parser.print_help()
            return 1
        success = add_cp(args.id, args.location, args.price, args.kw_max, args.force)
        return 0 if success else 1
    
    if args.remove:
        if not args.id:
            print("\n❌ ERROR: Para eliminar un CP necesitas especificar --id\n")
            parser.print_help()
            return 1
        success = remove_cp(args.id)
        return 0 if success else 1
    
    # Si no hay argumentos, mostrar ayuda
    parser.print_help()
    return 0

if __name__ == '__main__':
    sys.exit(main())
