import React, { useState, useEffect } from 'react';
import { getQueryList, getQueryDetail } from '../services/adminApi';
import '../styles/QueryMetrics.css';

/**
 * Componente para mostrar métricas detalladas por consulta
 */
function QueryMetrics({ showNotification }) {
  const [queries, setQueries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [queryDetail, setQueryDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  
  // Paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalQueries, setTotalQueries] = useState(0);
  
  // Filtro
  const [complexOnly, setComplexOnly] = useState(false);

  useEffect(() => {
    loadQueries();
  }, [currentPage, complexOnly]);

  const loadQueries = async () => {
    setLoading(true);
    try {
      const response = await getQueryList(currentPage, 20, complexOnly);
      if (response.success) {
        setQueries(response.queries);
        setTotalPages(response.pagination.total_pages);
        setTotalQueries(response.pagination.total_queries);
      } else {
        showNotification('Error cargando consultas', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('❌ Error obteniendo lista de consultas', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadQueryDetail = async (queryId) => {
    setDetailLoading(true);
    try {
      const response = await getQueryDetail(queryId);
      if (response.success) {
        setQueryDetail(response.query);
        setSelectedQuery(queryId);
      } else {
        showNotification('Error cargando detalle', 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification('❌ Error obteniendo detalle de consulta', 'error');
    } finally {
      setDetailLoading(false);
    }
  };

  const formatTime = (seconds) => {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  const getComplexityBadge = (isComplex, score) => {
    if (isComplex) {
      return <span className="badge badge-complex">Compleja ({(score * 100).toFixed(0)}%)</span>;
    }
    return <span className="badge badge-simple">Simple ({(score * 100).toFixed(0)}%)</span>;
  };

  const getMetricColor = (value, metric) => {
    // Para precision, recall, faithfulness: mayor es mejor
    if (['precision', 'recall', 'faithfulness', 'relevancy'].includes(metric)) {
      if (value >= 0.8) return 'metric-good';
      if (value >= 0.6) return 'metric-ok';
      return 'metric-bad';
    }
    
    // Para hallucination: menor es mejor
    if (metric === 'hallucination') {
      if (value <= 0.1) return 'metric-good';
      if (value <= 0.3) return 'metric-ok';
      return 'metric-bad';
    }
    
    return '';
  };

  return (
    <div className="query-metrics-container">
      <div className="query-metrics-header">
        <h2>📊 Métricas Detalladas por Consulta</h2>
        <div className="query-metrics-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={complexOnly}
              onChange={(e) => {
                setComplexOnly(e.target.checked);
                setCurrentPage(1);
              }}
            />
            Solo consultas complejas
          </label>
          <button onClick={loadQueries} className="btn-secondary" disabled={loading}>
            {loading ? 'Cargando...' : '🔄 Actualizar'}
          </button>
        </div>
      </div>

      <div className="query-metrics-stats">
        <div className="stat-card">
          <span className="stat-value">{totalQueries}</span>
          <span className="stat-label">Total Consultas</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{queries.length}</span>
          <span className="stat-label">En esta página</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{queries.filter(q => q.is_complex).length}</span>
          <span className="stat-label">Complejas</span>
        </div>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Cargando consultas...</p>
        </div>
      ) : (
        <>
          <div className="queries-grid">
            {queries.map((query) => (
              <div
                key={query.query_id}
                className={`query-card ${selectedQuery === query.query_id ? 'selected' : ''}`}
                onClick={() => loadQueryDetail(query.query_id)}
              >
                <div className="query-card-header">
                  <span className="query-timestamp">
                    {new Date(query.timestamp).toLocaleString()}
                  </span>
                  {getComplexityBadge(query.is_complex, query.complexity_score)}
                </div>
                
                <div className="query-text">
                  {query.query_text}
                </div>
                
                <div className="query-metrics-summary">
                  <div className="metric-mini">
                    <span className="metric-mini-label">⏱️ Tiempo Total</span>
                    <span className="metric-mini-value">{formatTime(query.performance.total_latency)}</span>
                  </div>
                  <div className="metric-mini">
                    <span className="metric-mini-label">⚡ TTFT</span>
                    <span className="metric-mini-value">{formatTime(query.performance.time_to_first_token)}</span>
                  </div>
                  <div className="metric-mini">
                    <span className="metric-mini-label">📄 Docs</span>
                    <span className="metric-mini-value">{query.performance.documents_retrieved}</span>
                  </div>
                </div>

                {query.precision && (
                  <div className="query-precision-mini">
                    <span className={`precision-badge ${getMetricColor(query.precision.precision_at_k, 'precision')}`}>
                      P: {(query.precision.precision_at_k * 100).toFixed(0)}%
                    </span>
                    <span className={`precision-badge ${getMetricColor(query.precision.recall_at_k, 'recall')}`}>
                      R: {(query.precision.recall_at_k * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Paginación */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="btn-secondary"
              >
                ← Anterior
              </button>
              <span className="pagination-info">
                Página {currentPage} de {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="btn-secondary"
              >
                Siguiente →
              </button>
            </div>
          )}

          {/* Detalle de consulta seleccionada */}
          {selectedQuery && queryDetail && (
            <div className="query-detail-modal" onClick={() => {setSelectedQuery(null); setQueryDetail(null);}}>
              <div className="query-detail-content" onClick={(e) => e.stopPropagation()}>
                <div className="query-detail-header">
                  <h3>🔍 Detalle de Consulta</h3>
                  <button onClick={() => {setSelectedQuery(null); setQueryDetail(null);}} className="btn-close">
                    ✕
                  </button>
                </div>

                {detailLoading ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <p>Cargando detalle...</p>
                  </div>
                ) : (
                  <div className="query-detail-body">
                    {/* Consulta y Metadata */}
                    <div className="detail-section">
                      <h4>📝 Consulta</h4>
                      <div className="query-detail-text">{queryDetail.query_text}</div>
                      <div className="query-detail-meta">
                        <span>🕐 {new Date(queryDetail.timestamp).toLocaleString()}</span>
                        <span>🆔 {queryDetail.query_id.substring(0, 8)}</span>
                      </div>
                    </div>

                    {/* LAS 4 MÉTRICAS PRINCIPALES */}
                    <div className="detail-section">
                      <h4>📊 3 Métricas Finales (RAGAS + Gemini)</h4>
                      <p className="detail-subtitle">Evaluación con RAGAS usando Gemini API</p>
                    </div>

                    {/* MÉTRICA 1: LATENCIA TOTAL */}
                    {queryDetail.tiempo_respuesta && (
                      <div className="detail-section">
                        <h4>⏱️ 1. Latencia Total</h4>
                        <div className="metric-detail-card highlight">
                          <div className="metric-detail-value-large">{queryDetail.tiempo_respuesta.valor.toFixed(4)}s</div>
                          <div className="metric-detail-formula">
                            <strong>Método:</strong> {queryDetail.tiempo_respuesta.metodo}
                          </div>
                          <div className="metric-detail-formula">
                            <strong>Fórmula:</strong> <code>{queryDetail.tiempo_respuesta.formula}</code>
                          </div>
                          <div className="metric-detail-explanation">
                            <strong>Cómo se calculó:</strong><br/>
                            {queryDetail.tiempo_respuesta.calculo_detallado.descripcion}<br/>
                            <code>{queryDetail.tiempo_respuesta.calculo_detallado.codigo_usado}</code><br/>
                            <strong>Resultado:</strong> {queryDetail.tiempo_respuesta.calculo_detallado.valor_final}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* MÉTRICA 2: REDUCCIÓN DE TIEMPO */}
                    {queryDetail.velocidad_procesamiento && (
                      <div className="detail-section">
                        <h4>🚀 2. Reducción de Tiempo</h4>
                        <div className="metric-detail-card highlight">
                          <div className="metric-detail-value-large">{queryDetail.velocidad_procesamiento.valor.toFixed(2)} tokens/s</div>
                          <div className="metric-detail-formula">
                            <strong>Método:</strong> {queryDetail.velocidad_procesamiento.metodo}
                          </div>
                          <div className="metric-detail-formula">
                            <strong>Fórmula:</strong> <code>{queryDetail.velocidad_procesamiento.formula}</code>
                          </div>
                          <div className="metric-detail-explanation">
                            <strong>Cómo se calculó:</strong><br/>
                            {queryDetail.velocidad_procesamiento.calculo_detallado.descripcion}<br/>
                            <strong>Tokens generados:</strong> {queryDetail.velocidad_procesamiento.calculo_detallado.tokens_generados}<br/>
                            <strong>Tiempo total:</strong> {queryDetail.velocidad_procesamiento.calculo_detallado.tiempo_total.toFixed(4)}s<br/>
                            <strong>Operación:</strong> {queryDetail.velocidad_procesamiento.calculo_detallado.operacion}<br/>
                            <strong>Resultado:</strong> {queryDetail.velocidad_procesamiento.calculo_detallado.valor_final}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* MÉTRICA 3: CALIDAD DE RESPUESTA (RAGAS) */}
                    {queryDetail.calidad_respuesta && (
                      <div className="detail-section">
                        <h4>✨ 3. Calidad de Respuesta (RAGAS)</h4>
                        <div className="metric-detail-card highlight">
                          <div className="metric-detail-value-large">{(queryDetail.calidad_respuesta.valor * 100).toFixed(2)}%</div>
                          <div className="metric-detail-formula">
                            <strong>Método:</strong> RAGAS con Gemini API
                          </div>
                          <div className="metric-detail-formula">
                            <strong>Fórmula:</strong> <code>Faithfulness*0.4 + Answer Relevancy*0.4 + Context Precision*0.2</code>
                          </div>
                          <div className="metric-detail-explanation">
                            <strong>Desglose RAGAS:</strong><br/>
                            <strong>Faithfulness:</strong> {(queryDetail.calidad_respuesta.faithfulness * 100).toFixed(2)}% (Fidelidad al contexto)<br/>
                            <strong>Answer Relevancy:</strong> {(queryDetail.calidad_respuesta.answer_relevancy * 100).toFixed(2)}% (Relevancia de respuesta)<br/>
                            <strong>Context Precision:</strong> {(queryDetail.calidad_respuesta.context_precision * 100).toFixed(2)}% (Precisión de recuperación)<br/><br/>
                            <strong>Resultado final:</strong> {(queryDetail.calidad_respuesta.valor * 100).toFixed(2)}%<br/>
                            <em>Evaluado por Gemini API usando framework RAGAS</em>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default QueryMetrics;
