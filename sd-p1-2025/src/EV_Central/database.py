#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database.py
Capa de base de datos SQLite para CENTRAL
"""

import sqlite3
import os
from typing import List, Optional
from contextlib import contextmanager

try:
    from loguru import logger
except Exception:
    class _L:
        def info(self, *a, **k): print("[INFO]", *a)
        def warning(self, *a, **k): print("[WARN]", *a)
        def error(self, *a, **k): print("[ERROR]", *a)
    logger = _L()


class Database:
    def __init__(self, db_path: str = "central.db"):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Inicializar esquema de base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de Charging Points
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS charging_points (
                    cp_id TEXT PRIMARY KEY,
                    location TEXT,
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
            """)
            
            # Tabla de Conductores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    driver_id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de Transacciones/Suministros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_id TEXT,
                    cp_id TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    kwh_consumed REAL DEFAULT 0.0,
                    total_cost REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
                    FOREIGN KEY (cp_id) REFERENCES charging_points(cp_id)
                )
            """)
            
            # Índices para mejorar rendimiento
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cp_connected 
                ON charging_points(connected, ok)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_driver 
                ON transactions(driver_id)
            """)
            
            conn.commit()
            logger.info("Base de datos inicializada: {}", self.db_path)
    
    # ==================== CHARGING POINTS ====================
    
    def get_all_cps(self) -> List[dict]:
        """Obtener todos los CPs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM charging_points")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_cp(self, cp_id: str) -> Optional[dict]:
        """Obtener un CP específico"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM charging_points WHERE cp_id = ?", (cp_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def upsert_cp(self, cp_id: str, location: str = None, connected: bool = None, 
                  ok: bool = None, charging: bool = None, stopped_by_central: bool = None,
                  driver_id: str = None, last_kw: float = None, euros_accum: float = None, 
                  last_ts: float = None, price_eur_kwh: float = None, kw_max: float = None):
        """Insertar o actualizar un CP"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si existe
            existing = self.get_cp(cp_id)
            
            if existing:
                # Actualizar solo campos proporcionados
                updates = []
                params = []
                
                if location is not None:
                    updates.append("location = ?")
                    params.append(location)
                if connected is not None:
                    updates.append("connected = ?")
                    params.append(1 if connected else 0)
                if ok is not None:
                    updates.append("ok = ?")
                    params.append(1 if ok else 0)
                if charging is not None:
                    updates.append("charging = ?")
                    params.append(1 if charging else 0)
                if stopped_by_central is not None:
                    updates.append("stopped_by_central = ?")
                    params.append(1 if stopped_by_central else 0)
                if driver_id is not None:
                    updates.append("driver_id = ?")
                    params.append(driver_id)
                if last_kw is not None:
                    updates.append("last_kw = ?")
                    params.append(last_kw)
                if euros_accum is not None:
                    updates.append("euros_accum = ?")
                    params.append(euros_accum)
                if last_ts is not None:
                    updates.append("last_ts = ?")
                    params.append(last_ts)
                if price_eur_kwh is not None:
                    updates.append("price_eur_kwh = ?")
                    params.append(price_eur_kwh)
                if kw_max is not None:
                    updates.append("kw_max = ?")
                    params.append(kw_max)
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(cp_id)
                
                if updates:
                    sql = f"UPDATE charging_points SET {', '.join(updates)} WHERE cp_id = ?"
                    cursor.execute(sql, params)
            else:
                # Insertar nuevo
                cursor.execute("""
                    INSERT INTO charging_points 
                    (cp_id, location, connected, ok, charging, stopped_by_central, driver_id, last_kw, euros_accum, last_ts, price_eur_kwh, kw_max)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cp_id,
                    location or "Desconocido",
                    1 if connected else 0,
                    1 if ok else 0,
                    1 if charging else 0,
                    1 if stopped_by_central else 0,
                    driver_id,
                    last_kw or 0.0,
                    euros_accum or 0.0,
                    last_ts or 0.0,
                    price_eur_kwh or 0.35,
                    kw_max or 11.0
                ))
            
            conn.commit()
    
    def delete_cp(self, cp_id: str):
        """Eliminar un CP"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM charging_points WHERE cp_id = ?", (cp_id,))
            conn.commit()
    
    # ==================== DRIVERS ====================
    
    def upsert_driver(self, driver_id: str, name: str = None):
        """Insertar o actualizar un conductor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drivers (driver_id, name)
                VALUES (?, ?)
                ON CONFLICT(driver_id) DO UPDATE SET
                    name = COALESCE(excluded.name, name)
            """, (driver_id, name))
            conn.commit()
    
    def get_driver(self, driver_id: str) -> Optional[dict]:
        """Obtener un conductor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers WHERE driver_id = ?", (driver_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== TRANSACTIONS ====================
    
    def create_transaction(self, driver_id: str, cp_id: str) -> int:
        """Crear una nueva transacción"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (driver_id, cp_id, start_time, status)
                VALUES (?, ?, CURRENT_TIMESTAMP, 'active')
            """, (driver_id, cp_id))
            conn.commit()
            return cursor.lastrowid
    
    def finish_transaction(self, transaction_id: int, kwh_consumed: float, total_cost: float):
        """Finalizar una transacción"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE transactions 
                SET end_time = CURRENT_TIMESTAMP,
                    kwh_consumed = ?,
                    total_cost = ?,
                    status = 'completed'
                WHERE id = ?
            """, (kwh_consumed, total_cost, transaction_id))
            conn.commit()
    
    def get_active_transaction(self, driver_id: str, cp_id: str) -> Optional[dict]:
        """Obtener transacción activa de un conductor en un CP"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE driver_id = ? AND cp_id = ? AND status = 'active'
                ORDER BY start_time DESC
                LIMIT 1
            """, (driver_id, cp_id))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_transaction_history(self, driver_id: str = None, limit: int = 50) -> List[dict]:
        """Obtener historial de transacciones"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if driver_id:
                cursor.execute("""
                    SELECT * FROM transactions 
                    WHERE driver_id = ?
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (driver_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM transactions 
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
