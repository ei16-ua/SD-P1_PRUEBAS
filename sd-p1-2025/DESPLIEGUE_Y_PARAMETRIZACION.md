# Guía de Despliegue y Parametrización del Sistema

## 📋 CUMPLIMIENTO: Despliegue, Modularidad y Escalabilidad (2 puntos)

---

## 1. Despliegue sin Compilación ✅

**Tu sistema es Python → NO requiere compilación**

```bash
# Simplemente ejecutar:
python src/EV_Central/EV_Central.py --host 0.0.0.0 --port 8888
```

✅ **Ventaja:** Cualquier máquina con Python 3.8+ puede ejecutarlo sin compilar.

---

## 2. Parametrización Completa ✅

### 📍 CENTRAL

**Parámetros configurables:**
```bash
python src/EV_Central/EV_Central.py \
    --host 0.0.0.0 \              # IP donde escucha (0.0.0.0 = todas las interfaces)
    --port 8888 \                  # Puerto TCP para sockets
    --kafka-bootstrap localhost:29092  # Servidor Kafka (opcional)
```

**Sin parámetros fijos en código:** ✅
- Host, puerto, Kafka configurables por CLI
- Base de datos SQLite en ruta relativa (portable)

---

### 📍 ENGINE (CP_E)

**Parámetros configurables:**
```bash
python src/EV_CP_E/EV_CP_E.py \
    --cp-id ALC1 \                # ID del punto de carga (único)
    --port 5001 \                 # Puerto para health check
    --kafka-bootstrap 192.168.1.10:29092  # Servidor Kafka
```

**Múltiples instancias:**
```bash
# Máquina 1
python src/EV_CP_E/EV_CP_E.py --cp-id ALC1 --port 5001

# Máquina 2
python src/EV_CP_E/EV_CP_E.py --cp-id ALC2 --port 5002

# Máquina 3
python src/EV_CP_E/EV_CP_E.py --cp-id MAD1 --port 5003
```

✅ **Escalable:** Puedes lanzar N instancias con diferentes `--cp-id` y `--port`

---

### 📍 MONITOR (CP_M)

**Parámetros configurables:**
```bash
python src/EV_CP_M/EV_CP_M.py \
    --cp-id ALC1 \                     # ID del CP que monitorea
    --engine-host localhost \          # IP del ENGINE
    --engine-port 5001 \               # Puerto del ENGINE
    --central-host 192.168.1.10 \     # IP del CENTRAL
    --central-port 8888 \              # Puerto del CENTRAL
    --interval 1.0 \                   # Intervalo de heartbeat (segundos)
    --engine-timeout 1.5 \             # Timeout para ENGINE
    --central-timeout 10.0             # Timeout para CENTRAL
```

**Múltiples instancias:**
```bash
# Monitor para ALC1 (Máquina 1)
python src/EV_CP_M/EV_CP_M.py --cp-id ALC1 --engine-host 192.168.1.20 --engine-port 5001 --central-host 192.168.1.10 --central-port 8888

# Monitor para ALC2 (Máquina 2)
python src/EV_CP_M/EV_CP_M.py --cp-id ALC2 --engine-host 192.168.1.21 --engine-port 5002 --central-host 192.168.1.10 --central-port 8888
```

✅ **Cada MONITOR se conecta a su ENGINE local y al CENTRAL remoto**

---

### 📍 DRIVER

**Parámetros configurables:**
```bash
python src/EV_Driver/EV_Driver.py \
    --driver-id DRIVER1 \              # ID único del driver
    --central-host 192.168.1.10 \     # IP del CENTRAL
    --central-port 8888 \              # Puerto del CENTRAL
    --kafka-bootstrap 192.168.1.10:29092  # Servidor Kafka
```

**Múltiples instancias simultáneas:**
```bash
# Driver 1 (Máquina A)
python src/EV_Driver/EV_Driver.py --driver-id DRIVER1 --central-host 192.168.1.10 --central-port 8888

# Driver 2 (Máquina B)
python src/EV_Driver/EV_Driver.py --driver-id DRIVER2 --central-host 192.168.1.10 --central-port 8888

# Driver 3 (Máquina C)
python src/EV_Driver/EV_Driver.py --driver-id DRIVER3 --central-host 192.168.1.10 --central-port 8888
```

