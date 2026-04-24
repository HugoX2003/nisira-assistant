#!/bin/bash

# =============================================================================
# Script de Configuracion Inicial para Digital Ocean
# =============================================================================
# Ejecutar este script en un droplet nuevo de Ubuntu

set -e

echo "[INFO] Configuracion inicial de servidor Digital Ocean"
echo "=================================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Actualizar sistema
echo -e "${YELLOW}[INFO] Actualizando sistema...${NC}"
apt update && apt upgrade -y

# Instalar Docker
echo -e "${YELLOW}[INFO] Instalando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}[OK] Docker instalado${NC}"
else
    echo -e "${GREEN}[OK] Docker ya esta instalado${NC}"
fi

# Verificar Docker Compose
echo -e "${YELLOW}[INFO] Verificando Docker Compose...${NC}"
docker compose version
echo -e "${GREEN}[OK] Docker Compose disponible${NC}"

# Instalar utilidades
echo -e "${YELLOW}[INFO] Instalando utilidades...${NC}"
apt install -y git curl wget htop nano ufw net-tools

# Configurar firewall
echo -e "${YELLOW}[INFO] Configurando firewall...${NC}"
ufw --force enable
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload
echo -e "${GREEN}[OK] Firewall configurado${NC}"

# Instalar Certbot (para SSL)
echo -e "${YELLOW}[INFO] Instalando Certbot...${NC}"
apt install -y certbot python3-certbot-nginx
echo -e "${GREEN}[OK] Certbot instalado${NC}"

# Crear estructura de directorios
echo -e "${YELLOW}[INFO] Creando directorios...${NC}"
mkdir -p /opt/nisira-assistant
mkdir -p /backups
echo -e "${GREEN}[OK] Directorios creados${NC}"

# Configurar timezone
echo -e "${YELLOW}[INFO] Configurando timezone...${NC}"
timedatectl set-timezone America/Lima
echo -e "${GREEN}[OK] Timezone configurado${NC}"

# Mostrar informacion del sistema
echo ""
echo -e "${GREEN}=================================================="
echo "[OK] Configuracion inicial completada"
echo "==================================================${NC}"
echo ""
echo "Informacion del sistema:"
echo "   SO: $(lsb_release -d | cut -f2)"
echo "   Docker: $(docker --version)"
echo "   Docker Compose: $(docker compose version)"
echo "   IP: $(curl -s ifconfig.me)"
echo "   Timezone: $(timedatectl | grep "Time zone" | awk '{print $3}')"
echo ""
echo "Firewall (UFW):"
ufw status numbered
echo ""
echo "Proximos pasos:"
echo "   1. Clonar repositorio: cd /opt && git clone <repo-url>"
echo "   2. Configurar .env.production"
echo "   3. Copiar credentials.json"
echo "   4. Ejecutar ./deploy.sh"
echo "   5. Configurar SSL: certbot --nginx -d tu-dominio.com"
echo ""
