#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de integración del protocolo STX-ETX-LRC
Prueba comunicación CENTRAL ↔ DRIVER con el nuevo protocolo
"""

import socket
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from UTILS.protocol import ProtocolMessage

def test_protocol_with_central():
    """
    Simula un Driver conectándose a CENTRAL con el protocolo
    """
    print("=" * 60)
    print("TEST: Protocolo STX-ETX-LRC con CENTRAL")
    print("=" * 60)
    
    CENTRAL_HOST = "localhost"
    CENTRAL_PORT = 8888
    
    try:
        print(f"\n1. Conectando a CENTRAL en {CENTRAL_HOST}:{CENTRAL_PORT}...")
        sock = socket.create_connection((CENTRAL_HOST, CENTRAL_PORT), timeout=10.0)
        print("   ✓ Conexión establecida")
        
        # Enviar REQ (solicitud de autorización)
        print("\n2. Enviando REQ#DRIVER_TEST#CP01...")
        message = "REQ#DRIVER_TEST#CP01"
        success = ProtocolMessage.send_with_protocol(sock, message, wait_ack=True, timeout=5.0)
        
        if not success:
            print("   ✗ No se recibió ACK del CENTRAL")
            sock.close()
            return False
        
        print("   ✓ CENTRAL envió ACK (protocolo OK)")
        
        # Recibir respuesta (AUTH_GRANTED o AUTH_DENIED)
        print("\n3. Esperando respuesta del CENTRAL...")
        response, valid = ProtocolMessage.receive_with_protocol(sock, send_ack=True, timeout=5.0)
        
        if not valid or response is None:
            print("   ✗ Respuesta inválida o corrupta")
            sock.close()
            return False
        
        print(f"   ✓ Respuesta recibida: {response}")
        print(f"   ✓ LRC válido, ACK enviado automáticamente")
        
        # Si fue GRANTED, enviar FINISH
        if response.startswith("AUTH_GRANTED"):
            print("\n4. Autenticación exitosa! Enviando FINISH...")
            time.sleep(1)
            
            finish_msg = "FINISH#CP01#DRIVER_TEST"
            success = ProtocolMessage.send_with_protocol(sock, finish_msg, wait_ack=True, timeout=5.0)
            
            if not success:
                print("   ✗ No se recibió ACK para FINISH")
                sock.close()
                return False
            
            print("   ✓ FINISH enviado correctamente")
            
            # Recibir ACK final
            ack_response, ack_valid = ProtocolMessage.receive_with_protocol(sock, send_ack=True, timeout=5.0)
            if ack_valid and ack_response:
                print(f"   ✓ Respuesta final: {ack_response}")
        
        sock.close()
        print("\n" + "=" * 60)
        print("✓ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        return True
        
    except ConnectionRefusedError:
        print(f"\n✗ ERROR: CENTRAL no está corriendo en {CENTRAL_HOST}:{CENTRAL_PORT}")
        print("   Ejecuta: start_central.bat")
        return False
    except socket.timeout:
        print("\n✗ ERROR: Timeout esperando respuesta del CENTRAL")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n⚠ IMPORTANTE: Asegúrate de que CENTRAL esté corriendo antes de ejecutar este test")
    print("   Ejecuta: start_central.bat o EV_Central_Web.py\n")
    
    # Check if running with --auto flag
    if "--auto" in sys.argv:
        print("Modo automático activado, conectando directamente...")
        time.sleep(2)  # Esperar 2 segundos para dar tiempo a CENTRAL
    else:
        input("Presiona ENTER cuando CENTRAL esté corriendo...")
    
    success = test_protocol_with_central()
    
    sys.exit(0 if success else 1)
