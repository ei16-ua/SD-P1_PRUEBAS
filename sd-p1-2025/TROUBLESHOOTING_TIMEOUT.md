# 🔧 DIAGNÓSTICO Y SOLUCIÓN - Timeout en MONITOR

## Problema Actual
El MONITOR no puede conectarse al CENTRAL y da timeout.

## ✅ SOLUCIÓN RÁPIDA - Test Local (Todo en tu PC)

### Opción 1: Test Automático con Script

```powershell
# Ejecuta este comando (lanza todo automáticamente)
.\test_protocol_simple.bat
```

El script abre 3 ventanas:
- CENTRAL en puerto 8888
- ENGINE ALC1 en puerto 5001  
- MONITOR ALC1 conectado

Espera 10 segundos y ejecuta el test automáticamente.

---

### Opción 2: Test Manual Paso a Paso

#### PASO 1: Abrir 4 terminales

**Terminal 1 - CENTRAL:**
```powershell
cd C:\Users\Charlie\SistemasDistribuidos\sd-p1-2025
python src\EV_Central\EV_Central.py --host 127.0.0.1 --port 8888
```

Espera a ver:
```
[INFO] CENTRAL listening on 127.0.0.1:8888
```

---

**Terminal 2 - ENGINE:**
```powershell
cd C:\Users\Charlie\SistemasDistribuidos\sd-p1-2025
python src\EV_CP_E\EV_CP_E.py --cp-id ALC1 --port 5001
```

⚠️ **NO PRESIONES ENTER** (dejar en estado OK)

Espera a ver:
```
[INFO] Health server on 0.0.0.0:5001
Pulsa Enter para alternar OK/KO…
```

---

**Terminal 3 - MONITOR:**
```powershell
cd C:\Users\Charlie\SistemasDistribuidos\sd-p1-2025
python src\EV_CP_M\EV_CP_M.py --cp-id ALC1 --engine-host localhost --engine-port 5001 --central-host localhost --central-port 8888
```

Deberías ver:
```
[INFO] Central AUTH response: ACK
[INFO] Heartbeat -> Engine: OK
```

Si ves timeout aquí, ve a la sección "Diagnóstico de Timeout" abajo.

---

**Terminal 4 - TEST:**
```powershell
cd C:\Users\Charlie\SistemasDistribuidos\sd-p1-2025
python test_protocol_manual.py
```

Este test hace diagnóstico paso a paso y te dice exactamente dónde falla.

---

## 🔍 DIAGNÓSTICO DE TIMEOUT

Si el MONITOR da timeout, ejecuta este diagnóstico:

```powershell
python test_protocol_manual.py
```

El test verifica:
1. ✓ ¿CENTRAL está corriendo y acepta conexiones?
2. ✓ ¿El protocolo STX-ETX-LRC funciona?
3. ✓ ¿Se puede enviar/recibir mensajes?

---

## 🐛 CAUSAS COMUNES DE TIMEOUT

### 1. CENTRAL no tiene el código actualizado

**Síntoma**: MONITOR conecta pero no recibe respuesta

**Solución**: 
- Asegúrate de cerrar el CENTRAL viejo
- Reinicia el CENTRAL con el código nuevo que tiene `protocol.py`

```powershell
# Matar cualquier Python viejo
taskkill /F /IM python.exe

# Reiniciar CENTRAL
python src\EV_Central\EV_Central.py --host 127.0.0.1 --port 8888
```

---

### 2. Puerto 8888 ocupado

**Síntoma**: Error "Address already in use"

**Verificar**:
```powershell
netstat -ano | findstr 8888
```

**Solución**:
```powershell
# Matar proceso que usa el puerto
taskkill /F /PID <PID_DEL_PROCESO>
```

---

### 3. Firewall bloqueando

**Síntoma**: Conexión refused o timeout

**Solución**:
```powershell
# Deshabilitar temporalmente el firewall para localhost
# O agregar regla:
netsh advfirewall firewall add rule name="EV Central" dir=in action=allow protocol=TCP localport=8888
```

---

### 4. Versión vieja de `protocol.py`

**Verificar que existe**:
```powershell
dir src\UTILS\protocol.py
```

**Si no existe**, el código no está actualizado. Necesitas:
- `src\UTILS\protocol.py` (195 líneas, con ProtocolMessage class)

---

### 5. MONITOR esperando respuesta después de AUTH

**Síntoma**: MONITOR se queda colgado después de enviar AUTH

**Causa**: El código viejo de MONITOR esperaba una respuesta después del ACK

**Verificar**: Abre `src\EV_CP_M\EV_CP_M.py` y busca:
```python
def send_auth(self, cp_id: str) -> str:
    """Envía AUTH y solo espera ACK"""
```

Si NO existe ese método, el código está desactualizado.

---

## 📋 CHECKLIST ANTES DE PROBAR

- [ ] Código actualizado con `protocol.py`
- [ ] CENTRAL cerrado (matar procesos viejos)
- [ ] Puerto 8888 libre
- [ ] 4 terminales preparadas
- [ ] CENTRAL iniciado y mostrando "listening on 127.0.0.1:8888"
- [ ] ENGINE iniciado (NO presionar Enter)
- [ ] MONITOR iniciado y mostrando "Central AUTH response: ACK"

---

## 🚀 TEST FINAL

Una vez que MONITOR muestre:
```
[INFO] Central AUTH response: ACK
[INFO] Heartbeat -> Engine: OK
```

Ejecuta en otra terminal:
```powershell
python test_protocol_complete.py --auto
```

**Resultado esperado**:
```
✅ Conexión establecida
✅ CENTRAL envió ACK (protocolo OK)
✅ Respuesta recibida: AUTH_GRANTED#ALC1#DRIVER_TEST_001
✅ TEST COMPLETADO EXITOSAMENTE
```

---

## 📞 SI SIGUE FALLANDO

Envíame el output exacto de:

1. **CENTRAL** (primeras 20 líneas después de iniciar)
2. **MONITOR** (el error de timeout completo)
3. **Test manual**:
```powershell
python test_protocol_manual.py
```

Con eso puedo diagnosticar exactamente qué está pasando.

---

## 💡 ALTERNATIVA: Test sin MONITOR

Si el MONITOR sigue dando problemas, puedes probar el protocolo directamente:

```powershell
# Terminal 1: Solo CENTRAL
python src\EV_Central\EV_Central.py --host 127.0.0.1 --port 8888

# Terminal 2: Test directo
python test_protocol_manual.py
```

Este test solo verifica:
- CENTRAL vivo ✓
- Protocolo funciona ✓
- Comunicación REQ → AUTH_DENIED OK ✓

(AUTH_DENIED es normal porque no hay ENGINE/MONITOR, pero confirma que el protocolo funciona)
