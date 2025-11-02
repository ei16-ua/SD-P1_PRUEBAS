# 🚗 Comandos del Driver

## Driver Web GUI (Recomendado)

### **Localhost (Todo en la misma PC)**
```powershell
python src/EV_Driver/EV_Driver_Web.py --driver-id Maria1 --central-host 127.0.0.1 --central-port 50000 --web-port 5000 --kafka-bootstrap 127.0.0.1:29092 --db-path central.db
```

O simplemente:
```powershell
.\START_DRIVER_LOCAL.bat
```

### **Red Local (CENTRAL en otra PC)**
```powershell
python src/EV_Driver/EV_Driver_Web.py --driver-id Maria1 --central-host 192.168.1.11 --central-port 50000 --web-port 5000 --kafka-bootstrap 192.168.1.11:9092 --db-path central.db
```

### **Parámetros:**

- `--driver-id` **(Requerido)**: ID del conductor (puede ser cualquiera: Maria1, Juan2, pepe, etc.)
- `--central-host` **(Requerido)**: IP del CENTRAL
  - `127.0.0.1` si es local
  - `192.168.1.11` si es PC1 en red
- `--central-port` **(Requerido)**: Puerto del CENTRAL (default: 50000)
- `--web-port`: Puerto del navegador (default: 5000)
- `--kafka-bootstrap`: Kafka
  - `127.0.0.1:29092` para localhost
  - `192.168.1.11:9092` para red
- `--db-path`: Ruta a la base de datos (default: `central.db`)
  - **✨ NUEVO**: El driver se auto-registra si no existe

### **Abrir en el navegador:**
```
http://localhost:5000
```

---

## Driver Consola (Sin GUI)

### **Desde archivo de CPs:**
```powershell
python src/EV_Driver/EV_Driver.py --driver-id Maria1 --central-host 127.0.0.1 --central-port 50000 --kafka-bootstrap 127.0.0.1:29092 --file cp_list_example.txt --db-path central.db
```

### **Modo interactivo:**
```powershell
python src/EV_Driver/EV_Driver.py --driver-id Maria1 --central-host 127.0.0.1 --central-port 50000 --kafka-bootstrap 127.0.0.1:29092 --db-path central.db
```

---

## Auto-registro en Base de Datos

✅ **Ahora el driver se registra automáticamente** en la base de datos si no existe

Cuando ejecutas el driver con `--db-path central.db`, automáticamente:
1. Verifica si el `driver_id` existe en la BD
2. Si NO existe, lo registra con:
   - `driver_id`: El ID proporcionado
   - `name`: "Driver {driver_id}"
   - `email`: "{driver_id}@example.com"
3. Si ya existe, continúa sin cambios

### **Verificar drivers en la BD:**
```powershell
python explore_db.py
# Opción 2: Ver todos los drivers
```

---

## Ejemplos de Driver IDs

Puedes usar cualquier ID, por ejemplo:
- `Maria1`, `Juan2`, `Ana3`, `Carlos4`, `Laura5`
- `pepe`, `juan`, `test123`
- `DANTE`, `charlie`, `driver001`

**No es necesario crearlos previamente**, se auto-registran al ejecutar el driver.

---

## Scripts Rápidos

### **PC Local (todo en una PC):**
```powershell
.\START_DRIVER_LOCAL.bat
```

### **PC3 en red (CENTRAL en PC1):**
```powershell
.\PC3_DRIVER.bat
```

---

## Flujo Completo

1. **Iniciar CENTRAL** (PC1 o local):
   ```powershell
   .\start_central_web.bat
   ```

2. **Iniciar Driver** (cualquier PC):
   ```powershell
   .\START_DRIVER_LOCAL.bat
   ```
   
3. **Abrir navegador**: http://localhost:5000

4. **Escribir CP_ID** (ej: ALC1) y hacer click en "REQUEST SERVICE"

5. **Iniciar ENGINE** de ese CP:
   ```powershell
   python src/EV_CP_E/EV_CP_E.py --cp-id ALC1 --kafka-bootstrap 127.0.0.1:29092 --db-path central.db
   ```

6. Ver el panel de carga actualizarse con:
   - ⚡ Potencia actual (kW)
   - 📊 Consumo total (kWh)
   - 💰 Importe total (€)

7. **Detener carga**: Click en "🛑 DETENER CARGA"

8. **Pagar**: Click en "💳 PAGAR Y SALIR"

---

## Notas

- ✅ El driver se auto-registra en la BD al iniciar
- ✅ Muestra potencia actual + consumo total + importe
- ✅ Dos botones separados: DETENER CARGA y PAGAR Y SALIR
- ✅ Puede escribir CP_ID manualmente si no hay lista
- ✅ Funciona sin CENTRAL Web GUI (solo necesita CENTRAL socket)
