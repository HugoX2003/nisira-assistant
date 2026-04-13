# 🐳 Comandos Rápidos de Docker

## 📦 Desarrollo Local

```bash
# Iniciar servicios (desarrollo)
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reconstruir
docker-compose up -d --build
```

## 🚀 Producción (Digital Ocean)

```bash
# Desplegar en producción
./deploy.sh

# O manualmente:
docker compose -f docker-compose.production.yml up -d --build

# Ver logs
docker compose -f docker-compose.production.yml logs -f

# Detener
docker compose -f docker-compose.production.yml down

# Reiniciar servicio específico
docker compose -f docker-compose.production.yml restart backend
```

## 🔍 Debugging

```bash
# Entrar al contenedor backend
docker compose exec backend bash

# Ejecutar comando Django
docker compose exec backend python manage.py shell

# Ver logs de un servicio
docker compose logs -f backend

# Ver uso de recursos
docker stats

# Inspeccionar red
docker network inspect nisira-assistant_nisira-network
```

## 🗄️ Base de Datos

```bash
# Entrar a PostgreSQL
docker compose exec db psql -U postgres -d rag_asistente

# Backup
docker compose exec db pg_dump -U postgres rag_asistente > backup.sql

# Restaurar
cat backup.sql | docker compose exec -T db psql -U postgres rag_asistente

# Ver tablas
docker compose exec db psql -U postgres -d rag_asistente -c "\dt"
```

## 🧹 Limpieza

```bash
# Limpiar todo (⚠️ CUIDADO)
docker system prune -a --volumes

# Limpiar solo imágenes no usadas
docker image prune -a

# Limpiar solo volúmenes no usados
docker volume prune
```

## 📊 Monitoreo

```bash
# Estado de servicios
docker compose ps

# Health checks
docker compose ps
docker inspect --format='{{.State.Health.Status}}' container_name

# Uso de recursos en tiempo real
docker stats
```

## 🔄 Actualización

```bash
# Pull últimos cambios (si usas Git)
git pull origin main

# Reconstruir solo backend
docker compose build backend
docker compose up -d backend

# Reconstruir todo
docker compose up -d --build
```

## 🐛 Troubleshooting

```bash
# Ver logs con timestamps
docker compose logs -f --timestamps

# Ver logs de errores
docker compose logs backend | grep ERROR

# Ver variables de entorno
docker compose exec backend env

# Reiniciar desde cero
docker compose down -v
docker compose up -d --build
```

## 📈 Producción - Digital Ocean

```bash
# SSH al droplet
ssh root@your-droplet-ip

# Ir al directorio del proyecto
cd /opt/nisira-assistant

# Ver logs en producción
docker compose -f docker-compose.production.yml logs -f

# Backup automático
./backup.sh

# Monitorear recursos del servidor
htop
df -h
free -h
```
