# 🐛 Corrección: Bug de Reconexión del Driver

## Problema Original

Cuando un conductor (Driver) se conectaba a un punto de carga (CP) y luego salía de la aplicación sin finalizar el pago (por cierre inesperado, crash, o simplemente olvidando pagar), el CP quedaba bloqueado indefinidamente:

- ✅ Primera conexión: `AUTH_GRANTED`
- 💥 Driver cierra sin FINISH
- ❌ Intento de reconexión: `AUTH_DENIED#BUSY`
- ❌ Otro driver: `AUTH_DENIED#BUSY`
- 🔒 **CP bloqueado permanentemente**

### Impacto
- El CP quedaba inutilizable hasta reiniciar CENTRAL o resetear la base de datos
- El conductor no podía volver a pagar
- Otros conductores tampoco podían usar ese CP

---

## Solución Implementada

### 1. Detección de Reconexión en CENTRAL

**Archivo:** `src/EV_Central/EV_Central.py`

Añadida lógica para detectar cuando el **mismo driver** intenta reconectarse a **su propia carga activa**:

```python
# SOLUCIÓN AL BUG: Si el CP está ocupado PERO es el mismo driver, permitir reconexión
if rec.charging and rec.driver_id == driver_id:
    # El mismo driver está reconectándose a su carga activa
    resp = f"AUTH_GRANTED#{cp_id}#{driver_id}#RECONNECT\n".encode()
    conn.sendall(resp)
    logger.info("Driver {} RECONNECTED to active charge on {}", driver_id, cp_id)
    # No reiniciar la carga, solo reconectar
    continue
```

**Cambios clave:**
- Se verifica si `rec.charging == True` y `rec.driver_id == driver_id`
- Si coincide, se envía `AUTH_GRANTED` con flag `#RECONNECT`
- NO se reinicia el contador de kW ni EUR (se mantienen los valores acumulados)
- El driver puede continuar cargando o finalizar para pagar

### 2. Manejo de RECONNECT en Driver

**Archivo:** `src/EV_Driver/EV_Driver.py`

Actualizada la función `request_service()` para reconocer la respuesta de reconexión:

```python
if parts[0] == "AUTH_GRANTED":
    # Verificar si es una reconexión
    is_reconnect = len(parts) > 3 and parts[3] == "RECONNECT"
    
    if is_reconnect:
        # Reconexión a carga existente
        self.state.current_cp = cp_id
        self.state.charging = True
        # Mantener los valores actuales de kW y EUR
        
        print(f"\n🔄 RECONEXIÓN A CARGA ACTIVA")
        print(f"   Última potencia: {self.state.last_kw:.2f} kW")
        print(f"   Importe acumulado: {self.state.last_eur:.4f} €")
        print(f"   Puedes continuar cargando o FINALIZAR para pagar\n")
```

**Ventajas:**
- Muestra claramente que es una reconexión
- Preserva el estado de la carga (kW y EUR acumulados)
- Permite al usuario decidir: continuar cargando o finalizar

---

## Flujo Corregido

### Escenario 1: Reconexión del Mismo Driver

```
1. DRIVER01 solicita ALC1
   → CENTRAL: AUTH_GRANTED ✅
   → CP: charging=True, driver_id=DRIVER01

2. DRIVER01 se desconecta sin FINISH 💥
   → CP sigue: charging=True, driver_id=DRIVER01

3. DRIVER01 vuelve a conectarse y solicita ALC1
   → CENTRAL detecta: charging=True && driver_id==DRIVER01
   → CENTRAL: AUTH_GRANTED#ALC1#DRIVER01#RECONNECT ✅
   → Driver muestra: "Reconexión a carga activa, importe acumulado: X €"

4. DRIVER01 puede:
   - Opción A: Continuar cargando (recibe telemetría)
   - Opción B: Finalizar con FINISH (paga y libera el CP) ✅
```

### Escenario 2: Otro Driver Intenta Usar el CP

```
1. DRIVER01 solicita ALC1
   → CENTRAL: AUTH_GRANTED ✅

2. DRIVER02 intenta usar ALC1
   → CENTRAL detecta: charging=True && driver_id!=DRIVER02
   → CENTRAL: AUTH_DENIED#BUSY ❌
   → Correcto: otro driver no puede robar la carga
```

---

## Testing

### Script de Prueba Automático

Ejecutar: `python test_reconnect_bug.py`

Este script verifica:
1. ✅ Primera solicitud funciona
2. ✅ Después de desconexión, el mismo driver puede reconectarse
3. ✅ La reconexión incluye el flag RECONNECT
4. ✅ El driver puede finalizar y pagar
5. ✅ Otros drivers son correctamente bloqueados

### Prueba Manual

```powershell
# Terminal 1: CENTRAL
python src\EV_Central\EV_Central.py --host 0.0.0.0 --port 9099 --kafka-bootstrap localhost:29092

# Terminal 2: ENGINE + MONITOR (usa start_all_cps.bat o manual)

# Terminal 3: DRIVER01 - Primera conexión
python src\EV_Driver\EV_Driver.py --driver-id DRIVER01 --central-host localhost --central-port 9099 --kafka-bootstrap localhost:29092
> Solicita ALC1
> Cierra la ventana (Ctrl+C) SIN finalizar ❌

# Terminal 4: DRIVER01 - Reconexión
python src\EV_Driver\EV_Driver.py --driver-id DRIVER01 --central-host localhost --central-port 9099 --kafka-bootstrap localhost:29092
> Solicita ALC1 de nuevo
> Debería mostrar: "🔄 RECONEXIÓN A CARGA ACTIVA" ✅
> Finaliza para pagar ✅
```

---

## Casos de Uso Cubiertos

| Caso | Antes del Fix | Después del Fix |
|------|---------------|-----------------|
| Driver se desconecta sin pagar | ❌ CP bloqueado | ✅ Puede reconectarse y pagar |
| Mismo driver vuelve | ❌ AUTH_DENIED#BUSY | ✅ AUTH_GRANTED#RECONNECT |
| Otro driver intenta usar | ❌ AUTH_DENIED#BUSY | ✅ AUTH_DENIED#BUSY (correcto) |
| Driver reconectado recibe telemetría | ❌ No funciona | ✅ Sigue recibiendo telemetría |
| Driver puede finalizar tras reconexión | ❌ No puede | ✅ FINISH funciona correctamente |

---

## Compatibilidad

✅ **Compatible con código existente:**
- Los drivers antiguos siguen funcionando (ignoran el flag RECONNECT)
- Los CPs y CENTRAL funcionan igual
- No rompe el protocolo existente

✅ **Sin efectos secundarios:**
- Otros drivers siguen siendo bloqueados correctamente
- La telemetría sigue funcionando
- El GUI actualizado muestra la reconexión claramente

---

## Logs de Ejemplo

### CENTRAL (reconexión exitosa)
```
[INFO] Driver DRIVER01 RECONNECTED to active charge on ALC1
```

### Driver (consola)
```
🔄 RECONEXIÓN A CARGA ACTIVA
   CP: ALC1
   Última potencia: 11.23 kW
   Importe acumulado: 0.0456 €
   Puedes continuar cargando o FINALIZAR para pagar
```

---

**Fecha de corrección:** 1 de noviembre de 2025  
**Archivos modificados:**
- `src/EV_Central/EV_Central.py` (lógica de reconexión)
- `src/EV_Driver/EV_Driver.py` (manejo de flag RECONNECT)
- `test_reconnect_bug.py` (nuevo test)