✅ **Cada driver con ID único, conectándose al mismo CENTRAL**

---

## 3. Escenario de Despliegue Distribuido (3 máquinas)

### 🖥️ **Máquina 1: CENTRAL + Kafka**
**IP:** 192.168.1.10

```bash
# Terminal 1: Kafka (Docker)
docker run -d --name kafka -p 29092:29092 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://192.168.1.10:29092 apache/kafka

# Terminal 2: CENTRAL
python src/EV_Central/EV_Central_Web.py --host 0.0.0.0 --port 8888 --kafka-bootstrap 192.168.1.10:29092

# Web GUI disponible en: http://192.168.1.10:8000
```

---

### 🖥️ **Máquina 2: ENGINE + MONITOR (CP ALC1)**
**IP:** 192.168.1.20

```bash
# Terminal 1: ENGINE
python src/EV_CP_E/EV_CP_E.py --cp-id ALC1 --port 5001 --kafka-bootstrap 192.168.1.10:29092

# Terminal 2: MONITOR
python src/EV_CP_M/EV_CP_M.py \
    --cp-id ALC1 \
    --engine-host localhost --engine-port 5001 \
    --central-host 192.168.1.10 --central-port 8888
```

---

### 🖥️ **Máquina 3: DRIVER**
**IP:** 192.168.1.30

```bash
# Terminal 1: DRIVER
python src/EV_Driver/EV_Driver.py \
    --driver-id DRIVER1 \
    --central-host 192.168.1.10 --central-port 8888 \
    --kafka-bootstrap 192.168.1.10:29092
```

---

## 4. Escalabilidad Dinámica Durante la Corrección ✅

### ✅ **Añadir un nuevo CP en tiempo real:**

**El profesor dice:** "Añade otro CP en esta máquina"

```bash
# Nueva terminal en Máquina 2:

# Terminal 3: ENGINE ALC2
python src/EV_CP_E/EV_CP_E.py --cp-id ALC2 --port 5002 --kafka-bootstrap 192.168.1.10:29092

# Terminal 4: MONITOR ALC2
python src/EV_CP_M/EV_CP_M.py \
    --cp-id ALC2 \
    --engine-host localhost --engine-port 5002 \
    --central-host 192.168.1.10 --central-port 8888
```

**Resultado:** CENTRAL detecta nuevo CP automáticamente (conexión AUTH) ✅

---

### ✅ **Añadir múltiples DRIVERs:**

**El profesor dice:** "Lanza 3 drivers más"

```bash
# Máquina 3:
python src/EV_Driver/EV_Driver.py --driver-id DRIVER2 --central-host 192.168.1.10 --central-port 8888 &
python src/EV_Driver/EV_Driver.py --driver-id DRIVER3 --central-host 192.168.1.10 --central-port 8888 &
python src/EV_Driver/EV_Driver.py --driver-id DRIVER4 --central-host 192.168.1.10 --central-port 8888 &
```

**Resultado:** CENTRAL acepta todas las conexiones concurrentemente ✅

---

### ✅ **Simular crash de un módulo:**

**El profesor dice:** "Para súbitamente el ENGINE de ALC1"

```bash
# En la terminal del ENGINE:
Ctrl+C
```

**Resultado esperado:**
1. ENGINE se detiene
2. MONITOR detecta timeout en el PING
3. MONITOR envía `FAULT#ALC1#TIMEOUT` a CENTRAL
4. CENTRAL marca ALC1 como "AVERIADO" (rojo)
5. Si había un driver cargando, se notifica fin de sesión
6. Resto del sistema sigue funcionando ✅

---

## 5. Parametrización de Base de Datos y Kafka ✅

### 📊 **Base de Datos SQLite**

**Ubicación:** `central.db` (raíz del proyecto)

```python
# En EV_Central.py:
DB_FILENAME = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "central.db")
```

