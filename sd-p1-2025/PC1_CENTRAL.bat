@echo off
REM ========================================
REM ORDENADOR 1: CENTRAL + KAFKA + WEB GUI
REM ========================================
REM Este ordenador ejecuta:
REM - Docker con Kafka/Zookeeper
REM - CENTRAL con GUI Web
REM ========================================

echo.
echo ========================================
echo   ORDENADOR 1: CENTRAL + KAFKA
echo ========================================
echo.
echo Este script iniciara:
echo  1. Docker Compose (Kafka + Zookeeper + Kafka-UI)
echo  2. CENTRAL con GUI Web (puerto 8000)
echo.
echo Presiona cualquier tecla para continuar...
pause > nul

echo.
echo ========================================
echo   INICIANDO KAFKA Y CREANDO TOPICS
echo ========================================
call START_KAFKA.bat nopause
if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar Kafka
    pause
    exit /b 1
)

echo.
echo ========================================
echo   KAFKA LISTO
echo ========================================
echo.
echo Kafka UI: http://localhost:8080
echo Kafka Bootstrap: localhost:29092
echo.
echo Presiona cualquier tecla para iniciar el CENTRAL...
pause > nul

REM Iniciar CENTRAL con GUI Web
echo.
echo ========================================
echo   INICIANDO CENTRAL CON GUI WEB
echo ========================================
echo.
echo CENTRAL TCP: puerto 9099
echo GUI Web: http://localhost:8000
echo.
echo Comandos disponibles en la consola:
echo   list          - Listar todos los CPs
echo   stop CP_ID    - Parar un CP (Out of Order)
echo   resume CP_ID  - Reanudar un CP
echo   quit          - Salir
echo.
echo ========================================

python src\EV_Central\EV_Central_Web.py --host 0.0.0.0 --port 9099 --kafka-bootstrap localhost:29092 --web-port 8000

echo.
echo CENTRAL detenido. Presiona cualquier tecla para salir...
pause > nul
