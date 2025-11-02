# GUI Web del Driver - Guía

## 🌐 Ventajas del GUI Web

### ✅ Sin instalaciones en el cliente
- Solo necesitas un **navegador web** moderno
- No requiere Python, Pygame ni otras librerías
- Funciona en **cualquier dispositivo**: PC, tablet, móvil

### ✅ Interfaz moderna y responsive
- Diseño atractivo con gradientes y animaciones
- Actualización en tiempo real vía WebSockets
- Compatible con pantallas táctiles

### ✅ Fácil despliegue
- Acceso remoto simple: `http://IP:5000`
- Múltiples drivers simultáneos (diferentes puertos)
- No requiere configuración en el cliente

---

## 🚀 Cómo iniciar

### Opción 1: Script automático
```powershell
.\START_DRIVER_WEB.bat
```

### Opción 2: Manual
```powershell
python src\EV_Driver\EV_Driver_Web.py --driver-id 5 --central-host localhost --central-port 9099 --web-port 5000 --kafka-bootstrap localhost:29092
```

### Opción 3: Desde PC3_DRIVER.bat
```powershell
.\PC3_DRIVER.bat
# Selecciona opción 1 (GUI Web)
```

---

## 📊 Parámetros

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--driver-id` | ID único del conductor | `5`, `23`, `100` |
| `--central-host` | IP del CENTRAL | `localhost`, `192.168.1.100` |
| `--central-port` | Puerto TCP del CENTRAL | `9099` (por defecto) |
| `--web-port` | Puerto del GUI Web | `5000`, `5001`, `5002`... |
| `--kafka-bootstrap` | Kafka (opcional) | `localhost:29092` |

---

## 🎨 Características de la Interfaz

### Panel Principal
- **Driver ID** destacado en dorado
- **Estado actual** con iconos:
  - ⏸️ EN ESPERA (blanco)
  - 🔌 CARGANDO (verde)

### Panel de Carga (solo cuando está activo)
- **Métricas grandes** y visibles
- **kW** en caja naranja
- **EUR** en caja amarilla con fondo resaltado
- Actualización automática cada segundo

### Selector de CP
- Lista desplegable con todos los CPs disponibles
- Estados mostrados: DISPONIBLE, OCUPADO, DESCONECTADO, FALLO
- Solo permite seleccionar CPs disponibles

### Botones de Acción
- **REQUEST SERVICE**: Solicitar carga (azul/morado)
- **FINISH & PAY**: Finalizar y pagar (rosa/rojo)
- Deshabilitados cuando no aplican

### Log de Mensajes
- Mensajes con timestamp
- Colores según tipo:
  - Verde: éxito
  - Rojo: error
  - Amarillo: advertencia
  - Blanco: información

---

## 🔌 Flujo de Uso

1. **Abrir navegador** en `http://localhost:5000` (o IP:puerto del servidor)

2. **Seleccionar CP** de la lista desplegable

3. **Hacer clic en "REQUEST SERVICE"**
   - El sistema solicita autorización al CENTRAL
   - Si se concede, el panel de carga aparece
   - Las métricas empiezan a actualizarse

4. **Observar la carga**
   - kW y EUR se actualizan en tiempo real
   - La información también se muestra en el panel superior

5. **Hacer clic en "FINISH & PAY"**
   - Finaliza la sesión de carga
   - Muestra el total consumido y pagado
   - El CP queda liberado

---

## 🌍 Acceso Remoto

### Desde otro PC en la misma red:
1. Averigua la IP del servidor:
   ```powershell
   ipconfig
   ```
   Busca "Dirección IPv4" (ej: `192.168.1.50`)

2. Abre en el navegador del cliente:
   ```
   http://192.168.1.50:5000
   ```

### Desde un móvil:
1. Conéctate a la misma WiFi
2. Abre el navegador del móvil
3. Introduce: `http://IP_DEL_SERVIDOR:5000`

---

## 🔧 Múltiples Drivers

Para ejecutar varios drivers simultáneamente, usa **puertos diferentes**:

```powershell
# Driver 5 en puerto 5001
python src\EV_Driver\EV_Driver_Web.py --driver-id 5 --web-port 5001 --central-host localhost

# Driver 23 en puerto 5002
python src\EV_Driver\EV_Driver_Web.py --driver-id 23 --web-port 5002 --central-host localhost

# Driver 100 en puerto 5003
python src\EV_Driver\EV_Driver_Web.py --driver-id 100 --web-port 5003 --central-host localhost
```

Acceso:
- Driver 5: http://localhost:5001
- Driver 23: http://localhost:5002
- Driver 100: http://localhost:5003

---

## 🐛 Troubleshooting

### El navegador no carga
```powershell
# Verifica que el servidor esté corriendo
netstat -ano | findstr :5000
```

### WebSocket no conecta
- Abre consola del navegador (F12)
- Verifica errores en la pestaña "Console"
- Refresca la página (F5)

### No se ven CPs en la lista
- El CENTRAL debe estar corriendo
- Verifica la conexión con el CENTRAL
- Mira el log del servidor para errores

### No se actualizan las métricas
- Kafka debe estar corriendo
- Verifica el parámetro `--kafka-bootstrap`
- El ENGINE debe estar enviando telemetría

---

## 📱 Comparación GUI Web vs Pygame

| Característica | GUI Web | Pygame GUI |
|----------------|---------|------------|
| Instalación en cliente | ❌ No requiere | ✅ Requiere Python + Pygame |
| Acceso remoto | ✅ Fácil (URL) | ❌ Difícil |
| Móviles/tablets | ✅ Sí | ❌ No |
| Múltiples monitores | ✅ Pestañas del navegador | ❌ Ventanas separadas |
| Diseño | ✅ Moderno HTML5/CSS3 | ⚠️ Básico |
| Actualización | ✅ WebSockets real-time | ⚠️ Polling |

---

## 🎯 Escenario de Examen

### PC1 - CENTRAL
```powershell
PC1_CENTRAL.bat
```
- GUI Web en: http://localhost:8000

### PC2 - Múltiples CPs
```powershell
PC2_MONITOR_ENGINE.bat  # Ejecutar varias veces
```

### PC3 - Drivers
```powershell
PC3_DRIVER.bat
# Opción 1: GUI Web
# Puertos: 5001, 5002, 5003...
```

Cada estudiante abre en su navegador:
- http://IP_PC3:5001 (Driver 1)
- http://IP_PC3:5002 (Driver 2)
- http://IP_PC3:5003 (Driver 3)

---

## ✨ Tips

- **F12** en el navegador para ver la consola de desarrollador y debugging
- **Ctrl+Shift+R** para refrescar forzando recarga de cache
- **Modo responsive** (F12 → Toggle device toolbar) para simular móvil
- Los **WebSockets se reconectan automáticamente** si se pierde la conexión

¡Disfruta del nuevo GUI web! 🚀
