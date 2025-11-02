# Script PowerShell para instalar dependencias de FastAPI

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalando FastAPI y dependencias" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si pipenv está instalado
if (Get-Command pipenv -ErrorAction SilentlyContinue) {
    Write-Host "Usando pipenv..." -ForegroundColor Green
    pipenv install fastapi uvicorn[standard] websockets
} else {
    Write-Host "pipenv no encontrado, usando pip..." -ForegroundColor Yellow
    pip install fastapi "uvicorn[standard]" websockets
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Instalacion completada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora puedes ejecutar: start_central_web.bat" -ForegroundColor Cyan

Read-Host "Presiona Enter para salir"
