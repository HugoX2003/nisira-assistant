# ✅ Checklist de Despliegue - Digital Ocean

## Pre-Despliegue (Local)

### 1. Preparación del Código
- [ ] Código limpio y sin errores
- [ ] Tests pasando (si aplica)
- [ ] RAGAS deshabilitado para evitar errores
- [ ] `.gitignore` actualizado
- [ ] Archivos sensibles NO están en Git

### 2. Configuración Docker
- [ ] `docker-compose.production.yml` revisado
- [ ] Dockerfiles optimizados
- [ ] `.dockerignore` configurado
- [ ] Health checks añadidos

### 3. Variables de Entorno
- [ ] `.env.production.example` creado con todas las variables
- [ ] Credenciales preparadas (no en Git)
- [ ] API keys verificadas

### 4. Base de Datos
- [ ] Migraciones creadas
- [ ] No hay migraciones pendientes
- [ ] Modelo de datos correcto

---

## Configuración Digital Ocean

### 1. Crear Droplet
- [ ] Crear cuenta Digital Ocean
- [ ] Crear Droplet (Ubuntu 22.04 LTS, mínimo 4GB RAM)
- [ ] Elegir región cercana
- [ ] Configurar SSH keys
- [ ] Habilitar backups automáticos (opcional)

**Comando:**
```bash
# En Digital Ocean Console
# Click: Create > Droplets
# OS: Ubuntu 22.04 LTS
# Plan: Basic, 4GB RAM, 2 vCPUs ($24/mes)
# SSH: Agregar tu clave pública
```

### 2. Configuración Inicial del Servidor
```bash
# Conectar al droplet
ssh root@your-droplet-ip

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verificar instalación
docker --version
docker compose version

# Instalar utilidades
apt install -y git curl htop nano ufw
```

- [ ] Servidor actualizado
- [ ] Docker instalado
- [ ] Docker Compose instalado
- [ ] Utilidades instaladas

### 3. Configurar Firewall
```bash
# Habilitar UFW
ufw enable

# Permitir SSH
ufw allow OpenSSH

# Permitir HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Ver estado
ufw status
```

- [ ] UFW habilitado
- [ ] Puertos abiertos (22, 80, 443)

### 4. Configurar Dominio (Opcional pero Recomendado)
- [ ] Dominio comprado/configurado
- [ ] DNS apuntando al IP del Droplet
- [ ] Registro A configurado
- [ ] Esperar propagación DNS (puede tardar hasta 48h)

**En tu proveedor DNS:**
```
Tipo: A
Nombre: @
Valor: [IP del Droplet]
TTL: 3600

Tipo: A
Nombre: www
Valor: [IP del Droplet]
TTL: 3600
```

---

## Despliegue

### 1. Subir Código al Servidor

**Opción A: Git (Recomendado)**
```bash
# En GitHub, crear repositorio privado
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/nisira-assistant.git
git push -u origin main

# En el droplet
cd /opt
git clone https://github.com/tu-usuario/nisira-assistant.git
cd nisira-assistant
```

**Opción B: SCP**
```bash
# Desde tu máquina local
scp -r . root@your-droplet-ip:/opt/nisira-assistant
```

- [ ] Código en el servidor
- [ ] En directorio `/opt/nisira-assistant`

### 2. Configurar Variables de Entorno
```bash
cd /opt/nisira-assistant

# Copiar ejemplo
cp .env.production.example .env.production

# Editar
nano .env.production
```

**Variables críticas:**
- [ ] `SECRET_KEY` - Generado nuevo y fuerte
- [ ] `DB_PASSWORD` - Password seguro para PostgreSQL
- [ ] `ALLOWED_HOSTS` - Tu dominio e IP
- [ ] `OPENROUTER_API_KEY` - Tu API key
- [ ] `GOOGLE_API_KEY` - Tu API key
- [ ] `GOOGLE_DRIVE_FOLDER_ID` - ID de tu carpeta
- [ ] `REACT_APP_API_URL` - URL de tu dominio

**Generar SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 3. Copiar Credenciales
```bash
# Copiar credentials.json
nano backend/credentials.json
# Pegar contenido

# Asegurar permisos
chmod 600 backend/credentials.json
```

- [ ] `credentials.json` copiado
- [ ] Permisos correctos (600)

### 4. Desplegar con Docker
```bash
# Dar permisos al script
chmod +x deploy.sh

# Ejecutar despliegue
./deploy.sh
```

O manualmente:
```bash
docker compose -f docker-compose.production.yml up -d --build
```

