#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test completo del protocolo STX-ETX-LRC
Prueba comunicación con CP real: DRIVER → CENTRAL → MONITOR
"""

import socket
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from UTILS.protocol import ProtocolMessage

def test_with_real_cp():
    """
    Test completo con CP real (debe estar ENGINE + MONITOR corriendo)
    """
    print("=" * 70)
    print("TEST COMPLETO: Protocolo STX-ETX-LRC con CP REAL")
    print("=" * 70)
    
    CENTRAL_HOST = "localhost"
    CENTRAL_PORT = 8888
    
    # Usar ALC1 que existe en la BD
    CP_ID = "ALC1"
    DRIVER_ID = "DRIVER_TEST_001"
    
    try:
        print(f"\n📡 FASE 1: DRIVER conectando a CENTRAL")
        print(f"   CP solicitado: {CP_ID}")
        print(f"   Driver ID: {DRIVER_ID}")
        print("=" * 70)
        
        # Conectar a CENTRAL
        print(f"\n1. Conectando a CENTRAL en {CENTRAL_HOST}:{CENTRAL_PORT}...")
        sock = socket.create_connection((CENTRAL_HOST, CENTRAL_PORT), timeout=10.0)
        print("   ✓ Conexión establecida")
        
        # Enviar REQ (solicitud de autorización)
        print(f"\n2. Enviando REQ#{DRIVER_ID}#{CP_ID}...")
        message = f"REQ#{DRIVER_ID}#{CP_ID}"
        
        # Mostrar mensaje en hex para debugging
        encoded = ProtocolMessage.encode(message)
        print(f"   → Mensaje codificado ({len(encoded)} bytes):")
        print(f"     STX={hex(encoded[0])}, DATA='{message}', ETX={hex(encoded[-3])}, LRC={hex(encoded[-2])}")
        
        success = ProtocolMessage.send_with_protocol(sock, message, wait_ack=True, timeout=5.0)
        
        if not success:
            print("   ✗ ERROR: No se recibió ACK del CENTRAL")
            sock.close()
            return False
        
        print("   ✓ CENTRAL envió ACK (mensaje recibido correctamente)")
        
        # Recibir respuesta (AUTH_GRANTED o AUTH_DENIED)
        print("\n3. Esperando respuesta de autorización del CENTRAL...")
        response, valid = ProtocolMessage.receive_with_protocol(sock, send_ack=True, timeout=5.0)
        
        if not valid or response is None:
            print("   ✗ ERROR: Respuesta inválida o corrupta")
            sock.close()
            return False
        
        print(f"   ✓ Respuesta recibida: {response}")
        print(f"   ✓ LRC validado correctamente")
        print(f"   ✓ ACK enviado automáticamente")
        
        # Analizar respuesta
        parts = response.split("#")
        
        if parts[0] == "AUTH_DENIED":
            reason = parts[1] if len(parts) > 1 else "UNKNOWN"
            print(f"\n⚠️  RESULTADO: Autorización DENEGADA")
            print(f"   Razón: {reason}")
            
            reasons_explained = {
                "CP_NOT_FOUND": "El CP no existe en la base de datos",
                "DISCONNECTED": "El CP está desconectado (ENGINE/MONITOR no corriendo)",
                "OUT_OF_ORDER": "El CP fue marcado como fuera de servicio",
                "FAULT": "El CP reportó un fallo",
                "BUSY": "El CP está ocupado con otro driver"
            }
            
            if reason in reasons_explained:
                print(f"   💡 {reasons_explained[reason]}")
                
                if reason == "DISCONNECTED":
                    print(f"\n   🔧 SOLUCIÓN: Ejecuta en otras terminales:")
                    print(f"      Terminal 2: start_engine_{CP_ID.lower()}.bat")
                    print(f"      Terminal 3: start_monitor_{CP_ID.lower()}.bat")
            
            sock.close()
            return reason != "DISCONNECTED"  # Success si no es por desconexión
        
        elif parts[0] == "AUTH_GRANTED":
            print(f"\n✅ RESULTADO: Autorización CONCEDIDA")
            print(f"   CP: {parts[1] if len(parts) > 1 else 'N/A'}")
            print(f"   Driver: {parts[2] if len(parts) > 2 else 'N/A'}")
            
            # Simular carga (esperar un poco)
            print(f"\n📊 FASE 2: Simulando carga...")
            print(f"   (En producción, aquí el driver recibiría telemetría vía Kafka)")
            for i in range(3):
                time.sleep(1)
                print(f"   ... cargando ({i+1}/3)")
            
            # Enviar FINISH
            print(f"\n4. Enviando FINISH#{CP_ID}#{DRIVER_ID}...")
            finish_msg = f"FINISH#{CP_ID}#{DRIVER_ID}"
            
            success = ProtocolMessage.send_with_protocol(sock, finish_msg, wait_ack=True, timeout=5.0)
            
            if not success:
                print("   ✗ ERROR: No se recibió ACK para FINISH")
                sock.close()
                return False
            
            print("   ✓ FINISH enviado correctamente")
            
            # Recibir ACK final
            print("\n5. Esperando confirmación final...")
            ack_response, ack_valid = ProtocolMessage.receive_with_protocol(sock, send_ack=True, timeout=5.0)
            
            if ack_valid and ack_response:
                print(f"   ✓ Respuesta final: {ack_response}")
                print(f"   ✓ Sesión de carga completada")
        
        sock.close()
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print("\n📋 VERIFICACIONES:")
        print("   ✓ Protocolo STX-ETX-LRC funcionando")
        print("   ✓ Double ACK implementado correctamente")
        print("   ✓ Validación LRC activa")
        print("   ✓ Comunicación DRIVER ↔ CENTRAL operativa")
        print("=" * 70)
        return True
        
    except ConnectionRefusedError:
        print(f"\n✗ ERROR: CENTRAL no está corriendo en {CENTRAL_HOST}:{CENTRAL_PORT}")
        print("\n🔧 SOLUCIÓN: Ejecuta en otra terminal:")
        print("   start_central.bat")
        print("   o")
        print("   python src\\EV_Central\\EV_Central_Web.py --host 127.0.0.1 --port 8888")
        return False
        
    except socket.timeout:
        print("\n✗ ERROR: Timeout esperando respuesta del CENTRAL")
        print("   El CENTRAL puede estar sobrecargado o no responde")
        return False
        
    except Exception as e:
        print(f"\n✗ ERROR INESPERADO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_protocol_basic():
    """Test básico del protocolo (sin CP real)"""
    print("\n" + "=" * 70)
    print("TEST BÁSICO: Protocolo STX-ETX-LRC")
    print("=" * 70)
    
    # Test de encoding/decoding
    print("\n1. Test de codificación/decodificación...")
    test_messages = [
        "REQ#DRIVER1#ALC1",
        "AUTH_GRANTED#ALC1#DRIVER1",
        "FINISH#ALC1#DRIVER1",
        "ACK"
    ]
    
    for msg in test_messages:
        encoded = ProtocolMessage.encode(msg)
        decoded, valid = ProtocolMessage.decode(encoded[:-1])  # Quitar \n
        
        if decoded == msg and valid:
            print(f"   ✓ '{msg}' → OK")
        else:
            print(f"   ✗ '{msg}' → ERROR")
            return False
    
    # Test de LRC corruption detection
    print("\n2. Test de detección de corrupción...")
    encoded = ProtocolMessage.encode("TEST_MESSAGE")
    # Corromper el mensaje cambiando un byte
    corrupted = bytearray(encoded)
    corrupted[5] = (corrupted[5] + 1) % 256  # Cambiar un byte de DATA
    
    decoded, valid = ProtocolMessage.decode(bytes(corrupted[:-1]))
    
    if not valid:
        print("   ✓ Corrupción detectada correctamente (LRC inválido)")
    else:
        print("   ✗ ERROR: No se detectó la corrupción")
        return False
    
    print("\n" + "=" * 70)
    print("✅ TEST BÁSICO COMPLETADO")
    print("=" * 70)
    return True


if __name__ == "__main__":
    print("\n" + "🚀 " * 35)
    print("TEST SUITE: Protocolo STX-ETX-LRC")
    print("🚀 " * 35)
    
    # Test 1: Protocolo básico
    print("\n[TEST 1/2] Verificando protocolo básico...")
    if not test_protocol_basic():
        print("\n❌ Test básico falló")
        sys.exit(1)
    
    # Test 2: Integración con CENTRAL
    print("\n[TEST 2/2] Verificando integración con CENTRAL...")
    
    if "--auto" in sys.argv:
        print("Modo automático: esperando 2 segundos...")
        time.sleep(2)
    else:
        print("\n⚠️  Asegúrate de que CENTRAL esté corriendo:")
        print("   Terminal 1: python src\\EV_Central\\EV_Central_Web.py")
        input("\nPresiona ENTER para continuar...")
    
    success = test_with_real_cp()
    
    if success:
        print("\n" + "🎉 " * 35)
        print("TODOS LOS TESTS PASARON")
        print("🎉 " * 35)
        sys.exit(0)
    else:
        print("\n❌ Algunos tests fallaron (revisar logs arriba)")
        sys.exit(1)
