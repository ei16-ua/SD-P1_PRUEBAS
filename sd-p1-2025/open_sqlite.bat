@echo off
REM Script para abrir SQLite con la base de datos del sistema

set DB_PATH=.\src\EV_Central\central.db

echo Abriendo SQLite con la base de datos...
echo Base de datos: %DB_PATH%
echo.
echo Comandos útiles:
echo   .tables          - Ver todas las tablas
echo   .schema          - Ver estructura de las tablas
echo   .headers on      - Mostrar nombres de columnas
echo   .mode column     - Formato de columnas
echo   SELECT * FROM charging_points;
echo   SELECT * FROM drivers;
echo   .quit            - Salir
echo.

sqlite3 %DB_PATH%
