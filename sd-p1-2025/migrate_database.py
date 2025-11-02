#!/usr/bin/env python3
"""
Script de migración para añadir campos price_eur_kwh y kw_max a la base de datos existente
"""
import sqlite3
import os

DB_PATH = os.path.join('src', 'EV_Central', 'central.db')

def migrate_database():
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró la base de datos en {DB_PATH}")
        return
    
    print(f"📦 Migrando base de datos: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(charging_points)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Añadir price_eur_kwh si no existe
        if 'price_eur_kwh' not in columns:
            print("  ➕ Añadiendo columna price_eur_kwh...")
            cursor.execute("ALTER TABLE charging_points ADD COLUMN price_eur_kwh REAL DEFAULT 0.35")
            print("     ✅ Columna price_eur_kwh añadida")
        else:
            print("  ✓ Columna price_eur_kwh ya existe")
        
        # Añadir kw_max si no existe
        if 'kw_max' not in columns:
            print("  ➕ Añadiendo columna kw_max...")
            cursor.execute("ALTER TABLE charging_points ADD COLUMN kw_max REAL DEFAULT 11.0")
            print("     ✅ Columna kw_max añadida")
        else:
            print("  ✓ Columna kw_max ya existe")
        
        # Actualizar valores por defecto si están en NULL
        cursor.execute("UPDATE charging_points SET price_eur_kwh = 0.35 WHERE price_eur_kwh IS NULL")
        cursor.execute("UPDATE charging_points SET kw_max = 11.0 WHERE kw_max IS NULL")
        
        conn.commit()
        
        # Mostrar CPs actualizados
        cursor.execute("SELECT cp_id, location, price_eur_kwh, kw_max FROM charging_points")
        cps = cursor.fetchall()
        
        if cps:
            print("\n📋 Puntos de carga actualizados:")
            print("="*80)
            print(f"{'ID':<12} {'Ubicación':<30} {'Precio':<15} {'kW Max':<10}")
            print("-"*80)
            for cp_id, location, price, kw in cps:
                print(f"{cp_id:<12} {location:<30} {price or 0.35:.2f} €/kWh    {kw or 11.0:.1f} kW")
            print("="*80)
        
        print("\n✅ Migración completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
