from django.core.management.base import BaseCommand
import os
import sys
try:
    import MySQLdb  # from mysqlclient
except Exception:
    MySQLdb = None


"""
- Crea la base de datos si no existe.
- Crea el usuario de aplicación y le da permisos si no existe.
- Permite automatizar el setup en cualquier máquina, evitando scripts SQL manuales.
Uso:
    python manage.py initdb --admin-user root --admin-password sistemas --db-name rag --app-user rag_user --app-password strong_password

Los parámetros pueden tomarse de variables de entorno o pasarse por argumento.
"""

class Command(BaseCommand):
    help = "Inicializa la base de datos MySQL (crea DB y usuario si no existen)"

    def add_arguments(self, parser):
        parser.add_argument('--admin-user', default=os.environ.get('DB_ADMIN_USER', 'root'))
        parser.add_argument('--admin-password', default=os.environ.get('DB_ADMIN_PASSWORD', ''))
        parser.add_argument('--host', default=os.environ.get('DB_HOST', '127.0.0.1'))
        parser.add_argument('--port', default=int(os.environ.get('DB_PORT', '3306')))
        parser.add_argument('--db-name', default=os.environ.get('DB_NAME', 'rag'))
        parser.add_argument('--app-user', default=os.environ.get('DB_USER', 'rag_user'))
        parser.add_argument('--app-password', default=os.environ.get('DB_PASSWORD', 'strong_password'))

    def handle(self, *args, **opts):
        if MySQLdb is None:
            self.stderr.write("mysqlclient no está instalado. Instálalo o cambia a PyMySQL.")
            sys.exit(1)

        admin_user = opts['admin_user']
        admin_password = opts['admin_password']
        host = opts['host']
        port = opts['port']
        db_name = opts['db_name']
        app_user = opts['app_user']
        app_password = opts['app_password']

        self.stdout.write(f"Conectando a MySQL {host}:{port} como {admin_user}...")
        conn = MySQLdb.connect(host=host, user=admin_user, passwd=admin_password, port=port)
        cur = conn.cursor()
        try:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            self.stdout.write(f"Base `{db_name}` lista.")

            cur.execute("CREATE USER IF NOT EXISTS %s@'%%' IDENTIFIED BY %s;", (app_user, app_password))
            cur.execute("CREATE USER IF NOT EXISTS %s@'localhost' IDENTIFIED BY %s;", (app_user, app_password))
            cur.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO %s@'%%';", (app_user,))
            cur.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO %s@'localhost';", (app_user,))
            cur.execute("FLUSH PRIVILEGES;")
            conn.commit()
            self.stdout.write(f"Usuario `{app_user}` con permisos en `{db_name}` listo.")
        finally:
            cur.close()
            conn.close()

        self.stdout.write(self.style.SUCCESS("initdb completado"))
