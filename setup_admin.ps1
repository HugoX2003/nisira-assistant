# Script de instalación y configuración del Panel de Administración
# Ejecutar desde el directorio raíz del proyecto

Write-Host "🚀 Configurando Panel de Administración de Nisira Assistant" -ForegroundColor Cyan
Write-Host ""

# 1. Instalar dependencias del backend
Write-Host "📦 Instalando dependencias del backend..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt

# 2. Aplicar migraciones
Write-Host ""
Write-Host "🗄️  Aplicando migraciones de base de datos..." -ForegroundColor Yellow
python manage.py migrate

# 3. Crear usuario admin
Write-Host ""
Write-Host "👤 Creando usuario administrador..." -ForegroundColor Yellow
python manage.py create_admin_user

# 4. Crear directorios necesarios
Write-Host ""
Write-Host "📁 Creando directorios del sistema..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data/documents" | Out-Null
New-Item -ItemType Directory -Force -Path "data/temp" | Out-Null
New-Item -ItemType Directory -Force -Path "data/processed" | Out-Null
New-Item -ItemType Directory -Force -Path "chroma_db" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host "✅ Directorios creados" -ForegroundColor Green

# 5. Volver al directorio raíz
Set-Location ..

# 6. Instalar dependencias del frontend
Write-Host ""
Write-Host "📦 Instalando dependencias del frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install

# Volver al directorio raíz
Set-Location ..

Write-Host ""
Write-Host "✅ ¡Instalación completada!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Credenciales del administrador:" -ForegroundColor Cyan
Write-Host "   Usuario: admin" -ForegroundColor White
Write-Host "   Contraseña: admin123" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Para iniciar el sistema:" -ForegroundColor Cyan
Write-Host "   Backend:  cd backend && python manage.py runserver" -ForegroundColor White
Write-Host "   Frontend: cd frontend && npm start" -ForegroundColor White
Write-Host ""
Write-Host "🌐 El panel de administración estará disponible en:" -ForegroundColor Cyan
Write-Host "   http://localhost:3000 (Login con admin/admin123)" -ForegroundColor White
Write-Host ""
