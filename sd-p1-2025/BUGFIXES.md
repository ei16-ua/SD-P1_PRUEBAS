# Correcciones de Bugs - Sistema EV Charging

## 🐛 Problema 1: Driver puede salir mientras está cargando

### Descripción del problema
Un conductor podía cerrar la aplicación (opción 4 del menú) mientras estaba en medio de un suministro activo, dejando el CP en un estado inconsistente.

### Solución implementada
**Archivo:** `src/EV_Driver/EV_Driver.py`

Modificada la opción 4 del menú interactivo para verificar si hay un suministro activo antes de permitir salir:

```python
elif choice == "4":
    # Verificar si está cargando antes de salir
    if self.state.charging and self.state.current_cp:
        print("\n  ⚠️  NO PUEDES SALIR mientras estás cargando!")
        print(f"     Debes finalizar el suministro en {self.state.current_cp} primero (opción 2)")
    else:
        print("\n👋 Saliendo...")
        self.running = False
        break
```

### Cómo probarlo
1. Inicia un driver: `start_driver.bat DRIVER01`
2. Solicita un CP (opción 1): por ejemplo, `ALC1`
3. Espera a que el suministro inicie
4. Intenta salir (opción 4)
5. **Resultado esperado:** El sistema muestra el mensaje de error y te obliga a finalizar primero (opción 2)

---

## 🐛 Problema 2: Se crean CPs inexistentes cuando el driver se equivoca

### Descripción del problema
Si un conductor solicitaba un CP que no existía (por ejemplo, `francia20`), el sistema CENTRAL automáticamente lo creaba en la base de datos con ubicación "DESCONOCIDO" en lugar de rechazar la solicitud.

### Solución implementada
**Archivo:** `src/EV_Central/EV_Central.py`

#### 1. Nueva función `cp_exists()`
Añadida función para verificar si un CP existe sin crearlo:

```python
def cp_exists(self, cp_id: str) -> bool:
    """Verificar si un CP existe en la base de datos"""
    with self._db_lock:
        return cp_id in self._db
```

#### 2. Modificado el handler de `REQ`
Ahora verifica si el CP existe ANTES de procesarlo:

```python
elif parts[0] == "REQ" and len(parts) >= 3:
    driver_id = parts[1]
    cp_id = parts[2]
    
    # PRIMERO verificar si el CP existe
    if not self.cp_exists(cp_id):
        resp = f"AUTH_DENIED#CP_NOT_FOUND\n".encode()
        conn.sendall(resp)
        logger.warning("Authorization denied for driver {} on {}: CP does not exist", driver_id, cp_id)
        continue
    
    # ... resto del código de autorización
```

#### 3. Documentada la función `ensure_cp()`
Clarificado que `ensure_cp()` solo debe usarse con AUTH/FAULT de Monitors:

```python
def ensure_cp(self, cp_id: str) -> CPRecord:
    """
    SOLO para AUTH/FAULT de Monitors conectados.
    Crea el CP si no existe (caso de Monitor nuevo conectándose).
    """
```

#### 4. Actualizado el Driver para mostrar mensaje claro
**Archivo:** `src/EV_Driver/EV_Driver.py`

Añadido el nuevo código de error:

```python
reasons_map = {
    "DISCONNECTED": "El punto de recarga está desconectado",
    "FAULT": "El punto de recarga está averiado",
    "BUSY": "El punto de recarga está ocupado",
    "OUT_OF_ORDER": "El punto de recarga está fuera de servicio",
    "CP_NOT_FOUND": "El punto de recarga NO EXISTE en el sistema",  # ← NUEVO
}
```

### Cómo probarlo
1. Inicia CENTRAL: `start_central_gui.bat`
2. Inicia un driver: `start_driver.bat DRIVER01`
3. Solicita un CP inexistente (opción 1): `francia20`
4. **Resultado esperado:**
   ```
   ❌ AUTORIZACIÓN DENEGADA
      CP: francia20
      Motivo: CP_NOT_FOUND
      Detalle: El punto de recarga NO EXISTE en el sistema
   ```
5. Verifica en la base de datos que NO se creó: `sqlite3 src/EV_Central/central.db "SELECT cp_id FROM charging_points WHERE cp_id='francia20';"`
   - **Resultado esperado:** Sin resultados

### Script de prueba automático
Ejecuta: `python test_corrections.py`

Este script:
- ✅ Verifica que CENTRAL rechaza CPs inexistentes (francia20)
- ✅ Verifica que CENTRAL acepta CPs existentes (ALC1)

---

## 📋 CPs válidos en el sistema

Los únicos CPs que existen y pueden ser solicitados son:

