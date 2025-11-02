#!/usr/bin/env python3
"""EV_Central with Web GUI

Integra el CENTRAL con un servidor web clásico para monitorización en tiempo real.
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
from typing import Dict, List
from urllib.parse import urlparse

# Añadir paths para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from EV_Central import Central, CPRecord

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
central_instance: Central = None
requests_log: List[dict] = []
messages_log: List[dict] = []
WEB_DIR = Path(__file__).parent / "web"


class CentralHTTPHandler(SimpleHTTPRequestHandler):
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
    
    def send_api_state(self):
        """Send current state as JSON"""
        if not central_instance:
            data = {"cps": {}, "requests": [], "messages": []}
        else:
            cps_dict = {}
            with central_instance._db_lock:
                for cp_id, cp in central_instance._db.items():
                    cps_dict[cp_id] = cp.to_dict()
            
            data = {
                "cps": cps_dict,
                "requests": requests_log[-20:],
                "messages": messages_log[-50:]
            }
        
        # Send JSON response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def gui_callback(event_type: str, **kwargs):
    """Callback llamado por Central para notificar eventos"""
    global requests_log, messages_log
    
    try:
        if event_type == 'request':
            # Nueva solicitud de driver
            driver_id = kwargs.get('driver_id')
            cp_id = kwargs.get('cp_id')
            now = datetime.now()
            request_data = {
                'date': now.strftime('%d/%m/%y'),
                'time': now.strftime('%H:%M'),
                'driver_id': str(driver_id),
                'cp_id': cp_id
            }
            requests_log.append(request_data)
            
        elif event_type == 'message':
            # Mensaje del sistema
            message_text = kwargs.get('message', '')
            now = datetime.now()
            msg_data = {
                'time': now.strftime('%H:%M:%S'),
                'text': message_text
            }
            messages_log.append(msg_data)
            
    except Exception as e:
        logger.warning("GUI callback error: {}", e)


def run_central(args):
    """Run the Central server in a separate thread"""
    global central_instance
    
    central_instance = Central(
        host=args.host,
        port=args.port,
        kafka_bootstrap=args.kafka_bootstrap,
        gui_callback=gui_callback
    )
    central_instance.load_db()
    central_instance.start()
    
    logger.info("Central server started on {}:{}", args.host, args.port)
    
    # Keep Central running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Central stopping...")


def run_http_server(web_port: int):
    """Run simple HTTP server for web GUI"""
    server = HTTPServer(('0.0.0.0', web_port), CentralHTTPHandler)
    logger.info("HTTP server started on port {}", web_port)
    logger.info("Open browser at: http://localhost:{}", web_port)
    server.serve_forever()


def main():
    ap = argparse.ArgumentParser(prog="EV_Central_Web")
    ap.add_argument("--host", default="0.0.0.0", help="TCP host for Central")
    ap.add_argument("--port", type=int, default=9099, help="TCP port for Central")
    ap.add_argument("--web-port", type=int, default=8000, help="Web GUI port")
    ap.add_argument("--kafka-bootstrap", help="host:port for Kafka (optional)")
    args = ap.parse_args()
    
    logger.info("Starting EV Central with Web GUI...")
    logger.info("Central TCP: {}:{}", args.host, args.port)
    logger.info("Web GUI: http://localhost:{}", args.web_port)
    
    # Start Central in a separate thread
    central_thread = threading.Thread(target=run_central, args=(args,), daemon=False)
    central_thread.start()
    
    # Give Central a moment to initialize
    time.sleep(2)
    
    # Start HTTP server
    logger.info("Starting HTTP server on port {}", args.web_port)
    run_http_server(args.web_port)


if __name__ == "__main__":
    main()
