#!/usr/bin/env python
"""
Script para arreglar permisos de PostgreSQL y correr migraciones
Ejecutar desde la console de Digital Ocean
"""
import os
import subprocess
import sys

def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"⚠️  {result.stderr}")
    
    if result.returncode != 0:
        print(f"❌ Error code: {result.returncode}")
        return False
    
    print(f"✅ {description} - Completado")
    return True

def main():
    print("🚀 Iniciando proceso de arreglo de base de datos...")
    
    # Verificar que DATABASE_URL existe
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurado")
        sys.exit(1)
    
    print(f"📊 DATABASE_URL encontrado")
    
    # Instalar psql si no existe
    print("\n📦 Verificando/Instalando postgresql-client...")
    run_command(
        "apt-get update > /dev/null 2>&1 && apt-get install -y postgresql-client > /dev/null 2>&1",
        "Instalando cliente PostgreSQL"
    )
    
    # SQL para arreglar permisos
    sql_commands = """
    GRANT ALL ON SCHEMA public TO "dev-db-503014";
    GRANT ALL ON SCHEMA public TO PUBLIC;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "dev-db-503014";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "dev-db-503014";
    """
    
    # Ejecutar comandos SQL
    print("\n🔧 Arreglando permisos de PostgreSQL...")
    sql_file = "/tmp/fix_permissions.sql"
    with open(sql_file, 'w') as f:
        f.write(sql_commands)
    
    cmd = f"psql {database_url} -f {sql_file}"
    success = run_command(cmd, "Aplicando permisos SQL")
    
    if not success:
        print("\n⚠️  Los permisos pueden ya estar configurados o necesitas privilegios de admin")
        print("    Intentando continuar con las migraciones de todas formas...")
    
    # Correr migraciones de Django
    print("\n📦 Corriendo migraciones de Django...")
    success = run_command(
        "python manage.py migrate --noinput",
        "Migraciones de Django"
    )
    
    if success:
        print("\n" + "="*60)
        print("✅ ¡TODO COMPLETADO CON ÉXITO!")
        print("="*60)
        print("\n🎉 Ahora puedes:")
        print("   1. Probar el registro en el frontend")
        print("   2. Crear usuarios en /admin/")
        print("   3. Usar el sistema RAG")
    else:
        print("\n" + "="*60)
        print("❌ Las migraciones fallaron")
        print("="*60)
        print("\nPosibles soluciones:")
        print("   1. Verificar permisos de usuario en Digital Ocean Database")
        print("   2. Usar usuario 'doadmin' en vez de 'dev-db-503014'")
        print("   3. Contactar soporte de Digital Ocean")
        sys.exit(1)

if __name__ == "__main__":
    main()
