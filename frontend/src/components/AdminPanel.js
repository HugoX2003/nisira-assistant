import React, { useState, useEffect } from 'react';
import '../styles/AdminPanel.css';
import QueryMetrics from './QueryMetrics';
import {
  getDriveFiles,
  uploadDriveFile,
  deleteDriveFile,
  syncDriveDocuments,
  getSyncProgress,
  getEmbeddingsStatus,
  generateEmbeddings,
  verifyEmbeddings,
  clearEmbeddings,
  getEmbeddingProgress,
  getSystemMetrics,
  getPipelineStatus,
  getRatingMetrics
} from '../services/adminApi';

/**
 * Panel de Administración
 * Solo accesible para el usuario admin (admin/admin123)
 */
function AdminPanel({ onLogout, user }) {
  // Estado para el tab activo
  const [activeTab, setActiveTab] = useState('drive');
  
  // Estados para Google Drive
  const [driveFiles, setDriveFiles] = useState([]);
  const [driveLoading, setDriveLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [syncProgress, setSyncProgress] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  
  // Estados para paginación y búsqueda
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchTerm, setSearchTerm] = useState('');
  const [pagination, setPagination] = useState({
    totalFiles: 0,
    totalPages: 0,
    hasNextPage: false,
    hasPrevPage: false
  });
  
  // Estados para Embeddings
  const [embeddingsStatus, setEmbeddingsStatus] = useState(null);
  const [embeddingsLoading, setEmbeddingsLoading] = useState(false);
  
  // Estados para Logs
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  
  // Estados para Metadata
  const [metadata, setMetadata] = useState(null);
  const [metadataLoading, setMetadataLoading] = useState(false);
  
  // Estado para Pipeline
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  
  // Estados para Métricas - SOLO 3 MÉTRICAS FINALES
  const [metrics, setMetrics] = useState({
    latenciaTotal: 0,         // Tiempo de respuesta promedio (segundos)
    reduccionTiempo: 0,       // Velocidad de procesamiento (tokens/segundo)
    calidadRespuesta: 0,      // Score RAGAS compuesto (0-1)
    totalQueries: 0
  });
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [metricsView, setMetricsView] = useState('summary'); // 'summary' o 'detailed'
  
  // Estados para Rating Metrics
  const [ratingMetrics, setRatingMetrics] = useState(null);
  const [ratingMetricsLoading, setRatingMetricsLoading] = useState(false);
  
  // Estados de notificaciones
  const [notification, setNotification] = useState(null);

  // Función para mostrar notificación
  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  // Cargar datos al cambiar de tab
  useEffect(() => {
    switch (activeTab) {
      case 'drive':
        loadDriveFiles();
        break;
      case 'embeddings':
        loadEmbeddingsStatus();
        break;
      case 'metrics':
        loadMetrics();
        break;
      case 'ratings':
        loadRatingMetrics();
        break;
      case 'pipeline':
        loadPipelineStatus();
        break;
      default:
        break;
    }
  }, [activeTab]);
  
  // Recargar archivos cuando cambian página, pageSize o búsqueda
  useEffect(() => {
    if (activeTab === 'drive') {
      loadDriveFiles();
    }
  }, [currentPage, pageSize, searchTerm]);

  // ==========================================
  // FUNCIONES DE GOOGLE DRIVE
  // ==========================================

  const loadDriveFiles = async () => {
    setDriveLoading(true);
    try {
      const response = await getDriveFiles(currentPage, pageSize, searchTerm);
      if (response.success) {
        setDriveFiles(response.files || []);
        setPagination(response.pagination || {
          totalFiles: 0,
          totalPages: 0,
          hasNextPage: false,
          hasPrevPage: false
        });
      } else {
        showNotification('Error cargando archivos de Drive', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error conectando con Drive', 'error');
    } finally {
      setDriveLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      showNotification('Selecciona un archivo', 'warning');
      return;
    }

    setDriveLoading(true);
    try {
      const response = await uploadDriveFile(uploadFile);
      if (response.success) {
        showNotification('Archivo subido correctamente', 'success');
        setUploadFile(null);
        loadDriveFiles();
      } else {
        showNotification(response.error || 'Error subiendo archivo', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error subiendo archivo', 'error');
    } finally {
      setDriveLoading(false);
    }
  };

  const handleDeleteFile = async (fileId, fileName) => {
    if (!window.confirm(`¿Eliminar "${fileName}"?`)) return;

    setDriveLoading(true);
    try {
      const response = await deleteDriveFile(fileId);
      if (response.success) {
        showNotification('Archivo eliminado', 'success');
        loadDriveFiles();
      } else {
        showNotification('Error eliminando archivo', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error eliminando archivo', 'error');
    } finally {
      setDriveLoading(false);
    }
  };

  const handleSyncDrive = async () => {
    setDriveLoading(true);
    setIsSyncing(true);
    setSyncProgress({ status: 'starting', message: 'Iniciando sincronización...', progress: 0 });
    
    try {
      // Iniciar sincronización
      const response = await syncDriveDocuments();
      
      if (response.success) {
        // Polling para obtener progreso
        const pollInterval = setInterval(async () => {
          try {
            const progressResponse = await getSyncProgress();
            
            if (progressResponse.status === 'completed') {
              clearInterval(pollInterval);
              setSyncProgress({
                status: 'completed',
                message: `✅ Sincronización completa: ${progressResponse.downloaded || 0} archivos descargados`,
                progress: 100,
                downloaded: progressResponse.downloaded
              });
              setIsSyncing(false);
              setDriveLoading(false);
              showNotification(
                `Sincronización completa: ${progressResponse.downloaded || 0} archivos descargados`,
                'success'
              );
              setCurrentPage(1);
              loadDriveFiles();
            } else if (progressResponse.status === 'error') {
              clearInterval(pollInterval);
              setSyncProgress({ status: 'error', message: progressResponse.message || 'Error en sincronización', progress: 0 });
              setIsSyncing(false);
              setDriveLoading(false);
              showNotification('Error en sincronización', 'error');
            } else {
              // En progreso
              setSyncProgress({
                status: 'syncing',
                message: progressResponse.message || 'Sincronizando archivos...',
                progress: progressResponse.progress || 0,
                current: progressResponse.current,
                total: progressResponse.total
              });
            }
          } catch (pollError) {
            console.error('Error polling progress:', pollError);
          }
        }, 1000); // Polling cada segundo
        
        // Timeout de seguridad (5 minutos)
        setTimeout(() => {
          clearInterval(pollInterval);
          if (isSyncing) {
            setIsSyncing(false);
            setDriveLoading(false);
            showNotification('Timeout en sincronización', 'warning');
          }
        }, 300000);
      } else {
        setSyncProgress({ status: 'error', message: 'Error iniciando sincronización', progress: 0 });
        setIsSyncing(false);
        setDriveLoading(false);
        showNotification('Error en sincronización', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      setSyncProgress({ status: 'error', message: error.message || 'Error sincronizando', progress: 0 });
      setIsSyncing(false);
      setDriveLoading(false);
      showNotification('Error sincronizando', 'error');
    }
  };
  
  // Funciones de paginación y búsqueda
  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1); // Reset a primera página al buscar
  };
  
  const handlePageSizeChange = (e) => {
    setPageSize(Number(e.target.value));
    setCurrentPage(1); // Reset a primera página
  };
  
  const handlePrevPage = () => {
    if (pagination.hasPrevPage) {
      setCurrentPage(prev => prev - 1);
    }
  };
  
  const handleNextPage = () => {
    if (pagination.hasNextPage) {
      setCurrentPage(prev => prev + 1);
    }
  };

  // ==========================================
  // FUNCIONES DE EMBEDDINGS
  // ==========================================

  const loadEmbeddingsStatus = async () => {
    setEmbeddingsLoading(true);
    try {
      const response = await getEmbeddingsStatus();
      if (response.success) {
        setEmbeddingsStatus(response);
      } else {
        showNotification('Error cargando estado de embeddings', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error obteniendo embeddings', 'error');
    } finally {
      setEmbeddingsLoading(false);
    }
  };

  const [generationProgress, setGenerationProgress] = useState(null);
  const [progressInterval, setProgressInterval] = useState(null);

  const handleGenerateEmbeddings = async () => {
    if (!window.confirm('¿Generar embeddings para documentos nuevos?\n\nEsto puede tardar varios minutos.')) return;

    setEmbeddingsLoading(true);
    setGenerationProgress({ status: 'starting', logs: ['Iniciando...'] });
    showNotification('🚀 Iniciando generación de embeddings...', 'info');
    
    // Iniciar polling del progreso
    const interval = setInterval(async () => {
      try {
        const progress = await getEmbeddingProgress();
        setGenerationProgress(progress);
        
        if (progress.status === 'completed' || progress.status === 'idle') {
          clearInterval(interval);
          setProgressInterval(null);
        }
      } catch (error) {
        console.error('Error obteniendo progreso:', error);
      }
    }, 1000); // Actualizar cada segundo
    
    setProgressInterval(interval);
    
    try {
      const response = await generateEmbeddings();
      clearInterval(interval);
      setProgressInterval(null);
      
      if (response.success) {
        let message = `✅ Generación completada!\n\n`;
        message += `📦 ${response.processed} archivo(s) nuevo(s) procesado(s)\n`;
        
        if (response.skipped > 0) {
          message += `⏭️ ${response.skipped} archivo(s) omitido(s) (ya existían)\n`;
        }
        
        if (response.errors > 0) {
          message += `❌ ${response.errors} error(es)\n`;
        }
        
        message += `\n💡 Los archivos duplicados fueron detectados y saltados automáticamente.`;
        
        showNotification(message, 'success');
        setGenerationProgress(null);
        loadEmbeddingsStatus();
      } else {
        showNotification('Error generando embeddings', 'error');
      }
    } catch (error) {
      clearInterval(interval);
      setProgressInterval(null);
      console.error('Error:', error);
      showNotification('❌ Error generando embeddings', 'error');
      setGenerationProgress(null);
    } finally {
      setEmbeddingsLoading(false);
    }
  };

  const handleVerifyEmbeddings = async () => {
    setEmbeddingsLoading(true);
    try {
      const response = await verifyEmbeddings();
      if (response.success) {
        showNotification(
          `Verificadas ${response.collections_verified} colecciones`,
          'success'
        );
        loadEmbeddingsStatus();
      } else {
        showNotification('Error verificando embeddings', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error verificando embeddings', 'error');
    } finally {
      setEmbeddingsLoading(false);
    }
  };

  const handleClearEmbeddings = async () => {
    if (!window.confirm('⚠️ ¿ELIMINAR TODOS LOS EMBEDDINGS?\n\nEsto eliminará todos los embeddings (actualmente: ' + (embeddingsStatus?.total_documents || 0) + ' documentos).\nDespués podrás generar embeddings frescos sin duplicados.\n\nEsta acción no se puede deshacer.')) return;
    
    setEmbeddingsLoading(true);
    try {
      const response = await clearEmbeddings();
      if (response.success) {
        showNotification(
          `${response.collections_deleted} colecciones eliminadas`,
          'success'
        );
        loadEmbeddingsStatus();
      } else {
        showNotification(response.error || 'Error limpiando embeddings', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error limpiando embeddings', 'error');
    } finally {
      setEmbeddingsLoading(false);
    }
  };

  // ==========================================
  // FUNCIONES DE LOGS
  // ==========================================

  const loadLogs = async () => {
    setLogsLoading(true);
    try {
      const response = await getSystemLogs();
      if (response.success) {
        setLogs(response.logs || []);
      } else {
        showNotification('Error cargando logs', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error obteniendo logs', 'error');
    } finally {
      setLogsLoading(false);
    }
  };

  // ==========================================
  // FUNCIONES DE METADATA
  // ==========================================

  const loadMetadata = async () => {
    setMetadataLoading(true);
    try {
      const response = await getMetadataInfo();
      if (response.success) {
        setMetadata(response.metadata);
      } else {
        showNotification('Error cargando metadata', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error obteniendo metadata', 'error');
    } finally {
      setMetadataLoading(false);
    }
  };

  // ==========================================
  // FUNCIONES DE PIPELINE
  // ==========================================

  const loadPipelineStatus = async () => {
    setPipelineLoading(true);
    try {
      const response = await getPipelineStatus();
      if (response.success) {
        setPipelineStatus(response);
      } else {
        showNotification('Error cargando estado del pipeline', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('Error obteniendo estado del pipeline', 'error');
    } finally {
      setPipelineLoading(false);
    }
  };

  // ==========================================
  // FUNCIONES DE MÉTRICAS
  // ==========================================

  const loadMetrics = async () => {
    setMetricsLoading(true);
    try {
      const response = await getSystemMetrics();
      if (response.success && response.metrics) {
        setMetrics(response.metrics);
        showNotification('✅ Métricas cargadas correctamente', 'success');
      } else {
        showNotification('Error cargando métricas', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('❌ Error obteniendo métricas del sistema', 'error');
    } finally {
      setMetricsLoading(false);
    }
  };

  // Cargar métricas de ratings
  const loadRatingMetrics = async () => {
    setRatingMetricsLoading(true);
    try {
      const response = await getRatingMetrics();
      if (response.success) {
        setRatingMetrics(response);
        showNotification('✅ Métricas de ratings cargadas', 'success');
      } else {
        showNotification('Error cargando métricas de ratings', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('❌ Error obteniendo métricas de ratings', 'error');
    } finally {
      setRatingMetricsLoading(false);
    }
  };

  // ==========================================
  // RENDERIZADO
  // ==========================================

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="admin-panel">
      {/* Header */}
      <div className="admin-header">
        <div className="admin-header-left">
          <h1>🛡️ Panel de Administración</h1>
          <p className="admin-user">Usuario: {user?.username || 'admin'}</p>
        </div>
        <button onClick={onLogout} className="logout-button">
          Cerrar Sesión
        </button>
      </div>

      {/* Notificaciones */}
      {notification && (
        <div className={`notification notification-${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* Tabs de navegación */}
      <div className="admin-tabs">
        <button
          className={`tab ${activeTab === 'drive' ? 'active' : ''}`}
          onClick={() => setActiveTab('drive')}
        >
          📁 Google Drive
        </button>
        <button
          className={`tab ${activeTab === 'embeddings' ? 'active' : ''}`}
          onClick={() => setActiveTab('embeddings')}
        >
          🧠 Embeddings
        </button>
        <button
          className={`tab ${activeTab === 'metrics' ? 'active' : ''}`}
          onClick={() => setActiveTab('metrics')}
        >
          📊 Métricas
        </button>
        <button
          className={`tab ${activeTab === 'ratings' ? 'active' : ''}`}
          onClick={() => setActiveTab('ratings')}
        >
          ⭐ Calificaciones
        </button>
        <button
          className={`tab ${activeTab === 'pipeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('pipeline')}
        >
          ⚙️ Pipeline RAG
        </button>
      </div>

      {/* Contenido de tabs */}
      <div className="admin-content">
        {/* TAB: Google Drive */}
        {activeTab === 'drive' && (
          <div className="tab-content">
            <div className="section-header">
              <h2>Gestión de Documentos - Google Drive</h2>
              <button 
                onClick={handleSyncDrive} 
                className="btn-primary"
                disabled={driveLoading || isSyncing}
              >
                {isSyncing ? '🔄 Sincronizando...' : '🔄 Sincronizar'}
              </button>
            </div>

            {/* Barra de progreso de sincronización */}
            {syncProgress && (
              <div className={`sync-progress-container ${syncProgress.status}`}>
                <div className="sync-progress-header">
                  <span className="sync-status-icon">
                    {syncProgress.status === 'starting' && '⏳'}
                    {syncProgress.status === 'syncing' && '🔄'}
                    {syncProgress.status === 'completed' && '✅'}
                    {syncProgress.status === 'error' && '❌'}
                  </span>
                  <span className="sync-message">{syncProgress.message}</span>
                  {syncProgress.current && syncProgress.total && (
                    <span className="sync-counter">
                      {syncProgress.current}/{syncProgress.total}
                    </span>
                  )}
                </div>
                <div className="sync-progress-bar">
                  <div 
                    className="sync-progress-fill"
                    style={{ width: `${syncProgress.progress}%` }}
                  >
                    {syncProgress.progress > 10 && `${syncProgress.progress}%`}
                  </div>
                </div>
              </div>
            )}

            {/* Formulario de subida */}
            <div className="upload-section">
              <h3>Subir Documento</h3>
              <form onSubmit={handleFileUpload} className="upload-form">
                <input
                  type="file"
                  accept=".pdf,.txt,.md,.doc,.docx"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  className="file-input"
                />
                <button 
                  type="submit" 
                  className="btn-success"
                  disabled={!uploadFile || driveLoading}
                >
                  {driveLoading ? 'Subiendo...' : '📤 Subir'}
                </button>
              </form>
              <p className="help-text">
                Formatos permitidos: PDF, TXT, MD, DOC, DOCX
              </p>
            </div>

            {/* Lista de archivos */}
            <div className="files-section">
              <div className="files-header">
                <h3>Archivos ({pagination.totalFiles})</h3>
                
                {/* Barra de búsqueda */}
                <div className="search-controls">
                  <input
                    type="text"
                    placeholder="🔍 Buscar archivos..."
                    value={searchTerm}
                    onChange={handleSearch}
                    className="search-input"
                  />
                  <select 
                    value={pageSize} 
                    onChange={handlePageSizeChange}
                    className="page-size-select"
                  >
                    <option value={10}>10 por página</option>
                    <option value={20}>20 por página</option>
                    <option value={50}>50 por página</option>
                    <option value={100}>100 por página</option>
                  </select>
                </div>
              </div>
              
              {driveLoading ? (
                <div className="loading">Cargando archivos...</div>
              ) : driveFiles.length === 0 ? (
                <p className="empty-state">
                  {searchTerm ? `No se encontraron archivos con "${searchTerm}"` : 'No hay archivos disponibles'}
                </p>
              ) : (
                <>
                  <div className="files-grid">
                    {driveFiles.map((file) => (
                      <div key={file.id} className="file-card">
                        <div className="file-icon">
                          {file.mimeType?.includes('pdf') ? '📄' : 
                           file.mimeType?.includes('text') ? '📝' : '📎'}
                        </div>
                        <div className="file-info">
                          <h4>{file.name}</h4>
                          <p className="file-size">{formatFileSize(file.size)}</p>
                          <p className="file-date">
                            {new Date(file.modifiedTime).toLocaleDateString()}
                          </p>
                        </div>
                        <button
                          onClick={() => handleDeleteFile(file.id, file.name)}
                          className="btn-delete"
                          disabled={driveLoading}
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                  
                  {/* Controles de paginación */}
                  {pagination.totalPages > 1 && (
                    <div className="pagination-controls">
                      <button
                        onClick={handlePrevPage}
                        disabled={!pagination.hasPrevPage || driveLoading}
                        className="btn-pagination"
                      >
                        ← Anterior
                      </button>
                      <span className="page-info">
                        Página {currentPage} de {pagination.totalPages}
                      </span>
                      <button
                        onClick={handleNextPage}
                        disabled={!pagination.hasNextPage || driveLoading}
                        className="btn-pagination"
                      >
                        Siguiente →
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* TAB: Embeddings */}
        {activeTab === 'embeddings' && (
          <div className="tab-content">
            <div className="warning-box">
              <h3>⚠️ PASO IMPORTANTE ANTES DE GENERAR</h3>
              <ol style={{textAlign: 'left', marginLeft: '20px'}}>
                <li>Ve a la pestaña <strong>"📂 Google Drive"</strong></li>
                <li>Verifica que veas tus archivos</li>
                <li>Haz clic en el botón <strong>"🔄 Sincronizar Documentos"</strong></li>
                <li>Espera a que termine la sincronización</li>
                <li>Regresa aquí y haz clic en <strong>"⚡ Generar"</strong></li>
              </ol>
              <div style={{marginTop: '15px', padding: '10px', background: 'rgba(34, 197, 94, 0.1)', borderRadius: '4px', border: '1px solid rgba(34, 197, 94, 0.3)'}}>
                <p style={{margin: 0, fontSize: '0.85em', color: '#4ade80'}}>
                  ✨ <strong>Detección automática de duplicados:</strong> El sistema verifica si un archivo ya fue procesado y lo omite automáticamente. Puedes generar embeddings sin preocuparte por duplicados.
                </p>
              </div>
              <p style={{marginTop: '10px', fontSize: '0.9em', color: '#fbbf24'}}>
                💡 <strong>Nota:</strong> El sistema divide cada archivo en fragmentos pequeños (chunks) para procesarlos mejor.
                <br/>
                � Estado actual: <strong>{embeddingsStatus?.total_documents || 0}</strong> fragmentos generados
              </p>
            </div>
            
            <div className="section-header">
              <h2>Gestión de Embeddings</h2>
              <div className="button-group">
                <button 
                  onClick={handleVerifyEmbeddings} 
                  className="btn-secondary"
                  disabled={embeddingsLoading}
                >
                  {embeddingsLoading ? 'Verificando...' : '🔍 Verificar'}
                </button>
                <button 
                  onClick={handleClearEmbeddings} 
                  className="btn-danger"
                  disabled={embeddingsLoading}
                >
                  {embeddingsLoading ? 'Limpiando...' : '🗑️ Limpiar'}
                </button>
                <button 
                  onClick={handleGenerateEmbeddings} 
                  className="btn-primary"
                  disabled={embeddingsLoading}
                >
                  {embeddingsLoading ? 'Generando...' : '⚡ Generar'}
                </button>
              </div>
            </div>

            {embeddingsLoading && generationProgress ? (
              <div className="loading">
                <div className="spinner"></div>
                <h3>⏳ Generando Embeddings</h3>
                {generationProgress.total > 0 && (
                  <div className="progress-info">
                    <p className="progress-text">
                      <strong>{generationProgress.current} / {generationProgress.total}</strong> archivos
                    </p>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{width: `${(generationProgress.current / generationProgress.total) * 100}%`}}
                      ></div>
                    </div>
                    <p className="current-file">📄 {generationProgress.current_file || 'Preparando...'}</p>
                    <div className="progress-stats">
                      <span>✅ Procesados: {generationProgress.processed}</span>
                      <span>❌ Errores: {generationProgress.errors}</span>
                    </div>
                  </div>
                )}
                <div className="progress-logs">
                  {generationProgress.logs && generationProgress.logs.slice(-10).map((log, idx) => (
                    <div key={idx} className="log-line">{log}</div>
                  ))}
                </div>
              </div>
            ) : embeddingsLoading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>⏳ Iniciando...</p>
              </div>
            ) : embeddingsStatus ? (
              <div className="embeddings-status">
                <div className="stats-grid">
                  <div className="stat-card">
                    <h3>Total Colecciones</h3>
                    <p className="stat-number">{embeddingsStatus.total_collections || 0}</p>
                  </div>
                  <div className="stat-card">
                    <h3>Total Fragmentos (Embeddings)</h3>
                    <p className="stat-number">{embeddingsStatus.total_documents || 0}</p>
                    <p className="stat-description">Chunks generados de los archivos procesados</p>
                  </div>
                </div>

                <div className="collections-section">
                  <h3>Colecciones</h3>
                  {embeddingsStatus.collections && embeddingsStatus.collections.length > 0 ? (
                    <div className="collections-list">
                      {embeddingsStatus.collections.map((col, idx) => (
                        <div key={idx} className="collection-card">
                          <h4>{col.name}</h4>
                          <p>{col.document_count} documentos</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-state">No hay colecciones disponibles</p>
                  )}
                </div>
              </div>
            ) : (
              <p className="empty-state">No hay información disponible</p>
            )}
          </div>
        )}

        {/* TAB: Calificaciones de Usuarios */}
        {activeTab === 'ratings' && (
          <div className="tab-content">
            <div className="section-header">
              <h2>⭐ Métricas de Calificaciones</h2>
              <button 
                onClick={loadRatingMetrics} 
                className="btn-secondary"
                disabled={ratingMetricsLoading}
              >
                {ratingMetricsLoading ? 'Actualizando...' : '🔄 Actualizar'}
              </button>
            </div>

            {ratingMetricsLoading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>Cargando métricas de calificaciones...</p>
              </div>
            ) : !ratingMetrics ? (
              <p className="empty-state">No hay métricas de calificaciones disponibles</p>
            ) : ratingMetrics.total_ratings === 0 ? (
              <div className="empty-state">
                <p>📊 Aún no hay calificaciones de usuarios</p>
                <p style={{fontSize: '0.9rem', color: '#666', marginTop: '0.5rem'}}>
                  Las calificaciones aparecerán aquí cuando los usuarios califiquen las respuestas del bot
                </p>
              </div>
            ) : (
              <div className="ratings-metrics-container">
                {/* Distribución General */}
                <div className="ratings-overview">
                  <div className="stats-card">
                    <h3>📊 Resumen General</h3>
                    <div className="stats-grid">
                      <div className="stat-item">
                        <div className="stat-label">Total de Calificaciones</div>
                        <div className="stat-value">{ratingMetrics.total_ratings}</div>
                      </div>
                      <div className="stat-item">
                        <div className="stat-label">👍 Likes</div>
                        <div className="stat-value likes">{ratingMetrics.distribution.likes}</div>
                        <div className="stat-percentage">{ratingMetrics.distribution.like_percentage}%</div>
                      </div>
                      <div className="stat-item">
                        <div className="stat-label">👎 Dislikes</div>
                        <div className="stat-value dislikes">{ratingMetrics.distribution.dislikes}</div>
                        <div className="stat-percentage">{ratingMetrics.distribution.dislike_percentage}%</div>
                      </div>
                    </div>
                  </div>

                  {/* Gráfico de distribución */}
                  <div className="stats-card">
                    <h3>📈 Distribución Like/Dislike</h3>
                    <div className="distribution-bar">
                      <div 
                        className="distribution-segment likes" 
                        style={{width: `${ratingMetrics.distribution.like_percentage}%`}}
                      >
                        {ratingMetrics.distribution.like_percentage > 10 && `${ratingMetrics.distribution.like_percentage}%`}
                      </div>
                      <div 
                        className="distribution-segment dislikes" 
                        style={{width: `${ratingMetrics.distribution.dislike_percentage}%`}}
                      >
                        {ratingMetrics.distribution.dislike_percentage > 10 && `${ratingMetrics.distribution.dislike_percentage}%`}
                      </div>
                    </div>
                    <div className="distribution-legend">
                      <span>👍 Likes: {ratingMetrics.distribution.likes}</span>
                      <span>👎 Dislikes: {ratingMetrics.distribution.dislikes}</span>
                    </div>
                  </div>

                  {/* Estadísticas por período */}
                  <div className="stats-card">
                    <h3>📅 Actividad Reciente</h3>
                    <div className="stats-grid">
                      <div className="stat-item">
                        <div className="stat-label">Última Semana</div>
                        <div className="stat-value">{ratingMetrics.period_stats.last_week}</div>
                      </div>
                      <div className="stat-item">
                        <div className="stat-label">Último Mes</div>
                        <div className="stat-value">{ratingMetrics.period_stats.last_month}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Problemas Más Comunes */}
                {ratingMetrics.top_issues && ratingMetrics.top_issues.length > 0 && (
                  <div className="ratings-section">
                    <h3>🚨 Problemas Más Reportados</h3>
                    <div className="issues-list">
                      {ratingMetrics.top_issues.map((issue, index) => (
                        <div key={index} className="issue-item">
                          <div className="issue-rank">#{index + 1}</div>
                          <div className="issue-content">
                            <div className="issue-label">{issue.label}</div>
                            <div className="issue-tag">{issue.tag}</div>
                          </div>
                          <div className="issue-count">{issue.count} veces</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Mensajes Más Votados - Positivos */}
                {ratingMetrics.top_liked_messages && ratingMetrics.top_liked_messages.length > 0 && (
                  <div className="ratings-section">
                    <h3>👍 Mensajes Más Gustados</h3>
                    <div className="messages-list">
                      {ratingMetrics.top_liked_messages.map((msg, index) => (
                        <div key={index} className="message-item liked">
                          <div className="message-rank">#{index + 1}</div>
                          <div className="message-content">
                            <p>{msg.text}</p>
                          </div>
                          <div className="message-votes">
                            <span className="vote-count likes">👍 {msg.likes}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Mensajes Más Votados - Negativos */}
                {ratingMetrics.top_disliked_messages && ratingMetrics.top_disliked_messages.length > 0 && (
                  <div className="ratings-section">
                    <h3>👎 Mensajes Menos Gustados</h3>
                    <div className="messages-list">
                      {ratingMetrics.top_disliked_messages.map((msg, index) => (
                        <div key={index} className="message-item disliked">
                          <div className="message-rank">#{index + 1}</div>
                          <div className="message-content">
                            <p>{msg.text}</p>
                          </div>
                          <div className="message-votes">
                            <span className="vote-count dislikes">👎 {msg.dislikes}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Calificaciones Recientes */}
                {ratingMetrics.recent_ratings && ratingMetrics.recent_ratings.length > 0 && (
                  <div className="ratings-section">
                    <h3>🕐 Calificaciones Recientes</h3>
                    <div className="recent-ratings-list">
                      {ratingMetrics.recent_ratings.map((rating) => (
                        <div key={rating.id} className={`recent-rating ${rating.value}`}>
                          <div className="rating-header">
                            <span className="rating-icon">
                              {rating.value === 'like' ? '👍' : '👎'}
                            </span>
                            <span className="rating-user">{rating.username}</span>
                            <span className="rating-date">
                              {new Date(rating.created_at).toLocaleString('es-ES', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                          <div className="rating-message">
                            <strong>Mensaje:</strong> {rating.message_preview}
                          </div>
                          {rating.issue_tag !== 'none' && (
                            <div className="rating-issue">
                              <strong>Problema:</strong> {rating.issue_tag_label}
                            </div>
                          )}
                          {rating.comment && (
                            <div className="rating-comment">
                              <strong>Comentario:</strong> {rating.comment}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB: Pipeline RAG */}
        {activeTab === 'pipeline' && (
          <div className="tab-content">
            <div className="section-header">
              <h2>Estado del Pipeline RAG</h2>
              <button 
                onClick={loadPipelineStatus} 
                className="btn-secondary"
                disabled={pipelineLoading}
              >
                {pipelineLoading ? 'Actualizando...' : '🔄 Actualizar'}
              </button>
            </div>

            {pipelineLoading ? (
              <div className="loading">Cargando estado del pipeline...</div>
            ) : pipelineStatus ? (
              <div className="pipeline-status">
                <div className="overall-status">
                  <h3>Estado General</h3>
                  <div className={`status-badge status-${pipelineStatus.overall}`}>
                    {pipelineStatus.overall === 'operational' ? '✅ Operacional' : '⚠️ Degradado'}
                  </div>
                </div>

                <div className="components-grid">
                  <div className={`component-card ${pipelineStatus.status?.drive_sync ? 'active' : 'inactive'}`}>
                    <h4>Google Drive Sync</h4>
                    <p>{pipelineStatus.status?.drive_sync ? '✅ Conectado' : '❌ Desconectado'}</p>
                  </div>
                  <div className={`component-card ${pipelineStatus.status?.embeddings ? 'active' : 'inactive'}`}>
                    <h4>Embeddings</h4>
                    <p>{pipelineStatus.status?.embeddings ? '✅ Disponible' : '❌ No disponible'}</p>
                  </div>
                  <div className={`component-card ${pipelineStatus.status?.vector_store ? 'active' : 'inactive'}`}>
                    <h4>Vector Store</h4>
                    <p>{pipelineStatus.status?.vector_store ? '✅ Operacional' : '❌ Sin datos'}</p>
                  </div>
                  <div className={`component-card ${pipelineStatus.status?.pipeline ? 'active' : 'inactive'}`}>
                    <h4>Pipeline</h4>
                    <p>{pipelineStatus.status?.pipeline ? '✅ Activo' : '❌ Inactivo'}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="empty-state">No hay información disponible</p>
            )}
          </div>
        )}

        {/* TAB: Métricas */}
        {activeTab === 'metrics' && (
          <div className="tab-content">
            <div className="section-header">
              <h2>📊 Métricas del Sistema RAG</h2>
              <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
                <div className="metrics-view-toggle">
                  <button 
                    className={`toggle-btn ${metricsView === 'summary' ? 'active' : ''}`}
                    onClick={() => setMetricsView('summary')}
                  >
                    📈 Resumen
                  </button>
                  <button 
                    className={`toggle-btn ${metricsView === 'detailed' ? 'active' : ''}`}
                    onClick={() => setMetricsView('detailed')}
                  >
                    🔍 Detalle por Consulta
                  </button>
                </div>
                {metricsView === 'summary' && (
                  <button 
                    onClick={loadMetrics} 
                    className="btn-secondary"
                    disabled={metricsLoading}
                  >
                    {metricsLoading ? 'Actualizando...' : '🔄 Actualizar'}
                  </button>
                )}
              </div>
            </div>

            {metricsView === 'detailed' ? (
              <QueryMetrics showNotification={showNotification} />
            ) : metricsLoading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>Cargando métricas...</p>
              </div>
            ) : (
              <div className="metrics-container">
                {/* SOLO 3 MÉTRICAS FINALES */}
                <div className="metrics-section">
                  <h3 className="metrics-section-title">📊 MÉTRICAS DEL SISTEMA (3 Métricas Finales con RAGAS)</h3>
                  <p className="metrics-section-subtitle">
                    Consultas analizadas: <strong>{metrics.totalQueries}</strong> | Evaluadas con RAGAS + Gemini API
                  </p>
                  
                  <div className="metrics-grid" style={{gridTemplateColumns: 'repeat(3, 1fr)'}}>
                    {/* MÉTRICA 1: LATENCIA TOTAL */}
                    <div className="metric-card precision-metric">
                      <div className="metric-icon">⏱️</div>
                      <div className="metric-content">
                        <h4>Latencia Total</h4>
                        <p className="metric-description">
                          <strong>Cálculo:</strong> end_time - start_time
                          <br/>
                          <strong>Método:</strong> time.time() en Python
                          <br/>
                          <strong>Unidad:</strong> Segundos (s)
                        </p>
                        <div className="metric-value">{metrics.latenciaTotal.toFixed(4)}s</div>
                        <div className="metric-progress">
                          <div 
                            className="metric-progress-bar" 
                            style={{width: `${Math.min((metrics.latenciaTotal / 10) * 100, 100)}%`}}
                          ></div>
                        </div>
                        <div className="metric-label">Tiempo promedio de respuesta completa</div>
                      </div>
                    </div>

                    {/* MÉTRICA 2: REDUCCIÓN DE TIEMPO */}
                    <div className="metric-card precision-metric">
                      <div className="metric-icon">🚀</div>
                      <div className="metric-content">
                        <h4>Reducción de Tiempo</h4>
                        <p className="metric-description">
                          <strong>Cálculo:</strong> tokens_generados / tiempo_total
                          <br/>
                          <strong>Método:</strong> len(respuesta.split()) / tiempo
                          <br/>
                          <strong>Unidad:</strong> Tokens por segundo
                        </p>
                        <div className="metric-value">{metrics.reduccionTiempo.toFixed(2)} tokens/s</div>
                        <div className="metric-progress">
                          <div 
                            className="metric-progress-bar recall" 
                            style={{width: `${Math.min((metrics.reduccionTiempo / 50) * 100, 100)}%`}}
                          ></div>
                        </div>
                        <div className="metric-label">Velocidad de procesamiento</div>
                      </div>
                    </div>

                    {/* MÉTRICA 3: CALIDAD DE RESPUESTA (RAGAS) */}
                    <div className="metric-card precision-metric">
                      <div className="metric-icon">✨</div>
                      <div className="metric-content">
                        <h4>Calidad de Respuesta</h4>
                        <p className="metric-description">
                          <strong>Cálculo:</strong> Score RAGAS compuesto
                          <br/>
                          <strong>Método:</strong> Faithfulness (40%) + Answer Relevancy (40%) + Context Precision (20%)
                          <br/>
                          <strong>Unidad:</strong> Score 0-1
                        </p>
                        <div className="metric-value">{(metrics.calidadRespuesta * 100).toFixed(2)}%</div>
                        <div className="metric-progress">
                          <div 
                            className="metric-progress-bar" 
                            style={{width: `${metrics.calidadRespuesta * 100}%`}}
                          ></div>
                        </div>
                        <div className="metric-label">Evaluación RAGAS con Gemini API</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Indicador de datos reales */}
                {metrics.totalQueries > 0 && (
                  <div style={{
                    background: 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)',
                    border: '2px solid #10b981',
                    borderRadius: '8px',
                    padding: '1rem',
                    marginBottom: '1rem',
                    textAlign: 'center'
                  }}>
                    <p style={{margin: 0, color: '#6ee7b7', fontSize: '0.9rem', fontWeight: 600}}>
                      ✅ <strong>DATOS REALES CON RAGAS</strong> - 3 métricas evaluadas con RAGAS + Gemini API
                      <br/>
                      <span style={{fontSize: '0.85rem', color: '#a7f3d0'}}>
                        {metrics.totalQueries} consultas analizadas | Evaluación de calidad con IA
                      </span>
                    </p>
                  </div>
                )}

                {/* Nota informativa */}
                <div className="metrics-info-box">
                  <h4>📖 Metodología de Medición</h4>
                  <div className="metrics-info-content">
                    <div className="metrics-info-item">
                      <strong>Captura Automática en Tiempo Real:</strong>
                      <ul>
                        <li>Cada consulta al sistema RAG se registra automáticamente</li>
                        <li>Tiempo de respuesta: Medido desde la solicitud hasta la respuesta completa</li>
                        <li>Time to First Token: Latencia hasta el primer token generado</li>
                        <li>Consultas complejas: Queries con múltiples pasos de razonamiento (clasificadas automáticamente)</li>
                        <li>Datos persistidos en base de datos PostgreSQL</li>
                      </ul>
                    </div>
                    <div className="metrics-info-item">
                      <strong>RAGAS Framework:</strong>
                      <ul>
                        <li>Precision@k: Proporción de documentos relevantes en los top-k resultados</li>
                        <li>Recall@k: Proporción de documentos relevantes totales recuperados</li>
                        <li>Faithfulness: Verificación de que las respuestas están respaldadas por contexto</li>
                        <li>Hallucination: Detección de información fabricada no presente en fuentes</li>
                        <li>Answer Relevancy: Qué tan relevante es la respuesta a la pregunta original</li>
                        <li>✅ Evaluación automática en cada consulta RAG</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminPanel;
