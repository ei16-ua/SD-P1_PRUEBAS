#!/usr/bin/env python3
"""EV_Driver with Web GUI

Driver web-based para solicitar suministros de recarga.
Usa SimpleHTTPRequestHandler (Python stdlib) sin dependencias externas.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

# Añadir paths para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EV_Driver import Driver, DriverState

try:
    from loguru import logger
except Exception:
    class _L:
        def info(self, *a, **k): print("[INFO]", *a)
        def warning(self, *a, **k): print("[WARN]", *a)
        def error(self, *a, **k): print("[ERROR]", *a)
        def debug(self, *a, **k): print("[DEBUG]", *a)
    logger = _L()


# Global state
driver_instance: Driver = None
messages_log: List[dict] = []
available_cps: List[dict] = []
WEB_DIR = Path(__file__).parent / "web"


class DriverHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP Handler que sirve archivos estáticos y API REST"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/state':
            self.send_api_state()
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/request':
            self.handle_request_service()
        elif parsed_path.path == '/api/finish':
            self.handle_finish_service()
        elif parsed_path.path == '/api/pay':
            self.handle_pay_service()
        else:
            self.send_error(404)
    
    def send_api_state(self):
        """Send current state as JSON"""
        if not driver_instance:
            data = {
                "state": {
                    "driver_id": "UNKNOWN",
                    "charging": False,
                    "current_cp": None,
                    "last_kw": 0.0,
                    "last_eur": 0.0,
                    "last_kwh": 0.0,
                    "finished_waiting_payment": False
                },
                "cps": [],
                "messages": []
            }
        else:
            data = {
                "state": {
                    "driver_id": driver_instance.driver_id,
                    "charging": driver_instance.state.charging,
                    "current_cp": driver_instance.state.current_cp,
                    "last_kw": driver_instance.state.last_kw,
                    "last_eur": driver_instance.state.last_eur,
                    "last_kwh": driver_instance.state.last_kwh,
                    "finished_waiting_payment": driver_instance.state.finished_waiting_payment
                },
                "cps": available_cps,
                "messages": messages_log[-50:]
            }
        
        # Send JSON response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def handle_request_service(self):
        """Handle service request"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            cp_id = data.get('cp_id')
            
            if not driver_instance or not cp_id:
                self.send_json_response({"success": False, "reason": "Invalid request"})
                return
            
            # Request service
            success = driver_instance.request_service(cp_id)
            
            if success:
                add_message(f"✅ Autorización concedida para {cp_id}", "success")
                self.send_json_response({"success": True})
            else:
                add_message(f"❌ Autorización denegada para {cp_id}", "error")
                self.send_json_response({"success": False, "reason": "Authorization denied"})
                
        except Exception as e:
            logger.error("Error handling request: {}", e)
            self.send_json_response({"success": False, "reason": str(e)})
    
    def handle_finish_service(self):
        """Handle finish service"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            cp_id = data.get('cp_id')
            
            if not driver_instance or not cp_id:
                self.send_json_response({"success": False, "reason": "Invalid request"})
                return
            
            # Finish service
            total_kw, total_eur = driver_instance.finish_service(cp_id)
            
            add_message(f"✅ Carga detenida. Total: {total_kw:.2f} kW, {total_eur:.4f} €", "success")
            
            self.send_json_response({
                "success": True,
                "total_kw": total_kw,
                "total_eur": total_eur
            })
                
        except Exception as e:
            logger.error("Error handling finish: {}", e)
            self.send_json_response({"success": False, "reason": str(e)})
    
    def handle_pay_service(self):
        """Handle pay service"""
        try:
            if not driver_instance:
                self.send_json_response({"success": False, "reason": "Invalid request"})
                return
            
            # Pay service
            driver_instance.pay_service()
            
            add_message("💳 Pago confirmado - Sesión completada", "success")
            
            self.send_json_response({"success": True})
                
        except Exception as e:
            logger.error("Error handling pay: {}", e)
            self.send_json_response({"success": False, "reason": str(e)})
    
    def send_json_response(self, data: dict):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def add_message(text: str, level: str = "info"):
    """Add message to log"""
    global messages_log
    now = datetime.now()
    messages_log.append({
        "time": now.strftime('%H:%M:%S'),
        "text": text,
        "level": level
    })


def update_available_cps():
    """Periodically update available CPs from CENTRAL"""
    global available_cps
    
    # Wait for driver to initialize
    time.sleep(2)
    
    if not driver_instance:
        return
    
    # Build URL for CENTRAL Web API
    central_web_url = f"http://{driver_instance.central_addr[0]}:8000/api/state"
    
    while True:
        try:
            import urllib.request
            import json
            
            # Fetch CP state from CENTRAL Web GUI
            response = urllib.request.urlopen(central_web_url, timeout=3)
            data = json.loads(response.read().decode())
            
            # Extract CP list
            cps = data.get('cps', {})
            available_cps = []
            
            for cp_id, cp_data in cps.items():
                available_cps.append({
                    'cp_id': cp_id,
                    'location': cp_data.get('location', 'Calle'),
                    'connected': cp_data.get('connected', False),
                    'ok': cp_data.get('ok', False),
                    'charging': cp_data.get('charging', False),
                    'stopped_by_central': cp_data.get('stopped_by_central', False),
                    'kw_max': cp_data.get('kw_max', 11.0),
                    'price_eur_kwh': cp_data.get('price_eur_kwh', 0.35)
                })
            
        except Exception as e:
            # Si no puede conectar al CENTRAL Web API, usar lista vacía
            # No es un error crítico, el usuario puede escribir el CP_ID manualmente
            pass
        
        time.sleep(10)  # Update every 10 seconds (reducido la frecuencia)


def run_driver(args):
    """Run the Driver in a separate thread"""
    global driver_instance
    
    driver_instance = Driver(
        driver_id=args.driver_id,
        central_host=args.central_host,
        central_port=args.central_port,
        kafka_bootstrap=args.kafka_bootstrap,
        db_path=args.db_path if hasattr(args, 'db_path') and args.db_path else None
    )
    
    logger.info("Driver {} initialized", args.driver_id)
    add_message(f"Driver {args.driver_id} conectado", "success")
    
    # Keep driver thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Driver stopping...")


def run_http_server(web_port: int):
    """Run simple HTTP server for web GUI"""
    server = HTTPServer(('0.0.0.0', web_port), DriverHTTPHandler)
    logger.info("HTTP server started on port {}", web_port)
    logger.info("Open browser at: http://localhost:{}", web_port)
    server.serve_forever()


def main():
    ap = argparse.ArgumentParser(prog="EV_Driver_Web")
    ap.add_argument("--driver-id", required=True, help="ID único del conductor")
    ap.add_argument("--central-host", required=True, help="Host de CENTRAL")
    ap.add_argument("--central-port", type=int, required=True, help="Puerto de CENTRAL")
    ap.add_argument("--web-port", type=int, default=5000, help="Web GUI port")
    ap.add_argument("--kafka-bootstrap", help="host:port de Kafka (opcional)")
    ap.add_argument("--db-path", default="central.db", help="Ruta a la base de datos (para auto-registro)")
    args = ap.parse_args()
    
    logger.info("Starting EV Driver with Web GUI...")
    logger.info("Driver ID: {}", args.driver_id)
    logger.info("Central: {}:{}", args.central_host, args.central_port)
    logger.info("Web GUI: http://localhost:{}", args.web_port)
    
    # Start Driver in a separate thread
    driver_thread = threading.Thread(target=run_driver, args=(args,), daemon=False)
    driver_thread.start()
    
    # Start CP update thread
    cp_thread = threading.Thread(target=update_available_cps, daemon=True)
    cp_thread.start()
    
    # Give Driver a moment to initialize
    time.sleep(1)
    
    # Start HTTP server
    logger.info("Starting HTTP server on port {}", args.web_port)
    run_http_server(args.web_port)


if __name__ == "__main__":
    main()
