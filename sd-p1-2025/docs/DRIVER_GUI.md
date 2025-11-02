# 🚗 Driver GUI - Interfaz Gráfica del Conductor

## 📋 Descripción

Interfaz gráfica con **Pygame** para que los conductores soliciten y monitoricen suministros de recarga en tiempo real.

## ✨ Características

### 🎯 Funcionalidades Principales

1. **Solicitud de Suministro**
   - Campo de entrada para introducir el CP_ID
   - Botón SOLICITAR para enviar la petición al CENTRAL
   - Validación y feedback visual instantáneo

2. **Monitorización en Tiempo Real**
   - 📍 CP donde estás cargando
   - ⚡ Potencia actual (kW) - actualizado cada segundo
   - 💰 Coste acumulado (€) - actualizado cada segundo
   - Telemetría vía **Kafka** directamente del Engine

3. **Control de Sesión**
   - ✅ Botón FINALIZAR para terminar la carga
   - 🔒 Protección: No permite salir mientras está cargando
   - Mensajes de estado con colores (verde=éxito, rojo=error)

4. **Interfaz Intuitiva**
   - Colores según estado (verde=cargando, gris=esperando)
   - Instrucciones siempre visibles
   - Diseño limpio y profesional

## 🚀 Cómo Usar

### Inicio Rápido

```bash
# Iniciar un driver específico
start_driver_gui.bat DRIVER01

# Demo con 3 drivers
demo_3drivers_gui.bat
```

### Uso Manual

```bash
python .\src\EV_Driver\EV_Driver_GUI.py --driver-id DRIVER01 --central-host 192.168.1.17 --central-port 9099 --kafka-bootstrap 192.168.1.17:9092
```

### Parámetros

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--driver-id` | ID único del conductor | DRIVER01 |
| `--central-host` | IP del servidor CENTRAL | 192.168.1.17 |
| `--central-port` | Puerto del CENTRAL | 9099 |
| `--kafka-bootstrap` | Kafka (opcional) | 192.168.1.17:9092 |

## 🎮 Interacción

### 1️⃣ Solicitar Suministro

1. **Click** en el campo de texto
2. Introduce el **CP_ID** (ej: `ALC1`, `MAD2`, `SEV3`)
3. **Click** en el botón **SOLICITAR**
4. Espera la respuesta del CENTRAL:
   - ✅ **Verde**: Autorizado → Comienza la carga
   - ❌ **Rojo**: Denegado → Ver razón en el mensaje

### 2️⃣ Durante la Carga

- La pantalla muestra automáticamente:
  - 📍 CP donde estás cargando (grande, amarillo)
  - ⚡ Potencia instantánea (actualizada cada segundo)
  - 💰 Coste total acumulado
- **NO puedes** solicitar otro CP mientras cargas
- **NO puedes** salir de la aplicación

### 3️⃣ Finalizar Suministro

1. **Click** en el botón **FINALIZAR** (rojo)
2. La carga termina
3. El sistema muestra el resumen:
   - Consumo total (kW)
   - Coste total (€)
4. Vuelves al estado de espera

### 4️⃣ Salir

- Presiona **ESC** o cierra la ventana
- Solo funciona si **NO estás cargando**
- Si intentas salir mientras cargas: mensaje de advertencia

## 🎨 Elementos Visuales

### Cabecera
```
┌─────────────────────────────────────────┐
│ 🚗 DRIVER: DRIVER01                     │
│ 🔌 CARGANDO / ⏸️  EN ESPERA             │
└─────────────────────────────────────────┘
```

### Estado de Carga (cuando está activo)
```
┌─────────────────────────────────────────┐
│           Punto de Recarga:             │
│                 ALC1                    │ (amarillo)
│                                         │
│    ⚡ 11.25 kW     💰 0.0531 €          │
│                                         │
│         [ FINALIZAR ]                   │ (botón rojo)
└─────────────────────────────────────────┘
```

### Panel de Solicitud (cuando está inactivo)
```
┌─────────────────────────────────────────┐
│ Solicitar Suministro                    │
│                                         │
│ [Introduce el CP_ID...   ] [SOLICITAR] │
└─────────────────────────────────────────┘
```

## 🔌 Integración con Kafka

El Driver GUI usa **Kafka** para recibir telemetría en tiempo real:

### Topic que consume
- `cp.telemetry`: Telemetría de todos los CPs

### Filtrado inteligente
```python
# Solo procesa mensajes de:
1. El CP donde está cargando (cp_id == current_cp)
2. Para este driver (driver_id == self.driver_id)
```

### Payload esperado
```json
{
  "cp_id": "ALC1",
  "driver_id": "DRIVER01",
  "kw": 11.25,
  "eur": 0.0531,
  "ts": 1730000000
}
```

### Actualización
- **Frecuencia**: Cada 1 segundo
- **Latencia**: < 100ms típica
- **Fallback**: Si no hay Kafka, solo muestra estado sin telemetría

## 📊 Estados del Driver

```
┌─────────────┐
│  EN ESPERA  │ ← Estado inicial
└──────┬──────┘
       │ Solicita CP
       ↓
