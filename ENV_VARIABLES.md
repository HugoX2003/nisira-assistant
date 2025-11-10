# 🔑 VARIABLES DE ENTORNO PARA DIGITAL OCEAN
# Copia y pega estas EXACTAMENTE en Digital Ocean

## BACKEND ENVIRONMENT VARIABLES

### Django Core
DJANGO_SETTINGS_MODULE=core.production_settings

SECRET_KEY=H8kL9mN2pQ4rS6tU7vX9yZ1aB3cD5eF7gH9jK1lM3nP5qR7sT9uV

DEBUG=False

ALLOWED_HOSTS=.ondigitalocean.app,.vercel.app

### Database (Digital Ocean genera esto automáticamente)
DATABASE_URL=${db.DATABASE_URL}

### API Keys (MARCAR COMO SECRET EN DIGITAL OCEAN)
OPENROUTER_API_KEY=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

GOOGLE_API_KEY=AIzaSyC0V18JMVm8fs3v1BuzBCXOyAITfZuIVw8

GOOGLE_DRIVE_FOLDER_ID=1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8

### Google OAuth Credentials (MARCAR COMO SECRET)
GOOGLE_CREDENTIALS_JSON={"installed":{"client_id":"22562789891-i5fr08se064ifl0dnkn25167j59s54lv.apps.googleusercontent.com","project_id":"nisira-assistance","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}}

### Gunicorn
PORT=8000

GUNICORN_WORKERS=2

GUNICORN_TIMEOUT=300

### Otros
ENVIRONMENT=production

---

## FRONTEND ENVIRONMENT VARIABLES

REACT_APP_API_URL=${backend.PUBLIC_URL}

---

## 📝 CÓMO USARLAS EN DIGITAL OCEAN

1. Digital Ocean > Apps > nisira-assistant
2. Click en **backend** component
3. Settings > Environment Variables
4. Click **Edit**
5. Para cada variable:
   - Click **Add Variable**
   - Name: (nombre de la variable)
   - Value: (valor de la variable)
   - **IMPORTANTE**: Marcar como **Encrypted** las que digan SECRET
6. **Save**

---

## ✅ VERIFICACIÓN

Después de agregar las variables, Digital Ocean reconstruirá la app automáticamente.

Logs exitosos deberían mostrar:
```
✅ Base de datos 'rag_asistente' lista
📦 Running migrations...
🚀 Launching Gunicorn on port 8000
```
