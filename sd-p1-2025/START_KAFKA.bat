@echo off
REM ========================================
REM INICIAR KAFKA Y CREAR TOPICS
REM ========================================

echo.
echo ========================================
echo   INICIALIZACION DE KAFKA
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar Docker
echo [1/4] Verificando Docker Desktop...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta corriendo
    echo.
    echo Por favor:
    echo 1. Abre Docker Desktop
    echo 2. Espera a que este completamente iniciado
    echo 3. Ejecuta este script de nuevo
    echo.
    pause
    exit /b 1
)
echo OK: Docker esta corriendo

REM Iniciar Docker Compose
echo.
echo [2/4] Iniciando Kafka con Docker Compose...
cd docker
docker-compose up -d

if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar Docker Compose
    pause
    exit /b 1
)

echo OK: Contenedores iniciados

REM Esperar a que Kafka este listo
echo.
echo [3/4] Esperando a que Kafka este listo...
echo (Esto puede tomar 15-20 segundos)
timeout /t 20 /nobreak > nul
echo OK: Kafka deberia estar listo

REM Crear topics
echo.
echo [4/4] Creando topics de Kafka (solo 2 topics compartidos)...
echo.

cd ..
python scripts/create_kafka_topics.py --bootstrap localhost:29092

if %errorlevel% neq 0 (
    echo.
    echo ADVERTENCIA: Error creando topics, pero Kafka esta funcionando
    echo Puedes crear topics manualmente despues si es necesario
    echo.
)

echo.
echo ========================================
echo   TOPICS CREADOS
echo ========================================
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 2>nul
if %errorlevel% neq 0 (
    echo [WARN] No se pudo listar topics con kafka-topics, intentando alternativa...
    timeout /t 2 /nobreak > nul
    python -c "from confluent_kafka.admin import AdminClient; admin = AdminClient({'bootstrap.servers': 'localhost:29092'}); topics = admin.list_topics(timeout=5).topics; [print(t) for t in topics.keys() if 'cp.' in t]" 2>nul
    if %errorlevel% neq 0 (
        echo [INFO] Topics creados correctamente (no se puede listar desde aqui)
    )
)

echo.
echo ========================================
echo   KAFKA LISTO PARA USAR
echo ========================================
echo.
echo Kafka Bootstrap: localhost:29092
echo Kafka UI: http://localhost:8080
echo.
echo Topics creados:
echo   - cp.telemetry (telemetria de todos los CPs)
echo   - cp.commands.all (comandos para todos los CPs)
echo.
echo IMPORTANTE: Ya NO necesitas crear topics por CP
echo             Todos usan cp.commands.all con filtrado por cp_id
echo.
echo Ya puedes iniciar el CENTRAL y los componentes.
echo.

REM Solo hacer pause si se ejecuta directamente (no desde otro script)
if "%1"=="" (
    pause
)
