# 🚨 SOLUCIÓN DEFINITIVA: Error "storageQuotaExceeded"

El error ocurre porque las **Service Accounts** de Google tienen **0 bytes de almacenamiento** y no pueden subir archivos, incluso a carpetas compartidas (a menos que sean Shared Drives de Workspace).

## ✅ La Solución: Usar tu Token de Usuario

Como ya tienes un archivo `token.json` local que funciona (porque te logueaste con tu cuenta personal/educativa), vamos a usar ESE token en producción. Tu cuenta sí tiene espacio.

### Paso 1: Copiar tu token local
1. Abre el archivo en tu proyecto local:
   `backend/data/token.json`
2. Copia **todo** el contenido (es un JSON que empieza con `{"token": "..."}`).

### Paso 2: Configurar en DigitalOcean
1. Ve a tu App en DigitalOcean > **Settings**.
2. Ve a **Environment Variables**.
3. Crea una nueva variable:
   - **Key**: `GOOGLE_TOKEN_JSON`
   - **Value**: (Pega aquí todo el contenido del archivo token.json)
4. Haz clic en **Save**.

### Paso 3: Esperar el Deploy
DigitalOcean reiniciará la aplicación.
El sistema detectará la variable `GOOGLE_TOKEN_JSON`, creará el archivo `token.json` en el servidor y lo usará **con prioridad** sobre la Service Account.

---

### ¿Por qué funciona esto?
Al usar este token, el sistema actúa como **TÚ** (tu usuario `amayagiura@...`), no como el robot (Service Account). Por lo tanto, usa **TU** cuota de almacenamiento, que sí tiene espacio disponible.
