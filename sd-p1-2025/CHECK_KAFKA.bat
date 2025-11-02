@echo off
REM ========================================
REM VERIFICAR ESTADO DE KAFKA
REM ========================================

echo.
echo ========================================
echo   ESTADO DE KAFKA
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar contenedores
echo [1/3] Verificando contenedores Docker...
echo.
docker ps --filter "name=kafka" --filter "name=zookeeper" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

if %errorlevel% neq 0 (
    echo ERROR: Docker no esta corriendo o no hay contenedores de Kafka
    echo.
    echo Ejecuta START_KAFKA.bat primero
    pause
    exit /b 1
)

REM Listar topics
echo.
echo [2/3] Listando topics existentes...
echo.
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 2>nul

if %errorlevel% neq 0 (
    echo ERROR: No se puede conectar a Kafka
    echo Kafka puede estar iniciandose todavia. Espera 10-20 segundos.
    pause
    exit /b 1
)

REM Informacion detallada de topics
echo.
echo [3/3] Informacion detallada de topics...
echo.
echo --- cp.telemetry ---
docker exec kafka kafka-topics --describe --topic cp.telemetry --bootstrap-server localhost:9092 2>nul
echo.
echo --- cp.commands.ALC1 ---
docker exec kafka kafka-topics --describe --topic cp.commands.ALC1 --bootstrap-server localhost:9092 2>nul
echo.
echo --- cp.commands.SEV1 ---
docker exec kafka kafka-topics --describe --topic cp.commands.SEV1 --bootstrap-server localhost:9092 2>nul

echo.
echo ========================================
echo   KAFKA ESTADO OK
echo ========================================
echo.
echo Kafka Bootstrap: localhost:29092
echo Kafka UI: http://localhost:8080
echo.
pause
