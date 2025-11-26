import React, { useState, useEffect, useCallback } from 'react';
import '../styles/AdminPanel.css';
import QueryMetrics from './QueryMetrics';
import {
  getDriveFiles, uploadDriveFile, deleteDriveFile, syncDriveDocuments, getSyncProgress,
  getEmbeddingsStatus, generateEmbeddings, verifyEmbeddings, clearEmbeddings, getEmbeddingProgress,
  getSystemMetrics, getPipelineStatus, getRatingMetrics
} from '../services/adminApi';

// Componente de notificación
const Notification = ({ notification }) => {
  if (!notification) return null;
  return <div className={`notification ${notification.type}`}>{notification.message}</div>;
};

// Componente de carga
const Loading = ({ text = 'Cargando...' }) => (
  <div className="loading"><div className="spinner" /><p>{text}</p></div>
);

// Componente de estado vacío
const Empty = ({ children }) => <p className="empty">{children}</p>;

// Componente de tarjeta de estadística
const StatCard = ({ title, value, subtitle, icon }) => (
  <div className="stat-card">
    {icon && <span className="stat-icon">{icon}</span>}
    <h4>{title}</h4>
    <p className="stat-value">{value}</p>
    {subtitle && <p className="stat-sub">{subtitle}</p>}
  </div>
);

// Componente de barra de progreso
const ProgressBar = ({ progress, status, message }) => (
  <div className={`progress-container ${status}`}>
    <div className="progress-header">
      <span>{status === 'completed' ? '✅' : status === 'error' ? '❌' : '🔄'}</span>
      <span>{message}</span>
    </div>
    <div className="progress-bar">
      <div className="progress-fill" style={{ width: `${progress}%` }}>{progress > 10 && `${progress}%`}</div>
    </div>
  </div>
);

// Tabs disponibles
const TABS = [
  { id: 'drive', label: '📁 Google Drive' },
  { id: 'embeddings', label: '🧠 Embeddings' },
  { id: 'metrics', label: '📊 Métricas' },
  { id: 'ratings', label: '⭐ Calificaciones' },
  { id: 'pipeline', label: '⚙️ Pipeline' }
];

function AdminPanel({ onLogout, user }) {
  const [activeTab, setActiveTab] = useState('drive');
  const [notification, setNotification] = useState(null);

  const notify = useCallback((message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  }, []);

  return (
    <div className="admin-panel">
      <header className="admin-header">
        <div>
          <h1>🛡️ Panel de Administración</h1>
          <p>Usuario: {user?.username || 'admin'}</p>
        </div>
        <button onClick={onLogout} className="btn-logout">Cerrar Sesión</button>
      </header>

      <Notification notification={notification} />

      <nav className="admin-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="admin-content">
        {activeTab === 'drive' && <DriveTab notify={notify} />}
        {activeTab === 'embeddings' && <EmbeddingsTab notify={notify} />}
        {activeTab === 'metrics' && <MetricsTab notify={notify} />}
        {activeTab === 'ratings' && <RatingsTab notify={notify} />}
        {activeTab === 'pipeline' && <PipelineTab notify={notify} />}
      </main>
    </div>
  );
}

