"""
Comando de Django para crear el usuario administrador
======================================================

Uso: python manage.py create_admin_user
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crear usuario administrador (admin/admin123)'

    def handle(self, *args, **options):
        """Crear usuario admin"""
        
        if User.objects.filter(username='admin').exists():
            self.stdout.write(
                self.style.WARNING('ℹ️  Usuario admin ya existe')
            )
            
            # Preguntar si quiere resetear la contraseña
            user = User.objects.get(username='admin')
            user.set_password('admin123')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Contraseña de admin reseteada a: admin123')
            )
        else:
            User.objects.create_user(
                username='admin',
                password='admin123',
                email='admin@nisira.local',
                is_staff=True,
                is_superuser=True
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Usuario admin creado exitosamente')
            )
            self.stdout.write('   Usuario: admin')
            self.stdout.write('   Contraseña: admin123')