┌─────────────┐
│ SOLICITANDO │
└──────┬──────┘
       │ AUTH_GRANTED
       ↓
┌─────────────┐
│  CARGANDO   │ ← Recibe telemetría cada 1s
└──────┬──────┘
       │ Click FINALIZAR
       ↓
┌─────────────┐
│  EN ESPERA  │ ← Vuelta al inicio
└─────────────┘
```

## ⚠️ Mensajes de Error

| Mensaje | Significado | Acción |
|---------|-------------|--------|
| `CP_NOT_FOUND` | El CP no existe | Verifica el ID correcto |
| `DISCONNECTED` | CP desconectado | Espera a que se conecte |
| `BUSY` | CP ocupado | Espera o elige otro |
| `FAULT` | CP averiado | Elige otro CP |
| `OUT_OF_ORDER` | CP parado por CENTRAL | Elige otro CP |

## 🎯 Ejemplo de Uso Completo

```bash
# 1. Asegúrate de que el sistema esté corriendo
start_complete_system.bat

# 2. Inicia tu driver con GUI
start_driver_gui.bat DRIVER01

# 3. En la ventana GUI:
#    - Click en el campo de texto
#    - Escribe: ALC1
#    - Click en SOLICITAR

# 4. Si está disponible:
#    - Verás "✅ Autorizado en ALC1" (verde)
#    - La pantalla cambia a modo CARGANDO
#    - kW y € se actualizan cada segundo

# 5. Cuando termines:
#    - Click en FINALIZAR
#    - Verás el resumen del suministro
#    - Vuelves al estado de espera

# 6. Para salir:
#    - Presiona ESC
#    - O cierra la ventana
```

## 🔧 Troubleshooting

### La GUI no se abre
```bash
# Verificar que Pygame está instalado
pip install pygame

# Verificar que Python encuentra el módulo
python -c "import pygame; print(pygame.version.ver)"
```

### No recibo telemetría
```bash
# 1. Verificar que Kafka está corriendo
netstat -an | findstr 9092

# 2. Verificar que el Engine está publicando
# (Mira los logs del Engine correspondiente)

# 3. Si no tienes Kafka: la GUI funciona igual
# pero sin actualizaciones en tiempo real
```

### No puedo solicitar otro CP
- ✅ **Normal**: Solo puedes tener un suministro activo
- Debes finalizar el actual primero

### No puedo salir
- ✅ **Normal**: Protección para evitar salir mientras cargas
- Debes finalizar el suministro primero

## 📁 Archivos Relacionados

- `src/EV_Driver/EV_Driver_GUI.py` - Código fuente de la GUI
- `src/EV_Driver/EV_Driver.py` - Lógica del driver (reutilizada)
- `start_driver_gui.bat` - Script de inicio
- `demo_3drivers_gui.bat` - Demo con 3 drivers

## 🎨 Personalización

### Colores (en el código)
```python
GREEN = (46, 204, 113)    # Éxito
RED = (231, 76, 60)       # Error
YELLOW = (241, 196, 15)   # Destacado
BLUE = (52, 152, 219)     # Input activo
GRAY = (149, 165, 166)    # Inactivo
```

### Tamaño de ventana
```python
# En main()
gui = DriverGUI(driver, width=800, height=600)
```

---

**Desarrollado para el Sistema EV Charging - Práctica SD 2024-2025**
