"""
Django settings for core project.
Configurado para entornos locales (MySQL) y Railway (PostgreSQL).
"""

from pathlib import Path
import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

# ============================================================================
# CARGA DE VARIABLES DE ENTORNO
# ============================================================================
load_dotenv()

# ============================================================================
# RUTAS BASE
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# CONFIGURACIÓN BÁSICA
# ============================================================================
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-(nuk1*q+$apqs734niuwz9xs^yrb6z57724w_!_q4t7(p2y@l1'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS
if os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS').split(',') if h.strip()]
elif os.environ.get('DYNO'):  # Heroku environment
    ALLOWED_HOSTS = [
        '.herokuapp.com',
        'nisira-assistant-51691aa80938.herokuapp.com',
        'localhost',
        '127.0.0.1'
    ]
elif os.environ.get('RAILWAY_ENVIRONMENT_NAME'):
    ALLOWED_HOSTS = [
        '.railway.app',
        'nisira-assistant-production-6a02.up.railway.app',
        'localhost',
        '127.0.0.1'
    ]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ============================================================================
# APLICACIONES INSTALADAS
# ============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'bootstrap',
    # Locales
    'api',
]

# ============================================================================
# MIDDLEWARE
# ============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================================
# REST FRAMEWORK + JWT
# ============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ============================================================================
# CORS
# ============================================================================
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# TEMPLATES
# ============================================================================
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ============================================================================
# BASE DE DATOS
# ============================================================================
if os.environ.get('DATABASE_URL'):
    # Producción (Railway)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Desarrollo local (SQLite para testing)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================================
# INTERNACIONALIZACIÓN
# ============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ============================================================================
# ARCHIVOS ESTÁTICOS
# ============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================================
# CONFIGURACIÓN AUTO DB (solo para MySQL local)
# ============================================================================
if ('runserver' in sys.argv or 'migrate' in sys.argv) and not os.environ.get('DATABASE_URL'):
    def auto_configure_database():
        """Crea la base de datos MySQL si no existe"""
        try:
            import mysql.connector
            from mysql.connector import Error

            db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': os.environ.get('DB_PORT', '3306'),
                'user': os.environ.get('DB_USER', 'root'),
                'password': os.environ.get('DB_PASSWORD', ''),
                'database': os.environ.get('DB_NAME', 'rag_asistente'),
            }

            print(f"🔍 Verificando base de datos '{db_config['database']}'...")

            conn = mysql.connector.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password']
            )
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.close()
            conn.close()

            print(f"✅ Base de datos '{db_config['database']}' lista")
        except ImportError:
            print("⚠️ Falta instalar mysql-connector-python → pip install mysql-connector-python")
        except Error as e:
            print(f"⚠️ Error MySQL: {e}")
        except Exception as e:
            print(f"⚠️ Error inesperado: {e}")

    auto_configure_database()

# ============================================================================
# CAMPO PRIMARIO POR DEFECTO
# ============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
