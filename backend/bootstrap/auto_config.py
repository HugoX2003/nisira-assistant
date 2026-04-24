"""
Sistema de auto-configuración de base de datos para RAG Asistente
Se ejecuta automáticamente al iniciar Django
"""

import os
import sys
import logging
import mysql.connector
from mysql.connector import Error
from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class DatabaseAutoConfigurator:
    """Configurador automático de base de datos"""
    
    def __init__(self):
        self.db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': os.environ.get('DB_PORT', '3306'),
            'user': os.environ.get('DB_USER', 'root'),
            'password': os.environ.get('DB_PASSWORD', ''),
            'database': os.environ.get('DB_NAME', 'rag_asistente'),
        }
        
    def ensure_database_exists(self):
        """Crear base de datos si no existe"""
        
        print("[CONFIG] Verificando/creando base de datos MySQL...")
        
        try:
            # Conectar sin especificar base de datos
            connection = mysql.connector.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            
            cursor = connection.cursor()
            
            # Crear base de datos si no existe
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            print(f"[OK] Base de datos '{self.db_config['database']}' verificada/creada")

            cursor.close()
            connection.close()

            return True

        except Error as e:
            print(f"[ERROR] Error configurando MySQL: {e}")
            return False

    def run_migrations(self):
        """Ejecutar migraciones automáticamente"""

        print("[SYNC] Ejecutando migraciones de base de datos...")

        try:
            # Ejecutar makemigrations primero
            execute_from_command_line(['manage.py', 'makemigrations'])

            # Ejecutar migrate
            execute_from_command_line(['manage.py', 'migrate'])

            print("[OK] Migraciones ejecutadas correctamente")
            return True

        except Exception as e:
            print(f"[ERROR] Error ejecutando migraciones: {e}")
            return False

    def create_default_superuser(self):
        """Crear superusuario por defecto si no existe"""

        print("[INFO] Verificando/creando superusuario por defecto...")

        try:
            User = get_user_model()

            # Verificar si ya existe un superusuario
            if User.objects.filter(is_superuser=True).exists():
                print("[OK] Superusuario ya existe")
                return True

            # Crear superusuario por defecto
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin'
            )

            print("[OK] Superusuario 'admin' creado (password: admin)")
            return True

        except Exception as e:
            print(f"[ERROR] Error creando superusuario: {e}")
            return False

    def setup_database(self):
        """Configurar base de datos completamente"""

        print("[START] CONFIGURACIÓN AUTOMÁTICA DE BASE DE DATOS")
        print("=" * 60)

        # 1. Crear base de datos
        if not self.ensure_database_exists():
            return False

        # 2. Ejecutar migraciones
        if not self.run_migrations():
            return False

        # 3. Crear superusuario por defecto
        if not self.create_default_superuser():
            return False

        print("=" * 60)
        print("[DONE] BASE DE DATOS CONFIGURADA AUTOMÁTICAMENTE")
        print("[OK] Base de datos MySQL creada/verificada")
        print("[OK] Tablas creadas/actualizadas")
        print("[OK] Superusuario disponible")
        print("[INFO] Login: admin / admin")
        print("=" * 60)
        
        return True

# Instancia global del configurador
auto_configurator = DatabaseAutoConfigurator()