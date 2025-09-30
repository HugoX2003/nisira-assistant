from django.apps import AppConfig
import os
import sys

class BootstrapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bootstrap'

    def ready(self):
        """Auto-configuración completa del sistema al iniciar Django"""
        
        # Solo ejecutar en runserver, no en migraciones o comandos de gestión
        if any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'collectstatic', 'shell']):
            return
        
        # Solo ejecutar si estamos usando MySQL
        from django.conf import settings
        engine = settings.DATABASES['default']['ENGINE']
        if 'mysql' not in engine:
            return
            
        print("\n🚀 SISTEMA RAG ASISTENTE - AUTO-CONFIGURACIÓN")
        print("=" * 60)
        
        # Ejecutar configuración automática
        self._auto_configure_system()
    
    def _auto_configure_system(self):
        """Configurar sistema completo automáticamente"""
        
        try:
            # 1. Configurar base de datos
            if self._setup_database():
                print("✅ Base de datos configurada")
            
            # 2. Ejecutar migraciones si es necesario
            if self._run_migrations_if_needed():
                print("✅ Migraciones aplicadas")
            
            # 3. Crear superusuario por defecto
            if self._create_default_superuser():
                print("✅ Superusuario configurado")
            
            print("=" * 60)
            print("🎉 SISTEMA COMPLETAMENTE CONFIGURADO")
            print("🌐 Servidor listo en: http://127.0.0.1:8000")
            print("👤 Admin: admin / admin")
            print("=" * 60)
            
        except Exception as e:
            print(f"⚠️ Error en auto-configuración: {e}")
    
    def _setup_database(self):
        """Configurar base de datos MySQL"""
        
        try:
            import mysql.connector
            from mysql.connector import Error
            from django.conf import settings
            
            db_settings = settings.DATABASES['default']
            
            # Conectar sin especificar base de datos
            connection = mysql.connector.connect(
                host=db_settings['HOST'],
                port=db_settings['PORT'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD']
            )
            
            cursor = connection.cursor()
            
            # Crear base de datos si no existe
            db_name = db_settings['NAME']
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            cursor.close()
            connection.close()
            
            return True
            
        except ImportError:
            print("⚠️ Instala mysql-connector-python: pip install mysql-connector-python")
            return False
        except Exception as e:
            print(f"⚠️ Error MySQL: {e}")
            return False
    
    def _run_migrations_if_needed(self):
        """Ejecutar migraciones si son necesarias"""
        
        try:
            from django.core.management import call_command
            from django.db import connection
            from django.db.migrations.executor import MigrationExecutor
            
            # Verificar si hay migraciones pendientes
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                print("🔄 Aplicando migraciones pendientes...")
                call_command('migrate', verbosity=0, interactive=False)
                
            return True
            
        except Exception as e:
            print(f"⚠️ Error en migraciones: {e}")
            return False
    
    def _create_default_superuser(self):
        """Crear superusuario por defecto si no existe"""
        
        try:
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Verificar si ya existe admin
            if User.objects.filter(username='admin').exists():
                return True
                
            # Crear superusuario por defecto
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin'
            )
            
            print("👤 Superusuario 'admin' creado")
            return True
            
        except Exception as e:
            print(f"⚠️ Error creando superusuario: {e}")
            return False
        import sys
        if any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'collectstatic', 'loaddata', 'dumpdata', 'shell']):
            return

        try:
            from django.core.management import call_command
            # Intenta migrar; si falla por base inexistente, crea y reintenta
            try:
                call_command('migrate')
                return
            except Exception:
                pass

            # Crear base y usuario con root (requiere DB_ADMIN_USER/PASSWORD)
            admin_user = os.environ.get('DB_ADMIN_USER', 'root')
            admin_password = os.environ.get('DB_ADMIN_PASSWORD', '')
            db_name = settings.DATABASES['default']['NAME']
            app_user = settings.DATABASES['default']['USER']
            app_password = settings.DATABASES['default']['PASSWORD']

            call_command('initdb',
                         **{
                             'admin_user': admin_user,
                             'admin_password': admin_password,
                             'host': settings.DATABASES['default'].get('HOST', '127.0.0.1'),
                             'port': int(settings.DATABASES['default'].get('PORT', '3306')),
                             'db_name': db_name,
                             'app_user': app_user,
                             'app_password': app_password,
                         })
            call_command('migrate')
        except Exception:
            # No interrumpir arranque en dev; logs del server mostrarán el error
            pass