1. **ALC1** - Alicante
2. **ALC3** - Gran Via 2
3. **MAD2** - C/Serrano 18
4. **MAD3** - C/Fco 23
5. **MAD1** - C/Alcalese
6. **SEV3** - Gran Via 1
7. **SEV2** - Valencia
8. **VAL3** - Malaga Aero
9. **VAL1** - San Javier
10. **COR1** - Menorca

Cualquier otro ID será rechazado con `CP_NOT_FOUND`.

---

## 🔄 Códigos de error de autorización

Ahora el sistema tiene estos códigos de rechazo:

| Código | Significado | Solución |
|--------|-------------|----------|
| `DISCONNECTED` | El CP está desconectado | Esperar a que el Monitor se conecte |
| `FAULT` | El CP reportó una avería | El CP debe ser reparado |
| `BUSY` | El CP está ocupado | Esperar a que el conductor actual termine |
| `OUT_OF_ORDER` | El CP fue detenido por CENTRAL | CENTRAL debe reabrirlo |
| `CP_NOT_FOUND` | El CP no existe | Verificar el ID correcto |

---

## ✅ Estado después de las correcciones

- ✅ **Driver**: No puede salir mientras carga (debe finalizar primero)
- ✅ **CENTRAL**: Solo acepta CPs que existen en la base de datos
- ✅ **CENTRAL**: No crea CPs fantasma automáticamente
- ✅ **Driver**: Muestra mensaje claro cuando el CP no existe
- ✅ **Base de datos**: Se mantiene limpia sin CPs inventados

---

## 🐛 CORRECCIONES ADICIONALES - Críticas

### **Problema 3: Comando STOP crea CPs inexistentes**

#### Descripción
Al ejecutar `stop francia20` desde el CLI de CENTRAL, se creaba automáticamente el CP "francia20" en la base de datos, igual que ocurría con REQ antes de la corrección.

#### Solución
**Archivo:** `src/EV_Central/EV_Central.py` (línea ~412)

Añadida validación con `cp_exists()` antes de ejecutar STOP:

```python
elif cmd == "stop" and len(parts) >= 2:
    cp_id = parts[1]
    # VALIDAR que el CP existe
    if not self.cp_exists(cp_id):
        print(f"❌ Error: El CP '{cp_id}' NO EXISTE en el sistema")
        logger.warning("STOP command failed: CP {} does not exist", cp_id)
        continue
    # ... resto del código
```

Lo mismo para RESUME.

---

### **Problema 4: CPs desconectados aparecen como conectados**

#### Descripción
Cuando un Monitor se desconectaba (Ctrl+C o pérdida de red), el CP permanecía marcado como `connected=True` en la base de datos. Esto permitía que drivers solicitaran servicio en CPs que ya no estaban disponibles (sin cobro real).

**Flujo del problema:**
1. Monitor se conecta → `connected=True` ✅
2. Monitor se cierra → `connected` sigue en `True` ❌
3. Driver solicita → AUTH_GRANTED ❌ (aunque el CP no está)
4. No hay telemetría, no se cobra ❌

#### Solución
**Archivo:** `src/EV_Central/EV_Central.py`

1. Trackear el CP de cada conexión en `_handle_conn()`:
```python
current_cp_id = None  # Al inicio
current_cp_id = cp_id  # En AUTH y FAULT
```

2. Marcar como desconectado en el bloque `finally`:
```python
finally:
    if current_cp_id:
        with self._db_lock:
            if current_cp_id in self._db:
                self._db[current_cp_id].connected = False
                self._db[current_cp_id].charging = False
        # Persistir y notificar
```

**Flujo corregido:**
1. Monitor se conecta → `connected=True` ✅
2. Monitor se cierra → **`connected=False`** ✅
3. Driver solicita → **AUTH_DENIED#DISCONNECTED** ✅
4. GUI muestra CP en GRIS ✅

---

### **Problema 5: Verificación de cálculo kW/€**

#### Descripción
Los kW y € varían durante la carga. **Esto es CORRECTO por diseño**:

- **kW varía:** 10.5 - 11.5 kW (simulación realista)
- **€ aumenta:** `(kW / 3600) * 0.35 €/kWh` por segundo

#### Fórmula (en EV_CP_E.py):
```python
self.kw_current = round(11.0 + random.uniform(-0.5, 0.5), 2)
self.euros_accum = round(self.euros_accum + (self.kw_current/3600.0)*0.35, 4)
```

**Ejemplo:** Para 11 kW → 0.001069 €/segundo → 3.85 €/hora ✅

---

## 🧪 Script de Pruebas

Ejecuta: `python test_critical_fixes.py`

Prueba automáticamente los 3 problemas críticos.

---

**Fecha de corrección:** 31 de octubre de 2025
