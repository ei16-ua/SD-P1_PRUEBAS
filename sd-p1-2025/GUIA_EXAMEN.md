# GUÍA DE CONFIGURACIÓN PARA EXAMEN
# ====================================

## 🖥️ Distribución de Ordenadores

### ORDENADOR 1: CENTRAL + KAFKA
- **Rol:** Servidor Central y Sistema de Mensajería
- **Script:** `PC1_CENTRAL.bat`
- **Puertos:**
  - 9099: TCP Central (conexiones de Monitors y Drivers)
  - 8000: GUI Web (monitorización)
  - 29092: Kafka (telemetría)
  - 8080: Kafka UI (opcional, para debug)

### ORDENADOR 2: MONITOR + ENGINE (uno o varios)
- **Rol:** Punto de Carga (Charging Point)
- **Script:** `PC2_MONITOR_ENGINE.bat`
- **Configuración necesaria:**
  - IP del CENTRAL
  - IP de Kafka
  - CP_ID (ej: ALC1, SEV1, MAD2)
  - Puerto del ENGINE (7001, 7002, 7003...)

### ORDENADOR 3: DRIVER (uno o varios)
- **Rol:** Cliente/Conductor
- **Script:** `PC3_DRIVER.bat`
- **Configuración necesaria:**
  - IP del CENTRAL
  - Driver ID (número único)

---

## 📋 SECUENCIA DE INICIO (Importante el orden)

### 1️⃣ ORDENADOR 1 - CENTRAL (primero)
```powershell
PC1_CENTRAL.bat
```

**Espera a ver:**
- ✅ "Kafka UI: http://localhost:8080"
- ✅ "CENTRAL listening on 0.0.0.0:9099"
- ✅ "Uvicorn running on http://0.0.0.0:8000"

**Abre en navegador:** http://localhost:8000 (para ver el panel)

---

### 2️⃣ ORDENADOR 2 - MONITOR+ENGINE (segundo)

Ejecuta tantas veces como CPs necesites (en terminales separadas):

```powershell
PC2_MONITOR_ENGINE.bat
```

**Ejemplo de configuración:**
```
IP del CENTRAL: 192.168.1.100  (o localhost si es el mismo PC)
IP de Kafka: 192.168.1.100     (o localhost si es el mismo PC)
ID del CP: ALC1
Puerto del ENGINE: 7001
```

**Para múltiples CPs en el mismo PC:**
- Terminal 1: CP_ID=ALC1, ENGINE_PORT=7001
- Terminal 2: CP_ID=SEV1, ENGINE_PORT=7002
- Terminal 3: CP_ID=MAD2, ENGINE_PORT=7003

---

### 3️⃣ ORDENADOR 3 - DRIVER (tercero)

Ejecuta tantas veces como conductores necesites:

```powershell
PC3_DRIVER.bat
```

**Ejemplo de configuración:**
```
IP del CENTRAL: 192.168.1.100  (o localhost si es el mismo PC)
Driver ID: 5
```

---

## 🌐 CONFIGURACIÓN DE RED

### Si todos los ordenadores están en PCs diferentes:

#### En el ORDENADOR 1 (CENTRAL):
1. Averigua tu IP:
   ```powershell
   ipconfig
   ```
   Busca "Dirección IPv4" (ej: 192.168.1.100)

2. Asegúrate de que el firewall permita:
   - Puerto 9099 (TCP)
   - Puerto 8000 (HTTP)
   - Puerto 29092 (Kafka)

#### En ORDENADORES 2 y 3:
- Usa la IP del ORDENADOR 1 cuando te la pida
- Ejemplo: `192.168.1.100`

### Si todo está en el mismo PC (prueba local):
- Usa `localhost` para todas las IPs
- Cada componente en una terminal diferente

---

## 🎯 ESCENARIO DE PRUEBA COMPLETO

### Setup mínimo funcional:

**PC1 - CENTRAL:**
```powershell
PC1_CENTRAL.bat
```

**PC2 - 2 CPs:**
Terminal 1:
```
CP_ID: ALC1
CENTRAL IP: localhost (o IP del PC1)
KAFKA IP: localhost (o IP del PC1)
ENGINE PORT: 7001
```

Terminal 2:
```
CP_ID: SEV1
CENTRAL IP: localhost (o IP del PC1)
KAFKA IP: localhost (o IP del PC1)
ENGINE PORT: 7002
```

**PC3 - 2 Drivers:**
Terminal 1:
```
DRIVER ID: 5
CENTRAL IP: localhost (o IP del PC1)
```

Terminal 2:
```
DRIVER ID: 23
CENTRAL IP: localhost (o IP del PC1)
```

---

## 📊 MONITORIZACIÓN

### GUI Web (ORDENADOR 1):
- Abre: http://localhost:8000 (o http://IP_PC1:8000 desde otros PCs)
- Verás en tiempo real:
  - Grid con todos los CPs y sus estados
  - Tabla de solicitudes activas
  - Log de mensajes del sistema

### Kafka UI (opcional):
- Abre: http://localhost:8080
- Puedes ver:
  - Topics creados
  - Mensajes de telemetría
  - Comandos enviados

---

## 🐛 TROUBLESHOOTING

### "Docker no está corriendo"
```powershell
# Inicia Docker Desktop y espera a que cargue completamente
```

### "Connection refused" en MONITOR/DRIVER
- Verifica que el CENTRAL esté corriendo
- Verifica la IP introducida
- Verifica el firewall

### No se ven CPs en el GUI Web
- El MONITOR debe conectarse DESPUÉS del CENTRAL
- Espera unos segundos después de iniciar el MONITOR
- Refresca el navegador (F5)

### ENGINE no arranca
- Verifica que el puerto esté libre
- Si usas múltiples ENGINEs, usa puertos diferentes (7001, 7002, 7003...)

### DRIVER no puede conectar
- Verifica que el CENTRAL esté corriendo
- Verifica la IP del CENTRAL
- El CP debe existir y estar conectado

---

## 📝 COMANDOS ÚTILES DEL CENTRAL

En la consola del CENTRAL puedes ejecutar:

```
list              # Ver todos los CPs y su estado
stop ALC1         # Parar ALC1 (Out of Order)
resume ALC1       # Reanudar ALC1
quit              # Cerrar el CENTRAL
```

---

## ✅ CHECKLIST PRE-EXAMEN

- [ ] Docker Desktop instalado y corriendo en PC1
- [ ] Python 3.12+ instalado en todos los PCs
- [ ] Dependencias instaladas: `pip install -r requirements.txt`
- [ ] FastAPI instalado: `pip install fastapi uvicorn[standard] websockets`
- [ ] Base de datos inicializada con CPs (ejecutar `python create_drivers.py` o `python add_cp.py`)
- [ ] Firewall configurado para permitir puertos 9099, 8000, 29092
- [ ] IPs de los PCs anotadas
- [ ] Scripts BAT probados en cada PC

---

## 🚀 INICIO RÁPIDO (TODO EN UN PC)

Si quieres probar todo en un solo PC:

Terminal 1:
```powershell
PC1_CENTRAL.bat
```

Terminal 2:
```powershell
PC2_MONITOR_ENGINE.bat
# IP: localhost, CP_ID: ALC1, PORT: 7001
```

Terminal 3:
```powershell
PC3_DRIVER.bat
# CENTRAL IP: localhost, DRIVER ID: 5
```

Navegador:
```
http://localhost:8000
```

¡Disfruta! 🎉
