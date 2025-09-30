import axios from "axios";

// URL base de la API del backend Django
const defaultBase = (typeof window !== 'undefined')
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'http://127.0.0.1:8000';
const API_BASE = process.env.REACT_APP_API_BASE || defaultBase;

// Variable global para almacenar el token de acceso
let accessToken = null;
let refreshToken = null;

/**
 * Función para establecer el token de acceso JWT
 * Se llama después del login exitoso
 */
export function setAccessToken(token) {
  accessToken = token;
  try { localStorage.setItem('token', token); } catch {}
}

export function setRefreshToken(token) {
  refreshToken = token;
  try { localStorage.setItem('refresh', token || ''); } catch {}
}

function getStoredAccessToken() {
  if (accessToken) return accessToken;
  try { return localStorage.getItem('token'); } catch { return null; }
}

function getStoredRefreshToken() {
  if (refreshToken) return refreshToken;
  try { return localStorage.getItem('refresh'); } catch { return null; }
}

function clearTokens() {
  accessToken = null;
  refreshToken = null;
  try { localStorage.removeItem('token'); localStorage.removeItem('refresh'); } catch {}
}

// Crear instancia de axios con configuración base
const api = axios.create({ baseURL: API_BASE });

// Interceptor para agregar el token JWT a las peticiones (lee de memoria y localStorage)
api.interceptors.request.use((config) => {
  const url = (config.url || '').toString();
  const isAuthEndpoint = url.includes('/auth/token') || url.includes('/auth/refresh') || url.includes('/auth/register');
  if (!isAuthEndpoint) {
    const token = getStoredAccessToken();
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Interceptor para manejar respuestas y errores de autenticación
api.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const originalRequest = error.config || {};
    const status = error.response?.status;
    const url = (originalRequest.url || '').toString();
    const isAuthEndpoint = url.includes('/auth/token') || url.includes('/auth/refresh') || url.includes('/auth/register');

    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      const rToken = getStoredRefreshToken();
      if (rToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, { refresh: rToken });
          setAccessToken(data.access);
          if (data.refresh) setRefreshToken(data.refresh);
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api.request(originalRequest);
        } catch (e) {
          clearTokens();
        }
      } else {
        clearTokens();
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Función para iniciar sesión
 * Envía credenciales al endpoint /auth/token y obtiene los tokens JWT
 */
export async function login(username, password) {
  const { data } = await api.post("/auth/token", { username, password });
  // Guardar el token de acceso para futuras peticiones
  setAccessToken(data.access);
  setRefreshToken(data.refresh || '');
  // TODO: Guardar el refresh token de forma segura (localStorage o cookie)
  return data;
}

/**
 * Función para registrar nuevos usuarios
 * Envía datos al endpoint /auth/register
 */
export async function register(username, email, password) {
  const { data } = await api.post("/auth/register", { username, email, password });
  return data;
}

/**
 * Función para realizar consultas RAG al sistema
 * Envía la pregunta y recibe respuesta con fuentes
 */
export async function query(question, top_k = 3, conversation_id) {
  const { data } = await api.post("/query", { question, top_k, conversation_id });
  return data;
}

/**
 * Función para ingerir documentos en el sistema
 * Permite subir archivos para ser procesados por el RAG
 */
export async function ingest(payload) {
  const { data } = await api.post("/ingest", payload);
  return data;
}

// Sincroniza PDFs desde Google Drive
export async function syncDrive() {
  const { data } = await api.post("/sync-drive", {});
  return data;
}

// Sincroniza y reingesta PDFs desde Google Drive en un solo paso
export async function syncDriveFull(opts = {}) {
  const payload = {};
  if (opts.chunk_size) payload.chunk_size = opts.chunk_size;
  if (opts.chunk_overlap) payload.chunk_overlap = opts.chunk_overlap;
  if (typeof opts.force !== 'undefined') payload.force = !!opts.force;
  const { data } = await api.post('/sync-drive/full', payload);
  return data;
}

// Sube un PDF y lo ingiere
export async function uploadPdf(file, opts = {}) {
  const form = new FormData();
  form.append('file', file);
  if (opts.chunk_size) form.append('chunk_size', String(opts.chunk_size));
  if (opts.chunk_overlap) form.append('chunk_overlap', String(opts.chunk_overlap));
  const { data } = await api.post("/ingest/upload", form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
}

/**
 * Función para verificar el estado del servidor
 * Endpoint de health check
 */
export async function health() {
  const { data } = await api.get("/health");
  return data;
}

// Listar conversaciones del usuario
export async function getConversations() {
  const { data } = await api.get('/conversations');
  return data;
}

// Listar mensajes de una conversación
export async function getMessages(convId) {
  const { data } = await api.get(`/conversations/${convId}/messages`);
  return data;
}

// ===== FUNCIONES DE TESTING =====

// Test simple del sistema RAG
export async function testRagSimple(question = null) {
  const params = question ? { q: question } : {};
  const { data } = await api.get('/test/rag/simple', { params });
  return data;
}

// Test con múltiples preguntas predefinidas
export async function testRagMultiple() {
  const { data } = await api.get('/test/rag/multiple');
  return data;
}

// Obtener estado completo del sistema RAG
export async function getRagSystemStatus() {
  const { data } = await api.get('/test/rag/status');
  return data;
}

// Test con pregunta personalizada
export async function testCustomQuestion(question) {
  const { data } = await api.post('/test/rag/custom', { question });
  return data;
}
