from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Conversation, Message
import os

class Command(BaseCommand):
    help = 'Inicializa la base de datos MySQL con datos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Crear usuario administrador',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Inicializando base de datos MySQL...'))
        
        # Crear superusuario si se solicita
        if options['create_admin']:
            self.create_admin_user()
        
        # Verificar conectividad con MySQL
        self.verify_database_connection()
        
        # Mostrar estadísticas
        self.show_statistics()
        
        self.stdout.write(self.style.SUCCESS('✅ Inicialización completada'))

    def create_admin_user(self):
        """Crear usuario administrador"""
        try:
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@example.com',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write(
                    self.style.SUCCESS('👤 Usuario administrador creado: admin / admin123')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('ℹ️ Usuario administrador ya existe')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear usuario administrador: {e}')
            )

    def verify_database_connection(self):
        """Verificar conexión con la base de datos"""
        try:
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            self.stdout.write(
                self.style.SUCCESS(f'🗃️ Conectado a MySQL versión: {version}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error de conexión a MySQL: {e}')
            )

    def show_statistics(self):
        """Mostrar estadísticas de la base de datos"""
        try:
            users_count = User.objects.count()
            conversations_count = Conversation.objects.count()
            messages_count = Message.objects.count()
            
            self.stdout.write('\n📊 Estadísticas de la base de datos:')
            self.stdout.write(f'   • Usuarios: {users_count}')
            self.stdout.write(f'   • Conversaciones: {conversations_count}')
            self.stdout.write(f'   • Mensajes: {messages_count}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al obtener estadísticas: {e}')
            )