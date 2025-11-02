# 🚀 Prueba del Protocolo STX-ETX-LRC en Red

## Setup Distribuido Recomendado

### 📍 Ordenador 1 (CENTRAL + DRIVER + TEST)
**IP ejemplo**: `192.168.1.100` (tu ordenador actual)

```powershell
# Terminal 1: CENTRAL Web
cd C:\Users\Charlie\SistemasDistribuidos\sd-p1-2025
python src\EV_Central\EV_Central_Web.py --host 0.0.0.0 --port 8888

# Terminal 2: Test del Protocolo (ejecutar después de conectar ENGINE+MONITOR)
python test_protocol_complete.py --auto
```

### 📍 Ordenador 2 (ENGINE + MONITOR)
**IP ejemplo**: `192.168.1.200` (otro ordenador en la red)

```bash
# Terminal 1: ENGINE para ALC1
cd sd-p1-2025
python src/EV_CP_E/EV_CP_E.py --cp-id ALC1 --port 5001 --kafka-bootstrap 192.168.1.100:29092

# Terminal 2: MONITOR para ALC1
python src/EV_CP_M/EV_CP_M.py --cp-id ALC1 \
    --engine-host localhost --engine-port 5001 \
    --central-host 192.168.1.100 --central-port 8888
```

---

## 🔧 Configuración Paso a Paso

### PASO 1: Preparar CENTRAL (Ordenador 1)

1. **Verificar IP del ordenador**:
```powershell
ipconfig
# Buscar "IPv4 Address" de tu adaptador de red
```

2. **Verificar que Kafka está corriendo** (si usas Kafka):
```powershell
# Si tienes Docker:
docker ps | findstr kafka

# O verificar puerto 29092:
netstat -an | findstr 29092
```

3. **Iniciar CENTRAL en modo red** (0.0.0.0 para aceptar conexiones externas):
```powershell
python src\EV_Central\EV_Central_Web.py --host 0.0.0.0 --port 8888
```

4. **Verificar que CENTRAL está escuchando**:
```powershell
netstat -an | findstr 8888
# Debe mostrar: 0.0.0.0:8888 LISTENING
```

---

### PASO 2: Configurar Firewall (Ordenador 1)

**Permitir conexiones entrantes en puerto 8888:**

```powershell
# PowerShell como Administrador:
New-NetFirewallRule -DisplayName "EV Central" -Direction Inbound -Protocol TCP -LocalPort 8888 -Action Allow
```

O manualmente:
1. Panel de Control → Firewall de Windows
2. Configuración avanzada → Reglas de entrada
3. Nueva regla → Puerto → TCP 8888 → Permitir conexión

---

### PASO 3: Conectar ENGINE + MONITOR (Ordenador 2)

**Reemplaza `192.168.1.100` con la IP real de tu Ordenador 1**

1. **Iniciar ENGINE**:
```bash
python src/EV_CP_E/EV_CP_E.py --cp-id ALC1 --port 5001 \
    --kafka-bootstrap 192.168.1.100:29092
```

2. **En OTRA terminal, iniciar MONITOR**:
```bash
python src/EV_CP_M/EV_CP_M.py --cp-id ALC1 \
    --engine-host localhost --engine-port 5001 \
    --central-host 192.168.1.100 --central-port 8888
```

3. **Verificar conexión en CENTRAL**:
   - Deberías ver en los logs del CENTRAL:
   ```
   [CENTRAL] New connection from ('192.168.1.200', XXXXX)
   [CENTRAL] recv: AUTH#ALC1
   CP ALC1 authenticated and now CONNECTED
   ```

---

### PASO 4: Ejecutar Test del Protocolo (Ordenador 1)

```powershell
python test_protocol_complete.py --auto
```

**Resultado esperado:**
```
✅ TEST BÁSICO COMPLETADO
✓ Protocolo STX-ETX-LRC funcionando
✓ Double ACK implementado correctamente
✓ Validación LRC activa

AUTH_GRANTED#ALC1#DRIVER_TEST_001
✓ Sesión de carga completada
✅ TEST COMPLETADO EXITOSAMENTE
```

---

## 🔍 Verificación de Conexión

### Desde Ordenador 1 (CENTRAL):
```powershell
# Ver conexiones activas al puerto 8888:
netstat -an | findstr 8888
```

### Desde Ordenador 2 (ENGINE/MONITOR):
```bash
# Probar conectividad al CENTRAL:
telnet 192.168.1.100 8888

# O con Python:
python -c "import socket; s=socket.create_connection(('192.168.1.100', 8888), timeout=5); print('✓ Conexión OK'); s.close()"
```

