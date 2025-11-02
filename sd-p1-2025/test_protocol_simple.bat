@echo off
REM Test rápido del protocolo sin Kafka
echo ========================================
echo TEST SIMPLE - Protocolo STX-ETX-LRC
echo (Sin Kafka, solo sockets TCP)
echo ========================================
echo.

REM Paso 1: Iniciar CENTRAL
echo [1/3] Iniciando CENTRAL...
start "CENTRAL-TEST" cmd /k "python src\EV_Central\EV_Central.py --host 127.0.0.1 --port 8888"
timeout /t 4 >nul

REM Paso 2: Iniciar ENGINE (sin Kafka)
echo [2/3] Iniciando ENGINE ALC1...
start "ENGINE-TEST" cmd /k "python src\EV_CP_E\EV_CP_E.py --cp-id ALC1 --port 5001"
timeout /t 3 >nul

REM Paso 3: Iniciar MONITOR
echo [3/3] Iniciando MONITOR ALC1...
start "MONITOR-TEST" cmd /k "python src\EV_CP_M\EV_CP_M.py --cp-id ALC1 --engine-host localhost --engine-port 5001 --central-host localhost --central-port 8888"
timeout /t 4 >nul

echo.
echo ========================================
echo Sistema iniciado (SIN Kafka)
echo ========================================
echo.
echo Presiona ENTER para ejecutar el test...
pause >nul

echo.
echo Ejecutando test del protocolo...
python test_protocol_complete.py --auto

echo.
echo ========================================
echo Presiona ENTER para cerrar todo...
pause >nul

taskkill /FI "WindowTitle eq *-TEST*" /F >nul 2>&1
echo Cerrado.
