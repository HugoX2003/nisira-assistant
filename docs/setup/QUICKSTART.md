# 🚀 Guía Rápida - Digital Ocean

## 1️⃣ Crear Droplet

1. Ir a [Digital Ocean](https://www.digitalocean.com)
2. **Create > Droplets**
3. Configuración:
   - **OS**: Ubuntu 22.04 LTS
   - **Plan**: Basic
   - **CPU**: Regular, 4GB RAM / 2 vCPUs ($24/mes)
   - **Región**: New York o la más cercana
   - **SSH**: Agregar tu clave pública
   - **Hostname**: nisira-assistant

## 2️⃣ Conectar al Servidor

```bash
ssh root@YOUR_DROPLET_IP
```

## 3️⃣ Configuración Inicial (Una Vez)

```bash
# Descargar script de setup
wget https://raw.githubusercontent.com/tu-usuario/nisira-assistant/main/setup-server.sh

# Dar permisos
chmod +x setup-server.sh

# Ejecutar
./setup-server.sh
```

O manualmente:

```bash
# Actualizar
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar utilidades
apt install -y git curl htop nano ufw certbot python3-certbot-nginx

# Firewall
ufw enable
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
```

## 4️⃣ Desplegar Aplicación

```bash
# Clonar
cd /opt
git clone https://github.com/tu-usuario/nisira-assistant.git
cd nisira-assistant

# Configurar
cp .env.production.example .env.production
nano .env.production

# Copiar credenciales
nano backend/credentials.json
# Pegar tu credentials.json

# Desplegar
chmod +x deploy.sh
./deploy.sh
```

## 5️⃣ Configurar SSL (HTTPS)

```bash
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

## 6️⃣ Verificar

```bash
# Estado
docker compose -f docker-compose.production.yml ps

# Logs
docker compose -f docker-compose.production.yml logs -f

# Health
curl https://tu-dominio.com/api/health/
```

## 🔄 Actualizar Aplicación

```bash
cd /opt/nisira-assistant
git pull origin main
docker compose -f docker-compose.production.yml up -d --build
```

## 📊 Comandos Útiles

### Ver Logs
```bash
docker compose -f docker-compose.production.yml logs -f backend
```

### Reiniciar Servicio
```bash
docker compose -f docker-compose.production.yml restart backend
```

### Entrar al Contenedor
```bash
docker compose -f docker-compose.production.yml exec backend bash
```

### Backup Base de Datos
```bash
docker compose -f docker-compose.production.yml exec db pg_dump -U postgres rag_asistente > backup.sql
```

### Ver Recursos
```bash
docker stats
htop
df -h
```

## 🐛 Troubleshooting

### Servicio no inicia
```bash
docker compose -f docker-compose.production.yml logs backend
```

### Reiniciar Todo
```bash
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d
```

### Limpiar y Reconstruir
```bash
docker compose -f docker-compose.production.yml down -v
docker compose -f docker-compose.production.yml up -d --build
```

## 📞 URLs

- **Frontend**: https://tu-dominio.com
- **API**: https://tu-dominio.com/api/
- **Admin**: https://tu-dominio.com/api/admin/
- **Health**: https://tu-dominio.com/api/health/

## 💡 Tips

1. **Backups**: Configura backups automáticos con `crontab -e`
2. **Monitoreo**: Revisa logs regularmente
3. **Seguridad**: Mantén el sistema actualizado
4. **SSL**: Certbot renueva automáticamente los certificados
5. **Recursos**: Monitorea uso con `docker stats` y `htop`

---

**¿Necesitas ayuda?** Revisa `DEPLOYMENT.md` y `DEPLOYMENT_CHECKLIST.md`
