# 🌐 GUI Web para EV Central

## ✅ Instalación Completada

Las dependencias de FastAPI ya están instaladas:
- ✅ FastAPI
- ✅ Uvicorn
- ✅ WebSockets

## 🚀 Cómo iniciar

### 1. Asegúrate de que Docker Kafka esté corriendo:
```powershell
cd docker
docker-compose up -d
```

### 2. Inicia el CENTRAL con GUI Web:
```powershell
.\start_central_web.bat
```

O directamente con Python:
```powershell
python src\EV_Central\EV_Central_Web.py --kafka-bootstrap localhost:29092
```

### 3. Abre tu navegador:
```
http://localhost:8000
```

## 📱 ¿Cómo funciona?

1. **El servidor corre en tu PC** (localhost:8000)
2. **Abre el navegador** y ve el panel en tiempo real
3. **Actualizaciones automáticas** vía WebSockets cada 2 segundos
4. **Múltiples navegadores** pueden ver el mismo panel simultáneamente

## 🎨 Características del diseño (según tu imagen)

### Panel de CPs (Grid superior)
- **Verde**: CP disponible o cargando
- **Naranja**: CP fuera de servicio
- **Rojo**: CP con fallo  
- **Gris**: CP desconectado

Cuando está cargando muestra:
```
ALC1
Sevilla A
Cargando...
┌──────────────┐
│ Driver 5     │  ← 24px bold
│ 0.54kWh      │  ← naranja
│ 0.18€        │  ← fondo amarillo
└──────────────┘
```

### Tabla de solicitudes activas
| DATE | START TIME | User ID | CP |
|------|------------|---------|-----|
| 12/9/25 | 10:58 | 5 | MAD2 |
| 12/9/25 | 9:00 | 23 | SEV1 |

### Mensajes del sistema
```
[10:58:32] ALC1 connected
[10:58:35] SEV1 authorized for driver 5
[10:59:01] MAD2 disconnected
```

## 🔧 Ventajas sobre Pygame

| Característica | Pygame | Web GUI |
|---------------|---------|---------|
| Instalación | Requiere Python + Pygame en cada PC | Solo navegador |
| Múltiples usuarios | ❌ No | ✅ Sí |
| Móviles | ❌ No | ✅ Sí |
| Acceso remoto | Difícil | Fácil (solo IP:8000) |
| Actualización | Polling | WebSockets real-time |

## 📊 Puertos usados

- **9099**: TCP del CENTRAL (para Monitors y Drivers)
- **8000**: Web GUI (HTTP + WebSockets)
- **29092**: Kafka (telemetría)

## 🐛 Troubleshooting

### El navegador no carga
```powershell
# Verifica que el servidor esté corriendo
netstat -ano | findstr :8000
```

### No se ven actualizaciones
- Abre la consola del navegador (F12)
- Verifica que diga "WebSocket connected"
- Si no conecta, revisa el firewall

### Error "Module not found"
```powershell
pip install fastapi "uvicorn[standard]" websockets
```

## 📸 Comparación con tu imagen

Tu imagen muestra el diseño que implementamos:
- ✅ Grid de CPs con colores según estado
- ✅ Info box blanca para datos del driver
- ✅ Tabla de solicitudes en curso
- ✅ Log de mensajes del sistema
- ✅ Título azul "SD EV CHARGING SOLUTION"

## 🎯 Siguiente paso

1. Ejecuta `.\start_central_web.bat`
2. Abre http://localhost:8000
3. Inicia algunos ENGINEs y MONITORs para ver los CPs en el grid
4. Conecta DRIVERs para ver las solicitudes y cargas en tiempo real

¡Disfruta del nuevo GUI! 🚀
