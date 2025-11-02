# Quick Reference - Scripts del Sistema

## 🔧 Scripts de Kafka

### Iniciar Kafka + Crear Topics
```powershell
START_KAFKA.bat
```
Inicia Docker Compose y crea todos los topics necesarios

### Verificar Estado de Kafka
```powershell
CHECK_KAFKA.bat
```
Muestra contenedores activos y lista todos los topics

### Detener Kafka
```powershell
STOP_KAFKA.bat
```
Detiene Kafka y Zookeeper (mantiene los datos)

---

## 🎯 Scripts para Examen (3 Ordenadores)

### PC 1 - Servidor Central
```powershell
PC1_CENTRAL.bat
```
Inicia: Kafka + Central + GUI Web (puerto 8000)

### PC 2 - Charging Point
```powershell
PC2_MONITOR_ENGINE.bat
```
Pide: IP Central, IP Kafka, CP_ID, Puerto Engine

### PC 3 - Cliente/Driver
```powershell
PC3_DRIVER.bat
```
Pide: IP Central, Driver ID
Opciones: GUI Web (sin instalaciones) o GUI Pygame

---

## 🚀 Demo Rápida (1 PC)

```powershell
DEMO_COMPLETA.bat
```
Inicia TODO automáticamente:
- Central + GUI Web
- 2 CPs (ALC1, SEV1)
- 2 Drivers (5, 23)

---

## 📋 Orden de Inicio Manual

1. **CENTRAL primero:**
   ```powershell
   PC1_CENTRAL.bat
   ```
   Espera ver: "Uvicorn running on http://0.0.0.0:8000"

2. **MONITOR+ENGINE después:**
   ```powershell
   PC2_MONITOR_ENGINE.bat
   ```
   Introduce IPs y CP_ID

3. **DRIVERS al final:**
   ```powershell
   PC3_DRIVER.bat
   ```
   Introduce IP y Driver ID

---

## 🌐 URLs Importantes

- **GUI Web:** http://localhost:8000
- **Kafka UI:** http://localhost:8080
- **Central TCP:** localhost:9099

---

## 📝 Comandos en Central CLI

```
list              # Ver todos los CPs
stop ALC1         # Parar CP (Out of Order)
resume ALC1       # Reanudar CP
quit              # Salir
```

---

## 🔧 Configuración Típica

### Mismo PC (localhost)
- Central IP: `localhost`
- Kafka IP: `localhost`

### Red local (3 PCs)
- Central IP: `192.168.1.XXX` (ipconfig en PC1)
- Kafka IP: `192.168.1.XXX` (mismo que Central)

### Múltiples CPs en mismo PC
- CP1: ENGINE_PORT=7001
- CP2: ENGINE_PORT=7002
- CP3: ENGINE_PORT=7003

---

## ✅ Pre-check

```powershell
# Docker corriendo?
docker ps

# Python instalado?
python --version

# Dependencias instaladas?
pip list | findstr fastapi
pip list | findstr uvicorn
pip list | findstr websockets
```

---

## 🐛 Problemas Comunes

**"Docker no está corriendo"**
→ Inicia Docker Desktop y espera

**"Connection refused"**
→ Verifica que Central esté corriendo primero

**No se ven CPs en GUI**
→ Refresca navegador (F5), espera 2-3 segundos

**Puerto ocupado**
→ Usa otro puerto para ENGINE (7001, 7002, 7003...)
