# Sistema EV Charging - Guía de Inicio Rápido

## 📋 Pre-requisitos
- Python 3.12+
- Kafka corriendo en 192.168.1.17:9092 (opcional pero recomendado)
- SQLite 3.49+
- Pygame 2.6+

## 🚀 Inicio Rápido - Sistema Completo

### Opción 1: Inicio Automático (Recomendado)
```bash
start_complete_system.bat
```
Esto iniciará:
- ✅ CENTRAL con GUI (puerto 9099)
- ✅ 10 Charging Points (puertos 7001-7010)
- ✅ 10 Monitors conectados al CENTRAL

### Opción 2: Inicio Manual por Componentes

#### 1. Inicializar Base de Datos
```bash
python reset_database.py
python create_drivers.py
```

#### 2. Iniciar CENTRAL con GUI
```bash
start_central_gui.bat
```

#### 3. Iniciar todos los CPs
```bash
start_all_cps.bat
```

#### 4. Iniciar Drivers

**Opción A: Interfaz Gráfica (Recomendado)**
```bash
start_driver_gui.bat DRIVER01
start_driver_gui.bat DRIVER02
start_driver_gui.bat DRIVER03
```

**Opción B: Interfaz de Consola**
```bash
start_driver.bat DRIVER01
start_driver.bat DRIVER02
start_driver.bat DRIVER03
```

**Opción C: Modo Automático con Archivo**
```bash
# Procesa lista de CPs automáticamente (espera 4s entre cada uno)
start_driver_auto.bat DRIVER01                      # Usa cp_list_example.txt
start_driver_auto.bat DRIVER01 cp_list_all.txt     # Usa archivo específico
```

**Demo Visual con 3 Drivers:**
```bash
demo_3drivers_gui.bat
```

## 🔧 Configuración

### Parámetros Obligatorios (Driver)

Según especificación, **EV_Driver** requiere:

```bash
python .\src\EV_Driver\EV_Driver.py \
  --kafka-bootstrap 192.168.1.17:9092 \  # IP:puerto del Broker Kafka
  --driver-id DRIVER01 \                  # ID único registrado en CENTRAL
  --central-host 192.168.1.17 \          # IP de CENTRAL
  --central-port 9099 \                   # Puerto de CENTRAL
  [--file archivo.txt]                    # Opcional: archivo con CPs
```

**Nota:** Los scripts `.bat` ya incluyen todos estos parámetros.

### Red
- **CENTRAL**: 192.168.1.17:9099
- **Engines**: 192.168.1.11:7001-7010
- **Kafka**: 192.168.1.17:9092

### Charging Points Disponibles
1. **ALC1** - Alicante (puerto 7001)
2. **ALC3** - Gran Via 2 (puerto 7002)
3. **MAD2** - C/Serrano 18 (puerto 7003)
4. **MAD3** - C/Fco 23 (puerto 7004)
5. **MAD1** - C/Alcalese (puerto 7005)
6. **SEV3** - Gran Via 1 (puerto 7006)
7. **SEV2** - Valencia (puerto 7007)
8. **VAL3** - Malaga Aero (puerto 7008)
9. **VAL1** - San Javier (puerto 7009)
10. **COR1** - Menorca (puerto 7010)

### Conductores Disponibles
- **DRIVER01** - Carlos Martinez
- **DRIVER02** - Ana Lopez
- **DRIVER03** - Miguel Garcia
- **DRIVER04** - Laura Sanchez
- **DRIVER05** - David Rodriguez
- **DRIVER06** - Sara Fernandez
- **DRIVER07** - Pedro Jimenez
- **DRIVER08** - Elena Ruiz
- **DRIVER09** - Javier Moreno

## 🎨 Interfaces Gráficas (GUI)

### Panel CENTRAL (Pygame)
**Estados de los CPs:**
- 🟢 **VERDE** - Disponible o Suministrando
- 🟠 **NARANJA** - Parado (Out of Order)
- 🔴 **ROJO** - Averiado (Fault)
- ⚫ **GRIS** - Desconectado

**Información en Tiempo Real:**
Cuando un CP está **SUMINISTRANDO**, se muestra:
- 👤 **ID del Conductor** (en amarillo, grande)
- ⚡ **Consumo actual** (kW)
- 💰 **Coste acumulado** (€, en amarillo)

