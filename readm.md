# Práctica SD - Módulo CENTRAL

Este repositorio contiene una implementación de referencia del módulo **CENTRAL** para la
práctica de recarga de vehículos eléctricos. El objetivo es disponer de un proceso que permanezca
en ejecución de forma indefinida, coordinando puntos de recarga y aplicaciones de conductores a
través de sockets TCP y mensajes JSON.

## Características principales

- Persistencia en disco de los puntos de recarga registrados.
- Servidor TCP asíncrono para puntos de recarga (puerto 9000) y aplicaciones de conductor (puerto 9001).
- Protocolo de mensajería basado en JSON por línea (`JSON Lines`).
- Difusión en tiempo real del estado de cada punto de recarga a todas las aplicaciones de conductor conectadas.
- Orquestación completa del ciclo de vida de un suministro: solicitud, autorización, seguimiento del consumo y cierre del ticket.
- Envío de órdenes remotas de *stop/resume* a puntos individuales o a todo el parque.

## Cómo ejecutar

```bash
python -m central
```

Al arrancar, CENTRAL mostrará un resumen de los puntos conocidos y quedará a la espera de
conexiones. Desde la consola interactiva se puede escribir `list` para ver el estado actual o
`stop <ID_CP>` / `resume <ID_CP>` para forzar el estado de un punto. Con `stop` o `resume` sin
identificador se envía el comando a todos los puntos conectados.

### Handshake y mensajes

Cada conexión debe comenzar enviando un `hello` JSON:

```json
{"role": "cp", "cp_id": "CP-01", "location": "Campus Norte"}
```

```json
{"role": "driver", "driver_id": "DRV-001"}
```

Tras el `welcome` de CENTRAL se pueden enviar mensajes:

- **Desde un CP**
  - `authorization_response`: acepta o deniega una autorización.
  - `supply_started`, `supply_update`, `supply_finished` para informar del suministro.
  - `health` para notificar averías o recuperaciones.
- **Desde un conductor**
  - `request_supply` para solicitar un suministro.
  - `remote_command` (`stop`/`resume`) para propagar la orden a puntos específicos.
  - `list_cps` para recibir un *snapshot* actualizado.

CENTRAL responde con mensajes `cp_state`, `supply_status` y `supply_update` para mantener
informados a conductores y puntos de recarga.

## Pruebas

Las pruebas unitarias (basadas en `pytest`) cubren la lógica del orquestador.

```bash
pip install -r requirements-dev.txt  # si todavía no lo has hecho
pytest
```

## Requisitos de desarrollo

- Python 3.10+
- `pytest` para ejecutar los tests.

La estructura modular permite reutilizar `CentralCore` en otros transportes (por ejemplo, WebSocket
o HTTP) cambiando únicamente el adaptador de canales.
