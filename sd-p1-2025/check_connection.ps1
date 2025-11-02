# Script de verificación de conectividad
# ========================================

Write-Host "=== VERIFICACIÓN DE CONECTIVIDAD ===" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar IP local
Write-Host "[1] Tu IP local:" -ForegroundColor Yellow
ipconfig | Select-String "IPv4"
Write-Host ""

# 2. Probar conexión a CENTRAL
Write-Host "[2] Probando conexión a CENTRAL (192.168.1.17:9099)..." -ForegroundColor Yellow
$result = Test-NetConnection -ComputerName 192.168.1.17 -Port 9099 -WarningAction SilentlyContinue

if ($result.TcpTestSucceeded) {
    Write-Host "  ✅ CENTRAL es accesible" -ForegroundColor Green
} else {
    Write-Host "  ❌ No se puede conectar a CENTRAL" -ForegroundColor Red
    Write-Host "     Posibles causas:" -ForegroundColor Yellow
    Write-Host "     - CENTRAL no está ejecutándose" -ForegroundColor Gray
    Write-Host "     - Firewall bloqueando puerto 9099" -ForegroundColor Gray
    Write-Host "     - IP incorrecta" -ForegroundColor Gray
}
Write-Host ""

# 3. Verificar puerto 7001 local (Engine)
Write-Host "[3] Verificando si Engine está escuchando en puerto 7001..." -ForegroundColor Yellow
$engine = Get-NetTCPConnection -LocalPort 7001 -State Listen -ErrorAction SilentlyContinue

if ($engine) {
    Write-Host "  ✅ Engine está ejecutándose (puerto 7001)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Engine NO está ejecutándose" -ForegroundColor Red
    Write-Host "     Ejecuta primero el Engine:" -ForegroundColor Yellow
    Write-Host "     python .\src\EV_CP_E\EV_CP_E.py --cp-id CP01 --port 7001 --kafka-bootstrap 192.168.1.17:9092" -ForegroundColor Gray
}
Write-Host ""

Write-Host "=== FIN VERIFICACIÓN ===" -ForegroundColor Cyan
