# Script para crear los topics de Kafka necesarios para el sistema EV Charging
# NOTA: Ya NO se crean topics individuales por CP
#       Todos los CPs usan 'cp.commands.all' (topic compartido con filtrado)

Write-Host "Creando topics de Kafka..." -ForegroundColor Cyan

# Topic de telemetría (compartido por todos los CPs)
Write-Host "`nCreando topic: cp.telemetry (telemetria de todos los CPs)" -ForegroundColor Yellow
docker exec kafka kafka-topics --create --if-not-exists --topic cp.telemetry --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Topic de comandos compartido (todos los CPs usan este)
Write-Host "Creando topic: cp.commands.all (comandos para todos los CPs)" -ForegroundColor Yellow
docker exec kafka kafka-topics --create --if-not-exists --topic cp.commands.all --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

Write-Host "`n✅ Todos los topics creados!" -ForegroundColor Green
Write-Host "   - cp.telemetry: Telemetria de todos los CPs" -ForegroundColor White
Write-Host "   - cp.commands.all: Comandos para todos los CPs (filtrado por cp_id)" -ForegroundColor White

# Listar todos los topics
Write-Host "`nTopics existentes:" -ForegroundColor Cyan
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

Write-Host "`nIMPORTANTE: Ya NO se crean topics individuales (cp.commands.ALC1, etc.)" -ForegroundColor Yellow
Write-Host "            Todos los CPs usan 'cp.commands.all' con filtrado automatico" -ForegroundColor Yellow

