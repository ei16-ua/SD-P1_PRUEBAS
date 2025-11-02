#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_central.py
Pruebas simples para validar el protocolo TCP de CENTRAL sin necesidad de Kafka.
"""

import socket
import time
import threading
import sys
import os

# Para poder importar EV_Central
sys.path.insert(0, os.path.dirname(__file__))

def send_and_receive(host: str, port: int, message: str) -> str:
    """Envía un mensaje a CENTRAL y devuelve la respuesta."""
    try:
        with socket.create_connection((host, port), timeout=2.0) as s:
            s.sendall((message + "\n").encode())
            response = s.recv(1024).decode().strip()
            return response
    except Exception as e:
        return f"ERROR: {e}"


def run_tests(host="127.0.0.1", port=9099):
    """Ejecuta una batería de pruebas contra CENTRAL."""
    
    print("=" * 60)
    print("PRUEBAS DE CENTRAL - Protocolo TCP")
    print("=" * 60)
    
    # Esperar un momento para que CENTRAL esté listo
    time.sleep(0.5)
    
    # TEST 1: AUTH - Registrar un CP
    print("\n[TEST 1] AUTH - Registrar CP01")
    resp = send_and_receive(host, port, "AUTH#CP01")
    print(f"  Enviado: AUTH#CP01")
    print(f"  Respuesta: {resp}")
    assert resp == "ACK", f"Se esperaba ACK, recibido: {resp}"
    print("  ✓ PASADO")
    
    # TEST 2: REQ - Solicitar autorización (debería concederse)
    print("\n[TEST 2] REQ - Solicitar autorización para driver1 en CP01")
    resp = send_and_receive(host, port, "REQ#driver1#CP01")
    print(f"  Enviado: REQ#driver1#CP01")
    print(f"  Respuesta: {resp}")
    assert resp.startswith("AUTH_GRANTED"), f"Se esperaba AUTH_GRANTED, recibido: {resp}"
    print("  ✓ PASADO")
    
    # TEST 3: REQ - Solicitar en CP ocupado (debería denegarse)
    print("\n[TEST 3] REQ - Solicitar en CP01 ocupado (driver2)")
    resp = send_and_receive(host, port, "REQ#driver2#CP01")
    print(f"  Enviado: REQ#driver2#CP01")
    print(f"  Respuesta: {resp}")
    assert resp.startswith("AUTH_DENIED#BUSY"), f"Se esperaba AUTH_DENIED#BUSY, recibido: {resp}"
    print("  ✓ PASADO")
    
    # TEST 4: FINISH - Terminar la carga
    print("\n[TEST 4] FINISH - Terminar carga de driver1 en CP01")
    resp = send_and_receive(host, port, "FINISH#CP01#driver1")
    print(f"  Enviado: FINISH#CP01#driver1")
    print(f"  Respuesta: {resp}")
    assert resp == "ACK", f"Se esperaba ACK, recibido: {resp}"
    print("  ✓ PASADO")
    
    # TEST 5: FAULT - Reportar avería
    print("\n[TEST 5] FAULT - Reportar avería en CP01")
    resp = send_and_receive(host, port, "FAULT#CP01#ENGINE_TIMEOUT")
    print(f"  Enviado: FAULT#CP01#ENGINE_TIMEOUT")
    print(f"  Respuesta: {resp}")
    assert resp == "ACK", f"Se esperaba ACK, recibido: {resp}"
    print("  ✓ PASADO")
    
    # TEST 6: REQ en CP averiado (debería denegarse)
    print("\n[TEST 6] REQ - Solicitar en CP01 averiado")
    resp = send_and_receive(host, port, "REQ#driver3#CP01")
    print(f"  Enviado: REQ#driver3#CP01")
    print(f"  Respuesta: {resp}")
    assert resp.startswith("AUTH_DENIED#FAULT"), f"Se esperaba AUTH_DENIED#FAULT, recibido: {resp}"
    print("  ✓ PASADO")
    
    # TEST 7: AUTH otro CP
    print("\n[TEST 7] AUTH - Registrar CP02")
    resp = send_and_receive(host, port, "AUTH#CP02")
    print(f"  Enviado: AUTH#CP02")
    print(f"  Respuesta: {resp}")
    assert resp == "ACK", f"Se esperaba ACK, recibido: {resp}"
    print("  ✓ PASADO")
    
    # TEST 8: REQ en CP desconocido (debería crear el CP y conceder si está OK)
    print("\n[TEST 8] REQ - Solicitar en CP03 (no registrado previamente)")
    resp = send_and_receive(host, port, "REQ#driver4#CP03")
    print(f"  Enviado: REQ#driver4#CP03")
    print(f"  Respuesta: {resp}")
    # Como CP03 no está conectado, debería denegar
    assert resp.startswith("AUTH_DENIED#DISCONNECTED"), f"Se esperaba AUTH_DENIED#DISCONNECTED, recibido: {resp}"
    print("  ✓ PASADO")
    
    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS PASARON ✓")
    print("=" * 60)


def start_central_server():
    """Inicia el servidor CENTRAL en un hilo separado."""
    import EV_Central
    
    # Modificar argumentos para el test
    sys.argv = ["EV_Central.py", "--host", "127.0.0.1", "--port", "9099"]
    
    def _run():
        try:
            EV_Central.main()
        except KeyboardInterrupt:
            pass
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    
    # Esperar a que el servidor esté listo
    time.sleep(1.5)
    
    return thread


if __name__ == "__main__":
    print("Iniciando servidor CENTRAL para pruebas...")
    
    # Limpiar DB si existe para empezar fresco
    db_path = os.path.join(os.path.dirname(__file__), "cp_db.json")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"DB limpiada: {db_path}")
    
    # Iniciar servidor
    server_thread = start_central_server()
    
    try:
        # Ejecutar pruebas
        run_tests()
    except AssertionError as e:
        print(f"\n✗ PRUEBA FALLIDA: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\nPresiona Ctrl+C para cerrar el servidor de pruebas...")
        try:
            # Mantener el servidor corriendo para inspección manual si se desea
            time.sleep(2)
        except KeyboardInterrupt:
            print("Cerrando...")
