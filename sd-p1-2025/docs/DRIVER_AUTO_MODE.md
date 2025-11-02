# 📄 Modo Automático con Archivo - EV Driver

## 📋 Descripción

El driver puede leer un archivo con una lista de CPs y solicitar suministros automáticamente, uno tras otro, con una **espera de 4 segundos** entre cada solicitud.

## 📝 Formato del Archivo

### Estructura
```
# Comentarios empiezan con #
# Un CP_ID por línea

ALC1
MAD2
SEV3
VAL1
```

### Reglas
- ✅ **Un CP_ID por línea**
- ✅ Líneas que empiezan con `#` son ignoradas (comentarios)
- ✅ Líneas vacías son ignoradas
- ✅ Se procesan en orden secuencial

## 🚀 Cómo Usar

### Opción 1: Script automatizado (Recomendado)

```bash
# Usar archivo por defecto (cp_list_example.txt)
start_driver_auto.bat DRIVER01

# Usar archivo personalizado
start_driver_auto.bat DRIVER01 cp_list_all.txt
start_driver_auto.bat DRIVER02 mi_archivo.txt
```

### Opción 2: Comando directo

```bash
python .\src\EV_Driver\EV_Driver.py --driver-id DRIVER01 --central-host 192.168.1.17 --central-port 9099 --kafka-bootstrap 192.168.1.17:9092 --file cp_list_example.txt
```

### Opción 3: Con GUI (cae a modo consola si se usa --file)

```bash
python .\src\EV_Driver\EV_Driver_GUI.py --driver-id DRIVER01 --central-host 192.168.1.17 --central-port 9099 --kafka-bootstrap 192.168.1.17:9092 --file cp_list_example.txt
```

## 📊 Flujo de Ejecución

```
1. Leer archivo
   ↓
2. Mostrar lista de CPs a procesar
   ↓
3. Para cada CP en el archivo:
   ├─ Solicitar autorización al CENTRAL
   │  ├─ Si DENEGADO → Mostrar razón y continuar
   │  └─ Si AUTORIZADO:
   │     ├─ Esperar inicio de suministro (8 segundos)
   │     ├─ Recibir telemetría vía Kafka
   │     └─ Finalizar suministro
   ├─ Esperar 4 segundos
   └─ Continuar con siguiente CP
   ↓
4. Proceso completado
```

## ⏱️ Tiempos

| Evento | Duración | Nota |
|--------|----------|------|
| Espera de suministro | 8 segundos | Simulación de carga real |
| Entre solicitudes | **4 segundos** | ✅ Requisito cumplido |
| Total por CP (éxito) | ~12 segundos | 8s carga + 4s espera |
| Total por CP (fallo) | 4 segundos | Solo espera entre solicitudes |

## 📂 Archivos de Ejemplo Incluidos

### `cp_list_example.txt` (4 CPs)
```
ALC1
MAD2
SEV3
VAL1
```
**Uso:** Prueba rápida (~48 segundos)

### `cp_list_all.txt` (10 CPs)
```
ALC1
ALC3
MAD2
MAD3
MAD1
SEV3
SEV2
VAL3
VAL1
COR1
```
**Uso:** Prueba completa de todos los CPs (~2 minutos)

## 🎯 Ejemplo Completo

```bash
# 1. Asegúrate de que el sistema esté corriendo
start_complete_system.bat

# 2. Crea tu archivo de CPs (o usa uno existente)
notepad mi_ruta.txt
# Contenido:
#   ALC1
#   MAD2
#   SEV3

# 3. Ejecuta el driver en modo automático
start_driver_auto.bat DRIVER01 mi_ruta.txt

# Salida esperada:
#   ╔════════════════════════════════════════════╗
#   ║  📄 MODO AUTOMÁTICO - Leyendo archivo     ║
#   ║  Archivo: mi_ruta.txt                     ║
#   ╚════════════════════════════════════════════╝
#
#   📋 Se solicitarán 3 suministros:
#      1. ALC1
#      2. MAD2
#      3. SEV3
#
#   ════════════════════════════════════════════
#     SERVICIO 1/3
#   ════════════════════════════════════════════
#   📱 Solicitando servicio en ALC1
#   ✅ AUTORIZACIÓN CONCEDIDA
#   ⏳ Esperando a que el CP inicie el suministro...
#
#   [Telemetría en tiempo real]
#   🔌 SUMINISTRANDO en ALC1
#   ⚡ Potencia: 11.25 kW
#   💰 Importe:  0.0531 €
#
#   ✅ SUMINISTRO FINALIZADO
#   CP:       ALC1
#   Consumo:  11.25 kW
#   Total:    0.0531 €
#
#   ⏰ Esperando 4 segundos antes del siguiente...
#   [Continúa con MAD2...]
```

## 🛑 Interrumpir el Proceso

### Durante la ejecución
- **Ctrl+C** durante la espera → Salta al siguiente CP
- **Ctrl+C** dos veces → Termina el proceso completamente

### Ejemplo
```
⏳ Esperando a que el CP inicie el suministro...
   (Presiona Ctrl+C para saltar al siguiente)

[Usuario presiona Ctrl+C]

⏭️  Saltando al siguiente servicio...
⏰ Esperando 4 segundos antes del siguiente suministro...
```

## 📊 Casos de Uso

### 1. Testing de Múltiples CPs
```bash
# Probar todos los CPs del sistema
start_driver_auto.bat DRIVER01 cp_list_all.txt
```

### 2. Ruta Planificada
```bash
# Archivo: ruta_madrid.txt
# MAD1
# MAD2
# MAD3

start_driver_auto.bat DRIVER01 ruta_madrid.txt
```

### 3. Testing de Fallos
```bash
# Archivo: test_errores.txt
# ALC1        # ✅ Existe
# INVALID1    # ❌ No existe (CP_NOT_FOUND)
# MAD2        # ✅ Existe
# francia20   # ❌ No existe (CP_NOT_FOUND)

start_driver_auto.bat DRIVER01 test_errores.txt
```

## ⚠️ Requisitos Previos

1. ✅ CENTRAL corriendo (192.168.1.17:9099)
2. ✅ CPs (Engines + Monitors) corriendo
3. ✅ Kafka corriendo (192.168.1.17:9092) - opcional
4. ✅ Archivo con CPs válido y accesible

## 🔧 Troubleshooting

### "❌ Error: El archivo no existe"
```bash
# Verifica la ruta del archivo
dir cp_list_example.txt

# Si está en otro directorio, usa ruta completa
start_driver_auto.bat DRIVER01 C:\ruta\completa\archivo.txt
```

### No recibe telemetría
- Verifica que Kafka esté corriendo
- Verifica que el Engine esté publicando telemetría
- El modo automático funciona sin Kafka (sin telemetría en vivo)

### CPs siempre denegados
- Verifica que los Monitors estén conectados
- Usa `list` en el CLI de CENTRAL para ver estados
- Verifica IDs en el archivo (sensible a mayúsculas)

## 📋 Checklist de Requisitos (Especificación)

- ✅ **IP y puerto del Broker**: `--kafka-bootstrap 192.168.1.17:9092`
- ✅ **ID del cliente**: `--driver-id DRIVER01` (único en CENTRAL)
- ✅ **Solicitud puntual**: Modo interactivo (sin `--file`)
- ✅ **Leer fichero**: Parámetro `--file nombre.txt`
- ✅ **Procesamiento secuencial**: Un CP tras otro
- ✅ **Espera de 4 segundos**: Entre cada solicitud
- ✅ **Manejo de éxito/fracaso**: Continúa en ambos casos

---

**Sistema EV Charging - Práctica SD 2024-2025**
