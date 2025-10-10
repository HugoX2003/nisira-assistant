import axios from "axios";

// ================================
// CONFIGURACIÓN DE API
// ================================

// URL base de la API del backend Django
const defaultBase = (typeof window !== 'undefined')
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'http://127.0.0.1:8000';

// Soportar tanto REACT_APP_API_BASE como REACT_APP_API_URL
const API_BASE = process.env.REACT_APP_API_BASE || process.env.REACT_APP_API_URL || defaultBase;

// ================================
// MANEJO DE TOKENS
// ================================

class TokenManager {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
    this.refreshPromise = null;
    this.loadTokensFromStorage();
  }

  loadTokensFromStorage() {
    try {
      this.accessToken = localStorage.getItem('token');
      this.refreshToken = localStorage.getItem('refresh');
      
      // Verificar que los tokens sean válidos (no null, no undefined, no vacío)
      if (this.accessToken && this.accessToken !== 'null' && this.accessToken !== 'undefined') {
        console.log('✅ Token cargado desde localStorage');
      } else {
        console.log('⚠️ No hay token válido en localStorage');
        this.accessToken = null;
        this.refreshToken = null;
      }
    } catch (error) {
      console.warn('Error cargando tokens del localStorage:', error);
      this.accessToken = null;
      this.refreshToken = null;
    }
  }

  setTokens(accessToken, refreshToken = null) {
    this.accessToken = accessToken;
    if (refreshToken) {
      this.refreshToken = refreshToken;
    }
    
    try {
      if (accessToken) {
        localStorage.setItem('token', accessToken);
      }
      if (refreshToken) {
        localStorage.setItem('refresh', refreshToken);
      }
    } catch (error) {
      console.warn('Error guardando tokens en localStorage:', error);
    }
  }

  getAccessToken() {
    return this.accessToken;
  }

  getRefreshToken() {
    return this.refreshToken;
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    this.refreshPromise = null;
    
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh');
    } catch (error) {
      console.warn('Error limpiando tokens del localStorage:', error);
    }
  }

  async refreshAccessToken() {
    // Evitar múltiples refresh simultáneos
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    if (!this.refreshToken) {
      throw new Error('No hay refresh token disponible');
    }

    this.refreshPromise = api.post('/auth/refresh/', {
      refresh: this.refreshToken
    });

    try {
      const response = await this.refreshPromise;
      const newAccessToken = response.data.access;
      
      this.setTokens(newAccessToken);
      return newAccessToken;
    } catch (error) {
      // Si el refresh falla, limpiar tokens
      this.clearTokens();
      throw error;
    } finally {
      this.refreshPromise = null;
    }
  }
}

const tokenManager = new TokenManager();

// ================================
// CONFIGURACIÓN DE AXIOS
// ================================

// Crear instancia de axios con configuración base
const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutos (para consultas RAG que pueden tardar)
  headers: {
    'Content-Type': 'application/json',
  }
});