// ========== TAB: GOOGLE DRIVE ==========
function DriveTab({ notify }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [pagination, setPagination] = useState({ totalFiles: 0, totalPages: 0, hasNextPage: false, hasPrevPage: false });

  const loadFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getDriveFiles(page, pageSize, search);
      if (res.success) {
        setFiles(res.files || []);
        setPagination(res.pagination || {});
      }
    } catch (e) {
      notify('Error cargando archivos', 'error');
    }
    setLoading(false);
  }, [page, pageSize, search, notify]);

  useEffect(() => { loadFiles(); }, [loadFiles]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return notify('Selecciona un archivo', 'warning');
    setLoading(true);
    try {
      const res = await uploadDriveFile(uploadFile);
      if (res.success) {
        notify('Archivo subido', 'success');
        setUploadFile(null);
        loadFiles();
      } else {
        notify(res.error || 'Error', 'error');
      }
    } catch (e) {
      notify('Error subiendo', 'error');
    }
    setLoading(false);
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`¿Eliminar "${name}"?`)) return;
    setLoading(true);
    try {
      const res = await deleteDriveFile(id);
      if (res.success) {
        notify('Archivo eliminado', 'success');
        loadFiles();
      }
    } catch (e) {
      notify('Error eliminando', 'error');
    }
    setLoading(false);
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncProgress({ status: 'starting', message: 'Iniciando...', progress: 0 });
    try {
      const res = await syncDriveDocuments();
      if (res.success) {
        const interval = setInterval(async () => {
          const prog = await getSyncProgress();
          setSyncProgress({ status: prog.status, message: prog.message, progress: prog.progress || 0 });
          if (prog.status === 'completed' || prog.status === 'error') {
            clearInterval(interval);
            setSyncing(false);
            if (prog.status === 'completed') {
              notify(`Sincronización completa: ${prog.downloaded || 0} archivos`, 'success');
              loadFiles();
            }
          }
        }, 1000);
        setTimeout(() => { clearInterval(interval); setSyncing(false); }, 300000);
      }
    } catch (e) {
      notify('Error sincronizando', 'error');
      setSyncing(false);
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return 'N/A';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <div className="tab-content">
      <div className="section-header">
        <h2>Gestión de Documentos</h2>
        <button onClick={handleSync} className="btn-primary" disabled={loading || syncing}>
          {syncing ? '🔄 Sincronizando...' : '🔄 Sincronizar'}
        </button>
      </div>

      {syncProgress && <ProgressBar {...syncProgress} />}

      <div className="card">
        <h3>Subir Documento</h3>
        <form onSubmit={handleUpload} className="upload-form">
          <input type="file" accept=".pdf,.txt,.md,.doc,.docx" onChange={(e) => setUploadFile(e.target.files[0])} />
          <button type="submit" className="btn-success" disabled={!uploadFile || loading}>📤 Subir</button>
        </form>
      </div>

      <div className="card">
        <div className="files-header">
          <h3>Archivos ({pagination.totalFiles})</h3>
          <div className="files-controls">
            <input type="text" placeholder="🔍 Buscar..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
            <select value={pageSize} onChange={(e) => { setPageSize(+e.target.value); setPage(1); }}>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>

        {loading ? <Loading /> : files.length === 0 ? <Empty>No hay archivos</Empty> : (
          <>
            <div className="files-grid">
              {files.map(file => (
                <div key={file.id} className="file-card">
                  <span className="file-icon">{file.mimeType?.includes('pdf') ? '📄' : '📝'}</span>
                  <div className="file-info">
                    <h4>{file.name}</h4>
                    <p>{formatSize(file.size)} • {new Date(file.modifiedTime).toLocaleDateString()}</p>
                  </div>
                  <button onClick={() => handleDelete(file.id, file.name)} className="btn-icon" disabled={loading}>🗑️</button>
                </div>
              ))}
            </div>
            {pagination.totalPages > 1 && (
              <div className="pagination">
                <button onClick={() => setPage(p => p - 1)} disabled={!pagination.hasPrevPage}>← Anterior</button>
                <span>Página {page} de {pagination.totalPages}</span>
                <button onClick={() => setPage(p => p + 1)} disabled={!pagination.hasNextPage}>Siguiente →</button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ========== TAB: EMBEDDINGS ==========
function EmbeddingsTab({ notify }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(null);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getEmbeddingsStatus();
      if (res.success) setStatus(res);
    } catch (e) {
      notify('Error cargando embeddings', 'error');
    }
    setLoading(false);
  }, [notify]);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  const handleGenerate = async () => {
    if (!window.confirm('¿Generar embeddings? Esto puede tardar varios minutos.')) return;
    setLoading(true);
    setProgress({ status: 'starting', logs: ['Iniciando...'] });
    const interval = setInterval(async () => {
      try {
        const p = await getEmbeddingProgress();
        setProgress(p);
        if (p.status === 'completed' || p.status === 'idle') clearInterval(interval);
      } catch (e) {}
    }, 1000);
    try {
      const res = await generateEmbeddings();
      clearInterval(interval);
      if (res.success) {
        notify(`✅ ${res.processed} archivos procesados`, 'success');
        loadStatus();
      }
    } catch (e) {
      notify('Error generando', 'error');
    }
    setProgress(null);
    setLoading(false);
  };

  const handleVerify = async () => {
    setLoading(true);
    try {
      const res = await verifyEmbeddings();
      if (res.success) notify(`Verificadas ${res.collections_verified} colecciones`, 'success');
    } catch (e) {
      notify('Error verificando', 'error');
    }
    setLoading(false);
  };

  const handleClear = async () => {
    if (!window.confirm('⚠️ ¿ELIMINAR TODOS LOS EMBEDDINGS?')) return;
    setLoading(true);
    try {
      const res = await clearEmbeddings();
      if (res.success) {
        notify('Embeddings eliminados', 'success');
        loadStatus();
      }
    } catch (e) {
      notify('Error limpiando', 'error');
    }
    setLoading(false);
  };

  return (
    <div className="tab-content">
      <div className="info-box">
        <h3>⚠️ Antes de generar</h3>
        <ol>
          <li>Ve a "📁 Google Drive" y sincroniza</li>
          <li>Espera a que termine</li>
          <li>Regresa aquí y genera</li>
        </ol>
        <p className="info-note">✨ El sistema detecta duplicados automáticamente</p>
      </div>

      <div className="section-header">
        <h2>Gestión de Embeddings</h2>
        <div className="btn-group">
          <button onClick={handleVerify} className="btn-secondary" disabled={loading}>🔍 Verificar</button>
          <button onClick={handleClear} className="btn-danger" disabled={loading}>🗑️ Limpiar</button>
          <button onClick={handleGenerate} className="btn-primary" disabled={loading}>⚡ Generar</button>
        </div>
      </div>

      {loading && progress ? (
        <div className="loading">
          <div className="spinner" />
          <h3>⏳ Generando Embeddings</h3>
          {progress.total > 0 && (
            <>
              <p>{progress.current} / {progress.total} archivos</p>
              <ProgressBar progress={(progress.current / progress.total) * 100} status="syncing" message={progress.current_file || ''} />
            </>
          )}
        </div>
      ) : loading ? <Loading text="Procesando..." /> : status ? (
        <div className="stats-grid">
          <StatCard title="Colecciones" value={status.total_collections || 0} icon="📚" />
          <StatCard title="Fragmentos" value={status.total_documents || 0} subtitle="Chunks generados" icon="🧩" />
        </div>
      ) : <Empty>Sin información</Empty>}
    </div>
  );
}

// ========== TAB: MÉTRICAS ==========
function MetricsTab({ notify }) {
  const [metrics, setMetrics] = useState({ latenciaTotal: 0, reduccionTiempo: 0, calidadRespuesta: 0, totalQueries: 0 });
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('summary');

  const loadMetrics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getSystemMetrics();
      if (res.success && res.metrics) setMetrics(res.metrics);
    } catch (e) {
      notify('Error cargando métricas', 'error');
    }
    setLoading(false);
  }, [notify]);

  useEffect(() => { loadMetrics(); }, [loadMetrics]);

  return (
    <div className="tab-content">
      <div className="section-header">
        <h2>📊 Métricas del Sistema</h2>
        <div className="btn-group">
          <button className={`btn-toggle ${view === 'summary' ? 'active' : ''}`} onClick={() => setView('summary')}>📈 Resumen</button>
          <button className={`btn-toggle ${view === 'detailed' ? 'active' : ''}`} onClick={() => setView('detailed')}>🔍 Detalle</button>
          {view === 'summary' && <button onClick={loadMetrics} className="btn-secondary" disabled={loading}>🔄</button>}
        </div>
      </div>

      {view === 'detailed' ? <QueryMetrics showNotification={notify} /> : loading ? <Loading /> : (
        <>
          <p className="metrics-subtitle">Consultas analizadas: <strong>{metrics.totalQueries}</strong></p>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-icon">⏱️</span>
              <h4>Latencia Total</h4>
              <p className="metric-value">{metrics.latenciaTotal.toFixed(4)}s</p>
              <div className="metric-bar"><div style={{ width: `${Math.min((metrics.latenciaTotal / 10) * 100, 100)}%` }} /></div>
              <p className="metric-label">Tiempo promedio de respuesta</p>
            </div>
            <div className="metric-card">
              <span className="metric-icon">🚀</span>
              <h4>Velocidad</h4>
              <p className="metric-value">{metrics.reduccionTiempo.toFixed(2)} tok/s</p>
              <div className="metric-bar"><div style={{ width: `${Math.min((metrics.reduccionTiempo / 50) * 100, 100)}%` }} /></div>
              <p className="metric-label">Tokens por segundo</p>
            </div>
            <div className="metric-card">
              <span className="metric-icon">✨</span>
              <h4>Calidad (RAGAS)</h4>
              <p className="metric-value">{(metrics.calidadRespuesta * 100).toFixed(1)}%</p>
              <div className="metric-bar"><div style={{ width: `${metrics.calidadRespuesta * 100}%` }} /></div>
              <p className="metric-label">Score compuesto</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ========== TAB: CALIFICACIONES ==========
function RatingsTab({ notify }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadRatings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getRatingMetrics();
      if (res.success) setData(res);
    } catch (e) {
      notify('Error cargando ratings', 'error');
    }
    setLoading(false);
  }, [notify]);

  useEffect(() => { loadRatings(); }, [loadRatings]);

  if (loading) return <Loading />;
  if (!data || data.total_ratings === 0) return <Empty>📊 Aún no hay calificaciones</Empty>;

  return (
    <div className="tab-content">
      <div className="section-header">
        <h2>⭐ Métricas de Calificaciones</h2>
        <button onClick={loadRatings} className="btn-secondary" disabled={loading}>🔄 Actualizar</button>
      </div>

      <div className="stats-grid">
        <StatCard title="Total" value={data.total_ratings} icon="📊" />
        <StatCard title="👍 Likes" value={data.distribution.likes} subtitle={`${data.distribution.like_percentage}%`} />
        <StatCard title="👎 Dislikes" value={data.distribution.dislikes} subtitle={`${data.distribution.dislike_percentage}%`} />
      </div>

      <div className="card">
        <h3>Distribución</h3>
        <div className="distribution-bar">
          <div className="like-bar" style={{ width: `${data.distribution.like_percentage}%` }}>
            {data.distribution.like_percentage > 10 && `${data.distribution.like_percentage}%`}
          </div>
          <div className="dislike-bar" style={{ width: `${data.distribution.dislike_percentage}%` }}>
            {data.distribution.dislike_percentage > 10 && `${data.distribution.dislike_percentage}%`}
          </div>
        </div>
      </div>

      {data.top_issues?.length > 0 && (
        <div className="card">
          <h3>🚨 Problemas Reportados</h3>
          <div className="issues-list">
            {data.top_issues.map((issue, i) => (
              <div key={i} className="issue-item">
                <span className="issue-rank">#{i + 1}</span>
                <span className="issue-label">{issue.label}</span>
                <span className="issue-count">{issue.count}x</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.recent_ratings?.length > 0 && (
        <div className="card">
          <h3>🕐 Recientes</h3>
          <div className="recent-list">
            {data.recent_ratings.slice(0, 5).map(r => (
              <div key={r.id} className={`recent-item ${r.value}`}>
                <span>{r.value === 'like' ? '👍' : '👎'}</span>
                <span className="recent-user">{r.username}</span>
                <span className="recent-msg">{r.message_preview}</span>
                <span className="recent-date">{new Date(r.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ========== TAB: PIPELINE ==========
function PipelineTab({ notify }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPipelineStatus();
      if (res.success) setStatus(res);
    } catch (e) {
      notify('Error cargando pipeline', 'error');
    }
    setLoading(false);
  }, [notify]);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  if (loading) return <Loading />;
  if (!status) return <Empty>Sin información</Empty>;

  const components = [
    { key: 'drive_sync', label: 'Google Drive', icon: '📁' },
    { key: 'embeddings', label: 'Embeddings', icon: '🧠' },
    { key: 'vector_store', label: 'Vector Store', icon: '🗄️' },
    { key: 'pipeline', label: 'Pipeline', icon: '⚙️' }
  ];

  return (
    <div className="tab-content">
      <div className="section-header">
        <h2>Estado del Pipeline RAG</h2>
        <button onClick={loadStatus} className="btn-secondary" disabled={loading}>🔄 Actualizar</button>
      </div>

      <div className={`status-badge ${status.overall}`}>
        {status.overall === 'operational' ? '✅ Operacional' : '⚠️ Degradado'}
      </div>

      <div className="pipeline-grid">
        {components.map(c => (
          <div key={c.key} className={`pipeline-card ${status.status?.[c.key] ? 'active' : 'inactive'}`}>
            <span className="pipeline-icon">{c.icon}</span>
            <h4>{c.label}</h4>
            <p>{status.status?.[c.key] ? '✅ Activo' : '❌ Inactivo'}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AdminPanel;
