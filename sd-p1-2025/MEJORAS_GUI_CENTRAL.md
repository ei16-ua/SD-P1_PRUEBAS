# 🎨 Mejoras Visuales - GUI del CENTRAL

## Problema Original

El GUI del CENTRAL no mostraba claramente la información de los drivers cuando estaban cargando:
- ❌ Texto del driver pequeño y poco visible
- ❌ kW y € difíciles de leer sobre fondo verde
- ❌ No se distinguía bien quién estaba cargando
- ❌ Faltaba el color NARANJA en la leyenda (Out of Order)

---

## Mejoras Implementadas

### 1. Panel de CP Suministrando - REDISEÑADO

**Cuando un CP está SUMINISTRANDO:**

#### Antes:
```
┌────────────────┐
│ ALC1           │ (verde)
│ Alicante       │
│ SUMINISTRANDO  │ (texto pequeño blanco)
│ DRIVER01       │ (amarillo, tamaño normal)
│ 11.25 kW       │ (blanco)
│ 0.0012 €       │ (amarillo)
└────────────────┘
```

#### Ahora:
```
┌────────────────────┐
│ ALC1 (bold, grande)│ (verde)
│ Alicante           │
├────────────────────┤
│ ╔════════════════╗ │
│ ║   DRIVER01     ║ │ ← GRANDE (24px, bold, azul oscuro)
│ ║ ───────────────║ │
│ ║ Potencia:      ║ │
│ ║  11.25 kW      ║ │ ← GRANDE (20px, naranja)
│ ║ Importe:       ║ │
│ ║ ╔═══════════╗  ║ │
│ ║ ║ 0.0012 € ║   ║ │ ← DESTACADO (fondo amarillo)
│ ║ ╚═══════════╝  ║ │
│ ╚════════════════╝ │
└────────────────────┘
```

### 2. Jerarquía Visual Clara

**Información por importancia:**

1. **CP ID** - 18px bold (parte superior)
2. **Driver ID** - 24px bold en azul oscuro (MÁS GRANDE)
3. **Potencia (kW)** - 20px bold en naranja
4. **Importe (€)** - 20px bold en negro sobre fondo amarillo (MUY DESTACADO)

### 3. Caja Interior con Contraste

- **Fondo blanco semi-transparente** dentro del panel verde
- **Borde azul oscuro** alrededor de la información
- **Separadores** entre secciones para mejor legibilidad

### 4. Paneles Más Grandes

#### Antes:
- Tamaño: 180x120 px
- Padding: 10px

#### Ahora:
- Tamaño: 200x170 px (11% más grandes)
- Padding: 15px (más espacio entre paneles)

### 5. Leyenda Actualizada

**Añadido el color NARANJA:**
```
┌─────────────────────────────┐
│ Leyenda de Estados          │
├─────────────────────────────┤
│ █ Disponible/Suministrando  │ (verde)
│ █ Parado (Out of Order)     │ (naranja) ← NUEVO
│ █ Averiado                  │ (rojo)
│ █ Desconectado              │ (gris)
└─────────────────────────────┘
```

---

## Colores del Sistema

| Estado | Color | Código RGB | Cuándo |
|--------|-------|------------|--------|
| **VERDE** | `#2ECC71` | (46, 204, 113) | Disponible o Suministrando |
| **NARANJA** | `#E67E22` | (230, 126, 34) | Parado (Out of Order) |
| **ROJO** | `#E74C3C` | (231, 76, 60) | Averiado (Fault) |
| **GRIS** | `#95A5A6` | (149, 165, 166) | Desconectado |

### Colores de Texto (cuando está Suministrando):
- **Driver ID**: Azul oscuro `#2C3E50` (máximo contraste)
- **kW**: Naranja `#E67E22` (destaca la potencia)
- **EUR**: Negro sobre fondo amarillo `#F1C40F` (máxima visibilidad)

---

## Ejemplo Visual Completo

### CP en Estado: DISPONIBLE
```
┌─────────────────┐
│    ALC1 (18px)  │ ← CP ID bold
│   Alicante      │ ← Ubicación
├─────────────────┤
│                 │
│   DISPONIBLE    │ ← Estado (16px)
│                 │
└─────────────────┘
Verde, texto blanco
```

