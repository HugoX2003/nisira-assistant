# 🚀 Guía de Despliegue en Digital Ocean

Esta guía te ayudará a desplegar Nisira Assistant en Digital Ocean usando Docker.

## 📋 Requisitos Previos

1. **Cuenta de Digital Ocean**
2. **Droplet creado** (recomendado: 4GB RAM, 2 vCPUs)
3. **Docker y Docker Compose instalados** en el Droplet
4. **Dominio configurado** (opcional pero recomendado)

## 🔧 Paso 1: Preparar el Droplet

### Opción A: Usar Droplet con Docker pre-instalado

En Digital Ocean, crea un Droplet con la imagen **"Docker on Ubuntu"**.

### Opción B: Instalar Docker manualmente

```bash
# Conectar al droplet
ssh root@your-droplet-ip

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
apt install docker-compose-plugin -y

# Verificar instalación
docker --version
docker compose version
```

## 📦 Paso 2: Subir el Proyecto

### Opción A: Desde GitHub (Recomendado)

```bash
# En el droplet
cd /opt
git clone https://github.com/tu-usuario/nisira-assistant.git
cd nisira-assistant
```

### Opción B: Usando SCP

```bash
# Desde tu máquina local
scp -r . root@your-droplet-ip:/opt/nisira-assistant
```

## ⚙️ Paso 3: Configurar Variables de Entorno

```bash
# En el droplet
cd /opt/nisira-assistant

# Copiar archivo de ejemplo
cp .env.production.example .env.production

# Editar con tus valores reales
nano .env.production
```

**Variables críticas a cambiar:**

```bash
SECRET_KEY=genera-una-clave-secreta-fuerte-aqui
DB_PASSWORD=tu-password-seguro-para-postgresql
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,IP-del-droplet
REACT_APP_API_URL=https://tu-dominio.com
```

**Generar SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 🔐 Paso 4: Copiar Credenciales

```bash
# Copiar credentials.json de Google Drive API
nano backend/credentials.json
# Pega tu credentials.json aquí

# Asegurar permisos
chmod 600 backend/credentials.json
```

## 🚀 Paso 5: Desplegar

```bash
# Dar permisos de ejecución al script
chmod +x deploy.sh

# Ejecutar despliegue
./deploy.sh
```

O manualmente:

```bash
# Construir y levantar servicios
docker compose -f docker-compose.production.yml up -d --build

# Ver logs
docker compose -f docker-compose.production.yml logs -f
```

## 🌐 Paso 6: Configurar Nginx y SSL (Opcional pero Recomendado)

### Instalar Certbot para SSL

```bash
# Instalar Certbot
apt install certbot python3-certbot-nginx -y

# Obtener certificado SSL
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Renovación automática (ya configurado por Certbot)
```

## 📊 Verificación

```bash
# Ver estado de servicios
docker compose -f docker-compose.production.yml ps

# Ver logs
docker compose -f docker-compose.production.yml logs -f backend
docker compose -f docker-compose.production.yml logs -f frontend

# Verificar health
curl http://localhost/api/health/
```

## 🔄 Actualizar la Aplicación

```bash
# Pull últimos cambios (si usas Git)
git pull origin main

# Reconstruir y reiniciar
docker compose -f docker-compose.production.yml up -d --build

# Ver logs
docker compose -f docker-compose.production.yml logs -f
```

## 🛠️ Comandos Útiles

```bash
# Ver logs en tiempo real
docker compose -f docker-compose.production.yml logs -f

# Reiniciar un servicio específico
docker compose -f docker-compose.production.yml restart backend

# Entrar al contenedor backend
docker compose -f docker-compose.production.yml exec backend bash

# Ver uso de recursos
docker stats

# Limpiar recursos no usados
docker system prune -a

# Backup de base de datos
docker compose -f docker-compose.production.yml exec db pg_dump -U postgres rag_asistente > backup.sql

# Restaurar base de datos
docker compose -f docker-compose.production.yml exec -T db psql -U postgres rag_asistente < backup.sql
```

## 🔥 Firewall (UFW)

```bash
# Habilitar firewall
ufw enable

# Permitir SSH
ufw allow OpenSSH

# Permitir HTTP y HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Ver estado
ufw status
```

## 📈 Monitoreo

### Ver logs de Django

```bash
docker compose -f docker-compose.production.yml logs -f backend | grep ERROR
```

### Ver logs de Nginx

```bash
docker compose -f docker-compose.production.yml logs -f nginx
```

### Monitorear uso de recursos

```bash
# Instalar htop
apt install htop -y
htop
```

## 🐛 Troubleshooting

### Backend no inicia

```bash
# Ver logs detallados
docker compose -f docker-compose.production.yml logs backend

# Verificar variables de entorno
docker compose -f docker-compose.production.yml exec backend env

# Ejecutar migraciones manualmente
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

### Base de datos no conecta

```bash
# Verificar que PostgreSQL está corriendo
docker compose -f docker-compose.production.yml ps db

# Conectar a PostgreSQL
docker compose -f docker-compose.production.yml exec db psql -U postgres
```

### Frontend muestra error de API

```bash
# Verificar REACT_APP_API_URL en .env.production
# Reconstruir frontend
docker compose -f docker-compose.production.yml up -d --build frontend
```

## 📱 URLs de Acceso

- **Frontend**: `https://tu-dominio.com`
- **Backend API**: `https://tu-dominio.com/api/`
- **Health Check**: `https://tu-dominio.com/api/health/`
- **Admin Django**: `https://tu-dominio.com/api/admin/`

## 🔒 Seguridad Adicional

### Cambiar puerto SSH (Opcional)

```bash
nano /etc/ssh/sshd_config
# Cambiar Port 22 a otro puerto
systemctl restart sshd
ufw allow nuevo-puerto/tcp
```

### Configurar fail2ban

```bash
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

## 💾 Backup Automatizado

```bash
# Crear script de backup
nano /root/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR

# Backup base de datos
docker compose -f /opt/nisira-assistant/docker-compose.production.yml exec -T db \
  pg_dump -U postgres rag_asistente > $BACKUP_DIR/db_$DATE.sql

# Backup archivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz \
  /opt/nisira-assistant/backend/data \
  /opt/nisira-assistant/backend/chroma_db

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Dar permisos
chmod +x /root/backup.sh

# Agregar a crontab (diario a las 2 AM)
crontab -e
0 2 * * * /root/backup.sh
```

## 📞 Soporte

Si encuentras problemas, revisa:
1. Logs de Docker: `docker compose logs -f`
2. Estado de servicios: `docker compose ps`
3. Variables de entorno: verificar .env.production

---

**¡Listo para producción! 🎉**