- [ ] Imágenes construidas sin errores
- [ ] Servicios iniciados (db, backend, frontend, nginx)

### 5. Verificar Servicios
```bash
# Ver estado
docker compose -f docker-compose.production.yml ps

# Ver logs
docker compose -f docker-compose.production.yml logs -f

# Verificar health
curl http://localhost/api/health/
```

**Todos los servicios deben estar "healthy" o "running"**

- [ ] Database: running/healthy
- [ ] Backend: running/healthy
- [ ] Frontend: running/healthy
- [ ] Nginx: running/healthy

---

## Post-Despliegue

### 1. Configurar SSL (HTTPS)
```bash
# Instalar Certbot
apt install -y certbot python3-certbot-nginx

# Obtener certificado (reemplaza con tu dominio)
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Verificar renovación automática
certbot renew --dry-run
```

- [ ] Certbot instalado
- [ ] Certificado SSL obtenido
- [ ] Renovación automática configurada
- [ ] HTTPS funcionando

### 2. Crear Superusuario Django
```bash
docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

- [ ] Superusuario creado
- [ ] Acceso a /api/admin/ verificado

### 3. Inicializar RAG (Opcional)
```bash
# Sincronizar Google Drive
docker compose -f docker-compose.production.yml exec backend python manage.py sync_drive_full

# O configurar sync automático
docker compose -f docker-compose.production.yml exec backend python manage.py start_drive_sync
```

- [ ] Documentos sincronizados
- [ ] Embeddings generados
- [ ] ChromaDB poblado

### 4. Pruebas Funcionales
- [ ] Frontend carga correctamente
- [ ] Login funciona
- [ ] Registro de usuarios funciona
- [ ] Chat responde correctamente
- [ ] API endpoints funcionan
- [ ] Admin Django accesible

### 5. Configurar Backups
```bash
# Crear script de backup
nano /root/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR

# Backup BD
docker compose -f /opt/nisira-assistant/docker-compose.production.yml exec -T db \
  pg_dump -U postgres rag_asistente > $BACKUP_DIR/db_$DATE.sql

# Backup archivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz \
  /opt/nisira-assistant/backend/data \
  /opt/nisira-assistant/backend/chroma_db

# Limpiar antiguos (>7 días)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Permisos
chmod +x /root/backup.sh

# Crontab (diario 2 AM)
crontab -e
# Agregar: 0 2 * * * /root/backup.sh
```

- [ ] Script de backup creado
- [ ] Cron configurado
- [ ] Backup manual probado

### 6. Monitoreo
```bash
# Ver logs en tiempo real
docker compose -f docker-compose.production.yml logs -f

# Monitorear recursos
htop
docker stats
```

- [ ] Logs revisados
- [ ] Recursos monitoreados
- [ ] Sin errores críticos

### 7. Seguridad Adicional (Opcional)
```bash
# Cambiar puerto SSH
nano /etc/ssh/sshd_config
# Port 2222
systemctl restart sshd
ufw allow 2222/tcp

# Instalar fail2ban
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

- [ ] Puerto SSH cambiado
- [ ] fail2ban instalado

---

## URLs Finales

✅ **Frontend**: https://tu-dominio.com
✅ **Backend API**: https://tu-dominio.com/api/
✅ **Health Check**: https://tu-dominio.com/api/health/
✅ **Admin Django**: https://tu-dominio.com/api/admin/

---

## Troubleshooting Común

### Backend no inicia
```bash
docker compose -f docker-compose.production.yml logs backend
# Verificar DATABASE_URL y migraciones
```

### Frontend muestra error
```bash
# Verificar REACT_APP_API_URL
# Reconstruir: docker compose -f docker-compose.production.yml up -d --build frontend
```

### Base de datos no conecta
```bash
docker compose -f docker-compose.production.yml exec db psql -U postgres
# Verificar contraseña en .env.production
```

### SSL no funciona
```bash
certbot renew --force-renewal
nginx -t
systemctl reload nginx
```

---

## 🎉 ¡Despliegue Completo!

Si todos los checkboxes están marcados, tu aplicación está correctamente desplegada en Digital Ocean.

**Próximos Pasos:**
1. Monitorear logs regularmente
2. Configurar alertas (opcional)
3. Optimizar rendimiento si es necesario
4. Escalar recursos según uso

**Soporte:**
- Documentación: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Comandos: [DOCKER_COMMANDS.md](./DOCKER_COMMANDS.md)