### CP en Estado: SUMINISTRANDO
```
┌─────────────────┐
│    ALC1 (18px)  │ ← CP ID bold
│   Alicante      │ ← Ubicación
├─────────────────┤
│ ┌─────────────┐ │
│ │  DRIVER01   │ │ ← 24px bold, azul
│ ├─────────────┤ │
│ │ Potencia:   │ │
│ │ 11.25 kW    │ │ ← 20px bold, naranja
│ │ Importe:    │ │
│ │ ┌─────────┐ │ │
│ │ │0.0012 € │ │ │ ← 20px bold, fondo amarillo
│ │ └─────────┘ │ │
│ └─────────────┘ │
└─────────────────┘
Verde, con caja blanca interior
```

### CP en Estado: PARADO (Out of Order)
```
┌─────────────────┐
│    MAD2 (18px)  │ ← CP ID bold
│  C/Serrano 18   │ ← Ubicación
├─────────────────┤
│                 │
│     PARADO      │ ← 16px
│  Out of Order   │ ← 14px
│                 │
└─────────────────┘
Naranja, texto blanco
```

### CP en Estado: AVERIADO
```
┌─────────────────┐
│    VAL1 (18px)  │ ← CP ID bold
│  San Javier     │ ← Ubicación
├─────────────────┤
│                 │
│    AVERIADO     │ ← 16px
│                 │
└─────────────────┘
Rojo, texto blanco
```

### CP en Estado: DESCONECTADO
```
┌─────────────────┐
│    SEV3 (18px)  │ ← CP ID bold
│   Gran Via 1    │ ← Ubicación
├─────────────────┤
│                 │
│ DESCONECTADO    │ ← 16px
│                 │
└─────────────────┘
Gris, texto negro
```

---

## Comparación de Tamaños de Fuente

| Elemento | Antes | Ahora | Cambio |
|----------|-------|-------|--------|
| CP ID | 16px normal | 18px **bold** | +12.5% |
| Driver ID | 16px | 24px **bold** | +50% 🔥 |
| kW | 16px | 20px **bold** | +25% |
| EUR | 16px | 20px **bold** | +25% |
| Estado | 14px | 16px | +14% |

---

## Testing Visual

### Para ver todas las combinaciones:

```powershell
# 1. Iniciar CENTRAL con GUI
python src\EV_Central\EV_Central_GUI.py --host 0.0.0.0 --port 9099 --kafka-bootstrap localhost:29092

# 2. Verificar estados:
# - GRIS: CPs sin Monitor conectado
# - VERDE: CPs con Monitor conectado
# - VERDE + Info: CP suministrando (con Driver cargando)
# - ROJO: Engine responde KO (presiona Enter en ventana del Engine)
# - NARANJA: Desde CLI de CENTRAL ejecuta: stop <CP_ID>
```

### Estados a verificar:
1. ✅ **10 CPs en GRIS** (al inicio, sin Monitors)
2. ✅ **CPs pasan a VERDE** (cuando Monitors se conectan)
3. ✅ **CP muestra DRIVER01** en grande (cuando driver carga)
4. ✅ **kW y € actualizándose** cada segundo
5. ✅ **CP vuelve a DISPONIBLE** (cuando driver finaliza)
6. ✅ **CP pasa a NARANJA** (comando `stop <CP_ID>`)
7. ✅ **CP pasa a ROJO** (Engine presiona Enter para toggle KO)

---

## Resolución Recomendada

**Mínimo:** 1200x800 px  
**Óptimo:** 1400x900 px o superior

El GUI se adapta automáticamente pero con 10 CPs en pantalla se recomienda al menos 1200px de ancho.

---

## Accesibilidad

### Contraste Mejorado:
- ✅ Driver ID sobre fondo blanco (ratio >7:1)
- ✅ Precio sobre fondo amarillo (ratio >4.5:1)
- ✅ Bordes gruesos (3px) para mejor definición
- ✅ Tamaños de fuente aumentados para mejor legibilidad

### Jerarquía Clara:
1. **Nivel 1**: CP ID (lo primero que se ve)
2. **Nivel 2**: Driver ID (si está cargando)
3. **Nivel 3**: Métricas (kW y EUR)
4. **Nivel 4**: Estado (DISPONIBLE, PARADO, etc.)

---

**Fecha de mejoras:** 1 de noviembre de 2025  
**Archivo modificado:** `src/EV_Central/EV_Central_GUI.py`