✅ **Portable:** La base de datos viaja con el proyecto
✅ **10+ CPs disponibles:** ALC1, ALC3, MAD1, MAD2, MAD3, SEV2, SEV3, VAL1, VAL3, COR1

**Verificar CPs disponibles:**
```bash
python -c "import sqlite3; conn = sqlite3.connect('central.db'); print(conn.execute('SELECT cp_id, location FROM charging_points').fetchall())"
```

---

### 🔌 **Kafka (Opcional pero Recomendado)**

**Si Kafka está disponible:**
```bash
--kafka-bootstrap 192.168.1.10:29092
```

**Si Kafka NO está disponible:**
```bash
# Omitir el parámetro --kafka-bootstrap
python src/EV_Central/EV_Central.py --host 0.0.0.0 --port 8888
# (Kafka es None, sistema sigue funcionando)
```

✅ **Sistema funciona con o sin Kafka** (sockets TCP siempre funcionan)

---

## 6. Concurrencia en CENTRAL ✅

**Código en `EV_Central.py`:**

```python
def _accept_loop(self):
    """Acepta conexiones concurrentemente"""
    while True:
        conn, addr = self._socket.accept()
        # Crear thread nuevo para cada conexión
        threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()
```

✅ **CENTRAL acepta conexiones ilimitadas:**
- Cada conexión en un thread separado
- Múltiples CP conectados simultáneamente
- Múltiples DRIVER haciendo peticiones en paralelo

**Demostración:**
```bash
# Conectar 5 CPs al mismo tiempo:
for i in {1..5}; do
    python src/EV_CP_M/EV_CP_M.py --cp-id CP0$i --engine-host localhost --engine-port 500$i --central-host localhost --central-port 8888 &
done
```

Resultado: CENTRAL acepta todas las conexiones sin bloquear ✅

---

## 7. Observabilidad del Sistema ✅

### 📺 **Interfaces de Visualización**

#### **1. CENTRAL - Logs en Terminal:**
```
[INFO] CENTRAL listening on 127.0.0.1:8888
[INFO] [CENTRAL] New connection from ('192.168.1.20', 54321)
[INFO] [CENTRAL] recv: AUTH#ALC1 from ('192.168.1.20', 54321)
[INFO] CP ALC1 authenticated and now CONNECTED
[INFO] [CENTRAL] recv: REQ#DRIVER1#ALC1 from ('192.168.1.30', 54322)
[INFO] Authorization GRANTED for driver DRIVER1 on ALC1
```

#### **2. CENTRAL - GUI Web (puerto 8000):**
- Estado de todos los CPs (verde=OK, rojo=FAULT, gris=DESCONECTADO)
- Driver conectado en cada CP
- kWh acumulados, €/kWh, potencia actual
- Mensajes de aplicación (conexiones, desconexiones)

#### **3. MONITOR - Logs:**
```
[INFO] Central AUTH response: ACK
[INFO] Heartbeat -> Engine: OK
[INFO] Heartbeat -> Engine: OK
[WARN] Heartbeat -> Engine: TIMEOUT
[WARN] FAULT sent to CENTRAL: ACK (TIMEOUT)
```

#### **4. DRIVER - Interfaz Texto/GUI:**
- Solicitud de autorización
- Respuesta AUTH_GRANTED/DENIED
- Telemetría en tiempo real (kWh, €)
- Finalización de carga

---

## 8. Checklist de Despliegue para Corrección

### ✅ **Antes de la Corrección:**

- [ ] Código actualizado con `protocol.py`
- [ ] Base de datos `central.db` con 10+ CPs
- [ ] Scripts de arranque preparados
- [ ] IPs de las máquinas anotadas
- [ ] Firewall configurado (puertos 8888, 29092 abiertos)
- [ ] Python 3.8+ instalado en todas las máquinas
- [ ] Dependencias instaladas: `pip install loguru kafka-python`

---

### ✅ **Durante la Corrección:**

