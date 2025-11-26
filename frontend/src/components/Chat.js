import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ragEnhancedChat, getConversations, getMessages, deleteConversation, submitRating } from '../services/api';
import '../styles/Chat.css';

// Componente para renderizar Markdown
const Markdown = ({ content }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
);

// Componente de fuentes con visor integrado
const Sources = ({ sources, onOpenPdf }) => {
  const [open, setOpen] = useState(false);
  
  if (!sources?.length) return null;

  return (
    <div className="sources">
      <button className="sources-btn" onClick={() => setOpen(!open)}>
        📚 Fuentes ({sources.length})
        <span className={`sources-arrow ${open ? 'open' : ''}`}>▼</span>
      </button>
      
      {open && (
        <div className="sources-list">
          {sources.map((s, i) => (
            <div key={i} className="source-item" onClick={() => onOpenPdf(s)}>
              <div className="source-name">📄 {s.file_name || `Documento ${i + 1}`}</div>
              <div className="source-meta">
                {s.page && `Pág. ${s.page} • `}
                Relevancia: {((s.similarity_score || 0) * 100).toFixed(0)}%
              </div>
              {s.content && (
                <div className="source-preview">
                  {s.content.substring(0, 150)}{s.content.length > 150 ? '...' : ''}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Componente del visor de PDF lateral
const PdfViewer = ({ source, onClose }) => {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadPdf = async () => {
      setLoading(true);
      setError(null);
      
      const baseUrl = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
      const token = localStorage.getItem('token');
      
      if (!token || !source?.file_name) {
        setError('No se puede cargar el documento');
        setLoading(false);
        return;
      }

      try {
        const url = `${baseUrl}/api/documents/${encodeURIComponent(source.file_name)}/`;
        const res = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) throw new Error('Error al cargar');
        
        const blob = await res.blob();
        const objectUrl = URL.createObjectURL(blob);
        
        // Agregar página específica si está disponible
        const pageParam = source.page ? `#page=${source.page}` : '';
        setPdfUrl(objectUrl + pageParam);
      } catch (e) {
        setError('Error al cargar el documento');
      } finally {
        setLoading(false);
      }
    };

    loadPdf();

    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [source]);

  return (
    <div className="pdf-viewer">
      <div className="pdf-header">
        <div className="pdf-info">
          <span className="pdf-title">📄 {source?.file_name}</span>
          {source?.page && <span className="pdf-page">Página {source.page}</span>}
        </div>
        <button className="pdf-close" onClick={onClose}>✕</button>
      </div>
      
      {/* Texto del chunk resaltado */}
      {source?.content && (
        <div className="pdf-chunk">
          <div className="chunk-label">📝 Fragmento referenciado:</div>
          <div className="chunk-text">{source.content}</div>
        </div>
      )}
      
      <div className="pdf-content">
        {loading && <div className="pdf-loading">Cargando documento...</div>}
        {error && <div className="pdf-error">{error}</div>}
        {pdfUrl && !loading && (
          <iframe 
            src={pdfUrl} 
            title="Documento PDF"
            className="pdf-iframe"
          />
        )}
      </div>
    </div>
  );
};

// Componente de feedback
const Feedback = ({ value, onChange, disabled }) => (
  <div className="feedback">
    <button
      className={`fb-btn ${value === 'like' ? 'active' : ''}`}
      onClick={() => onChange(value === 'like' ? 'clear' : 'like')}
      disabled={disabled}
    >
      👍 Útil
    </button>
    <button
      className={`fb-btn ${value === 'dislike' ? 'active' : ''}`}
      onClick={() => onChange(value === 'dislike' ? 'clear' : 'dislike')}
      disabled={disabled}
    >
      👎 No útil
    </button>
  </div>
);

// Componente de mensaje
const Message = ({ msg, onRate, ratingBusy, onOpenPdf }) => (
  <div className={`message ${msg.sender}`}>
    <div className="message-text">
      {msg.sender === 'user' ? msg.text : <Markdown content={msg.text || ''} />}
    </div>
    
    {msg.sender === 'bot' && msg.sources?.length > 0 && (
      <Sources sources={msg.sources} onOpenPdf={onOpenPdf} />
    )}
    
    {msg.sender === 'bot' && onRate && (
      <Feedback value={msg.rating} onChange={onRate} disabled={ratingBusy} />
    )}
    
    <div className="message-time">{msg.timestamp}</div>
  </div>
);

// Componente de carga
const Loading = () => (
  <div className="loading">
    Pensando
    <div className="dots"><span></span><span></span><span></span></div>
  </div>
);

// Componente principal del Chat
export default function Chat({ onLogout, user }) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
  const [deleteModal, setDeleteModal] = useState(null);
  const [ratingBusy, setRatingBusy] = useState({});
  const [pdfSource, setPdfSource] = useState(null); // Estado para el visor PDF
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll al final
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    setTimeout(scrollToBottom, 100);
  }, [messages, scrollToBottom]);

  // Cargar conversaciones
  const loadConversations = useCallback(async () => {
    try {
      const res = await getConversations();
      setConversations(res.conversations || []);
    } catch (e) {
      console.error('Error cargando conversaciones:', e);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Cargar mensajes al cambiar conversación
  useEffect(() => {
    if (!activeConv) {
      setMessages([]);
      return;
    }

    const loadMessages = async () => {
      try {
        const res = await getMessages(activeConv);
        setMessages((res.messages || []).map(m => ({
          id: m.id,
          text: m.content || '',
          sender: m.is_user ? 'user' : 'bot',
          timestamp: new Date(m.timestamp).toLocaleTimeString(),
          sources: m.sources || [],
          rating: m.rating
        })));
      } catch (e) {
        console.error('Error cargando mensajes:', e);
      }
    };

    loadMessages();
  }, [activeConv]);

  // Enviar mensaje
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userMsg = {
      id: Date.now(),
      text: message.trim(),
      sender: 'user',
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMsg]);
    setMessage('');
    setLoading(true);
    setError(null);

    try {
      const res = await ragEnhancedChat(userMsg.text, activeConv);
      
      setMessages(prev => [...prev, {
        id: res.assistant_message?.id || Date.now() + 1,
        text: res.assistant_message?.content || res.response || '',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        sources: res.sources || [],
        rating: null
      }]);

      if (res.conversation_id && res.conversation_id !== activeConv) {
        setActiveConv(res.conversation_id);
      }
      
      loadConversations();
    } catch (e) {
      setError(e.message || 'Error al enviar mensaje');
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: 'Lo siento, ocurrió un error. Intenta de nuevo.',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  // Nueva conversación
  const handleNewConversation = () => {
    setActiveConv(null);
    setMessages([]);
    setError(null);
    inputRef.current?.focus();
  };

  // Eliminar conversación
  const handleDelete = async () => {
    if (!deleteModal) return;
    
    try {
      await deleteConversation(deleteModal);
      if (deleteModal === activeConv) {
        setActiveConv(null);
        setMessages([]);
      }
      loadConversations();
    } catch (e) {
      setError('Error al eliminar');
    }
    setDeleteModal(null);
  };

  // Calificar mensaje
  const handleRate = async (msgId, value) => {
    if (!msgId) return;
    
    setRatingBusy(prev => ({ ...prev, [msgId]: true }));
    
    try {
      const res = await submitRating({ messageId: msgId, value });
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, rating: res?.value || null } : m
      ));
    } catch (e) {
      console.error('Error al calificar:', e);
    } finally {
      setRatingBusy(prev => {
        const next = { ...prev };
        delete next[msgId];
        return next;
      });
    }
  };

  return (
    <div className={`chat-layout ${pdfSource ? 'with-pdf' : ''}`}>
      {/* Overlay móvil */}
      {sidebarOpen && window.innerWidth <= 768 && (
        <div className="sidebar-overlay show" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${!sidebarOpen ? 'hidden' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-title">Conversaciones</span>
          <button className="btn-new" onClick={handleNewConversation}>+ Nueva</button>
          <button className="btn-close" onClick={() => setSidebarOpen(false)}>✕</button>
        </div>

        <div className="conversations">
          {conversations.map(c => (
            <div
              key={c.id}
              className={`conv-item ${c.id === activeConv ? 'active' : ''}`}
              onClick={() => setActiveConv(c.id)}
            >
              <span className="conv-title">{c.title || `Conversación ${c.id}`}</span>
              <button
                className="btn-delete"
                onClick={(e) => { e.stopPropagation(); setDeleteModal(c.id); }}
              >
                🗑️
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <span className="user-name">{user?.username || 'Usuario'}</span>
          <button className="btn-logout" onClick={onLogout}>Salir</button>
        </div>
      </aside>

      {/* Main */}
      <main className="chat-main">
        <header className="chat-header">
          <button className="btn-menu" onClick={() => setSidebarOpen(true)}>☰</button>
          <h1 className="chat-title">NISIRA Assistant</h1>
          {loading && <span className="chat-status">Procesando...</span>}
        </header>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        <div className="messages">
          {messages.length === 0 && !loading && (
            <div className="welcome">
              <div className="welcome-icon">🤖</div>
              <h2>¡Hola! Soy NISIRA Assistant</h2>
              <p>Tu asistente inteligente. Pregúntame lo que necesites.</p>
            </div>
          )}

          {messages.map(msg => (
            <Message
              key={msg.id}
              msg={msg}
              onRate={msg.sender === 'bot' ? (v) => handleRate(msg.id, v) : null}
              ratingBusy={!!ratingBusy[msg.id]}
              onOpenPdf={setPdfSource}
            />
          ))}

          {loading && <Loading />}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <form className="input-form" onSubmit={handleSubmit}>
            <div className="input-wrapper">
              <textarea
                ref={inputRef}
                className="msg-input"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Escribe tu pregunta..."
                disabled={loading}
                rows="1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <button type="submit" className="btn-send" disabled={!message.trim() || loading}>
                ➤
              </button>
            </div>
          </form>
        </div>
      </main>

      {/* Modal de confirmación */}
      {deleteModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>¿Eliminar conversación?</h3>
            <p>Esta acción no se puede deshacer.</p>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setDeleteModal(null)}>
                Cancelar
              </button>
              <button className="btn btn-danger" onClick={handleDelete}>
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Visor de PDF lateral */}
      {pdfSource && (
        <PdfViewer source={pdfSource} onClose={() => setPdfSource(null)} />
      )}
    </div>
  );
}
