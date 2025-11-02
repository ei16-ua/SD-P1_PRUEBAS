# 🚗⚡ EV Charging System - Guía de Prueba Rápida

## 📋 Requisitos Previos

- Python 3.7 o superior
- pip (gestor de paquetes de Python)

## 🚀 Prueba Rápida (Sin Kafka)

### Opción 1: Usar el script automático

```powershell
# En PowerShell
.\test_system.ps1
```

### Opción 2: Paso a paso manual

#### 1. Instalar pygame (solo la primera vez)
```powershell
pip install pygame
```

#### 2. Iniciar CENTRAL con interfaz gráfica

**Terminal 1:**
```powershell
cd c:\Users\Charlie\SistemasDistribuidos\sd-p1-2025
python .\src\EV_Central\EV_Central_GUI.py --host 127.0.0.1 --port 9099
```

✅ **Resultado esperado:**
- Se abre una ventana con el panel de monitorización
- Verás los CPs de ejemplo con sus colores (verde, rojo, gris)
- El servidor está escuchando en el puerto 9099

#### 3. Probar un conductor (modo interactivo)

**Terminal 2 (nueva ventana):**
```powershell
cd c:\Users\Charlie\SistemasDistribuidos\sd-p1-2025
python .\src\EV_Driver\EV_Driver.py --driver-id driver1 --central-host 127.0.0.1 --central-port 9099
```

✅ **Resultado esperado:**
- Aparece un menú interactivo
- Opción 1: Solicitar suministro → Introduce "CP01" (o cualquier CP que veas en la GUI)
- La GUI de CENTRAL se actualiza mostrando la petición
- Recibirás AUTH_GRANTED o AUTH_DENIED según el estado del CP

#### 4. Probar modo automático (desde archivo)

**Terminal 2:**
```powershell
python .\src\EV_Driver\EV_Driver.py --driver-id driver2 --central-host 127.0.0.1 --central-port 9099 --file .\src\EV_Driver\example_services.txt
```

✅ **Resultado esperado:**
- Lee los CPs del archivo (CP01, CP02, CP01, CP03)
- Solicita cada uno automáticamente
- Espera 4 segundos entre cada petición
- La GUI de CENTRAL se actualiza en tiempo real

## 🎨 Interpretación de la GUI

### Colores de los CPs:
- 🟢 **VERDE**: CP disponible o suministrando
- 🔴 **ROJO**: CP averiado
- ⚫ **GRIS**: CP desconectado

### Paneles:
1. **Grid superior**: Estado de todos los CPs
2. **Tabla central**: Peticiones de conductores en curso
3. **Panel inferior**: Mensajes del sistema

### Controles:
- **ESC**: Cerrar la aplicación
- **X**: Cerrar ventana

## 🧪 Verificar que Funciona

### ✅ CENTRAL funciona si:
1. Se abre la ventana gráfica sin errores
2. En la consola dice: "Panel de monitorización iniciado"
3. Ves los CPs de ejemplo en el grid

### ✅ DRIVER funciona si:
1. Se conecta sin error "connection refused"
2. Aparece el menú o inicia el modo automático
3. Puedes solicitar un suministro y recibes respuesta

### ✅ Comunicación funciona si:
1. Al solicitar un suministro desde DRIVER, aparece en la tabla de la GUI
2. Los mensajes se actualizan en el panel inferior de la GUI
3. CENTRAL responde con AUTH_GRANTED o AUTH_DENIED según el estado

## 🐛 Problemas Comunes

### "ModuleNotFoundError: No module named 'pygame'"
```powershell
pip install pygame
```

### "Connection refused" en DRIVER
- Verifica que CENTRAL está ejecutándose
- Comprueba que el puerto es el correcto (9099)
- Asegúrate de usar 127.0.0.1 como host

### La ventana de pygame no se abre
- Verifica que pygame está instalado correctamente
- Ejecuta: `python -c "import pygame; print(pygame.version.ver)"`

## 📝 Ejemplo Completo de Sesión

```powershell
# Terminal 1: Iniciar CENTRAL
PS> python .\src\EV_Central\EV_Central_GUI.py --host 127.0.0.1 --port 9099
# Se abre ventana gráfica ✓

# Terminal 2: Probar conductor
PS> python .\src\EV_Driver\EV_Driver.py --driver-id test1 --central-host 127.0.0.1 --central-port 9099
# Aparece menú
👉 Opción: 1
  Introduce el ID del CP: CP01
# Resultado: ✅ AUTORIZACIÓN CONCEDIDA o ❌ DENEGADA

# Terminal 2: Probar modo automático
PS> python .\src\EV_Driver\EV_Driver.py --driver-id test2 --central-host 127.0.0.1 --central-port 9099 --file .\src\EV_Driver\example_services.txt
# Procesa todos los CPs del archivo automáticamente
```

## 🔧 Archivos Importantes

- `src/EV_Central/EV_Central_GUI.py` - CENTRAL con GUI
- `src/EV_Central/EV_Central.py` - CENTRAL sin GUI (CLI)
- `src/EV_Driver/EV_Driver.py` - Aplicación del conductor
- `src/EV_Driver/example_services.txt` - Archivo de prueba con CPs
- `src/EV_Central/cp_db.json` - Base de datos de CPs (se crea automáticamente)

## 🎯 Siguiente Paso: Añadir Kafka

Para habilitar telemetría en tiempo real y comandos a los CPs:

1. Instalar Kafka y levantarlo (Docker recomendado)
2. Ejecutar CENTRAL con: `--kafka-bootstrap localhost:9092`
3. Ejecutar DRIVER con: `--kafka-bootstrap localhost:9092`
4. Ejecutar CP_E (Engine) y CP_M (Monitor)

Pero primero verifica que todo funciona sin Kafka! ✅
