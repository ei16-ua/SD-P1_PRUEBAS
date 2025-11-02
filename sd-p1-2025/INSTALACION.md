# 🚀 Guía de Instalación - Sistema EV Charging

## 📋 Requisitos Previos

### Software necesario:
1. **Python 3.13** - [Descargar](https://www.python.org/downloads/)
2. **Docker Desktop** - [Descargar](https://www.docker.com/products/docker-desktop/)
3. **Git** - [Descargar](https://git-scm.com/downloads)

---

## 🔧 Instalación Paso a Paso

### 1️⃣ Clonar el Repositorio

```powershell
# Navegar a tu carpeta de proyectos
cd C:\Users\TuUsuario\

# Clonar el repositorio
git clone https://github.com/jcz13-ua/sd-p1-2025.git

# Entrar al directorio
cd sd-p1-2025
```

### 2️⃣ Instalar Dependencias de Python

**Opción A: Con pipenv (Recomendado)**
```powershell
# Instalar pipenv si no lo tienes
pip install pipenv

# Instalar dependencias del proyecto
pipenv install
```

**Opción B: Con pip**
```powershell
# Instalar dependencias directamente
pip install confluent-kafka loguru pygame
```

### 3️⃣ Inicializar la Base de Datos

```powershell
# Crear/resetear la base de datos con los 10 CPs
python reset_database.py

# Crear los 9 conductores (DRIVER01-DRIVER09)
python create_drivers.py
```

### 4️⃣ Iniciar Kafka con Docker

```powershell
# Ir a la carpeta docker
cd docker

# Iniciar Zookeeper, Kafka y Kafka UI
docker-compose up -d

# Verificar que están corriendo
docker-compose ps

# Esperar 30 segundos a que Kafka esté listo
Start-Sleep -Seconds 30

# Volver a la raíz del proyecto
cd ..
```

---

## 🎮 Iniciar el Sistema

### Opción 1: Sistema Completo Automático (SIN Kafka)

```powershell
# Inicia CENTRAL + 10 CPs automáticamente
start_complete_system.bat
```

⚠️ **Nota:** Sin Kafka no verás telemetría en tiempo real, pero todo lo demás funciona.

### Opción 2: Sistema con Kafka (Recomendado)

#### Terminal 1 - CENTRAL
```powershell
python src\EV_Central\EV_Central.py --host 0.0.0.0 --port 9099 --kafka-bootstrap localhost:29092
```

#### Terminal 2 - ENGINE (ejemplo con ALC1)
```powershell
python src\EV_CP_E\EV_CP_E.py --cp-id ALC1 --host 0.0.0.0 --port 7001 --kafka-bootstrap localhost:29092
```

#### Terminal 3 - MONITOR (ejemplo con ALC1)
```powershell
python src\EV_CP_M\EV_CP_M.py --cp-id ALC1 --engine-host localhost --engine-port 7001 --central-host localhost --central-port 9099
```

#### Terminal 4 - DRIVER (ejemplo con DRIVER01)
```powershell
python src\EV_Driver\EV_Driver.py --driver-id DRIVER01 --central-host localhost --central-port 9099 --kafka-bootstrap localhost:29092
```

### Opción 3: Usar scripts .bat (múltiples CPs)

```powershell
# Iniciar CENTRAL con GUI
start_central_gui.bat

# En otra terminal: Iniciar todos los CPs (10 pares Engine+Monitor)
start_all_cps.bat

# En otra terminal: Iniciar Driver con GUI
start_driver_gui.bat DRIVER01
```

---

## 🌐 Acceder a Kafka UI

Abre tu navegador y ve a:
```
http://localhost:8080
```

Aquí podrás ver:
- Topics creados (`cp.telemetry`, `cp.commands.*`)
- Mensajes en tiempo real
- Consumer groups
- Estado de Kafka

---

## 📊 Verificar que Todo Funciona

### 1. Verificar Docker
```powershell
docker-compose ps
```
Deberías ver:
- ✅ zookeeper (Up)
- ✅ kafka (Up)
- ✅ kafka-ui (Up)

### 2. Verificar Base de Datos
```powershell
python explore_db.py
```

### 3. Probar Conexión
```powershell
python test_connection.py
```

### 4. Probar Sistema Completo
```powershell
python test_critical_fixes.py
```

---

## 🆘 Solución de Problemas

### ❌ Error: "confluent-kafka no instalado"
```powershell
pip install confluent-kafka
```

### ❌ Error: "Docker no está corriendo"
```powershell
# Abre Docker Desktop manualmente y espera a que inicie
# Luego ejecuta:
docker-compose up -d
```

### ❌ Error: "Puerto 9099 ya en uso"
```powershell
# Ver qué proceso usa el puerto
netstat -ano | findstr :9099

# Matar el proceso (reemplaza PID con el número que aparece)
taskkill /PID <PID> /F
```

### ❌ Error: "No se conecta a Kafka"
```powershell
# Verificar que Kafka está corriendo
docker-compose logs kafka

# Reiniciar Kafka
docker-compose restart kafka
Start-Sleep -Seconds 30
```

### ❌ Kafka UI no carga
```powershell
# Reiniciar solo la UI
docker-compose restart kafka-ui
```

---

## 🛑 Detener el Sistema

### Detener Componentes Python
- Presiona `Ctrl+C` en cada terminal

### Detener Kafka
```powershell
cd docker
docker-compose down
```

### Detener y Limpiar Todo (Reset completo)
```powershell
cd docker
docker-compose down -v  # Elimina también los volúmenes
cd ..
python reset_database.py
```

---

## 📝 Comandos Útiles de Kafka

### Ver topics
```powershell
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Ver mensajes en un topic
```powershell
docker exec -it kafka kafka-console-consumer --topic cp.telemetry --bootstrap-server localhost:9092 --from-beginning
```

### Crear topic manualmente
```powershell
docker exec -it kafka kafka-topics --create --topic mi-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

### Describir un topic
```powershell
docker exec -it kafka kafka-topics --describe --topic cp.telemetry --bootstrap-server localhost:9092
```

---

## 📂 Estructura de Archivos Importante

```
sd-p1-2025/
├── src/
│   ├── EV_Central/       # Servidor central
│   │   ├── EV_Central.py
│   │   ├── EV_Central_GUI.py
│   │   ├── database.py
│   │   └── central.db    # Se crea al ejecutar reset_database.py
│   ├── EV_CP_E/          # Engine (produce telemetría)
│   ├── EV_CP_M/          # Monitor (health checks)
│   ├── EV_Driver/        # Cliente conductor
│   └── UTILS/
│       └── kafka.py      # Utilidades de Kafka
├── docker/
│   ├── docker-compose.yml
│   └── create_kafka_topics.ps1
├── reset_database.py     # Inicializar DB
├── create_drivers.py     # Crear conductores
└── start_*.bat           # Scripts de inicio

```

---

## 🎯 Flujo de Trabajo Típico

```powershell
# 1. Iniciar Kafka (una sola vez al arrancar el PC)
cd docker
docker-compose up -d
cd ..

# 2. Resetear DB si es necesario
python reset_database.py

# 3. Iniciar sistema
start_complete_system.bat

# 4. Iniciar drivers
start_driver_gui.bat DRIVER01
start_driver_gui.bat DRIVER02

# 5. Ver telemetría en tiempo real
# Abrir http://localhost:8080

# 6. Al terminar
# Ctrl+C en cada terminal
cd docker
docker-compose down
```

---

## 📞 Contacto

**Autores:** Jiahao Chen, Erik Ikaev  
**Repositorio:** https://github.com/jcz13-ua/sd-p1-2025  
**Práctica:** Sistemas Distribuidos 2024-2025

---

✅ **¡Ya estás listo para trabajar con el sistema EV Charging!**
