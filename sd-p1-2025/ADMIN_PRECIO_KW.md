# 🔧 Gestión de Puntos de Carga con Precio y Potencia

## 🎯 Resumen

Ahora cada Punto de Carga (CP) tiene:
- **ID** único (ej: ALC1, FRANCIA)
- **Ubicación** (ej: "Calle Mayor 123")
- **Precio por kWh** (ej: 0.35 €/kWh) - personalizable
- **Potencia máxima** (ej: 11.0 kW) - personalizable

---

## 🚀 Formas de gestionar CPs

### 1️⃣ **Interfaz Gráfica (GUI) - RECOMENDADO**

**Lanzar la GUI:**
```powershell
.\start_admin_gui.bat
```

O directamente:
```powershell
python src/EV_Central/admin_gui.py
```

**Funcionalidades:**
- ✅ Ver todos los CPs con su precio y potencia
- ➕ Añadir nuevos CPs con interfaz visual
- ✏️ Editar ubicación, precio y potencia
- 🗑️ Eliminar CPs con confirmación
- 🔄 Refrescar lista en tiempo real

**Ventajas:**
- No necesitas recordar comandos
- Validación visual de datos
- Confirmaciones antes de eliminar
- Ver estado online/offline de cada CP

---

### 2️⃣ **Línea de comandos (admin_cps.py)**

#### Listar todos los CPs
```powershell
python admin_cps.py --list
```

Salida ejemplo:
```
==========================================================================================
  PUNTOS DE CARGA REGISTRADOS
==========================================================================================
ID           UBICACIÓN                      PRECIO       kW MAX     ESTADO    
------------------------------------------------------------------------------------------
ALC1         C/Helios 5                     0.35 €/kWh   11.0 kW    🟢 Online  
FRANCIA      Rue de Paris 10, Paris         0.40 €/kWh   22.0 kW    ⚫ Offline 
MAD2         C/Serrano 18                   0.40 €/kWh   22.0 kW    🟢 Online  
==========================================================================================
```

#### Añadir un CP con valores por defecto
```powershell
python admin_cps.py --add --id FRANCIA --location "Rue de Paris 10, Paris"
```
- Precio por defecto: **0.35 €/kWh**
- Potencia por defecto: **11.0 kW**

#### Añadir un CP con precio y potencia personalizados
```powershell
# CP caro y rápido (50 kW DC)
python admin_cps.py --add --id SUPER1 --location "Autopista A7" --price 0.55 --kw-max 50.0

# CP barato y lento (7 kW AC)
python admin_cps.py --add --id HOME1 --location "Parking residencial" --price 0.25 --kw-max 7.0

# CP ultra rápido (150 kW Tesla Supercharger)
python admin_cps.py --add --id TESLA1 --location "Centro comercial" --price 0.65 --kw-max 150.0
```

#### Eliminar un CP
```powershell
python admin_cps.py --remove --id FRANCIA
```

---

## ⚙️ Cómo funciona el ENGINE con precio y kW

### Comportamiento automático

El ENGINE lee automáticamente precio y potencia de la base de datos:

```powershell
# El ENGINE busca automáticamente central.db y lee su configuración
python src/EV_CP_E/EV_CP_E.py --cp-id FRANCIA --kafka-bootstrap localhost:29092
```

**Logs que verás:**
```
[INFO] Precio leído de la DB: 0.40 €/kWh
[INFO] Potencia máxima leída de la DB: 22.0 kW
[INFO] Configuración del CP: Precio=0.40 €/kWh, Potencia=22.0 kW
```

### Sobrescribir valores manualmente (opcional)

Si quieres forzar valores específicos sin usar la DB:

```powershell
# Forzar precio y potencia específicos
python src/EV_CP_E/EV_CP_E.py --cp-id FRANCIA --kafka-bootstrap localhost:29092 --price 0.50 --kw-max 100.0
```

### Especificar ruta de la DB (opcional)

Si la DB está en ubicación no estándar:

```powershell
python src/EV_CP_E/EV_CP_E.py --cp-id FRANCIA --kafka-bootstrap localhost:29092 --db-path "C:\ruta\custom\central.db"
```

