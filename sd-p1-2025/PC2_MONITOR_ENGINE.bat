@echo off
REM ========================================
REM ORDENADOR 2: MONITOR + ENGINE
REM ========================================
REM Este ordenador ejecuta:
REM - ENGINE (simulador de cargador)
REM - MONITOR (conexion con CENTRAL)
REM ========================================

echo.
echo ========================================
echo   ORDENADOR 2: MONITOR + ENGINE
echo ========================================
echo.

REM Solicitar IP del CENTRAL
set /p CENTRAL_IP="Introduce la IP del CENTRAL (o 'localhost' si es el mismo PC): "
if "%CENTRAL_IP%"=="" set CENTRAL_IP=localhost

REM Solicitar IP de Kafka
set /p KAFKA_IP="Introduce la IP de Kafka (o 'localhost' si es el mismo PC): "
if "%KAFKA_IP%"=="" set KAFKA_IP=localhost

REM Determinar el puerto de Kafka segun si es local o remoto
set KAFKA_PORT=29092
if /I "%KAFKA_IP%"=="localhost" (
    set KAFKA_PORT=29092
) else if /I "%KAFKA_IP%"=="127.0.0.1" (
    set KAFKA_PORT=29092
) else (
    REM IP remota: usar puerto 9092
    set KAFKA_PORT=9092
)

REM Solicitar CP_ID
set /p CP_ID="Introduce el ID del CP (ej: ALC1, SEV1, MAD2): "
if "%CP_ID%"=="" (
    echo ERROR: Debes introducir un CP_ID
    pause
    exit /b 1
)

REM Solicitar puerto del ENGINE
set /p ENGINE_PORT="Puerto del ENGINE (por defecto 7001): "
if "%ENGINE_PORT%"=="" set ENGINE_PORT=7001

echo.
echo ========================================
echo   CONFIGURACION
echo ========================================
echo.
echo CP_ID:        %CP_ID%
echo CENTRAL:      %CENTRAL_IP%:9099
echo KAFKA:        %KAFKA_IP%:%KAFKA_PORT%
echo ENGINE PORT:  %ENGINE_PORT%
echo.
echo Presiona cualquier tecla para iniciar...
pause > nul

REM Crear archivo temporal de configuracion
echo CP_ID=%CP_ID% > temp_config.txt
echo CENTRAL_IP=%CENTRAL_IP% >> temp_config.txt
echo KAFKA_IP=%KAFKA_IP% >> temp_config.txt
echo ENGINE_PORT=%ENGINE_PORT% >> temp_config.txt

echo.
echo ========================================
echo   INICIANDO ENGINE
echo ========================================
echo.

REM Iniciar ENGINE en segundo plano
start "ENGINE-%CP_ID%" python src\EV_CP_E\EV_CP_E.py --cp-id %CP_ID% --port %ENGINE_PORT% --kafka-bootstrap %KAFKA_IP%:%KAFKA_PORT%

echo Esperando a que ENGINE este listo (3 segundos)...
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo   INICIANDO MONITOR
echo ========================================
echo.
echo Conectando al CENTRAL en %CENTRAL_IP%:9099...
echo.

REM Iniciar MONITOR
python src\EV_CP_M\EV_CP_M.py --cp-id %CP_ID% --engine-host 127.0.0.1 --engine-port %ENGINE_PORT% --central-host %CENTRAL_IP% --central-port 9099

echo.
echo MONITOR detenido. Presiona cualquier tecla para salir...
pause > nul

REM Limpiar
del temp_config.txt 2>nul
