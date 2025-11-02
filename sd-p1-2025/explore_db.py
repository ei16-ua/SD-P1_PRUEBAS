#!/usr/bin/env python3
"""
Script para explorar la base de datos SQLite
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "src" / "EV_Central" / "central.db"

def show_all_cps():
    """Mostrar todos los CPs en la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("CHARGING POINTS EN LA BASE DE DATOS")
    print("="*70)
    
    cursor.execute("""
        SELECT cp_id, location, connected, ok, charging, driver_id, 
               last_kw, euros_accum, stopped_by_central
        FROM charging_points
        ORDER BY cp_id
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("⚠️  No hay CPs en la base de datos")
    else:
        print(f"\n{'CP_ID':<10} {'Location':<20} {'Conn':<6} {'OK':<5} {'Charging':<9} {'Driver':<10}")
        print("-"*70)
        for row in rows:
            cp_id, location, connected, ok, charging, driver_id, kw, eur, stopped = row
            conn_str = "✅" if connected else "❌"
            ok_str = "✅" if ok else "🔴"
            charging_str = "🔌" if charging else "-"
            driver_str = driver_id if driver_id else "-"
            print(f"{cp_id:<10} {location:<20} {conn_str:<6} {ok_str:<5} {charging_str:<9} {driver_str:<10}")
    
    conn.close()
    print(f"\nTotal: {len(rows)} CPs")

def show_all_drivers():
    """Mostrar todos los drivers"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("DRIVERS EN LA BASE DE DATOS")
    print("="*70)
    
    cursor.execute("SELECT driver_id, name, email FROM drivers ORDER BY driver_id")
    rows = cursor.fetchall()
    
    if not rows:
        print("⚠️  No hay drivers en la base de datos")
    else:
        print(f"\n{'Driver ID':<12} {'Name':<25} {'Email':<30}")
        print("-"*70)
        for driver_id, name, email in rows:
            print(f"{driver_id:<12} {name:<25} {email:<30}")
    
    conn.close()
    print(f"\nTotal: {len(rows)} drivers")

def show_active_sessions():
    """Mostrar sesiones activas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("SESIONES ACTIVAS DE CARGA")
    print("="*70)
    
    cursor.execute("""
        SELECT cp_id, driver_id, last_kw, euros_accum
        FROM charging_points
        WHERE charging = 1
        ORDER BY cp_id
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("⚠️  No hay sesiones de carga activas")
    else:
        print(f"\n{'CP_ID':<10} {'Driver':<12} {'kW':<10} {'Euros':<10}")
        print("-"*70)
        for cp_id, driver_id, kw, eur in rows:
            print(f"{cp_id:<10} {driver_id:<12} {kw:<10.2f} {eur:<10.4f}")
    
    conn.close()
    print(f"\nTotal: {len(rows)} sesiones activas")

def run_custom_query():
    """Ejecutar una consulta personalizada"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("CONSULTA PERSONALIZADA")
    print("="*70)
    print("Escribe tu consulta SQL (o 'exit' para salir):")
    print("Ejemplo: SELECT * FROM charging_points WHERE connected=1\n")
    
    while True:
        try:
            query = input("SQL> ").strip()
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            if not query:
                continue
            
            cursor.execute(query)
            
            if query.upper().startswith('SELECT'):
                rows = cursor.fetchall()
                if rows:
                    # Mostrar nombres de columnas
                    cols = [desc[0] for desc in cursor.description]
                    print("\n" + " | ".join(cols))
                    print("-" * 70)
                    for row in rows:
                        print(" | ".join(str(x) for x in row))
                    print(f"\n{len(rows)} rows")
                else:
                    print("No results")
            else:
                conn.commit()
                print(f"✅ Query executed. Rows affected: {cursor.rowcount}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    conn.close()

def main():
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║  SQLite Database Explorer - EV Charging System           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"\nBase de datos: {DB_PATH}")
    
    if not DB_PATH.exists():
        print("\n❌ La base de datos no existe!")
        print("   Ejecuta primero: python reset_database.py")
        return
    
    while True:
        print("\n┌─────────────────────────────────────────────────────────┐")
        print("│  MENÚ                                                   │")
        print("├─────────────────────────────────────────────────────────┤")
        print("│  1. Ver todos los CPs                                   │")
        print("│  2. Ver todos los drivers                               │")
        print("│  3. Ver sesiones activas de carga                       │")
        print("│  4. Ejecutar consulta personalizada                     │")
        print("│  5. Salir                                               │")
        print("└─────────────────────────────────────────────────────────┘")
        
        choice = input("\n👉 Opción: ").strip()
        
        if choice == "1":
            show_all_cps()
        elif choice == "2":
            show_all_drivers()
        elif choice == "3":
            show_active_sessions()
        elif choice == "4":
            run_custom_query()
        elif choice == "5":
            print("\n👋 Saliendo...")
            break
        else:
            print("⚠️  Opción no válida")

if __name__ == "__main__":
    main()