---

## 📊 Valores típicos de carga

### Por tipo de cargador

| Tipo | Potencia (kW) | Precio típico (€/kWh) | Uso |
|------|---------------|----------------------|-----|
| **AC Monofásico** | 3.7 kW | 0.15 - 0.25 | Casa, garaje privado |
| **AC Trifásico Lento** | 7.0 kW | 0.25 - 0.35 | Parkings públicos |
| **AC Trifásico Normal** | 11.0 kW | 0.30 - 0.40 | Gasolineras, centros comerciales |
| **AC Trifásico Rápido** | 22.0 kW | 0.35 - 0.45 | Electrolineras |
| **DC Rápido** | 50.0 kW | 0.45 - 0.60 | Autopistas, viajes largos |
| **DC Ultra Rápido** | 150.0 kW | 0.55 - 0.70 | Tesla Supercharger, Ionity |
| **DC Hiper Rápido** | 350.0 kW | 0.60 - 0.80 | Futuro (Porsche Taycan) |

### Precios por región (España, ejemplo)

| Ubicación | Precio típico |
|-----------|---------------|
| Casa (propia) | 0.15 €/kWh |
| Parking empresa | 0.20 €/kWh |
| Gasolinera urbana | 0.35 €/kWh |
| Autopista | 0.45 €/kWh |
| Tesla Supercharger | 0.55 €/kWh |

---

## 🔄 Migración de base de datos existente

Si ya tienes una base de datos `central.db` sin los campos `price_eur_kwh` y `kw_max`:

```powershell
python migrate_database.py
```

Esto añadirá automáticamente las columnas con valores por defecto:
- `price_eur_kwh`: 0.35 €/kWh
- `kw_max`: 11.0 kW

---

## 🧪 Flujo completo de trabajo

### Escenario: Añadir un CP en Francia

#### Opción A: Con GUI (más fácil)

1. **Lanzar la GUI:**
   ```powershell
   .\start_admin_gui.bat
   ```

2. **Rellenar el formulario:**
   - ID: `FRANCIA`
   - Ubicación: `Rue de Paris 10, Paris`
   - Precio: `0.40`
   - Potencia: `22.0`

3. **Clic en "➕ Añadir"**

4. **Crear topic de Kafka:**
   ```powershell
   python scripts/create_kafka_topics.py --bootstrap localhost:29092 --cp-id FRANCIA
   ```

5. **Iniciar ENGINE:**
   ```powershell
   python src/EV_CP_E/EV_CP_E.py --cp-id FRANCIA --kafka-bootstrap localhost:29092
   ```
   → Lee automáticamente 0.40 €/kWh y 22.0 kW de la DB

#### Opción B: Línea de comandos

```powershell
# 1. Añadir CP con configuración específica
python admin_cps.py --add --id FRANCIA --location "Rue de Paris 10, Paris" --price 0.40 --kw-max 22.0

# 2. Crear topic de Kafka
python scripts/create_kafka_topics.py --bootstrap localhost:29092 --cp-id FRANCIA

# 3. Iniciar ENGINE (lee configuración de la DB automáticamente)
python src/EV_CP_E/EV_CP_E.py --cp-id FRANCIA --kafka-bootstrap localhost:29092
```

### Verificar que funciona

1. **Ver en la GUI del CENTRAL:**
   ```powershell
   .\PC1_CENTRAL.bat
   ```
   → Abrir http://localhost:8000
   → Debe aparecer FRANCIA con precio 0.40 €/kWh

2. **Probar carga desde Driver Web:**
   ```powershell
   .\start_driver_gui.bat
   ```
   → Abrir http://localhost:8081
   → Seleccionar FRANCIA → Ver precio 0.40 €/kWh
   → Solicitar carga → Ver telemetría con ~22 kW

---

## 📝 Archivos modificados

### Base de datos
- ✅ `src/EV_Central/database.py` - Añadidos campos `price_eur_kwh` y `kw_max`
- ✅ `migrate_database.py` - Script de migración para DBs existentes
- ✅ `reset_database.py` - Incluye precios y potencias para CPs de ejemplo

