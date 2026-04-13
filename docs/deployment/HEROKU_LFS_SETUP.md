# Heroku Configuration - Buildpacks para Git LFS
# ================================================
# Heroku necesita un buildpack adicional para descargar objetos Git LFS
# antes de compilar la aplicación.

# OPCIÓN 1: Configurar vía CLI (recomendado para backend)
# -------------------------------------------------------
# Ejecuta estos comandos en tu terminal local:

# 1. Añadir buildpack de Git LFS ANTES del buildpack de Python
heroku buildpacks:add --index 1 https://github.com/raxod502/heroku-buildpack-git-lfs

# 2. Verificar el orden (LFS debe estar primero)
heroku buildpacks

# 3. Forzar rebuild para aplicar cambios
git commit --allow-empty -m "chore: habilitar Git LFS en Heroku"
git push heroku main


# OPCIÓN 2: Configurar vía archivo heroku.yml (Heroku Container Registry)
# ------------------------------------------------------------------------
# Si usas Heroku Container Registry (Docker), edita o crea heroku.yml:

build:
  docker:
    web: Dockerfile
  config:
    # Git LFS hooks se ejecutarán automáticamente durante el build
    # asegúrate de que el Dockerfile incluya git-lfs


# OPCIÓN 3: Configurar en el Dashboard Web de Heroku
# ---------------------------------------------------
# 1. Ve a tu app en dashboard.heroku.com
# 2. Settings → Buildpacks
# 3. Añade: https://github.com/raxod502/heroku-buildpack-git-lfs
# 4. Asegúrate de que esté ARRIBA del buildpack de Python
# 5. Haz un deploy para aplicar


# Variables de entorno necesarias en Heroku
# ------------------------------------------
# Configura estas variables en Settings → Config Vars:

ENABLE_GOOGLE_DRIVE=false
GOOGLE_API_KEY=tu_api_key_aqui
OPENROUTER_API_KEY=tu_api_key_aqui
SECRET_KEY=tu_secret_key_aqui
DATABASE_URL=postgres://...  (Heroku Postgres lo configura automáticamente)


# Verificación post-deploy
# -------------------------
# Después del deploy, verifica que LFS descargó los embeddings:

heroku run bash
cd /app
ls -lh chroma_db/
file chroma_db/chroma.sqlite3  # Debe decir "SQLite 3.x database"
exit

# Si dice "ASCII text" o "data", entonces son punteros LFS no descargados.
# En ese caso, verifica que el buildpack esté instalado correctamente.
