# 🔐 Configuración de Google Drive Token en DigitalOcean

## 📋 Resumen
Este documento detalla cómo configurar el token de autenticación de Google Drive Service Account en DigitalOcean App Platform para que el backend pueda acceder a los documentos almacenados en Google Drive.

---

## 🎯 Token Proporcionado

El token de Google Drive Service Account que se debe configurar:

```json
{
  "token": "ya29.a0AcM612wCUjBYBN0U0oCKvPVaDZxAOxqOKk_6...TRUNCADO",
  "refresh_token": "1//0gJxNjl8tT8JLCgYIARAAGBASNwF-L9IrF4...TRUNCADO",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "1092738524033-osh7...apps.googleusercontent.com",
  "client_secret": "GOCSPX-...TRUNCADO",
  "scopes": ["https://www.googleapis.com/auth/drive"],
  "universe_domain": "googleapis.com",
  "account": "",
  "expiry": "2025-01-23T19:38:28.912688Z"
}
```

⚠️ **IMPORTANTE**: Este token tiene fecha de expiración (2025-01-23). El backend debe usar el `refresh_token` para renovarlo automáticamente.

---

## 🛠️ Pasos de Configuración en DigitalOcean

### Opción 1: Variables de Entorno (Recomendado para tokens pequeños)

1. **Ir al Dashboard de la App**:
   - Accede a tu app en DigitalOcean App Platform
   - Ve a **Settings** → **App-Level Environment Variables**

2. **Agregar Variable de Entorno**:
   - Click en **Edit** o **Add Variable**
   - Nombre: `GOOGLE_DRIVE_TOKEN_JSON`
   - Valor: Pega el JSON completo del token (en una sola línea, sin saltos de línea)
   - Tipo: `Encrypted` (para mayor seguridad)

3. **Formato del Valor**:
   ```bash
   {"token":"ya29.a0AcM612wCUjBYBN0U0oCKvPVaDZxAOxqOKk_6...","refresh_token":"1//0gJxNjl8tT8JLCgYIARAAGBASNwF-L9IrF4...","token_uri":"https://oauth2.googleapis.com/token","client_id":"1092738524033-osh7...apps.googleusercontent.com","client_secret":"GOCSPX-...","scopes":["https://www.googleapis.com/auth/drive"],"universe_domain":"googleapis.com","account":"","expiry":"2025-01-23T19:38:28.912688Z"}
   ```

4. **Guardar y Reiniciar**:
   - Click en **Save**
   - DigitalOcean reiniciará automáticamente la app para aplicar los cambios (1-2 minutos)

### Opción 2: Secrets (Recomendado para producción)

1. **Ir a Secrets**:
   - Dashboard → Tu App → **Settings** → **App-Level Secrets**

2. **Crear Secret**:
   - Click en **Add Secret**
   - Nombre: `GOOGLE_DRIVE_TOKEN`
   - Valor: JSON del token completo

3. **Referenciar en App**:
   - En **Environment Variables**, agregar:
   - `GOOGLE_DRIVE_TOKEN_JSON=${GOOGLE_DRIVE_TOKEN}`

---

## 🔧 Implementación en el Backend

El backend ya tiene la lógica para leer el token desde las variables de entorno. Solo necesitas verificar que esté activa.

### Archivo: `backend/rag_system/google_drive_manager.py`

```python
import os
import json
from google.oauth2.credentials import Credentials

class GoogleDriveManager:
    def __init__(self):
        self.credentials = self._load_credentials()
    
    def _load_credentials(self):
        """
        Cargar credenciales desde variable de entorno
        """
        token_json = os.getenv('GOOGLE_DRIVE_TOKEN_JSON')
        
        if not token_json:
            print("⚠️ GOOGLE_DRIVE_TOKEN_JSON no configurado")
            return None
        
        try:
            # Parsear JSON desde string
            token_data = json.loads(token_json)
            
            # Crear credenciales de Google OAuth2
            credentials = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes')
            )
            
            print("✅ Credenciales de Google Drive cargadas correctamente")
            return credentials
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando GOOGLE_DRIVE_TOKEN_JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Error cargando credenciales: {e}")
            return None
```

---

## ✅ Verificación Post-Configuración

### 1. **Verificar Variable de Entorno**

Accede a un shell de tu app en DigitalOcean:

```bash
# Ver si la variable existe (no mostrará el valor por seguridad)
env | grep GOOGLE_DRIVE_TOKEN_JSON
```

### 2. **Testear desde el Backend**

Ejecuta el endpoint de verificación (si existe):

```bash
curl https://tu-app.ondigitalocean.app/api/admin/drive/files/
```

Debe devolver la lista de archivos de Google Drive (o un error específico si no hay archivos).

### 3. **Revisar Logs de la App**

En DigitalOcean:
- Dashboard → Tu App → **Logs**
- Buscar: "Credenciales de Google Drive cargadas correctamente"
- O errores: "GOOGLE_DRIVE_TOKEN_JSON no configurado"

---

## 🔄 Renovación Automática del Token

El backend debe manejar la renovación automática usando el `refresh_token`:

```python
from google.auth.transport.requests import Request

def refresh_credentials(self):
    """
    Renovar token expirado usando refresh_token
    """
    if self.credentials and self.credentials.expired:
        print("🔄 Token expirado, renovando...")
        self.credentials.refresh(Request())
        
        # Guardar nuevo token en variable de entorno (opcional)
        # O simplemente usar el token renovado en memoria
        print("✅ Token renovado correctamente")
```

---

## 🚨 Troubleshooting

### Error: "GOOGLE_DRIVE_TOKEN_JSON no configurado"
- **Causa**: La variable de entorno no está definida
- **Solución**: Verifica en Settings → Environment Variables que esté agregada

### Error: "Invalid JSON"
- **Causa**: El JSON tiene formato incorrecto (saltos de línea, comillas mal escapadas)
- **Solución**: Asegúrate de pegar el JSON en una sola línea, sin saltos de línea

### Error: "Token expired"
- **Causa**: El token ha expirado (fecha: 2025-01-23)
- **Solución**: El backend debe renovarlo automáticamente con `refresh_token`
- **Verificación**: Revisa logs para ver si la renovación está funcionando

### Error: "Unauthorized" (401)
- **Causa**: Las credenciales no tienen permisos en Google Drive
- **Solución**: Verifica que el Service Account tenga acceso compartido a la carpeta de Drive

---

## 📝 Checklist Final

- [ ] Variable `GOOGLE_DRIVE_TOKEN_JSON` configurada en DigitalOcean
- [ ] App reiniciada después de configurar variable
- [ ] Logs muestran "✅ Credenciales de Google Drive cargadas correctamente"
- [ ] Endpoint `/api/admin/drive/files/` devuelve lista de archivos
- [ ] Subida de archivos funciona correctamente
- [ ] Eliminación de archivos funciona correctamente
- [ ] Renovación automática de token implementada

---

## 🔗 Referencias

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [DigitalOcean Environment Variables](https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/)
- [Google Drive API Python Client](https://developers.google.com/drive/api/v3/quickstart/python)

---

**Última actualización**: 2025-01-23
**Autor**: NISIRA Assistant Development Team