### Administración
- ✅ `admin_cps.py` - CLI con parámetros `--price` y `--kw-max`
- ✅ `src/EV_Central/admin_gui.py` - **GUI nueva** para gestión visual
- ✅ `start_admin_gui.bat` - Lanzador de la GUI

### ENGINE
- ✅ `src/EV_CP_E/EV_CP_E.py` - Lee precio y kW de la DB automáticamente
  - Nuevo campo: `CPState.kw_max`
  - Nuevos parámetros: `--price`, `--kw-max`, `--db-path`
  - Simulación: kW = `kw_max ± 5%`

---

## ⚠️ Notas importantes

1. **Compatibilidad con DB antigua:**
   - Ejecuta `python migrate_database.py` si ya tienes CPs registrados

2. **Valores por defecto:**
   - Si NO especificas precio/kW al añadir un CP: 0.35 €/kWh y 11.0 kW
   - Si el ENGINE no encuentra la DB: usa 0.35 €/kWh y 11.0 kW

3. **Prioridad de configuración del ENGINE:**
   1. Parámetros `--price` y `--kw-max` (más alta prioridad)
   2. Valores en `central.db` para ese CP
   3. Valores por defecto: 0.35 €/kWh y 11.0 kW (más baja prioridad)

4. **Topic de Kafka:**
   - Sigue siendo necesario crear `cp.commands.<CP_ID>` manualmente
   - O usar `START_KAFKA.bat` con `--from-db` para crear todos automáticamente

---

## 🎓 Ejemplo completo para el examen

```powershell
# 1. Migrar DB si ya existe
python migrate_database.py

# 2. Abrir GUI de administración
.\start_admin_gui.bat

# 3. Añadir CP "EXAMEN" con precio 0.30 €/kWh y 50 kW DC
#    (desde la GUI o CLI)
python admin_cps.py --add --id EXAMEN --location "Aula 2B" --price 0.30 --kw-max 50.0

# 4. Crear topic
python scripts/create_kafka_topics.py --bootstrap localhost:29092 --cp-id EXAMEN

# 5. Iniciar sistema completo
.\START_KAFKA.bat
.\PC1_CENTRAL.bat
python src/EV_CP_E/EV_CP_E.py --cp-id EXAMEN --kafka-bootstrap localhost:29092

# 6. Verificar en la GUI: http://localhost:8000
#    → EXAMEN debe aparecer con 0.30 €/kWh y ~50 kW al cargar
```

---

## 🚨 Solución de problemas

### "Precio y kW no se leen de la DB"
- Verifica que ejecutaste `migrate_database.py`
- Comprueba que `central.db` existe en `src/EV_Central/`
- Mira los logs del ENGINE: debe decir "Precio leído de la DB"

### "El ENGINE usa siempre 0.35 €/kWh"
- El CP no está registrado en la DB → añádelo con `admin_cps.py --add`
- La DB está en ubicación no estándar → usa `--db-path`
- Especificaste `--price` manualmente → ese valor tiene prioridad

### "La GUI no muestra precios"
- Ejecuta `migrate_database.py` para añadir las columnas
- Cierra y vuelve a abrir la GUI con `.\start_admin_gui.bat`

---

## 📚 Comandos rápidos

```powershell
# Gestión
python admin_cps.py --list                                    # Listar CPs
.\start_admin_gui.bat                                         # GUI de administración

# Añadir CPs con diferentes configuraciones
python admin_cps.py --add --id CP1 --location "Calle X"                                # Default
python admin_cps.py --add --id CP2 --location "Calle Y" --price 0.50 --kw-max 22.0   # Custom

# Migración
python migrate_database.py                                    # Actualizar DB antigua
python reset_database.py                                      # Reset completo

# ENGINE con auto-configuración
python src/EV_CP_E/EV_CP_E.py --cp-id CP1 --kafka-bootstrap localhost:29092
```

---

✅ **Todo listo para gestionar CPs con precio y potencia personalizables!**
