#!/bin/bash

# =============================================================================
# Script de Configuración Inicial para Digital Ocean
# =============================================================================
# Ejecutar este script en un droplet nuevo de Ubuntu

set -e

echo "🚀 Configuración inicial de servidor Digital Ocean"
echo "=================================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Actualizar sistema
echo -e "${YELLOW}📦 Actualizando sistema...${NC}"
apt update && apt upgrade -y

# Instalar Docker
echo -e "${YELLOW}🐳 Instalando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker instalado${NC}"
else
    echo -e "${GREEN}✅ Docker ya está instalado${NC}"
fi

# Verificar Docker Compose
echo -e "${YELLOW}🔧 Verificando Docker Compose...${NC}"
docker compose version
echo -e "${GREEN}✅ Docker Compose disponible${NC}"

# Instalar utilidades
echo -e "${YELLOW}🛠️ Instalando utilidades...${NC}"
apt install -y git curl wget htop nano ufw net-tools

# Configurar firewall
echo -e "${YELLOW}🔥 Configurando firewall...${NC}"
ufw --force enable
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload
echo -e "${GREEN}✅ Firewall configurado${NC}"

# Instalar Certbot (para SSL)
echo -e "${YELLOW}🔒 Instalando Certbot...${NC}"
apt install -y certbot python3-certbot-nginx
echo -e "${GREEN}✅ Certbot instalado${NC}"

# Crear estructura de directorios
echo -e "${YELLOW}📁 Creando directorios...${NC}"
mkdir -p /opt/nisira-assistant
mkdir -p /backups
echo -e "${GREEN}✅ Directorios creados${NC}"

# Configurar timezone
echo -e "${YELLOW}🕐 Configurando timezone...${NC}"
timedatectl set-timezone America/Lima
echo -e "${GREEN}✅ Timezone configurado${NC}"

# Mostrar información del sistema
echo ""
echo -e "${GREEN}=================================================="
echo "✅ Configuración inicial completada"
echo "==================================================${NC}"
echo ""
echo "📊 Información del sistema:"
echo "   SO: $(lsb_release -d | cut -f2)"
echo "   Docker: $(docker --version)"
echo "   Docker Compose: $(docker compose version)"
echo "   IP: $(curl -s ifconfig.me)"
echo "   Timezone: $(timedatectl | grep "Time zone" | awk '{print $3}')"
echo ""
echo "🔥 Firewall (UFW):"
ufw status numbered
echo ""
echo "📝 Próximos pasos:"
echo "   1. Clonar repositorio: cd /opt && git clone <repo-url>"
echo "   2. Configurar .env.production"
echo "   3. Copiar credentials.json"
echo "   4. Ejecutar ./deploy.sh"
echo "   5. Configurar SSL: certbot --nginx -d tu-dominio.com"
echo ""
