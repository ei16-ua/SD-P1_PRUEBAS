# Protocolo de Comunicación STX-ETX-LRC

## Descripción General

Este proyecto implementa el **protocolo estándar STX-ETX-LRC** para comunicaciones entre los componentes del sistema de carga de vehículos eléctricos (CENTRAL ↔ DRIVER y CENTRAL ↔ MONITOR).

## Formato del Mensaje

Cada mensaje sigue este formato:

```
<STX><DATA><ETX><LRC>\n
```

### Componentes

| Byte | Valor | Descripción |
|------|-------|-------------|
| **STX** | `0x02` | Start of Text - Marca el inicio del mensaje |
| **DATA** | Variable | Contenido del mensaje (texto UTF-8) |
| **ETX** | `0x03` | End of Text - Marca el final del mensaje |
| **LRC** | 1 byte | Longitudinal Redundancy Check (XOR de todos los bytes de DATA) |
| **\n** | `0x0A` | Newline - Terminador del mensaje |

### Cálculo del LRC

El LRC se calcula aplicando XOR a todos los bytes del campo DATA:

```python
lrc = 0x00
for byte in data_bytes:
    lrc ^= byte
```

**Ejemplo:**
- Mensaje: `"HELLO"`
- Bytes: `[0x48, 0x45, 0x4C, 0x4C, 0x4F]`
- LRC: `0x48 ^ 0x45 ^ 0x4C ^ 0x4C ^ 0x4F = 0x42`
- Mensaje codificado: `b'\x02HELLO\x03\x42\n'`

## Flujo de Comunicación

### 1. Envío con Confirmación (Double ACK)

```
Cliente                          Servidor
   |                                |
   |------ STX-DATA-ETX-LRC ------->|
   |                                |
   |<---------- ACK ----------------|  (Validación LRC OK)
   |                                |
   |                                |  (Procesa mensaje)
   |                                |
   |<--- STX-RESPONSE-ETX-LRC ------|
   |                                |
   |---------- ACK ---------------->|  (Validación LRC OK)
   |                                |
```

### 2. Detección de Corrupción

Si el LRC no coincide, el receptor envía **NACK**:

```
Cliente                          Servidor
   |                                |
   |------ STX-DATA-ETX-LRC ------->|
   |     (mensaje corrupto)         |
   |                                |
   |<---------- NACK ---------------|  (LRC inválido)
   |                                |
```

## Implementación

### Clase `ProtocolMessage` (src/UTILS/protocol.py)

#### Métodos Principales

```python
# Codificar mensaje
encoded = ProtocolMessage.encode("REQ#DRIVER1#CP01")
# Resultado: b'\x02REQ#DRIVER1#CP01\x03\x14\n'

# Decodificar mensaje
message, valid = ProtocolMessage.decode(raw_bytes)
# message: "REQ#DRIVER1#CP01"
# valid: True (si LRC correcto), False (si corrupto)

# Enviar con espera de ACK
success = ProtocolMessage.send_with_protocol(
    socket=conn,
    message="AUTH#CP01",
    wait_ack=True,
    timeout=5.0
)

# Recibir con validación y envío de ACK/NACK automático
message, valid = ProtocolMessage.receive_with_protocol(
    socket=conn,
    send_ack=True,
    timeout=5.0
)
```

## Mensajes del Sistema

### Driver → Central

| Mensaje | Formato | Descripción |
|---------|---------|-------------|
| **REQ** | `REQ#<driver_id>#<cp_id>` | Solicitud de autorización para cargar |
| **FINISH** | `FINISH#<cp_id>#<driver_id>` | Notificación de fin de carga |

### Monitor → Central

| Mensaje | Formato | Descripción |
|---------|---------|-------------|
| **AUTH** | `AUTH#<cp_id>` | Autenticación del punto de carga |
| **FAULT** | `FAULT#<cp_id>#<reason>` | Reporte de fallo en el CP |

### Central → Driver/Monitor

| Mensaje | Formato | Descripción |
|---------|---------|-------------|
| **ACK** | `ACK` | Confirmación de recepción correcta |
| **NACK** | `NACK` | Rechazo por mensaje desconocido |
| **AUTH_GRANTED** | `AUTH_GRANTED#<cp_id>#<driver_id>` | Autorización concedida |
| **AUTH_DENIED** | `AUTH_DENIED#<reason>` | Autorización denegada |

### Razones de Denegación

- `CP_NOT_FOUND` - El CP solicitado no existe
- `DISCONNECTED` - El CP está desconectado
- `OUT_OF_ORDER` - El CP está fuera de servicio
- `FAULT` - El CP reportó un fallo
- `BUSY` - El CP está ocupado con otro driver

## Códigos de Error

Los métodos del protocolo pueden retornar estos errores:

| Error | Descripción |
|-------|-------------|
| `ERROR#NO_ACK` | No se recibió ACK dentro del timeout |
| `ERROR#CORRUPTED` | El mensaje recibido tiene LRC inválido |
| `ERROR#TIMEOUT` | Timeout al esperar datos |

## Ventajas del Protocolo

1. **Detección de Corrupción**: El LRC detecta cambios en los datos durante la transmisión
2. **Confirmación Dual**: Ambas partes confirman recepción (double ACK)
3. **Simplicidad**: Fácil de implementar y debugear
4. **Estándar**: Protocolo ampliamente usado en comunicaciones serie
5. **UTF-8 Compatible**: Soporta caracteres especiales (€, ñ, tildes)

## Testing

El archivo `test_protocol.py` contiene 6 tests que verifican:

1. ✅ Codificación y decodificación básica
2. ✅ Detección de mensajes corruptos
3. ✅ Múltiples tipos de mensajes
4. ✅ Caracteres especiales (UTF-8)
5. ✅ Reconocimiento de ACK/NACK
6. ✅ Cálculo correcto del LRC

Ejecutar tests:
```bash
python test_protocol.py
```

## Prueba de Integración

El archivo `test_protocol_integration.py` prueba la comunicación completa DRIVER ↔ CENTRAL:

```bash
# 1. Iniciar CENTRAL
start_central.bat

# 2. Ejecutar test (en otra terminal)
python test_protocol_integration.py
```

## Timeout Predeterminado

Todas las operaciones tienen un timeout de **5 segundos** por defecto para evitar bloqueos indefinidos.

## Notas Técnicas

### Delimitador Final

Cada mensaje termina con `\n` (0x0A) para facilitar la detección del fin del mensaje en operaciones de lectura por líneas.

### Orden de Bytes

El LRC se calcula **solo sobre los bytes de DATA**, no incluye STX ni ETX.

### Persistencia de Conexión

Las conexiones socket permanecen abiertas para múltiples intercambios de mensajes:
- **MONITOR**: Mantiene conexión persistente con CENTRAL para enviar AUTH + heartbeats
- **DRIVER**: Conexión one-shot por cada operación (REQ → FINISH)

### Compatibilidad

Este protocolo es compatible con:
- Python 3.8+
- Sockets TCP
- Codificación UTF-8
- Sistemas operativos: Windows, Linux, macOS