#### **Orden de arranque:**
1. **Kafka** (si se usa): `docker run kafka` o servicio externo
2. **CENTRAL**: `python src/EV_Central/EV_Central_Web.py --host 0.0.0.0 --port 8888`
3. **ENGINEs**: Un `EV_CP_E.py` por cada CP
4. **MONITORs**: Un `EV_CP_M.py` por cada CP
5. **DRIVERs**: Según demande el profesor

#### **Añadir instancia nueva:**
```bash
# Ejemplo: Nuevo CP en tiempo real
python src/EV_CP_E/EV_CP_E.py --cp-id NUEVO_CP --port 5099 --kafka-bootstrap <IP>:29092
python src/EV_CP_M/EV_CP_M.py --cp-id NUEVO_CP --engine-host localhost --engine-port 5099 --central-host <CENTRAL_IP> --central-port 8888
```

#### **Simular crash:**
```bash
# Ctrl+C en la terminal del módulo
# O cerrar la ventana/terminal directamente
```

---

## 9. Ejemplo de Comandos Completos

### 🎯 **Escenario Completo 3 Máquinas:**

#### **Máquina CENTRAL (192.168.1.10):**
```bash
cd sd-p1-2025

# Kafka (Docker)
docker run -d --name kafka -p 29092:29092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://192.168.1.10:29092 \
  apache/kafka

# CENTRAL
python src/EV_Central/EV_Central_Web.py \
  --host 0.0.0.0 \
  --port 8888 \
  --kafka-bootstrap 192.168.1.10:29092
```

#### **Máquina CP1 (192.168.1.20):**
```bash
cd sd-p1-2025

# ENGINE ALC1
python src/EV_CP_E/EV_CP_E.py \
  --cp-id ALC1 \
  --port 5001 \
  --kafka-bootstrap 192.168.1.10:29092

# (Nueva terminal) MONITOR ALC1
python src/EV_CP_M/EV_CP_M.py \
  --cp-id ALC1 \
  --engine-host localhost \
  --engine-port 5001 \
  --central-host 192.168.1.10 \
  --central-port 8888
```

#### **Máquina DRIVER (192.168.1.30):**
```bash
cd sd-p1-2025

# DRIVER 1
python src/EV_Driver/EV_Driver.py \
  --driver-id DRIVER1 \
  --central-host 192.168.1.10 \
  --central-port 8888 \
  --kafka-bootstrap 192.168.1.10:29092
```

---

## 10. Resumen de Cumplimiento

| Requisito | Cumplimiento | Evidencia |
|-----------|--------------|-----------|
| Sin compilación | ✅ | Python interpretado |
| Parametrización completa | ✅ | Todos los módulos usan `argparse` |
| Múltiples instancias | ✅ | Cada módulo con ID único |
| Escalabilidad dinámica | ✅ | Añadir/quitar módulos en caliente |
| Base de datos con 10+ CPs | ✅ | `central.db` con 10 CPs |
| Concurrencia en CENTRAL | ✅ | Threading para cada conexión |
| Observabilidad | ✅ | Logs + GUI Web |
| Protocolo STX-ETX-LRC | ✅ | Implementado en todas las comunicaciones |

---

## 📌 Notas Finales

### ✅ **Ventajas de Python:**
- No requiere compilación
- Portable entre Windows/Linux/Mac
- Fácil de lanzar múltiples instancias
- Logs claros y legibles

### ✅ **Preparación para Preguntas del Profesor:**

**P: "¿Cómo añado otro CP?"**
R: `python src/EV_CP_E/EV_CP_E.py --cp-id NUEVO_ID --port PUERTO` + MONITOR correspondiente

**P: "¿Puedo cambiar el puerto de CENTRAL?"**
R: Sí, `--port 9999` al lanzar CENTRAL, y todos los módulos deben usar `--central-port 9999`

**P: "¿Funciona sin Kafka?"**
R: Sí, Kafka es opcional. Las comunicaciones críticas (AUTH, REQ, FINISH) usan sockets TCP siempre.

**P: "¿Cuántos drivers puedo lanzar?"**
R: Ilimitados. CENTRAL es concurrente y acepta todas las conexiones.

---

**Puntos esperados en este apartado:** 2/2 puntos completos ✅
