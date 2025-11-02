@echo off
REM ========================================
REM REINICIAR KAFKA (Docker)
REM ========================================
REM Usa este script cuando cambies la configuracion de Kafka
REM o cuando tengas problemas de conexion
REM ========================================

echo.
echo ========================================
echo   REINICIANDO KAFKA
echo ========================================
echo.

cd docker

echo [1/4] Deteniendo contenedores...
docker-compose down

echo.
echo [2/4] Limpiando volumenes antiguos (opcional)...
set /p CLEAN_VOLUMES="Limpiar volumenes? (s/N): "
if /I "%CLEAN_VOLUMES%"=="s" (
    docker volume prune -f
    echo Volumenes limpiados
)

echo.
echo [3/4] Iniciando contenedores...
docker-compose up -d

echo.
echo [4/4] Esperando a que Kafka este listo...
timeout /t 15 /nobreak

cd ..

echo.
echo ========================================
echo   VERIFICANDO KAFKA
echo ========================================
echo.

REM Verificar que Kafka esta corriendo
docker ps | findstr kafka

echo.
echo ========================================
echo   CREANDO TOPICS
echo ========================================
echo.

python scripts\create_kafka_topics.py

echo.
echo ========================================
echo   KAFKA REINICIADO
echo ========================================
echo.
echo Kafka deberia estar listo en:
echo   - localhost:29092 (desde este PC)
echo   - %COMPUTERNAME%:9092 (desde otros PCs en red)
echo.
echo Para ver tu IP ejecuta: ipconfig
echo.
echo Abre Kafka UI en: http://localhost:8080
echo.
pause
