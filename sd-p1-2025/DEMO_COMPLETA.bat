@echo off
REM ========================================
REM DEMO COMPLETA - TODO EN UN PC
REM ========================================
REM Inicia CENTRAL + 2 CPs + 2 Drivers
REM ========================================

echo.
echo ========================================
echo   DEMO COMPLETA DEL SISTEMA
echo ========================================
echo.
echo Este script iniciara automaticamente:
echo   - CENTRAL con GUI Web (puerto 8000)
echo   - 2 Charging Points (ALC1, SEV1)
echo   - 2 Drivers (ID 5 y 23)
echo.
echo IMPORTANTE: Asegurate de que Docker este corriendo
echo.
echo Presiona cualquier tecla para continuar...
pause > nul

REM Iniciar Kafka con topics
echo.
echo [1/5] Iniciando Kafka y creando topics...
call START_KAFKA.bat
if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar Kafka
    pause
    exit /b 1
)
echo OK: Kafka y topics listos

REM Iniciar CENTRAL
echo.
echo [2/5] Iniciando CENTRAL...
start "CENTRAL" cmd /c "python src\EV_Central\EV_Central_Web.py --kafka-bootstrap localhost:29092 --web-port 8000"
timeout /t 5 /nobreak > nul
echo OK: CENTRAL iniciado en puerto 8000

REM Iniciar CP1 (ALC1)
echo.
echo [3/5] Iniciando Charging Points...
start "ENGINE-ALC1" cmd /k "python src\EV_CP_E\EV_CP_E.py --cp-id ALC1 --port 7001 --kafka-bootstrap localhost:29092"
timeout /t 2 /nobreak > nul
start "MONITOR-ALC1" cmd /k "python src\EV_CP_M\EV_CP_M.py --cp-id ALC1 --engine-addr 7001 --central-addr localhost:9099"
timeout /t 2 /nobreak > nul

REM Iniciar CP2 (SEV1)
start "ENGINE-SEV1" cmd /k "python src\EV_CP_E\EV_CP_E.py --cp-id SEV1 --port 7002 --kafka-bootstrap localhost:29092"
timeout /t 2 /nobreak > nul
start "MONITOR-SEV1" cmd /k "python src\EV_CP_M\EV_CP_M.py --cp-id SEV1 --engine-addr 7002 --central-addr localhost:9099"
timeout /t 2 /nobreak > nul
echo OK: 2 CPs iniciados (ALC1, SEV1)

REM Iniciar Drivers
echo.
echo [4/5] Iniciando Drivers con GUI Web...
start "DRIVER-5-WEB" cmd /k "python src\EV_Driver\EV_Driver_Web.py --driver-id 5 --central-host localhost --central-port 9099 --web-port 5001 --kafka-bootstrap localhost:29092"
timeout /t 2 /nobreak > nul
start "DRIVER-23-WEB" cmd /k "python src\EV_Driver\EV_Driver_Web.py --driver-id 23 --central-host localhost --central-port 9099 --web-port 5002 --kafka-bootstrap localhost:29092"
timeout /t 1 /nobreak > nul
echo OK: 2 Drivers iniciados (ID 5 en puerto 5001, ID 23 en puerto 5002)

echo.
echo ========================================
echo   SISTEMA COMPLETO INICIADO
echo ========================================
echo.
echo GUI Central: http://localhost:8000
echo GUI Driver 5: http://localhost:5001
echo GUI Driver 23: http://localhost:5002
echo Kafka UI:    http://localhost:8080
echo Central TCP: localhost:9099
echo.
echo CPs disponibles:
echo   - ALC1 (Alicante, puerto 7001)
echo   - SEV1 (Sevilla, puerto 7002)
echo.
echo Drivers activos:
echo   - Driver 5 (puerto 5001)
echo   - Driver 23 (puerto 5002)
echo.
echo Abriendo navegadores en 3 segundos...
timeout /t 3 /nobreak > nul

REM Abrir navegadores
start http://localhost:8000
timeout /t 1 /nobreak > nul
start http://localhost:5001
timeout /t 1 /nobreak > nul
start http://localhost:5002

echo.
echo ========================================
echo PRESIONA CUALQUIER TECLA PARA DETENER
echo ========================================
pause > nul

echo.
echo Deteniendo sistema...
taskkill /FI "WindowTitle eq CENTRAL*" /F 2>nul
taskkill /FI "WindowTitle eq ENGINE*" /F 2>nul
taskkill /FI "WindowTitle eq MONITOR*" /F 2>nul
taskkill /FI "WindowTitle eq DRIVER*" /F 2>nul

echo Sistema detenido.
pause
