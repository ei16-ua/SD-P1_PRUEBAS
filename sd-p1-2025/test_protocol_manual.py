#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test manual del protocolo - Paso a paso con pausas
Permite verificar cada componente individualmente
"""

import socket
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from UTILS.protocol import ProtocolMessage

def test_central_alive():
    """Verifica si CENTRAL está escuchando en el puerto"""
    print("\n" + "="*60)
    print("TEST 0: ¿Está CENTRAL corriendo?")
    print("="*60)
    
    HOST = "localhost"
    PORT = 8888
    
    try:
        print(f"Intentando conectar a {HOST}:{PORT}...")
        sock = socket.create_connection((HOST, PORT), timeout=3.0)
        print("✅ CENTRAL está corriendo y acepta conexiones")
        sock.close()
        return True
    except ConnectionRefusedError:
        print("❌ CENTRAL NO está corriendo")
        print("\n💡 SOLUCIÓN:")
        print("   Abre otra terminal y ejecuta:")
        print("   python src\\EV_Central\\EV_Central.py --host 127.0.0.1 --port 8888")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_protocol_encoding():
    """Test básico de codificación del protocolo"""
    print("\n" + "="*60)
    print("TEST 1: Codificación/Decodificación del Protocolo")
    print("="*60)
    
    test_cases = [
        "REQ#DRIVER1#ALC1",
        "AUTH#ALC1",
        "FINISH#ALC1#DRIVER1"
    ]
    
    all_ok = True
    for msg in test_cases:
        encoded = ProtocolMessage.encode(msg)
        decoded, valid = ProtocolMessage.decode(encoded[:-1])  # quitar \n
        
        if decoded == msg and valid:
            print(f"✅ '{msg}' → OK")
        else:
            print(f"❌ '{msg}' → FALLÓ")
            all_ok = False
    
    return all_ok


def test_simple_request():
    """Test simple: enviar REQ y recibir respuesta"""
    print("\n" + "="*60)
    print("TEST 2: Comunicación Básica con CENTRAL")
    print("="*60)
    
    HOST = "localhost"
    PORT = 8888
    
    try:
        print(f"\n1. Conectando a {HOST}:{PORT}...")
        sock = socket.create_connection((HOST, PORT), timeout=5.0)
        print("   ✅ Conectado")
        
        # Enviar REQ
        message = "REQ#TEST_DRIVER#ALC1"
        print(f"\n2. Enviando: {message}")
        
        # Codificar manualmente para mostrar
        encoded = ProtocolMessage.encode(message)
        print(f"   Bytes enviados: {len(encoded)}")
        print(f"   STX={hex(encoded[0])}, ETX={hex(encoded[-3])}, LRC={hex(encoded[-2])}")
        
        # Enviar con protocolo
        success = ProtocolMessage.send_with_protocol(sock, message, wait_ack=True, timeout=5.0)
        
        if not success:
            print("   ❌ No se recibió ACK del CENTRAL")
            sock.close()
            return False
        
        print("   ✅ ACK recibido del CENTRAL")
        
        # Recibir respuesta
        print("\n3. Esperando respuesta...")
        response, valid = ProtocolMessage.receive_with_protocol(sock, send_ack=True, timeout=5.0)
        
        if valid and response:
            print(f"   ✅ Respuesta: {response}")
            print(f"   ✅ LRC válido")
        else:
            print("   ❌ Respuesta inválida o timeout")
            sock.close()
            return False
        
        sock.close()
        print("\n✅ TEST 2 COMPLETADO")
        return True
        
    except socket.timeout:
        print("   ❌ TIMEOUT - El CENTRAL no respondió a tiempo")
        print("\n💡 Posibles causas:")
        print("   - CENTRAL está procesando pero muy lento")
        print("   - CENTRAL no está usando el protocolo STX-ETX-LRC")
        print("   - Firewall bloqueando la conexión")
        return False
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "🔍"*30)
    print("DIAGNÓSTICO DEL PROTOCOLO STX-ETX-LRC")
    print("🔍"*30)
    
    # Test 0: ¿CENTRAL vivo?
    if not test_central_alive():
        print("\n❌ ABORTANDO: CENTRAL no está corriendo")
        sys.exit(1)
    
    input("\nPresiona ENTER para continuar...")
    
    # Test 1: Protocolo básico
    if not test_protocol_encoding():
        print("\n❌ ABORTANDO: Protocolo básico falló")
        sys.exit(1)
    
    input("\nPresiona ENTER para continuar...")
    
    # Test 2: Comunicación con CENTRAL
    if not test_simple_request():
        print("\n❌ TEST FALLÓ")
        print("\n📋 CHECKLIST DE VERIFICACIÓN:")
        print("   [ ] ¿CENTRAL está corriendo?")
        print("   [ ] ¿CENTRAL tiene el código actualizado con protocol.py?")
        print("   [ ] ¿El puerto 8888 está libre?")
        print("   [ ] ¿Firewall permite conexiones locales?")
        sys.exit(1)
    
    print("\n" + "🎉"*30)
    print("TODOS LOS TESTS PASARON")
    print("🎉"*30)
    print("\n✅ El protocolo STX-ETX-LRC está funcionando correctamente")
    print("✅ La comunicación con CENTRAL es exitosa")


if __name__ == "__main__":
    main()
