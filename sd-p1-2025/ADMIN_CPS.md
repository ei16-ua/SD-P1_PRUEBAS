# Administración de Puntos de Carga (CPs)

Este documento explica cómo añadir y eliminar puntos de carga del sistema.

## Script de administración: `admin_cps.py`

El script `admin_cps.py` permite gestionar los puntos de carga de forma segura con validación de duplicados.

---

## 📋 Listar puntos de carga

```powershell
python admin_cps.py --list
```

Muestra todos los CPs registrados con su ID, ubicación y estado.

**Ejemplo de salida:**
```
======================================================================
  PUNTOS DE CARGA REGISTRADOS
======================================================================
ID              UBICACIÓN                           ESTADO         
----------------------------------------------------------------------
ALC1            Calle Mayor 123, Alicante          active         
ALC2            Avenida del Mar 45, Alicante       inactive       
FRANCIA         Rue de Paris 10, Paris             inactive       
MAD2            Gran Vía 28, Madrid                active         
SEV1            Avenida de la Constitución, Sevilla inactive       
======================================================================

Total: 5 punto(s) de carga
```

---

## ➕ Añadir un punto de carga

### Sintaxis básica

```powershell
python admin_cps.py --add --id <ID> --location "<Ubicación>"
```

### Ejemplos

**1. Añadir un CP en Francia:**
```powershell
python admin_cps.py --add --id FRANCIA --location "Rue de Paris 10, Paris"
```

**2. Añadir un CP en Barcelona:**
```powershell
python admin_cps.py --add --id BCN1 --location "Passeig de Gràcia 92, Barcelona"
```

**3. Añadir un CP en Lisboa:**
```powershell
python admin_cps.py --add --id LIS1 --location "Rua Augusta 100, Lisboa"
```

### Validación de duplicados

El script verifica automáticamente:
- ✅ **ID duplicado:** No permite dos CPs con el mismo ID
- ✅ **Ubicación duplicada:** No permite dos CPs en la misma dirección

**Ejemplo de error por ID duplicado:**
```
❌ ERROR: Ya existe un punto de carga con el ID 'FRANCIA'
   Usa --force para sobrescribir o elige otro ID.
```

**Ejemplo de error por ubicación duplicada:**
```
❌ ERROR: Ya existe un punto de carga en 'Rue de Paris 10, Paris' (ID: FRANCIA)
   Usa --force para sobrescribir o elige otra ubicación.
```

### Forzar sobrescritura

Si realmente quieres sobrescribir un CP existente:

```powershell
python admin_cps.py --add --id FRANCIA --location "Nueva dirección" --force
```

---

## ❌ Eliminar un punto de carga

### Sintaxis

```powershell
python admin_cps.py --remove --id <ID>
```

### Ejemplos

**Eliminar el CP de Francia:**
```powershell
python admin_cps.py --remove --id FRANCIA
```

### Confirmación de seguridad

El script pide confirmación antes de eliminar:

```
⚠️  ¿Estás seguro de eliminar el punto de carga?
   ID: FRANCIA
   Ubicación: Rue de Paris 10, Paris

   Escribe 'SI' para confirmar: _
```

**Debes escribir exactamente `SI` (en mayúsculas) para confirmar.**

---

## 🔧 Crear topics de Kafka después de añadir un CP

Después de añadir un nuevo CP, **debes crear su topic de Kafka**:

### Opción 1: Topic individual (recomendado)
```powershell
python scripts/create_kafka_topics.py --bootstrap localhost:29092 --cp-id FRANCIA
```

### Opción 2: Todos los topics desde la DB
```powershell
python scripts/create_kafka_topics.py --bootstrap localhost:29092 --from-db
```

### Opción 3: Recrear todo con START_KAFKA.bat
```powershell
cd docker
.\START_KAFKA.bat
```

---

## 🗑️ Eliminar topics de Kafka después de eliminar un CP

Después de eliminar un CP, **puedes eliminar su topic de Kafka** (opcional):

```powershell
docker exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic cp.commands.FRANCIA
```

---

## 📝 Flujo completo de trabajo

### Añadir un nuevo CP "PORTUGAL"

1. **Añadir a la base de datos:**
   ```powershell
   python admin_cps.py --add --id PORT1 --location "Avenida da Liberdade, Lisboa"
   ```

2. **Crear el topic de Kafka:**
   ```powershell
   python scripts/create_kafka_topics.py --bootstrap localhost:29092 --cp-id PORT1
   ```

3. **Verificar que está registrado:**
   ```powershell
   python admin_cps.py --list
   ```

