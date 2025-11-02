@echo off
title EV DRIVER WEB GUI - LOCAL
echo ========================================
echo   DRIVER con Web GUI (Local)
echo ========================================
echo.

REM Solicitar Driver ID
set /p DRIVER_ID="Introduce Driver ID (ej: Maria1, Juan2, pepe): "
if "%DRIVER_ID%"=="" set DRIVER_ID=TestDriver

echo.
echo Driver ID: %DRIVER_ID%
echo Central: localhost:50000
echo Web GUI: http://localhost:5000
echo Kafka: localhost:29092
echo.
echo El driver se registrara automaticamente en la BD si no existe
echo.
echo ========================================

REM Iniciar DRIVER con Web GUI
python src\EV_Driver\EV_Driver_Web.py --driver-id %DRIVER_ID% --central-host 127.0.0.1 --central-port 50000 --web-port 5000 --kafka-bootstrap 127.0.0.1:29092 --db-path central.db

echo.
echo DRIVER detenido. Presiona cualquier tecla para salir...
pause > nul
