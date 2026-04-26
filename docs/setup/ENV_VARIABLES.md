# 🔑 VARIABLES DE ENTORNO PARA DIGITAL OCEAN
# Copia y pega estas EXACTAMENTE en Digital Ocean

## BACKEND ENVIRONMENT VARIABLES

### Django Core
DJANGO_SETTINGS_MODULE=core.production_settings

SECRET_KEY=tu_secret_key_aqui_generar_uno_largo_y_aleatorio

DEBUG=False

ALLOWED_HOSTS=.ondigitalocean.app,.vercel.app

### Database (Digital Ocean genera esto automáticamente)
DATABASE_URL=${db.DATABASE_URL}

### API Keys (MARCAR COMO SECRET EN DIGITAL OCEAN)
OPENROUTER_API_KEY=sk-or-v1-tu_openrouter_key_aqui

GOOGLE_API_KEY=tu_google_api_key_aqui

GOOGLE_DRIVE_FOLDER_ID=tu_folder_id_aqui

### Google OAuth Credentials (MARCAR COMO SECRET)
GOOGLE_CREDENTIALS_JSON={"installed":{"client_id":"TU_CLIENT_ID.apps.googleusercontent.com","project_id":"tu_project_id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"GOCSPX-TU_CLIENT_SECRET","redirect_uris":["http://localhost"]}}

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
