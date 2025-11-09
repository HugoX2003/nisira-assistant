@echo off
REM =============================================================================
REM Script de Despliegue para Windows
REM =============================================================================

echo 🚀 Iniciando despliegue de Nisira Assistant...

REM Verificar docker-compose.production.yml
if not exist docker-compose.production.yml (
    echo ❌ Error: docker-compose.production.yml no encontrado
    echo Ejecuta este script desde la raíz del proyecto
    exit /b 1
)

REM Verificar .env.production
if not exist .env.production (
    echo ❌ Error: .env.production no encontrado
    echo Crea el archivo .env.production con las variables necesarias
    exit /b 1
)

echo ✅ Archivos de configuración encontrados

REM Detener servicios antiguos
echo 🛑 Deteniendo servicios antiguos...
docker-compose -f docker-compose.production.yml down

REM Construir imágenes
echo 🔨 Construyendo imágenes Docker...
docker-compose -f docker-compose.production.yml build

REM Iniciar servicios
echo 🚀 Iniciando servicios...
docker-compose -f docker-compose.production.yml up -d

REM Esperar
echo ⏳ Esperando a que los servicios inicien...
timeout /t 15 /nobreak > nul

REM Ver estado
echo 📊 Estado de servicios:
docker-compose -f docker-compose.production.yml ps

REM Ver logs
echo 📋 Últimos logs:
docker-compose -f docker-compose.production.yml logs --tail=30

echo.
echo ✅ Despliegue completado!
echo.
echo 📱 URLs disponibles:
echo    Frontend: http://localhost
echo    Backend API: http://localhost/api/
echo    Health Check: http://localhost/api/health/
echo.
echo 📊 Comandos útiles:
echo    Ver logs: docker-compose -f docker-compose.production.yml logs -f
echo    Detener: docker-compose -f docker-compose.production.yml down
echo    Reiniciar: docker-compose -f docker-compose.production.yml restart
echo.
pause
