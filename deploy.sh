#!/bin/bash

# =============================================================================
# Script de Despliegue para Digital Ocean
# =============================================================================

set -e

echo "[INFO] Iniciando despliegue de Nisira Assistant..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}[ERROR] docker-compose.production.yml no encontrado${NC}"
    echo "Ejecuta este script desde la raiz del proyecto"
    exit 1
fi

# Verificar que existe .env.production
if [ ! -f ".env.production" ]; then
    echo -e "${RED}[ERROR] .env.production no encontrado${NC}"
    echo "Crea el archivo .env.production con las variables necesarias"
    exit 1
fi

# Cargar variables de entorno
export $(cat .env.production | grep -v '^#' | xargs)

echo -e "${GREEN}[OK] Variables de entorno cargadas${NC}"

# Detener servicios antiguos
echo -e "${YELLOW}[INFO] Deteniendo servicios antiguos...${NC}"
docker-compose -f docker-compose.production.yml down

# Limpiar imagenes antiguas (opcional)
read -p "Limpiar imagenes Docker antiguas? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}[INFO] Limpiando imagenes antiguas...${NC}"
    docker system prune -af --volumes
fi

# Construir imagenes
echo -e "${YELLOW}[INFO] Construyendo imagenes Docker...${NC}"
docker-compose -f docker-compose.production.yml build --no-cache

# Iniciar servicios
echo -e "${YELLOW}[INFO] Iniciando servicios...${NC}"
docker-compose -f docker-compose.production.yml up -d

# Esperar a que los servicios esten listos
echo -e "${YELLOW}[INFO] Esperando a que los servicios inicien...${NC}"
sleep 10

# Verificar estado de servicios
echo -e "${YELLOW}[INFO] Estado de servicios:${NC}"
docker-compose -f docker-compose.production.yml ps

# Verificar logs
echo -e "${YELLOW}[INFO] Ultimos logs:${NC}"
docker-compose -f docker-compose.production.yml logs --tail=50

# Verificar health checks
echo -e "${YELLOW}[INFO] Verificando health checks...${NC}"
sleep 5

# Mostrar URLs
echo -e "${GREEN}[OK] Despliegue completado${NC}"
echo ""
echo "URLs disponibles:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost/api/"
echo "   Health Check: http://localhost/api/health/"
echo ""
echo "Comandos utiles:"
echo "   Ver logs: docker-compose -f docker-compose.production.yml logs -f"
echo "   Detener: docker-compose -f docker-compose.production.yml down"
echo "   Reiniciar: docker-compose -f docker-compose.production.yml restart"
echo ""
