@echo off
title EV CENTRAL WEB GUI
echo ========================================
echo   CENTRAL con Web GUI
echo ========================================
echo.
echo Iniciando servidor web en puerto 8000...
echo.
python src/EV_Central/EV_Central_Web.py --host 0.0.0.0 --port 9099 --web-port 8000 --kafka-bootstrap localhost:29092
pause