// Interceptor para agregar el token JWT a las peticiones
api.interceptors.request.use(
  (config) => {
    const url = (config.url || '').toString();
    const isAuthEndpoint = url.includes('/auth/token') || 
                          url.includes('/auth/refresh') || 
                          url.includes('/auth/register') ||
                          url.includes('/health');

    if (!isAuthEndpoint) {
      const token = tokenManager.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('🔐 Agregando token a la petición:', config.url);
      } else {
        console.warn('⚠️ No hay token disponible para:', config.url);
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar respuestas y renovar tokens automáticamente
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si es error 401 y no hemos intentado renovar el token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await tokenManager.refreshAccessToken();
        // Reintentar la petición original
        return api(originalRequest);
      } catch (refreshError) {
        // Si el refresh falla, redirigir al login
        tokenManager.clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// ================================
// FUNCIONES DE API OPTIMIZADAS
// ================================

// Cache simple para respuestas
const responseCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutos

function getCachedResponse(key) {
  const cached = responseCache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }
  responseCache.delete(key);
  return null;
}

function setCachedResponse(key, data) {
  responseCache.set(key, {
    data,
    timestamp: Date.now()
  });
}

// Helper para manejo de errores estandarizado
function handleApiError(error, operation = 'operación') {
  console.error(`Error en ${operation}:`, error);
  
  if (error.response) {
    // Error del servidor
    const message = error.response.data?.message || 
                   error.response.data?.detail || 
                   `Error ${error.response.status}`;
    throw new Error(message);
  } else if (error.request) {
    // Error de red
    throw new Error('Error de conexión. Verifica tu conexión a internet.');
  } else {
    // Error de configuración
    throw new Error(error.message || `Error en ${operation}`);
  }
}

// ================================
// FUNCIONES DE AUTENTICACIÓN
// ================================

export async function login(username, password) {
  try {
    const response = await api.post('/auth/login/', { username, password });
    const { access, refresh, user } = response.data;
    
    tokenManager.setTokens(access, refresh);
    
    // Guardar información del usuario en localStorage
    localStorage.setItem('user', JSON.stringify(user));
    
    // Retornar en el formato que espera Login.js
    return {
      access,
      refresh,
      user
    };
  } catch (error) {
    handleApiError(error, 'login');
  }
}

export function getCurrentUser() {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.warn('Error al obtener usuario del localStorage:', error);
    return null;
  }
}

export function clearUserData() {
  try {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    tokenManager.clearTokens();
  } catch (error) {
    console.warn('Error al limpiar datos del usuario:', error);
  }
}

export async function register(username, email, password) {
  try {
    const response = await api.post('/auth/register/', {
      username,
      email,
      password
    });
    
    return {
      success: true,
      message: 'Usuario registrado exitosamente',
      data: response.data
    };
  } catch (error) {
    handleApiError(error, 'registro');
  }
}

export function logout() {
  tokenManager.clearTokens();
  
  // Limpiar cache
  responseCache.clear();
  
  return { success: true };
}

export function isAuthenticated() {
  return !!tokenManager.getAccessToken();
}

// ================================
// FUNCIONES DE CHAT/RAG
// ================================

export async function query(question, options = {}) {
  try {
    const payload = {
      question: question.trim(),
      top_k: options.top_k || 5,
      include_metadata: options.include_metadata || false
    };

    // Verificar cache para preguntas idénticas
    const cacheKey = `query:${JSON.stringify(payload)}`;
    const cachedResult = getCachedResponse(cacheKey);
    
    if (cachedResult) {
      return {
        ...cachedResult,
        fromCache: true
      };
    }

    const response = await api.post('/api/rag/query/', payload);
    const result = response.data;
    
    // Cachear resultado exitoso
    if (result.success) {
      setCachedResponse(cacheKey, result);
    }
    
    return result;
  } catch (error) {
    handleApiError(error, 'consulta');
  }
}

export async function semanticSearch(query, options = {}) {
  try {
    const payload = {
      query: query.trim(),
      top_k: options.top_k || 5,
      include_metadata: options.include_metadata || true
    };

    const response = await api.post('/api/search/', payload);
    return response.data;
  } catch (error) {
    handleApiError(error, 'búsqueda semántica');
  }
}

// ================================
// FUNCIONES DE CONVERSACIONES
// ================================

export async function getConversations() {
  try {
    const cacheKey = 'conversations';
    const cachedResult = getCachedResponse(cacheKey);
    
    if (cachedResult) {
      return cachedResult;
    }

    const response = await api.get('/api/conversations/');
    const result = response.data;
    
    setCachedResponse(cacheKey, result);
    return result;
  } catch (error) {
    handleApiError(error, 'obtener conversaciones');
  }
}

export async function getMessages(conversationId) {
  try {
    const response = await api.get(`/api/conversations/${conversationId}/messages/`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'obtener mensajes');
  }
}

export async function createConversation(title) {
  try {
    const response = await api.post('/api/conversations/', { title });
    
    // Invalidar cache de conversaciones
    responseCache.delete('conversations');
    
    return response.data;
  } catch (error) {
    handleApiError(error, 'crear conversación');
  }
}

export async function deleteConversation(conversationId) {
  try {
    await api.delete(`/api/conversations/${conversationId}/delete/`);
    
    // Invalidar cache de conversaciones
    responseCache.delete('conversations');
    
    return { success: true };
  } catch (error) {
    handleApiError(error, 'eliminar conversación');
  }
}

// ================================
// FUNCIONES DE ESTADO DEL SISTEMA
// ================================

export async function getSystemHealth() {
  try {
    const response = await api.get('/api/health/');
    return response.data;
  } catch (error) {
    handleApiError(error, 'verificar estado del sistema');
  }
}

export async function getRagStatus() {
  try {
    const cacheKey = 'rag_status';
    const cachedResult = getCachedResponse(cacheKey);
    
    if (cachedResult) {
      return cachedResult;
    }

    const response = await api.get('/api/rag/status/');
    const result = response.data;
    
    // Cachear por menos tiempo (1 minuto)
    responseCache.set(cacheKey, {
      data: result,
      timestamp: Date.now()
    });
    
    return result;
  } catch (error) {
    handleApiError(error, 'obtener estado RAG');
  }
}

// ================================
// FUNCIONES RAG ADICIONALES
// ================================

export async function ragQuery(question, options = {}) {
  try {
    const payload = {
      question: question.trim(),
      top_k: options.top_k || 3,
      include_generation: options.include_generation !== false
    };

    const response = await api.post('/api/rag/query/', payload);
    return response.data;
  } catch (error) {
    handleApiError(error, 'consulta RAG');
  }
}

export async function ragEnhancedChat(content, conversationId = null, options = {}) {
  try {
    const payload = {
      content: content.trim(),
      conversation_id: conversationId,
      use_rag: options.use_rag !== false
    };

    // Timeout extendido para consultas RAG (pueden tardar en generar embeddings y respuestas)
    const response = await api.post('/api/rag/chat/', payload, {
      timeout: 180000 // 3 minutos para RAG
    });
    
    // Invalidar cache de conversaciones cuando se crea una nueva
    if (!conversationId && response.data.conversation_id) {
      responseCache.delete('conversations');
    }
    
    return response.data;
  } catch (error) {
    handleApiError(error, 'chat RAG mejorado');
  }
}

export async function getDocuments(options = {}) {
  try {
    const params = {
      page: options.page || 1,
      page_size: options.page_size || 10
    };

    const response = await api.get('/api/rag/documents/', { params });
    return response.data;
  } catch (error) {
    handleApiError(error, 'obtener documentos');
  }
}

export async function syncDocuments() {
  try {
    const response = await api.post('/api/rag/sync/');
    return response.data;
  } catch (error) {
    handleApiError(error, 'sincronizar documentos');
  }
}

export async function getVectorStats() {
  try {
    const response = await api.get('/api/rag/status/');
    return response.data;
  } catch (error) {
    handleApiError(error, 'obtener estadísticas de vectores');
  }
}

// ================================
// FUNCIONES DE UTILIDAD
// ================================

export function clearApiCache() {
  responseCache.clear();
}

export function getApiStats() {
  return {
    cacheSize: responseCache.size,
    baseUrl: API_BASE,
    isAuthenticated: isAuthenticated()
  };
}

// Funciones de compatibilidad (deprecated)
export function setAccessToken(token) {
  console.warn('setAccessToken está obsoleta, usar login() en su lugar');
  tokenManager.setTokens(token);
}

export function setRefreshToken(token) {
  console.warn('setRefreshToken está obsoleta, usar login() en su lugar');
  tokenManager.setTokens(tokenManager.getAccessToken(), token);
}

// Exportar instancia de API y TokenManager para uso avanzado
export { api, tokenManager };

export default {
  login,
  register,
  logout,
  isAuthenticated,
  query,
  ragQuery,
  ragEnhancedChat,
  semanticSearch,
  getConversations,
  getMessages,
  createConversation,
  deleteConversation,
  getSystemHealth,
  getRagStatus,
  getDocuments,
  syncDocuments,
  getVectorStats,
  clearApiCache,
  getApiStats,
  tokenManager
};