#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EV_Driver - Aplicación del conductor para solicitar suministros

Funcionalidades:
- Solicitar suministro en un CP específico (manual o desde archivo)
- Comunicarse con CENTRAL vía TCP (REQ/FINISH)
- Recibir telemetría del CP que está suministrando vía Kafka
- Mostrar en pantalla el estado del suministro
- Esperar 4 segundos entre suministros consecutivos
"""

from __future__ import annotations
import argparse
import os
import socket
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

try:
    from loguru import logger
except Exception:
    class _L:
        def info(self, *a, **k): print("[INFO]", *a)
        def warning(self, *a, **k): print("[WARN]", *a)
        def error(self, *a, **k): print("[ERROR]", *a)
        def debug(self, *a, **k): print("[DEBUG]", *a)
    logger = _L()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import kafka as bus
from UTILS.protocol import ProtocolMessage

# Intentar importar el módulo de base de datos
try:
    from EV_Central.database import Database
except ImportError:
    Database = None  # No disponible si no se encuentra


@dataclass
class DriverState:
    driver_id: str
    current_cp: Optional[str] = None
    charging: bool = False
    last_kw: float = 0.0
    last_eur: float = 0.0
    last_kwh: float = 0.0  # Consumo total acumulado en kWh
    finished_waiting_payment: bool = False  # True cuando se finaliza pero aún no se ha pagado


class Driver:
    def __init__(self, driver_id: str, central_host: str, central_port: int, 
                 kafka_bootstrap: Optional[str] = None, db_path: Optional[str] = None):
        self.driver_id = driver_id
        self.central_addr = (central_host, central_port)
        self.kafka_bootstrap = kafka_bootstrap
        self.state = DriverState(driver_id=driver_id)
        self.consumer_telemetry = None
        self.consumer_invoices = None
        self.running = True
        self.last_invoice = None  # Para almacenar la última factura recibida
        
        # Auto-registrar driver en la base de datos si está disponible
        if db_path and Database:
            self._register_in_database(db_path)
        
        # Inicializar consumidor de telemetría si Kafka está disponible
        if kafka_bootstrap:
            try:
                self.consumer_telemetry = bus.BusConsumer(
                    bootstrap=kafka_bootstrap,
                    group_id=f"driver-{driver_id}-grp",
                    topics=[bus.topic_telemetry()],
                )
                self.consumer_telemetry.start(on_message=self._on_telemetry)
                logger.info("Driver {} conectado a telemetría Kafka", driver_id)
            except Exception as e:
                logger.warning("No se pudo conectar a Kafka telemetría: {}", e)
                self.consumer_telemetry = None
            
            # Inicializar consumidor de facturas
            try:
                self.consumer_invoices = bus.BusConsumer(
                    bootstrap=kafka_bootstrap,
                    group_id=f"driver-{driver_id}-invoices-grp",
                    topics=[bus.topic_invoices()],
                )
                self.consumer_invoices.start(on_message=self._on_invoice)
                logger.info("Driver {} conectado a facturas Kafka", driver_id)
            except Exception as e:
                logger.warning("No se pudo conectar a Kafka facturas: {}", e)
                self.consumer_invoices = None
    
    def _register_in_database(self, db_path: str):
        """Registrar driver en la base de datos si no existe"""
        try:
            db = Database(db_path)
            # Intentar obtener el driver de la BD
            existing = db._execute_query(
                "SELECT driver_id FROM drivers WHERE driver_id = ?",
                (self.driver_id,)
            )
            
            if not existing:
                # Driver no existe, registrarlo
                db.upsert_driver(
                    driver_id=self.driver_id,
                    name=f"Driver {self.driver_id}"
                )
                logger.info("✅ Driver {} registrado en la base de datos", self.driver_id)
            else:
                logger.debug("Driver {} ya existe en la base de datos", self.driver_id)
        except Exception as e:
            logger.warning("No se pudo registrar driver en BD: {}", e)

    def _on_telemetry(self, payload: dict, _raw_msg):
        """Procesar telemetría solo del CP que nos está suministrando"""
        try:
            cp_id = payload.get("cp_id")
            if cp_id != self.state.current_cp:
                return  # Ignorar telemetría de otros CPs
            
            driver_id = payload.get("driver_id")
            if driver_id != self.driver_id:
                return  # No es para nosotros
            
            kw = payload.get("kw", 0.0)
            eur = payload.get("eur", 0.0)
            
            self.state.last_kw = kw
            self.state.last_eur = eur
            # Acumular consumo en kWh (aproximadamente kW/3600 por segundo de telemetría)
            self.state.last_kwh += kw / 3600.0
            
            # Mostrar telemetría en pantalla
            print(f"\n╔═══════════════════════════════════════════════════════════╗")
            print(f"║  🔌 SUMINISTRANDO en {cp_id:20s}              ║")
            print(f"║  ⚡ Potencia: {kw:6.2f} kW                                  ║")
            print(f"║  📊 Consumo:  {self.state.last_kwh:6.3f} kWh                           ║")
            print(f"║  💰 Importe:  {eur:6.4f} €                                  ║")
            print(f"╚═══════════════════════════════════════════════════════════╝")
            
        except Exception as e:
            logger.warning("Error procesando telemetría: {}", e)

    def _on_invoice(self, payload: dict, _raw_msg):
        """Procesar factura/ticket recibido via Kafka"""
        try:
            driver_id = payload.get("driver_id")
            if driver_id != self.driver_id:
                return  # No es para nosotros
            
            cp_id = payload.get("cp_id")
            total_kw = payload.get("total_kw", 0.0)
            total_eur = payload.get("total_eur", 0.0)
            
            # Almacenar la factura
            self.last_invoice = {
                "cp_id": cp_id,
                "total_kw": total_kw,
                "total_eur": total_eur
            }
            
            # Mostrar ticket en pantalla
            print(f"\n")
            print(f"╔═══════════════════════════════════════════════════════════╗")
            print(f"║                   🧾 TICKET DE PAGO                       ║")
            print(f"╠═══════════════════════════════════════════════════════════╣")
            print(f"║  Driver:     {self.driver_id:40s}    ║")
            print(f"║  CP:         {cp_id:40s}    ║")
            print(f"║  Consumo:    {total_kw:6.2f} kW                                      ║")
            print(f"║  TOTAL:      {total_eur:6.4f} €                                      ║")
            print(f"╚═══════════════════════════════════════════════════════════╝")
            print(f"\n")
            
            logger.info("Factura recibida via Kafka: {:.2f} kW, {:.4f} €", total_kw, total_eur)
            
        except Exception as e:
            logger.warning("Error procesando factura: {}", e)

    def _send_to_central(self, message: str, timeout: float = 5.0) -> str:
        """Enviar mensaje a CENTRAL con protocolo STX-ETX-LRC y recibir respuesta"""
        try:
            with socket.create_connection(self.central_addr, timeout=timeout) as s:
                # Enviar mensaje con protocolo
                success = ProtocolMessage.send_with_protocol(s, message, wait_ack=True, timeout=timeout)
                if not success:
                    logger.error("CENTRAL no envió ACK o timeout")
                    return "ERROR#NO_ACK"
                
                # Recibir respuesta con protocolo
                response, valid = ProtocolMessage.receive_with_protocol(s, send_ack=True, timeout=timeout)
                
                if not valid:
                    logger.error("Respuesta de CENTRAL corrupta (LRC inválido)")
                    return "ERROR#CORRUPTED"
                
                return response
                
        except Exception as e:
            logger.error("Error comunicando con CENTRAL: {}", e)
            return f"ERROR#{e}"

    def request_service(self, cp_id: str) -> bool:
        """
        Solicitar autorización de suministro en un CP
        Retorna True si fue autorizado, False en caso contrario
        """
        print(f"\n┌─────────────────────────────────────────────────────────┐")
        print(f"│ 📱 Solicitando servicio en {cp_id:26s} │")
        print(f"└─────────────────────────────────────────────────────────┘")
        
        # Enviar solicitud a CENTRAL
        message = f"REQ#{self.driver_id}#{cp_id}"
        logger.info("Enviando a CENTRAL: {}", message)
        
        response = self._send_to_central(message)
        logger.info("Respuesta de CENTRAL: {}", response)
        
        parts = response.split("#")
        
        if parts[0] == "AUTH_GRANTED":
            # Verificar si es una reconexión
            is_reconnect = len(parts) > 3 and parts[3] == "RECONNECT"
            
            if is_reconnect:
                # Reconexión a carga existente
                self.state.current_cp = cp_id
                self.state.charging = True
                # Mantener los valores actuales de kW y EUR (se actualizarán por telemetría)
                
                print(f"\n🔄 RECONEXIÓN A CARGA ACTIVA")
                print(f"   CP: {cp_id}")
                print(f"   Última potencia: {self.state.last_kw:.2f} kW")
                print(f"   Importe acumulado: {self.state.last_eur:.4f} €")
                print(f"   Puedes continuar cargando o FINALIZAR para pagar\n")
                
            else:
                # Nueva autorización
                self.state.current_cp = cp_id
                self.state.charging = True
                self.state.last_kw = 0.0
                self.state.last_eur = 0.0
                self.state.last_kwh = 0.0
                
                print(f"\n✅ AUTORIZACIÓN CONCEDIDA")
                print(f"   CP: {cp_id}")
                print(f"   Esperando inicio de suministro...")
                print(f"   (El CP debe iniciar el suministro manualmente)\n")
            
            return True
            
        elif parts[0] == "AUTH_DENIED":
            reason = parts[1] if len(parts) > 1 else "UNKNOWN"
            print(f"\n❌ AUTORIZACIÓN DENEGADA")
            print(f"   CP: {cp_id}")
            print(f"   Motivo: {reason}")
            
            reasons_map = {
                "DISCONNECTED": "El punto de recarga está desconectado",
                "FAULT": "El punto de recarga está averiado",
                "BUSY": "El punto de recarga está ocupado",
                "OUT_OF_ORDER": "El punto de recarga está fuera de servicio",
                "CP_NOT_FOUND": "El punto de recarga NO EXISTE en el sistema",
            }
            
            if reason in reasons_map:
                print(f"   Detalle: {reasons_map[reason]}\n")
            
            return False
        else:
            print(f"\n⚠️  RESPUESTA INESPERADA DE CENTRAL: {response}\n")
            return False

    def finish_service(self, cp_id: str):
        """Notificar a CENTRAL que el suministro ha finalizado"""
        if not self.state.charging or self.state.current_cp != cp_id:
            logger.warning("Intento de finalizar servicio sin estar cargando")
            return (0.0, 0.0)
        
        # Guardar valores actuales
        final_kw = self.state.last_kw
        final_eur = self.state.last_eur
        
        message = f"FINISH#{cp_id}#{self.driver_id}"
        logger.info("Enviando a CENTRAL: {}", message)
        
        response = self._send_to_central(message)
        logger.info("Respuesta de CENTRAL: {}", response)
        
        if response == "ACK":
            # Esperar un poco a la factura de Kafka (si está disponible)
            if self.consumer_invoices:
                print(f"\n⏳ Esperando factura desde CENTRAL via Kafka...")
                time.sleep(2)  # Esperar hasta 2 segundos
                
                # Si recibimos factura por Kafka, usar esos valores
                if self.last_invoice and self.last_invoice.get("cp_id") == cp_id:
                    final_kw = self.last_invoice["total_kw"]
                    final_eur = self.last_invoice["total_eur"]
                    self.last_invoice = None  # Limpiar
                    print(f"✅ Factura recibida correctamente\n")
                else:
                    print(f"⚠️  No se recibió factura por Kafka, usando valores locales\n")
            
            print(f"╔═══════════════════════════════════════════════════════════╗")
            print(f"║  ✅ SUMINISTRO FINALIZADO                                  ║")
            print(f"║                                                           ║")
            print(f"║  CP:       {cp_id:20s}                        ║")
            print(f"║  Consumo:  {final_kw:6.2f} kW                             ║")
            print(f"║  Total:    {final_eur:6.4f} €                             ║")
            print(f"╚═══════════════════════════════════════════════════════════╝\n")
            
            # Cambiar estado: ya no está cargando pero espera pago
            self.state.charging = False
            self.state.finished_waiting_payment = True
            # NO resetear last_kw, last_eur ni current_cp todavía
        
        return (final_kw, final_eur)
    
    def pay_service(self):
        """Confirmar pago y resetear completamente el estado"""
        if not self.state.finished_waiting_payment:
            logger.warning("Intento de pagar sin haber finalizado servicio")
            return
        
        print(f"\n💳 PAGO CONFIRMADO - Sesión completada")
        
        # Resetear completamente el estado
        self.state.finished_waiting_payment = False
        self.state.current_cp = None
        self.state.last_kw = 0.0
        self.state.last_eur = 0.0
        self.state.last_kwh = 0.0

    def run_from_file(self, filepath: str):
        """
        Leer archivo con IDs de CPs y solicitar suministros automáticamente
        Espera 4 segundos entre cada suministro
        """
        if not os.path.exists(filepath):
            print(f"❌ Error: El archivo {filepath} no existe")
            return
        
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║  📄 MODO AUTOMÁTICO - Leyendo archivo                     ║")
        print(f"║  Archivo: {os.path.basename(filepath):40s}    ║")
        print(f"╚═══════════════════════════════════════════════════════════╝\n")
        
        cp_ids: List[str] = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        cp_ids.append(line)
        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")
            return
        
        if not cp_ids:
            print("⚠️  El archivo está vacío o no contiene CPs válidos")
            return
        
        print(f"📋 Se solicitarán {len(cp_ids)} suministros:\n")
        for i, cp_id in enumerate(cp_ids, 1):
            print(f"   {i}. {cp_id}")
        print()
        
        # Procesar cada CP del archivo
        for i, cp_id in enumerate(cp_ids, 1):
            if not self.running:
                break
            
            print(f"\n{'═'*60}")
            print(f"  SERVICIO {i}/{len(cp_ids)}")
            print(f"{'═'*60}")
            
            # Solicitar autorización
            granted = self.request_service(cp_id)
            
            if granted:
                # Simular que el conductor espera el suministro
                # En un caso real, el CP debe iniciar el suministro y el conductor
                # recibiría telemetría. Aquí simulamos una espera
                print("⏳ Esperando a que el CP inicie el suministro...")
                print("   (Presiona Ctrl+C para saltar al siguiente)\n")
                
                try:
                    # Esperar un tiempo razonable (en producción esperaríamos señal del CP)
                    time.sleep(8)
                except KeyboardInterrupt:
                    print("\n⏭️  Saltando al siguiente servicio...")
                
                # Finalizar servicio
                self.finish_service(cp_id)
            
            # Esperar 4 segundos antes del siguiente (si no es el último)
            if i < len(cp_ids):
                print(f"⏰ Esperando 4 segundos antes del siguiente suministro...")
                try:
                    time.sleep(4)
                except KeyboardInterrupt:
                    print("\n🛑 Proceso interrumpido por el usuario")
                    break
        
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║  ✅ PROCESO AUTOMÁTICO COMPLETADO                          ║")
        print(f"║  Total de suministros procesados: {len(cp_ids):2d}                     ║")
        print(f"╚═══════════════════════════════════════════════════════════╝\n")

    def run_interactive(self):
        """Modo interactivo con menú"""
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║  🚗 EV_DRIVER - Aplicación del Conductor                  ║")
        print(f"║  Driver ID: {self.driver_id:40s}    ║")
        print(f"╚═══════════════════════════════════════════════════════════╝\n")
        
        while self.running:
            print("\n┌─────────────────────────────────────────────────────────┐")
            print("│  MENÚ PRINCIPAL                                         │")
            print("├─────────────────────────────────────────────────────────┤")
            print("│  1. Solicitar suministro en un CP                       │")
            print("│  2. Finalizar suministro actual                         │")
            print("│  3. Ver estado actual                                   │")
            print("│  4. Salir                                               │")
            print("└─────────────────────────────────────────────────────────┘")
            
            try:
                choice = input("\n👉 Opción: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n")
                break
            
            if choice == "1":
                cp_id = input("  Introduce el ID del CP: ").strip()
                if cp_id:
                    self.request_service(cp_id)
                else:
                    print("  ⚠️  ID de CP no puede estar vacío")
            
            elif choice == "2":
                if self.state.charging and self.state.current_cp:
                    self.finish_service(self.state.current_cp)
                else:
                    print("  ⚠️  No hay ningún suministro activo")
            
            elif choice == "3":
                self._show_status()
            
            elif choice == "4":
                # Verificar si está cargando antes de salir
                if self.state.charging and self.state.current_cp:
                    print("\n  ⚠️  NO PUEDES SALIR mientras estás cargando!")
                    print(f"     Debes finalizar el suministro en {self.state.current_cp} primero (opción 2)")
                else:
                    print("\n👋 Saliendo...")
                    self.running = False
                    break
            
            else:
                print("  ⚠️  Opción no válida")

    def _show_status(self):
        """Mostrar estado actual del conductor"""
        print(f"\n┌─────────────────────────────────────────────────────────┐")
        print(f"│  📊 ESTADO ACTUAL                                        │")
        print(f"├─────────────────────────────────────────────────────────┤")
        print(f"│  Driver ID: {self.driver_id:40s} │")
        print(f"│  Estado:    {'🔌 CARGANDO' if self.state.charging else '⏸️  EN ESPERA':40s} │")
        
        if self.state.charging and self.state.current_cp:
            print(f"│  CP Actual: {self.state.current_cp:40s} │")
            print(f"│  Potencia:  {self.state.last_kw:6.2f} kW{' ':30s} │")
            print(f"│  Importe:   {self.state.last_eur:6.4f} €{' ':31s} │")
        
        print(f"└─────────────────────────────────────────────────────────┘")


def main():
    ap = argparse.ArgumentParser(
        prog="EV_Driver",
        description="Aplicación del conductor para solicitar suministros de recarga"
    )
    ap.add_argument("--driver-id", required=True, help="ID único del conductor")
    ap.add_argument("--central-host", required=True, help="Host de CENTRAL")
    ap.add_argument("--central-port", type=int, required=True, help="Puerto de CENTRAL")
    ap.add_argument("--kafka-bootstrap", help="host:port de Kafka (opcional)")
    ap.add_argument("--file", help="Archivo con IDs de CPs para modo automático")
    args = ap.parse_args()
    
    driver = Driver(
        driver_id=args.driver_id,
        central_host=args.central_host,
        central_port=args.central_port,
        kafka_bootstrap=args.kafka_bootstrap,
    )
    
    try:
        if args.file:
            # Modo automático: leer del archivo
            driver.run_from_file(args.file)
        else:
            # Modo interactivo
            driver.run_interactive()
    except KeyboardInterrupt:
        print("\n\n🛑 Aplicación interrumpida por el usuario")
    finally:
        driver.running = False
        if driver.consumer_telemetry:
            driver.consumer_telemetry.stop()
        if driver.consumer_invoices:
            driver.consumer_invoices.stop()
        logger.info("Driver {} finalizado", args.driver_id)


if __name__ == "__main__":
    main()
