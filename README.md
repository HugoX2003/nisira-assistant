# Nisira Assistant

Sistema de chat inteligente con frontend React y backend Django, diseñado con una arquitectura limpia y modular.

## 🏗️ Arquitectura

```
nisira-assistant/
├── frontend/                 # Aplicación React
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── services/        # Servicios API
│   │   └── styles/          # Estilos CSS
│   ├── public/
│   └── package.json
├── backend/                  # API Django
│   ├── chat/               # App de chat
│   ├── core/               # Configuración del proyecto
│   ├── users/              # App de usuarios
│   ├── utils/              # Utilidades compartidas
│   ├── manage.py
│   └── requirements.txt
├── .env.example            # Variables de entorno
├── .gitignore
└── README.md
```

## 🚀 Configuración e Instalación

### Prerequisitos

- Python 3.8+
- Node.js 14+
- npm o yarn

### Backend (Django)

1. **Navegar al directorio del backend:**
   ```bash
   cd backend
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv .venv
   ```

3. **Activar entorno virtual:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

4. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurar variables de entorno:**
   ```bash
   # Copiar el archivo de ejemplo
   copy ../.env.example .env
   
   # Editar .env con tus configuraciones
   ```

6. **Ejecutar migraciones:**
   ```bash
   python manage.py migrate
   ```

7. **Crear superusuario (opcional):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Iniciar servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

El backend estará disponible en `http://localhost:8000`

### Frontend (React)

1. **Navegar al directorio del frontend:**
   ```bash
   cd frontend
   ```

2. **Instalar dependencias:**
   ```bash
   npm install
   ```

3. **Iniciar servidor de desarrollo:**
   ```bash
   npm start
   ```

El frontend estará disponible en `http://localhost:3000`

## 📊 Funcionalidades

### Frontend
- **Interfaz de Chat**: Chat en tiempo real con UI moderna
- **Autenticación**: Sistema de login y registro
- **Responsive**: Diseño adaptable a diferentes dispositivos
- **Panel de Testing**: Herramientas para probar funcionalidades

### Backend
- **API REST**: Endpoints para chat, usuarios y autenticación
- **Autenticación JWT**: Sistema de tokens seguro
- **Modelos de Chat**: Gestión de conversaciones y mensajes
- **Panel de Admin**: Interface administrativa de Django

## 🔧 Comandos Útiles

### Backend
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic

# Ejecutar tests
python manage.py test
```

### Frontend
```bash
# Instalar dependencias
npm install

# Iniciar desarrollo
npm start

# Crear build de producción
npm run build

# Ejecutar tests
npm test
```

## 🌐 APIs Principales

### Autenticación
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/register/` - Registrar usuario
- `POST /api/auth/logout/` - Cerrar sesión

### Chat
- `GET /api/chat/conversations/` - Listar conversaciones
- `POST /api/chat/conversations/` - Crear conversación
- `GET /api/chat/messages/` - Obtener mensajes
- `POST /api/chat/messages/` - Enviar mensaje

## 🔐 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DATABASE_URL=sqlite:///db.sqlite3

# API Keys (si es necesario)
OPENAI_API_KEY=your-openai-key
DEEPSEEK_API_KEY=your-deepseek-key
```

## 🐳 Docker (Opcional)

Si prefieres usar Docker:

```bash
# Construir y ejecutar con docker-compose
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d
```

## 📝 Desarrollo

### Estructura del Código

- **Frontend**: Componentes modulares en React con servicios separados
- **Backend**: Apps Django organizadas por funcionalidad
- **Estilos**: CSS modular por componente
- **API**: Endpoints RESTful con versionado

### Mejores Prácticas

1. **Frontend**:
   - Usar hooks de React para estado
   - Separar lógica de negocio en servicios
   - Mantener componentes pequeños y reutilizables

2. **Backend**:
   - Seguir convenciones de Django
   - Usar serializers para API
   - Implementar tests para endpoints críticos

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

**Nota**: Esta es una versión reorganizada del proyecto original, separando claramente frontend y backend para mejor mantenibilidad y escalabilidad.