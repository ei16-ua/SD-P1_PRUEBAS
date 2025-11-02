@echo off
REM ========================================
REM ORDENADOR 3: DRIVER (Cliente)
REM ========================================
REM Este ordenador ejecuta:
REM - DRIVER con GUI WEB (sin instalar nada)
REM ========================================

echo.
echo ========================================
echo   ORDENADOR 3: DRIVER (Cliente Web)
echo ========================================
echo.
echo Opciones:
echo   1. Driver con GUI Web (recomendado - no requiere instalaciones)
echo   2. Driver con GUI Pygame (requiere Pygame)
echo.
set /p GUI_CHOICE="Selecciona una opcion (1/2): "

if "%GUI_CHOICE%"=="2" goto pygame_gui

:web_gui
echo.
echo === DRIVER WEB GUI ===
echo.

REM Solicitar IP del CENTRAL
set /p CENTRAL_IP="Introduce la IP del CENTRAL (o 'localhost' si es el mismo PC): "
if "%CENTRAL_IP%"=="" set CENTRAL_IP=localhost

REM Solicitar Driver ID
set /p DRIVER_ID="Introduce tu Driver ID (numero): "
if "%DRIVER_ID%"=="" (
    echo ERROR: Debes introducir un Driver ID
    pause
    exit /b 1
)

REM Solicitar puerto web
set /p WEB_PORT="Puerto del GUI Web (por defecto 5000): "
if "%WEB_PORT%"=="" set WEB_PORT=5000

REM Solicitar IP de Kafka (IMPORTANTE para telemetria)
set /p KAFKA_IP="IP de Kafka para telemetria (ej: 192.168.1.11, o enter=sin telemetria): "

REM Determinar el puerto de Kafka segun si es local o remoto
set KAFKA_PORT=29092
if not "%KAFKA_IP%"=="" (
    if /I "%KAFKA_IP%"=="localhost" (
        set KAFKA_PORT=29092
    ) else if /I "%KAFKA_IP%"=="127.0.0.1" (
        set KAFKA_PORT=29092
    ) else (
        REM IP remota: usar puerto 9092
        set KAFKA_PORT=9092
    )
)

echo.
echo ========================================
echo   CONFIGURACION WEB GUI
echo ========================================
echo.
echo Driver ID:    %DRIVER_ID%
echo CENTRAL:      %CENTRAL_IP%:9099
echo Web GUI:      http://localhost:%WEB_PORT%
if not "%KAFKA_IP%"=="" (
    echo Kafka:        %KAFKA_IP%:%KAFKA_PORT%
    echo.
    echo IMPORTANTE: Kafka configurado - recibiras telemetria en tiempo real
) else (
    echo.
    echo ADVERTENCIA: Kafka NO configurado - NO veras kW/EUR en tiempo real
)
echo.
echo Presiona cualquier tecla para iniciar...
pause > nul

echo.
echo ========================================
echo   INICIANDO DRIVER WEB GUI
echo ========================================
echo.
echo Instrucciones:
echo  1. El navegador se abrira automaticamente
echo  2. Selecciona un CP de la lista desplegable
echo  3. Haz clic en "REQUEST SERVICE"
echo  4. Espera autorizacion
echo  5. La carga empezara automaticamente
echo  6. Haz clic en "FINISH & PAY" cuando termines
echo.
echo ========================================

REM Construir comando Web
set CMD_WEB=python src\EV_Driver\EV_Driver_Web.py --driver-id %DRIVER_ID% --central-host %CENTRAL_IP% --central-port 9099 --web-port %WEB_PORT%
if not "%KAFKA_IP%"=="" set CMD_WEB=%CMD_WEB% --kafka-bootstrap %KAFKA_IP%:%KAFKA_PORT%

REM Iniciar servidor web en segundo plano
start "DRIVER-%DRIVER_ID%-WEB" %CMD_WEB%

REM Esperar y abrir navegador
timeout /t 3 /nobreak > nul
start http://localhost:%WEB_PORT%

echo.
echo GUI Web iniciado en http://localhost:%WEB_PORT%
echo Presiona cualquier tecla para salir (esto NO cerrara el servidor)...
pause > nul
exit /b 0

:pygame_gui
echo.
echo === DRIVER PYGAME GUI ===
echo.

echo.
echo ========================================
echo   CONFIGURACION
echo ========================================
echo.
echo Driver ID:    %DRIVER_ID%
echo CENTRAL:      %CENTRAL_IP%:9099
echo.
echo Presiona cualquier tecla para iniciar el GUI del DRIVER...
pause > nul

echo.
echo ========================================
echo   INICIANDO DRIVER GUI
echo ========================================
echo.
echo Instrucciones:
echo  1. Selecciona un CP de la lista
echo  2. Haz clic en "REQUEST SERVICE"
echo  3. Espera autorizacion
echo  4. La carga empezara automaticamente
echo  5. Haz clic en "DETENER CARGA" cuando termines
echo  6. Haz clic en "PAGAR Y SALIR" para completar
echo  7. Abre http://localhost:5000 en tu navegador
echo.
echo ========================================

REM Iniciar DRIVER con Web GUI
python src\EV_Driver\EV_Driver_Web.py --driver-id %DRIVER_ID% --central-host %CENTRAL_IP% --central-port 50000 --web-port 5000 --kafka-bootstrap %CENTRAL_IP%:9092

echo.
echo DRIVER detenido. Presiona cualquier tecla para salir...
pause > nul
