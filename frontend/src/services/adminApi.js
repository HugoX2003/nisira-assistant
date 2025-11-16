/**
 * API Service para funcionalidades de administración
 * Endpoints exclusivos para el usuario admin
 */

const rawBaseUrl =
  process.env.REACT_APP_API_URL ||
  process.env.REACT_APP_API_BASE ||
  'http://localhost:8000';

const trimmedBaseUrl = rawBaseUrl.replace(/\/+$/, '');
const API_BASE_URL = trimmedBaseUrl.endsWith('/api')
  ? trimmedBaseUrl
  : `${trimmedBaseUrl}/api`;

/**
 * Función auxiliar para hacer peticiones con autenticación
 */
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('token');
  
  const headers = {
    ...options.headers,
  };

  // Solo agregar Content-Type si no es FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token expirado o inválido
    localStorage.removeItem('token');
    window.location.href = '/';
    throw new Error('Sesión expirada');
  }

  return response.json();
}

// ==========================================
// GOOGLE DRIVE
// ==========================================

/**
 * Obtener lista de archivos de Google Drive con paginación y búsqueda
 * @param {number} page - Número de página (default: 1)
 * @param {number} pageSize - Archivos por página (default: 20)
 * @param {string} search - Término de búsqueda
 */
export async function getDriveFiles(page = 1, pageSize = 20, search = '') {
  const params = new URLSearchParams({
    page: page.toString(),
    pageSize: pageSize.toString(),
  });
  
  if (search) {
    params.append('search', search);
  }
  
  return fetchWithAuth(`${API_BASE_URL}/admin/drive/files/?${params}`, {
    method: 'GET',
  });
}

/**
 * Subir un archivo a Google Drive
 * @param {File} file - Archivo a subir
 */
export async function uploadDriveFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  return fetchWithAuth(`${API_BASE_URL}/admin/drive/upload/`, {
    method: 'POST',
    body: formData,
  });
}

/**
 * Eliminar un archivo de Google Drive
 * @param {string} fileId - ID del archivo a eliminar
 */
export async function deleteDriveFile(fileId) {
  return fetchWithAuth(`${API_BASE_URL}/admin/drive/delete/${fileId}/`, {
    method: 'DELETE',
  });
}

/**
 * Sincronizar documentos de Google Drive
 */
export async function syncDriveDocuments() {
  return fetchWithAuth(`${API_BASE_URL}/admin/drive/sync/`, {
    method: 'POST',
  });
}

// ==========================================
// EMBEDDINGS
// ==========================================

/**
 * Obtener estado de embeddings
 */
export async function getEmbeddingsStatus() {
  return fetchWithAuth(`${API_BASE_URL}/admin/embeddings/status/`, {
    method: 'GET',
  });
}

/**
 * Generar embeddings para documentos nuevos
 */
export async function generateEmbeddings() {
  return fetchWithAuth(`${API_BASE_URL}/admin/embeddings/generate/`, {
    method: 'POST',
  });
}

/**
 * Verificar embeddings y detectar duplicados
 */
export async function verifyEmbeddings() {
  return fetchWithAuth(`${API_BASE_URL}/admin/embeddings/verify/`, {
    method: 'POST',
  });
}

/**
 * Limpiar/eliminar todos los embeddings
 */
export async function clearEmbeddings() {
  return fetchWithAuth(`${API_BASE_URL}/admin/embeddings/clear/`, {
    method: 'POST',
  });
}

/**
 * Obtener progreso de generación de embeddings
 */
export async function getEmbeddingProgress() {
  return fetchWithAuth(`${API_BASE_URL}/admin/embeddings/progress/`);
}

// ==========================================
// LOGS Y METADATA
// ==========================================

/**
 * Obtener métricas del sistema para la tesis
 * Incluye métricas de rendimiento y precisión (Sistema Personalizado)
 */
export async function getSystemMetrics() {
  return fetchWithAuth(`${API_BASE_URL}/admin/metrics/`, {
    method: 'GET',
  });
}

/**
 * Obtener lista de consultas individuales con sus métricas
 * @param {number} page - Número de página
 * @param {number} pageSize - Consultas por página
 * @param {boolean} complexOnly - Solo consultas complejas
 */
export async function getQueryList(page = 1, pageSize = 20, complexOnly = false) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    complex_only: complexOnly.toString()
  });
  
  return fetchWithAuth(`${API_BASE_URL}/admin/metrics/queries/?${params}`, {
    method: 'GET',
  });
}

/**
 * Obtener detalles completos de una consulta específica
 * Incluye explicación de cómo se calculó cada métrica
 * @param {string} queryId - ID de la consulta
 */
export async function getQueryDetail(queryId) {
  return fetchWithAuth(`${API_BASE_URL}/admin/metrics/queries/${queryId}/`, {
    method: 'GET',
  });
}

/**
 * Obtener estado del pipeline RAG
 */
export async function getPipelineStatus() {
  return fetchWithAuth(`${API_BASE_URL}/admin/pipeline/status/`, {
    method: 'GET',
  });
}
