#!/bin/bash

# =============================================================================
# Script de Despliegue para Digital Ocean
# =============================================================================

set -e

echo "🚀 Iniciando despliegue de Nisira Assistant..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.production.yml no encontrado${NC}"
    echo "Ejecuta este script desde la raíz del proyecto"
    exit 1
fi

# Verificar que existe .env.production
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ Error: .env.production no encontrado${NC}"
    echo "Crea el archivo .env.production con las variables necesarias"
    exit 1
fi

# Cargar variables de entorno
export $(cat .env.production | grep -v '^#' | xargs)

echo -e "${GREEN}✅ Variables de entorno cargadas${NC}"

# Detener servicios antiguos
echo -e "${YELLOW}🛑 Deteniendo servicios antiguos...${NC}"
docker-compose -f docker-compose.production.yml down

# Limpiar imágenes antiguas (opcional)
read -p "¿Limpiar imágenes Docker antiguas? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 Limpiando imágenes antiguas...${NC}"
    docker system prune -af --volumes
fi

# Construir imágenes
echo -e "${YELLOW}🔨 Construyendo imágenes Docker...${NC}"
docker-compose -f docker-compose.production.yml build --no-cache

# Iniciar servicios
echo -e "${YELLOW}🚀 Iniciando servicios...${NC}"
docker-compose -f docker-compose.production.yml up -d

# Esperar a que los servicios estén listos
echo -e "${YELLOW}⏳ Esperando a que los servicios inicien...${NC}"
sleep 10

# Verificar estado de servicios
echo -e "${YELLOW}📊 Estado de servicios:${NC}"
docker-compose -f docker-compose.production.yml ps

# Verificar logs
echo -e "${YELLOW}📋 Últimos logs:${NC}"
docker-compose -f docker-compose.production.yml logs --tail=50

# Verificar health checks
echo -e "${YELLOW}🏥 Verificando health checks...${NC}"
sleep 5

# Mostrar URLs
echo -e "${GREEN}✅ Despliegue completado!${NC}"
echo ""
echo "📱 URLs disponibles:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost/api/"
echo "   Health Check: http://localhost/api/health/"
echo ""
echo "📊 Comandos útiles:"
echo "   Ver logs: docker-compose -f docker-compose.production.yml logs -f"
echo "   Detener: docker-compose -f docker-compose.production.yml down"
echo "   Reiniciar: docker-compose -f docker-compose.production.yml restart"
echo ""