---

## 📊 Flujo del Protocolo en Red

```
Ordenador 2 (MONITOR)           Ordenador 1 (CENTRAL)           Ordenador 1 (DRIVER/TEST)
      |                                |                                    |
      |---- STX-AUTH-ETX-LRC --------->|                                    |
      |                                | (valida LRC)                       |
      |<--------- ACK -----------------|                                    |
      |                                |                                    |
      |    (conexión persistente)      |                                    |
      |                                |                                    |
      |                                |<--- STX-REQ-ETX-LRC ---------------|
      |                                | (valida LRC)                       |
      |                                |---- ACK -------------------------->|
      |                                |                                    |
      |                                | (verifica CP disponible)           |
      |                                |                                    |
      |                                |---- STX-AUTH_GRANTED-ETX-LRC ---->|
      |                                | (valida LRC)                       |
      |                                |<--- ACK ---------------------------|
      |                                |                                    |
```

---

## 🐛 Troubleshooting

### Error: "Connection refused"
- ✓ Verificar que CENTRAL está corriendo
- ✓ Verificar IP correcta con `ipconfig`
- ✓ Verificar firewall permite puerto 8888
- ✓ Probar desde mismo ordenador: `telnet localhost 8888`

### Error: "AUTH_DENIED#DISCONNECTED"
- ✓ Verificar que ENGINE está corriendo en Ordenador 2
- ✓ Verificar que MONITOR está corriendo y conectado
- ✓ Ver logs del CENTRAL: debe mostrar "CP ALC1 authenticated"

### Error: "ERROR#NO_ACK" o "ERROR#CORRUPTED"
- ✓ Verificar que ambos ordenadores usan la misma versión del código
- ✓ Verificar que protocol.py está actualizado en ambos
- ✓ Revisar logs con nivel DEBUG para ver bytes en hex

### Kafka no disponible
- Si no tienes Kafka corriendo, el sistema sigue funcionando pero sin telemetría
- Los mensajes de control (AUTH, REQ, FINISH) usan sockets TCP, no Kafka
- Para test básico del protocolo, Kafka es opcional

---

## 📝 Checklist de Prueba

- [ ] CENTRAL iniciado en 0.0.0.0:8888
- [ ] Firewall permite conexiones en puerto 8888
- [ ] ENGINE corriendo en Ordenador 2
- [ ] MONITOR conectado al CENTRAL (ver logs)
- [ ] CP aparece como "connected" en web GUI (http://localhost:8000)
- [ ] Test ejecutado: `python test_protocol_complete.py --auto`
- [ ] Resultado: AUTH_GRANTED recibido
- [ ] Protocolo STX-ETX-LRC validado (double ACK funcionando)

---

## 🎯 Alternativa: Todo en un Ordenador (para debugging rápido)

Si no tienes otro ordenador disponible, puedes probar todo localmente:

```powershell
# Terminal 1: CENTRAL
python src\EV_Central\EV_Central_Web.py --host 127.0.0.1 --port 8888

# Terminal 2: ENGINE
python src\EV_CP_E\EV_CP_E.py --cp-id ALC1 --port 5001

# Terminal 3: MONITOR (NO TOCAR ENTER en el ENGINE!)
python src\EV_CP_M\EV_CP_M.py --cp-id ALC1 ^
    --engine-host localhost --engine-port 5001 ^
    --central-host localhost --central-port 8888

# Terminal 4: TEST
python test_protocol_complete.py --auto
```

---

## 📸 Capturas Esperadas

### En CENTRAL (logs):
```
[CENTRAL] recv: AUTH#ALC1 from ('192.168.1.200', 54321)
CP ALC1 authenticated and now CONNECTED
[CENTRAL] recv: REQ#DRIVER_TEST_001#ALC1 from ('127.0.0.1', 54322)
Authorization GRANTED for driver DRIVER_TEST_001 on ALC1
```

### En MONITOR (logs):
```
[MONITOR] Connected to CENTRAL at 192.168.1.100:8888
[MONITOR] Sent AUTH#ALC1
[MONITOR] Received: ACK
[MONITOR] Heartbeat loop started
```

### En TEST (output):
```
✓ Conexión establecida
✓ CENTRAL envió ACK (protocolo OK)
✓ Respuesta recibida: AUTH_GRANTED#ALC1#DRIVER_TEST_001
✓ LRC válido, ACK enviado automáticamente
✅ TEST COMPLETADO EXITOSAMENTE
```

---

¿Listo para probar? 🚀
