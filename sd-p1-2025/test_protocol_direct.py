#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test SOLO del protocolo - Sin MONITOR, sin ENGINE
Verifica comunicación directa DRIVER → CENTRAL
"""

import socket
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from UTILS.protocol import ProtocolMessage

def test_direct_protocol():
    """
    Test directo del protocolo sin componentes intermedios
    """
    print("\n" + "="*70)
    print("TEST DIRECTO: Protocolo STX-ETX-LRC (Sin MONITOR/ENGINE)")
    print("="*70)
    
    HOST = "localhost"
    PORT = 8888
    
    print("\n📋 Este test verifica:")
    print("   1. Codificación/Decodificación del protocolo")
    print("   2. Conexión al CENTRAL")
    print("   3. Envío de mensajes con STX-ETX-LRC")
    print("   4. Recepción de ACK")
    print("   5. Validación de LRC")
    print("\n" + "="*70)
    
    # Test 1: Protocolo básico
    print("\n[TEST 1/3] Protocolo básico...")
    messages = ["REQ#DRIVER1#ALC1", "AUTH#CP01", "FINISH#CP01#DRIVER1"]
    
    for msg in messages:
        encoded = ProtocolMessage.encode(msg)
        decoded, valid = ProtocolMessage.decode(encoded[:-1])
        if decoded == msg and valid:
            print(f"   ✓ {msg[:20]:20s} → OK")
        else:
            print(f"   ✗ {msg[:20]:20s} → FALLÓ")
            return False
    
    # Test 2: Conexión a CENTRAL
    print("\n[TEST 2/3] Conexión a CENTRAL...")
    try:
        print(f"   Conectando a {HOST}:{PORT}...")
        sock = socket.create_connection((HOST, PORT), timeout=5.0)
        print(f"   ✓ Conexión establecida")
    except ConnectionRefusedError:
        print(f"   ✗ ERROR: CENTRAL no está corriendo en {HOST}:{PORT}")
        print("\n   💡 SOLUCIÓN: En otra terminal ejecuta:")
        print("      python src\\EV_Central\\EV_Central.py --host 127.0.0.1 --port 8888")
        return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    # Test 3: Comunicación completa
    print("\n[TEST 3/3] Comunicación con protocolo...")
    
    try:
        # Enviar REQ para un CP que NO existe (esperamos AUTH_DENIED)
        message = "REQ#DRIVER_TEST#CP_INEXISTENTE"
        print(f"\n   Enviando: {message}")
        
        # Mostrar mensaje codificado
        encoded = ProtocolMessage.encode(message)
        print(f"   → Codificado: {len(encoded)} bytes")
        print(f"      STX={hex(encoded[0])}, ETX={hex(encoded[-3])}, LRC={hex(encoded[-2])}")
        
        # Enviar con protocolo
        print(f"\n   Esperando ACK del CENTRAL...")
        success = ProtocolMessage.send_with_protocol(sock, message, wait_ack=True, timeout=5.0)
        
        if not success:
            print("   ✗ ERROR: No se recibió ACK")
            print("\n   💡 Posibles causas:")
            print("      - CENTRAL no está usando el protocolo STX-ETX-LRC")
            print("      - CENTRAL está corriendo código viejo")
            print("      - Timeout de red")
            sock.close()
            return False
        
        print("   ✓ ACK recibido del CENTRAL")
        
        # Recibir respuesta
        print(f"\n   Esperando respuesta del CENTRAL...")
        response, valid = ProtocolMessage.receive_with_protocol(sock, send_ack=True, timeout=5.0)
        
        if response is None:
            print("   ✗ ERROR: Timeout esperando respuesta")
            print("\n   💡 CENTRAL recibió el mensaje pero no respondió")
            sock.close()
            return False
        
        if not valid:
            print("   ✗ ERROR: Respuesta con LRC inválido (mensaje corrupto)")
            sock.close()
            return False
        
        print(f"   ✓ Respuesta recibida: {response}")
        print(f"   ✓ LRC validado correctamente")
        print(f"   ✓ ACK enviado automáticamente al CENTRAL")
        
        # Analizar respuesta
        if response.startswith("AUTH_DENIED"):
            print("\n   ℹ️  AUTH_DENIED es ESPERADO (el CP no existe)")
            print("      Lo importante es que el protocolo funcionó!")
        elif response.startswith("AUTH_GRANTED"):
            print("\n   ℹ️  AUTH_GRANTED (sorpresa, el CP existe!)")
        
        sock.close()
        return True
        
    except socket.timeout:
        print("   ✗ ERROR: TIMEOUT")
        print("\n   💡 El CENTRAL está corriendo pero no responde")
        print("      Verifica que CENTRAL tenga el código actualizado con protocol.py")
        sock.close()
        return False
    except Exception as e:
        print(f"   ✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sock.close()
        return False


def main():
    print("\n" + "🔬 "*35)
    print("TEST DIRECTO DEL PROTOCOLO STX-ETX-LRC")
    print("🔬 "*35)
    
    print("\n⚠️  REQUISITO: CENTRAL debe estar corriendo")
    print("   Si no lo está, abre otra terminal y ejecuta:")
    print("   python src\\EV_Central\\EV_Central.py --host 127.0.0.1 --port 8888")
    
    if "--auto" not in sys.argv:
        input("\nPresiona ENTER cuando CENTRAL esté corriendo...")
    else:
        print("\nModo automático: esperando 2 segundos...")
        time.sleep(2)
    
    success = test_direct_protocol()
    
    if success:
        print("\n" + "="*70)
        print("✅ TEST EXITOSO - EL PROTOCOLO FUNCIONA CORRECTAMENTE")
        print("="*70)
        print("\n📊 VERIFICADO:")
        print("   ✓ Codificación STX-DATA-ETX-LRC")
        print("   ✓ Envío de mensajes")
        print("   ✓ Recepción de ACK")
        print("   ✓ Validación de LRC")
        print("   ✓ Recepción de respuestas")
        print("   ✓ Double ACK (ida y vuelta)")
        print("\n🎉 El protocolo está implementado correctamente!")
        print("="*70)
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("❌ TEST FALLÓ")
        print("="*70)
        print("\n📋 CHECKLIST:")
        print("   [ ] ¿CENTRAL está corriendo?")
        print("   [ ] ¿CENTRAL tiene src/UTILS/protocol.py?")
        print("   [ ] ¿CENTRAL tiene el código actualizado?")
        print("   [ ] ¿Puerto 8888 está libre?")
        print("\n💡 TIP: Mira los logs del CENTRAL para más detalles")
        print("="*70)
        sys.exit(1)


if __name__ == "__main__":
    main()
