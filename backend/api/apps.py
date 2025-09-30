from django.apps import AppConfig

# Reconoce y configura la app 'api' en el proyecto Django
class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
