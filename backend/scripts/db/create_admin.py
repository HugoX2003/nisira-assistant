"""
Script para crear el usuario administrador
===========================================

Ejecutar: python manage.py shell < create_admin.py
"""

from django.contrib.auth.models import User

# Crear usuario admin si no existe
if not User.objects.filter(username='admin').exists():
    User.objects.create_user(
        username='admin',
        password='admin123',
        email='admin@nisira.local',
        is_staff=True,
        is_superuser=True
    )
    print("✅ Usuario admin creado exitosamente")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
else:
    print("ℹ️  Usuario admin ya existe")