### Panel DRIVER (Pygame)
**Características:**
- 🎯 Campo de entrada para solicitar CP por ID
- 🔌 Vista de estado de carga en tiempo real
- ⚡ Telemetría vía Kafka (kW y € actualizados cada segundo)
- ✅ Botón SOLICITAR para pedir suministro
- 🛑 Botón FINALIZAR para terminar la carga
- 🔒 Protección: No permite salir mientras está cargando

**Flujo de uso:**
1. Introduce el CP_ID (ej: ALC1)
2. Click en SOLICITAR
3. Si autorizado: visualiza en tiempo real kW y €
4. Cuando termines: Click en FINALIZAR
5. ESC para salir (solo si NO estás cargando)

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                    CENTRAL (GUI)                     │
│              192.168.1.17:9099                       │
│  - Base de datos SQLite                              │
│  - Autorización de drivers                           │
│  - Panel Pygame con estado de todos los CPs         │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┬───────────┐
        │                     │           │
   ┌────▼────┐           ┌────▼────┐     ...
   │ MONITOR │           │ MONITOR │
   │  (ALC1) │           │  (ALC3) │
   └────┬────┘           └────┬────┘
        │                     │
   ┌────▼────┐           ┌────▼────┐
   │ ENGINE  │           │ ENGINE  │
   │ :7001   │◄──Kafka──►│ :7002   │
   │ (ALC1)  │           │ (ALC3)  │
   └─────────┘           └─────────┘
        ▲                     ▲
        │                     │
   ┌────┴────┐           ┌────┴────┐
   │ DRIVER  │           │ DRIVER  │
   │  (GUI)  │           │  (GUI)  │
   │    01   │◄──Kafka──►│    02   │
   │  (TCP)  │ Telemetry │  (TCP)  │
   └─────────┘           └─────────┘
```

**Comunicación:**
- **TCP**: Drivers ↔ CENTRAL (REQ/AUTH/FINISH)
- **Kafka**: Engines → CENTRAL → Drivers (telemetría en tiempo real)

## 🔍 Verificación

### Comprobar que todo funciona
1. Abre el GUI → Todos los CPs deben aparecer **GRISES** inicialmente
2. Tras ~2 segundos → Los CPs se ponen **VERDES** (Disponible)
3. Inicia un driver → El CP pasa a **VERDE** "Suministrando" con datos del conductor
4. Forzar fallo → El CP pasa a **ROJO** (Averiado)
5. Stop desde CENTRAL → El CP pasa a **NARANJA** (Parado)

### Logs
Cada componente muestra logs en su ventana de terminal:
- **CENTRAL**: Conexiones, autorizaciones, comandos
- **ENGINE**: Telemetría, health checks, estados
- **MONITOR**: Sincronización con CENTRAL
- **DRIVER**: Solicitudes, confirmaciones, consumo

## ⚠️ Troubleshooting

### "Connection refused" en CENTRAL
- Verifica que Kafka esté corriendo: `netstat -an | findstr 9092`
- Si no tienes Kafka, el sistema funcionará igual (sin telemetría)

### CPs quedan en GRIS
- Verifica que los Engines están corriendo en puertos 7001-7010
- Verifica que los Monitors pueden conectarse a 192.168.1.17:9099

### Driver no se autoriza
- Verifica que el DRIVER_ID existe en la base de datos
- Ejecuta `create_drivers.py` para recrear los 9 conductores

### GUI no se abre
- Verifica que Pygame está instalado: `pip install pygame`
- Verifica que no hay otro proceso en puerto 9099

## 📝 Notas

- El sistema soporta **10 CPs simultáneos**
- Cada CP puede atender **1 conductor a la vez**
- La tarifa es **0.35 €/kWh** por defecto
- Los datos se persisten en `src/EV_Central/central.db`
- Kafka es **opcional** pero recomendado para telemetría completa

## 🎯 Prueba Completa

```bash
# 1. Reset completo
python reset_database.py
python create_drivers.py

# 2. Iniciar sistema
start_complete_system.bat

# 3. Iniciar 3 drivers en paralelo
start_driver.bat DRIVER01
start_driver.bat DRIVER02
start_driver.bat DRIVER03

# 4. Observar el GUI
# - 3 CPs pasan a SUMINISTRANDO
# - Se muestra DRIVER0X, kW, y € en tiempo real
# - Resto de CPs quedan DISPONIBLES

# 5. Detener un driver (Ctrl+C)
# - El CP vuelve a DISPONIBLE
```

---
**Sistema SD EV Charging Solution** - Práctica Sistemas Distribuidos 2024-2025