4. **Iniciar el ENGINE para ese CP:**
   ```powershell
   python src/EV_CP_E/EV_CP_E.py --cp-id PORT1 --kafka-bootstrap localhost:29092
   ```

5. **Verificar en la GUI Web:**
   - Abrir http://localhost:8000
   - Debería aparecer PORT1 en la lista de CPs

### Eliminar el CP "PORTUGAL"

1. **Eliminar de la base de datos:**
   ```powershell
   python admin_cps.py --remove --id PORT1
   ```

2. **Confirmar con "SI"**

3. **Eliminar el topic de Kafka (opcional):**
   ```powershell
   docker exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic cp.commands.PORT1
   ```

4. **Verificar que ya no está:**
   ```powershell
   python admin_cps.py --list
   ```

---

## ⚠️ Notas importantes

1. **Los IDs se convierten automáticamente a MAYÚSCULAS:**
   - Si escribes `--id francia` → se guarda como `FRANCIA`

2. **La ubicación NO se modifica:**
   - Se guarda exactamente como la escribas (respeta mayúsculas/minúsculas)

3. **Estado inicial:**
   - Todos los CPs nuevos se crean con estado `inactive`
   - Cuando el ENGINE se conecta, el estado cambia a `active`

4. **No puedes eliminar un CP que está activo:**
   - Primero detén el ENGINE correspondiente
   - Luego elimina el CP de la base de datos

5. **Kafka topics:**
   - Los topics NO se eliminan automáticamente
   - Usa el comando `docker exec` si quieres limpiarlos

---

## 🚨 Solución de problemas

### "ERROR: No existe un punto de carga con el ID 'XXX'"
- Verifica que el ID esté bien escrito (recuerda que se convierte a mayúsculas)
- Lista todos los CPs con `--list` para ver los IDs correctos

### "ERROR: Ya existe un punto de carga..."
- Si realmente quieres sobrescribir, usa `--force`
- Si fue un error, elige otro ID o ubicación

### "El CP no aparece en la GUI Web"
- Verifica que el topic de Kafka se haya creado
- Reinicia el CENTRAL: `.\PC1_CENTRAL.bat`
- Espera 5-10 segundos para que se actualice

### "El ENGINE no puede publicar mensajes"
- Verifica que el topic `cp.commands.<CP_ID>` exista:
  ```powershell
  docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
  ```
- Si no existe, créalo con:
  ```powershell
  python scripts/create_kafka_topics.py --bootstrap localhost:29092 --cp-id <CP_ID>
  ```

---

## 📚 Ejemplos de casos de uso

### Caso 1: Expandir red a Francia (3 CPs)

```powershell
# Añadir CPs
python admin_cps.py --add --id PAR1 --location "Rue de Rivoli 10, Paris"
python admin_cps.py --add --id PAR2 --location "Avenue des Champs-Élysées 50, Paris"
python admin_cps.py --add --id LYO1 --location "Place Bellecour 1, Lyon"

# Crear topics
python scripts/create_kafka_topics.py --bootstrap localhost:29092 --from-db

# Verificar
python admin_cps.py --list
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 | findstr PAR
```

### Caso 2: Eliminar CPs obsoletos

```powershell
# Eliminar CPs antiguos
python admin_cps.py --remove --id OLD1
python admin_cps.py --remove --id OLD2

# Limpiar topics
docker exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic cp.commands.OLD1
docker exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic cp.commands.OLD2
```

### Caso 3: Actualizar ubicación de un CP

```powershell
# Eliminar el antiguo
python admin_cps.py --remove --id MAD1

# Añadir con nueva ubicación
python admin_cps.py --add --id MAD1 --location "Nueva dirección, Madrid"

# No es necesario recrear el topic (ya existe)
```

---

## 🎯 Resumen de comandos

| Acción | Comando |
|--------|---------|
| Listar CPs | `python admin_cps.py --list` |
| Añadir CP | `python admin_cps.py --add --id <ID> --location "<ubicación>"` |
| Añadir (forzar) | `python admin_cps.py --add --id <ID> --location "<ubicación>" --force` |
| Eliminar CP | `python admin_cps.py --remove --id <ID>` |
| Crear topic | `python scripts/create_kafka_topics.py --bootstrap localhost:29092 --cp-id <ID>` |
| Crear todos | `python scripts/create_kafka_topics.py --bootstrap localhost:29092 --from-db` |
| Listar topics | `docker exec kafka kafka-topics --list --bootstrap-server localhost:9092` |
| Eliminar topic | `docker exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic cp.commands.<ID>` |

