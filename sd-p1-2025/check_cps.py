import sqlite3
import sys
import os

# Ruta por defecto de la BD (raíz del proyecto)
DB_PATH = 'central.db'

print(f'\n📁 Usando BD: {DB_PATH}\n')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT cp_id, connected, ok, charging, driver_id FROM charging_points ORDER BY cp_id')
rows = cursor.fetchall()

print('\n✅ Estado actual de los CPs en la BD:')
print('=' * 70)
print(f"{'CP_ID':<10} {'Connected':<12} {'OK':<8} {'Charging':<12} {'Driver':<15}")
print('-' * 70)

for row in rows:
    cp_id, connected, ok, charging, driver_id = row
    conn_str = '✅ SI' if connected else '❌ NO'
    ok_str = '✅ SI' if ok else '🔴 NO'
    charging_str = '🔌 SI' if charging else '⏸️  NO'
    driver_str = driver_id if driver_id else '-'
    
    print(f"{cp_id:<10} {conn_str:<12} {ok_str:<8} {charging_str:<12} {driver_str:<15}")

conn.close()

print('=' * 70)
print('\n📝 Leyenda:')
print('  Connected: ✅ = ENGINE corriendo | ❌ = ENGINE parado')
print('  OK: ✅ = Funcionando | 🔴 = Averiado')
print('  Charging: 🔌 = Cargando | ⏸️ = Libre')
