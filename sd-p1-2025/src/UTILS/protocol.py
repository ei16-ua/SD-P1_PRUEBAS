#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
protocol.py
Protocolo estándar STX-DATA-ETX-LRC para comunicación robusta entre módulos
"""

class ProtocolMessage:
    """
    Implementa el protocolo estándar de empaquetado:
    <STX><DATA><ETX><LRC>
    
    STX (Start of Text): 0x02
    ETX (End of Text): 0x03
    ACK (Acknowledge): 0x06
    NACK (Not Acknowledge): 0x15
    LRC (Longitudinal Redundancy Check): XOR de todos los bytes del DATA
    """
    
    STX = b'\x02'
    ETX = b'\x03'
    ACK = b'\x06'
    NACK = b'\x15'
    EOT = b'\x04'  # End of Transmission
    
    @staticmethod
    def encode(message: str) -> bytes:
        """
        Codifica un mensaje con el formato STX-DATA-ETX-LRC
        
        Args:
            message: Mensaje en texto plano (ej: "REQ#DRIVER1#ALC3")
        
        Returns:
            bytes: Mensaje codificado con STX-DATA-ETX-LRC-\n
        """
        data = message.encode('utf-8')
        
        # Calcular LRC (XOR de todos los bytes)
        lrc = 0
        for byte in data:
            lrc ^= byte
        
        # Formato: STX + DATA + ETX + LRC + newline
        return ProtocolMessage.STX + data + ProtocolMessage.ETX + bytes([lrc]) + b'\n'
    
    @staticmethod
    def decode(raw: bytes) -> tuple[str, bool]:
        """
        Decodifica y valida un mensaje con formato STX-DATA-ETX-LRC
        
        Args:
            raw: Bytes recibidos del socket
        
        Returns:
            tuple: (mensaje_decodificado, es_válido)
                   mensaje_decodificado: string con el contenido entre STX y ETX
                   es_válido: True si el LRC es correcto, False si está corrupto
        """
        # Validar que empiece con STX
        if not raw or not raw.startswith(ProtocolMessage.STX):
            return "", False
        
        try:
            # Buscar ETX
            etx_pos = raw.index(ProtocolMessage.ETX)
            
            # Extraer DATA (entre STX y ETX)
            data = raw[1:etx_pos]
            
            # Extraer LRC recibido (después de ETX)
            if len(raw) <= etx_pos + 1:
                return "", False
            received_lrc = raw[etx_pos + 1]
            
            # Calcular LRC esperado
            expected_lrc = 0
            for byte in data:
                expected_lrc ^= byte
            
            # Validar LRC
            is_valid = (received_lrc == expected_lrc)
            
            # Decodificar mensaje
            message = data.decode('utf-8')
            
            return message, is_valid
            
        except (ValueError, IndexError, UnicodeDecodeError) as e:
            # Error al buscar ETX o decodificar
            return "", False
    
    @staticmethod
    def is_ack(data: bytes) -> bool:
        """Verifica si el mensaje recibido es un ACK"""
        return data.startswith(ProtocolMessage.ACK)
    
    @staticmethod
    def is_nack(data: bytes) -> bool:
        """Verifica si el mensaje recibido es un NACK"""
        return data.startswith(ProtocolMessage.NACK)
    
    @staticmethod
    def send_with_protocol(sock, message: str, wait_ack: bool = True, timeout: float = 5.0) -> bool:
        """
        Envía un mensaje con protocolo completo y espera ACK
        
        Args:
            sock: Socket de conexión
            message: Mensaje a enviar
            wait_ack: Si debe esperar confirmación ACK
            timeout: Tiempo máximo de espera para ACK
        
        Returns:
            bool: True si se envió correctamente (y recibió ACK si wait_ack=True)
        """
        import socket as sock_module
        
        # Codificar y enviar
        encoded = ProtocolMessage.encode(message)
        sock.sendall(encoded)
        
        if not wait_ack:
            return True
        
        # Esperar ACK
        original_timeout = sock.gettimeout()
        try:
            sock.settimeout(timeout)
            ack_data = sock.recv(1)
            
            if ProtocolMessage.is_ack(ack_data):
                return True
            elif ProtocolMessage.is_nack(ack_data):
                return False
            else:
                return False
        except sock_module.timeout:
            return False
        finally:
            sock.settimeout(original_timeout)
    
    @staticmethod
    def receive_with_protocol(sock, send_ack: bool = True, timeout: float = 5.0) -> tuple[str, bool]:
        """
        Recibe un mensaje con protocolo y envía ACK/NACK automáticamente
        
        Args:
            sock: Socket de conexión
            send_ack: Si debe enviar ACK/NACK automáticamente
            timeout: Tiempo máximo de espera
        
        Returns:
            tuple: (mensaje, éxito)
        """
        import socket as sock_module
        
        original_timeout = sock.gettimeout()
        try:
            sock.settimeout(timeout)
            raw_data = sock.recv(4096)
            
            if not raw_data:
                return "", False
            
            # Decodificar mensaje
            message, is_valid = ProtocolMessage.decode(raw_data)
            
            # Enviar ACK o NACK si se solicita
            if send_ack:
                if is_valid:
                    sock.sendall(ProtocolMessage.ACK)
                else:
                    sock.sendall(ProtocolMessage.NACK)
            
            return message, is_valid
            
        except sock_module.timeout:
            return "", False
        finally:
            sock.settimeout(original_timeout)


# Funciones de conveniencia
def encode_message(message: str) -> bytes:
    """Shortcut para codificar mensaje"""
    return ProtocolMessage.encode(message)

def decode_message(raw: bytes) -> tuple[str, bool]:
    """Shortcut para decodificar mensaje"""
    return ProtocolMessage.decode(raw)
