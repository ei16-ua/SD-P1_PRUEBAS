# Guía de instalación y uso del GUI Web para EV Central

## 📦 Instalación

### Opción 1: Usando el script automático (Recomendado)
```powershell
.\install_fastapi.ps1
```

### Opción 2: Manual con pipenv
```bash
pipenv install
```

### Opción 3: Manual con pip
```bash
pip install fastapi "uvicorn[standard]" websockets
```

## 🚀 Iniciar el sistema

### Iniciar CENTRAL con GUI Web
```bash
.\start_central_web.bat
```

O directamente:
```bash
python src\EV_Central\EV_Central_Web.py --kafka-bootstrap localhost:29092 --web-port 8000
```

## 🌐 Acceder al GUI

Una vez iniciado el servidor, abre tu navegador en:
- **URL local:** http://localhost:8000
- **Desde otra PC:** http://[IP_DEL_SERVIDOR]:8000

### Ventajas del GUI Web:
- ✅ **Múltiples clientes:** Varias personas pueden ver el panel simultáneamente
- ✅ **Actualizaciones en tiempo real:** WebSockets para updates instantáneos
- ✅ **Sin instalaciones:** Solo necesitas un navegador web
- ✅ **Multiplataforma:** Funciona en PC, tablet, móvil
- ✅ **Diseño moderno:** Interfaz HTML5/CSS3 responsive

## 📊 Características del GUI

### Panel de CPs
- **Verde:** CP disponible o cargando
- **Naranja:** CP fuera de servicio (Out of Order)
- **Rojo:** CP con fallo
- **Gris:** CP desconectado

Cuando un CP está cargando, muestra:
- **Driver ID:** En 24px bold
- **kWh consumidos:** Con color naranja
- **Euros acumulados:** Con fondo amarillo

### Tabla de solicitudes activas
Muestra las últimas 20 solicitudes de drivers con:
- Fecha
- Hora de inicio
- User ID
- CP asignado

### Mensajes del sistema
Log en tiempo real de eventos del sistema:
- Conexiones/desconexiones de CPs
- Autorizaciones concedidas/denegadas
- Fallos y errores
- Comandos ejecutados

## 🔧 Configuración

### Puertos
- **TCP Central:** 9099 (por defecto)
- **Web GUI:** 8000 (por defecto, configurable con `--web-port`)

### Argumentos disponibles
```bash
python src\EV_Central\EV_Central_Web.py --help

Opciones:
  --host HOST                Host TCP para Central (default: 0.0.0.0)
  --port PORT                Puerto TCP para Central (default: 9099)
  --web-port WEB_PORT        Puerto para GUI Web (default: 8000)
  --kafka-bootstrap BOOTSTRAP Kafka bootstrap server (opcional)
```

## 🔄 Comparación con GUI Pygame

| Característica | Pygame GUI | Web GUI (FastAPI) |
|---------------|------------|-------------------|
| Instalación cliente | Python + Pygame | Solo navegador |
| Múltiples monitores | ❌ No | ✅ Sí |
| Acceso remoto | ❌ Difícil | ✅ Fácil |
| Actualizaciones | Polling | WebSockets |
| Diseño | Básico | Moderno HTML5 |
| Móviles/tablets | ❌ No | ✅ Sí |

## 🐛 Troubleshooting

### El navegador no conecta
1. Verifica que el servidor esté corriendo: `docker ps`
2. Comprueba el firewall de Windows
3. Verifica la URL: http://localhost:8000

### WebSocket no conecta
- El navegador mostrará "Conexión perdida, reconectando..."
- Verifica que no haya proxy bloqueando WebSockets
- Revisa la consola del navegador (F12) para errores

### No se ven actualizaciones
1. Abre la consola del navegador (F12)
2. Verifica que el WebSocket esté conectado
3. El sistema envía updates cada 2 segundos automáticamente

## 📝 Arquitectura

```
┌─────────────────┐
│   Navegador     │
│   (Cliente)     │
└────────┬────────┘
         │ HTTP/WebSocket
         │ (puerto 8000)
         ▼
┌─────────────────┐
│  FastAPI        │◄──► GUI Callback
│  (Web Server)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   EV_Central    │
│   (TCP Server)  │◄──── Monitors/Drivers (TCP 9099)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Kafka         │◄──── Telemetría
│  (Mensajería)   │
└─────────────────┘
```

## 🎨 Personalización

Los archivos del GUI están en `src/EV_Central/web/`:
- `index.html` - Estructura HTML
- `style.css` - Estilos y colores
- `app.js` - Lógica JavaScript y WebSockets

Puedes modificarlos para personalizar el aspecto y comportamiento del GUI.

## 📱 Acceso desde móvil

1. Asegúrate de que el móvil esté en la misma red WiFi
2. Averigua la IP del servidor: `ipconfig` (Windows) o `ifconfig` (Linux)
3. En el móvil, abre: http://[IP_SERVIDOR]:8000

## 🔒 Seguridad

⚠️ **IMPORTANTE:** Este GUI está diseñado para uso en red local/privada.

Para uso en producción, considera:
- Añadir autenticación (OAuth2, JWT)
- Usar HTTPS/WSS en lugar de HTTP/WS
- Configurar CORS apropiadamente
- Limitar acceso por IP o firewall
