#!/usr/bin/env python3
"""
Test del protocolo STX-ETX-LRC
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'UTILS'))

from protocol import ProtocolMessage

def test_encode_decode():
    """Test básico de codificación y decodificación"""
    print("=" * 60)
    print("TEST 1: Codificación y Decodificación")
    print("=" * 60)
    
    # Test 1: Mensaje simple
    message = "REQ#DRIVER1#ALC3"
    encoded = ProtocolMessage.encode(message)
    
    print(f"Original: {message}")
    print(f"Codificado (hex): {encoded.hex()}")
    print(f"Codificado (repr): {repr(encoded)}")
    
    decoded, valid = ProtocolMessage.decode(encoded)
    print(f"Decodificado: {decoded}")
    print(f"Válido: {'✅' if valid else '❌'}")
    print()
    
    assert decoded == message, "El mensaje decodificado no coincide"
    assert valid, "El mensaje debería ser válido"
    print("✅ Test 1 PASADO\n")

def test_corrupted_message():
    """Test con mensaje corrupto"""
    print("=" * 60)
    print("TEST 2: Mensaje Corrupto")
    print("=" * 60)
    
    message = "REQ#DRIVER1#ALC3"
    encoded = ProtocolMessage.encode(message)
    
    # Corromper el mensaje (cambiar un byte del DATA)
    corrupted = bytearray(encoded)
    corrupted[5] = (corrupted[5] + 1) % 256  # Modificar un byte
    corrupted = bytes(corrupted)
    
    print(f"Original: {encoded.hex()}")
    print(f"Corrupto: {corrupted.hex()}")
    
    decoded, valid = ProtocolMessage.decode(corrupted)
    print(f"Decodificado: {decoded}")
    print(f"Válido: {'✅' if valid else '❌'}")
    
    assert not valid, "El mensaje corrupto debería ser inválido"
    print("✅ Test 2 PASADO (detectó corrupción)\n")

def test_multiple_messages():
    """Test con varios tipos de mensajes"""
    print("=" * 60)
    print("TEST 3: Múltiples Tipos de Mensajes")
    print("=" * 60)
    
    messages = [
        "ENQ#ALC3",
        "FAULT#MAD2#OVERHEAT",
        "REQ#DANTE#COR1",
        "AUTH_GRANTED#ALC3#DRIVER1",
        "FINISH#ALC3#DRIVER1",
        "START_CHARGE#ALC3#DRIVER1",
    ]
    
    for msg in messages:
        encoded = ProtocolMessage.encode(msg)
        decoded, valid = ProtocolMessage.decode(encoded)
        
        status = "✅" if (decoded == msg and valid) else "❌"
        print(f"{status} {msg:40s} -> {decoded:40s} [válido: {valid}]")
        
        assert decoded == msg and valid, f"Falló para: {msg}"
    
    print("\n✅ Test 3 PASADO\n")

def test_special_characters():
    """Test con caracteres especiales"""
    print("=" * 60)
    print("TEST 4: Caracteres Especiales")
    print("=" * 60)
    
    messages = [
        "MSG#Usuario con espacios#CP con-guiones",
        "DATA#Tilde:José#Ñoño",
        "INFO#Precio:2.50€/kWh",
    ]
    
    for msg in messages:
        encoded = ProtocolMessage.encode(msg)
        decoded, valid = ProtocolMessage.decode(encoded)
        
        status = "✅" if (decoded == msg and valid) else "❌"
        print(f"{status} {decoded} [válido: {valid}]")
        
        assert decoded == msg and valid, f"Falló para: {msg}"
    
    print("\n✅ Test 4 PASADO\n")

def test_ack_nack():
    """Test de ACK/NACK"""
    print("=" * 60)
    print("TEST 5: ACK/NACK")
    print("=" * 60)
    
    print(f"ACK byte: {ProtocolMessage.ACK.hex()} ({repr(ProtocolMessage.ACK)})")
    print(f"NACK byte: {ProtocolMessage.NACK.hex()} ({repr(ProtocolMessage.NACK)})")
    
    assert ProtocolMessage.is_ack(ProtocolMessage.ACK), "is_ack debería detectar ACK"
    assert ProtocolMessage.is_nack(ProtocolMessage.NACK), "is_nack debería detectar NACK"
    assert not ProtocolMessage.is_ack(ProtocolMessage.NACK), "is_ack no debería detectar NACK"
    
    print("✅ Test 5 PASADO\n")

def test_lrc_calculation():
    """Test del cálculo de LRC"""
    print("=" * 60)
    print("TEST 6: Cálculo de LRC")
    print("=" * 60)
    
    # Ejemplo conocido
    message = "HELLO"
    data = message.encode('utf-8')
    
    # Calcular LRC manualmente
    lrc = 0
    for byte in data:
        lrc ^= byte
    
    print(f"Mensaje: {message}")
    print(f"Bytes: {[hex(b) for b in data]}")
    print(f"LRC calculado: {hex(lrc)}")
    
    # Codificar y verificar
    encoded = ProtocolMessage.encode(message)
    etx_pos = encoded.index(b'\x03')
    received_lrc = encoded[etx_pos + 1]
    
    print(f"LRC en mensaje codificado: {hex(received_lrc)}")
    
    assert lrc == received_lrc, "El LRC calculado no coincide"
    print("✅ Test 6 PASADO\n")

if __name__ == "__main__":
    print("\n" + "🔬 PRUEBAS DEL PROTOCOLO STX-ETX-LRC ".center(60, "=") + "\n")
    
    try:
        test_encode_decode()
        test_corrupted_message()
        test_multiple_messages()
        test_special_characters()
        test_ack_nack()
        test_lrc_calculation()
        
        print("=" * 60)
        print("🎉 TODOS LOS TESTS PASARON".center(60))
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
