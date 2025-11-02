@echo off
REM Script para probar el protocolo STX-ETX-LRC localmente
REM Inicia CENTRAL + ENGINE + MONITOR + TEST automáticamente

echo ========================================
echo TEST LOCAL DEL PROTOCOLO STX-ETX-LRC
echo ========================================
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)

echo [1/4] Iniciando CENTRAL en puerto 8888...
start "CENTRAL" cmd /k "python src\EV_Central\EV_Central_Web.py --host 127.0.0.1 --port 8888"
timeout /t 3 >nul

echo [2/4] Iniciando ENGINE para ALC1 en puerto 5001...
start "ENGINE-ALC1" cmd /k "python src\EV_CP_E\EV_CP_E.py --cp-id ALC1 --port 5001"
timeout /t 2 >nul

echo [3/4] Iniciando MONITOR para ALC1...
start "MONITOR-ALC1" cmd /k "python src\EV_CP_M\EV_CP_M.py --cp-id ALC1 --engine-host localhost --engine-port 5001 --central-host localhost --central-port 8888"
timeout /t 3 >nul

echo [4/4] Esperando que el sistema se estabilice...
timeout /t 3 >nul

echo.
echo ========================================
echo Sistema iniciado!
echo ========================================
echo.
echo Ventanas abiertas:
echo   - CENTRAL: Puerto 8888 (socket) y 8000 (web)
echo   - ENGINE-ALC1: Puerto 5001
echo   - MONITOR-ALC1: Conectado a CENTRAL
echo.
echo Web GUI: http://localhost:8000
echo.
echo ========================================
echo Ejecutando TEST del protocolo...
echo ========================================
echo.

timeout /t 2 >nul
python test_protocol_complete.py --auto

echo.
echo ========================================
echo TEST COMPLETADO
echo ========================================
echo.
echo Presiona cualquier tecla para CERRAR todas las ventanas...
pause >nul

REM Cerrar todas las ventanas
taskkill /FI "WindowTitle eq CENTRAL*" /F >nul 2>&1
taskkill /FI "WindowTitle eq ENGINE*" /F >nul 2>&1
taskkill /FI "WindowTitle eq MONITOR*" /F >nul 2>&1

echo Todas las ventanas cerradas.
