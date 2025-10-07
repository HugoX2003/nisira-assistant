"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Usar production_settings en Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.production_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
