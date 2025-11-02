@echo off
REM ========================================
REM DETENER KAFKA Y LIMPIAR
REM ========================================

echo.
echo ========================================
echo   DETENER KAFKA
echo ========================================
echo.
echo Este script detendra Kafka y eliminara los contenedores.
echo Los datos se mantendran en volumenes Docker.
echo.
echo Presiona cualquier tecla para continuar o Ctrl+C para cancelar...
pause > nul

cd /d "%~dp0docker"

echo.
echo Deteniendo contenedores...
docker-compose down

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   KAFKA DETENIDO
    echo ========================================
    echo.
    echo Contenedores detenidos correctamente
    echo.
    echo Para reiniciar: START_KAFKA.bat
    echo.
) else (
    echo.
    echo ERROR: No se pudo detener los contenedores
    echo.
)

cd ..
pause
