import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  BookOpen,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Trash2,
  Menu,
  X,
  AlertTriangle,
  Bot,
  Send,
  ChevronDown,
} from 'lucide-react';
import { ragEnhancedChat, getConversations, getMessages, deleteConversation, submitRating } from '../services/api';
import '../styles/Chat.css';

const PAGE_SIZE = 15;

// Renderiza Markdown
const Markdown = ({ content }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
);

// Fuentes con visor integrado
const Sources = ({ sources, onOpenPdf }) => {
  const [open, setOpen] = useState(false);
  if (!sources?.length) return null;
  return (
    <div className="sources">
      <button className="sources-btn" onClick={() => setOpen(!open)}>
        <BookOpen size={16} /> Fuentes ({sources.length})
        <ChevronDown size={14} className={`sources-arrow ${open ? 'open' : ''}`} />
      </button>
      {open && (
        <div className="sources-list">
          {sources.map((s, i) => (
            <div key={i} className="source-item" onClick={() => onOpenPdf(s)}>
              <div className="source-name">
                <FileText size={14} /> {s.file_name || `Documento ${i + 1}`}
              </div>
              <div className="source-meta">
                {s.page && `Pag. ${s.page} - `}
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

// Visor de PDF lateral
const PdfViewer = ({ source, onClose }) => {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
    const baseUrl = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
    const token = localStorage.getItem('token');
    if (!token || !source?.file_name) { setError('No se puede cargar el documento'); return; }
    const fileNamePart = encodeURIComponent(source.file_name);
    const tokenPart = encodeURIComponent(token);
    const pageFragment = source.page ? `#page=${source.page}` : '';
    setPdfUrl(`${baseUrl}/api/documents/${fileNamePart}/?token=${tokenPart}${pageFragment}`);
  }, [source]);

  return (
    <div className="pdf-viewer">
      <div className="pdf-header">
        <div className="pdf-info">
          <span className="pdf-title"><FileText size={16} /> {source?.file_name}</span>
          {source?.page && <span className="pdf-page">Pagina {source.page}</span>}
        </div>
        <button className="pdf-close" onClick={onClose}><X size={18} /></button>
      </div>
      {source?.content && (
        <div className="pdf-chunk">
          <div className="chunk-label"><FileText size={14} /> Fragmento referenciado:</div>
          <div className="chunk-text">{source.content}</div>
        </div>
      )}
      <div className="pdf-content">
        {error && <div className="pdf-error">{error}</div>}
        {pdfUrl && !error && <iframe src={pdfUrl} title="Documento PDF" className="pdf-iframe" />}
      </div>
    </div>
  );
};

// Feedback
const Feedback = ({ value, onChange, disabled }) => (
  <div className="feedback">
    <button
      className={`fb-btn ${value === 'like' ? 'active' : ''}`}
      onClick={() => onChange(value === 'like' ? 'clear' : 'like')}
      disabled={disabled}
    >
      <ThumbsUp size={14} /> Util
    </button>
    <button
      className={`fb-btn ${value === 'dislike' ? 'active' : ''}`}
      onClick={() => onChange(value === 'dislike' ? 'clear' : 'dislike')}
      disabled={disabled}
    >
      <ThumbsDown size={14} /> No util
    </button>
  </div>
);

// Mensaje individual
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

// Indicador de "pensando"
const Loading = () => (
  <div className="loading">
    Pensando
    <div className="dots"><span></span><span></span><span></span></div>
  </div>
);

// ============================================================
// Componente principal
// ============================================================
export default function Chat({ onLogout, user }) {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const activeConv = conversationId || null;

  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // matchMedia usa el mismo motor que CSS; evita diferencias con window.innerWidth
  // (scrollbar nativa, zoom del SO, DevTools device mode, etc.)
  const [isMobile, setIsMobile] = useState(!window.matchMedia('(min-width: 769px)').matches);
  const [sidebarOpen, setSidebarOpen] = useState(window.matchMedia('(min-width: 769px)').matches);
  const [deleteModal, setDeleteModal] = useState(null);
  const [ratingBusy, setRatingBusy] = useState({});
  const [pdfSource, setPdfSource] = useState(null);

  // Paginación — conversaciones
  const [convPage, setConvPage] = useState(1);
  const [convHasMore, setConvHasMore] = useState(false);
  const [convLoadingMore, setConvLoadingMore] = useState(false);

  // Paginación — mensajes
  const [msgPage, setMsgPage] = useState(1);
  const [msgHasMore, setMsgHasMore] = useState(false);
  const [msgLoadingOlder, setMsgLoadingOlder] = useState(false);

  // Trigger explícito para hacer scroll al fondo (solo al enviar/cargar conversación)
  const [scrollTrigger, setScrollTrigger] = useState(0);

  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const convListRef = useRef(null);
  const inputRef = useRef(null);
  const loadMoreConvsRef = useRef(null);
  const loadOlderMsgsRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    setTimeout(scrollToBottom, 100);
  }, [scrollTrigger, scrollToBottom]);

  // Sincroniza sidebar e isMobile cuando el viewport cruza el breakpoint 769px.
  // matchMedia 'change' solo dispara al cruzar el umbral, no en cada pixel.
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 769px)');
    const onChange = (e) => {
      const desktop = e.matches;
      setIsMobile(!desktop);
      setSidebarOpen(desktop);
    };
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  // ── Conversaciones ───────────────────────────────────────

  const loadConversations = useCallback(async () => {
    try {
      const res = await getConversations(1, PAGE_SIZE);
      setConversations(res.conversations || []);
      setConvPage(1);
      setConvHasMore(res.has_more || false);
    } catch (e) {
      console.error('Error cargando conversaciones:', e);
    }
  }, []);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  const loadMoreConversations = useCallback(async () => {
    if (convLoadingMore || !convHasMore) return;
    setConvLoadingMore(true);
    try {
      const nextPage = convPage + 1;
      const res = await getConversations(nextPage, PAGE_SIZE);
      setConversations(prev => [...prev, ...(res.conversations || [])]);
      setConvPage(nextPage);
      setConvHasMore(res.has_more || false);
    } catch (e) {
      console.error('Error cargando más conversaciones:', e);
    } finally {
      setConvLoadingMore(false);
    }
  }, [convLoadingMore, convHasMore, convPage]);

  // Mantiene el ref siempre apuntando a la versión actual
  useEffect(() => { loadMoreConvsRef.current = loadMoreConversations; }, [loadMoreConversations]);

  // Scroll hacia abajo en el sidebar → cargar más conversaciones
  // El listener se attacha UNA SOLA VEZ para evitar que el cleanup/re-subscribe
  // en cada cambio de estado descarte eventos de scroll en pleno vuelo.
  useEffect(() => {
    const el = convListRef.current;
    if (!el) return;
    const onScroll = () => {
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 20) {
        loadMoreConvsRef.current?.();
      }
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  // ── Mensajes ─────────────────────────────────────────────

  // Carga los últimos PAGE_SIZE mensajes al abrir una conversación
  useEffect(() => {
    if (!activeConv) {
      setMessages([]);
      setMsgHasMore(false);
      setMsgPage(1);
      return;
    }
    const load = async () => {
      try {
        const res = await getMessages(activeConv, 1, PAGE_SIZE);
        setMessages(
          (res.messages || []).map(m => ({
            id: m.id,
            text: m.content || '',
            sender: m.is_user ? 'user' : 'bot',
            timestamp: new Date(m.timestamp).toLocaleTimeString(),
            sources: m.sources || [],
            rating: m.rating,
          }))
        );
        setMsgPage(1);
        setMsgHasMore(res.has_more || false);
        setScrollTrigger(v => v + 1);
      } catch (e) {
        console.error('Error cargando mensajes:', e);
      }
    };
    load();
  }, [activeConv]);

  // Carga mensajes más antiguos (prepend) preservando la posición de scroll
  const loadOlderMessages = useCallback(async () => {
    if (msgLoadingOlder || !msgHasMore || !activeConv) return;
    setMsgLoadingOlder(true);

    const container = messagesContainerRef.current;
    const prevScrollHeight = container?.scrollHeight || 0;

    try {
      const nextPage = msgPage + 1;
      const res = await getMessages(activeConv, nextPage, PAGE_SIZE);
      const older = (res.messages || []).map(m => ({
        id: m.id,
        text: m.content || '',
        sender: m.is_user ? 'user' : 'bot',
        timestamp: new Date(m.timestamp).toLocaleTimeString(),
        sources: m.sources || [],
        rating: m.rating,
      }));
      setMessages(prev => [...older, ...prev]);
      setMsgPage(nextPage);
      setMsgHasMore(res.has_more || false);

      // Restaurar posición de scroll después del prepend
      requestAnimationFrame(() => {
        if (container) {
          container.scrollTop = container.scrollHeight - prevScrollHeight;
        }
      });
    } catch (e) {
      console.error('Error cargando mensajes anteriores:', e);
    } finally {
      setMsgLoadingOlder(false);
    }
  }, [msgLoadingOlder, msgHasMore, activeConv, msgPage]);

  useEffect(() => { loadOlderMsgsRef.current = loadOlderMessages; }, [loadOlderMessages]);

  // Scroll hacia arriba en el área de mensajes → cargar más antiguos
  useEffect(() => {
    const el = messagesContainerRef.current;
    if (!el) return;
    const onScroll = () => {
      if (el.scrollTop <= 50) loadOlderMsgsRef.current?.();
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  // ── Envío de mensaje ─────────────────────────────────────

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userMsg = {
      id: Date.now(),
      text: message.trim(),
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
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
        rating: null,
      }]);

      setScrollTrigger(v => v + 1);

      if (res.conversation_id && res.conversation_id !== activeConv) {
        navigate(`/chat/${res.conversation_id}`, { replace: true });
      }

      loadConversations();
    } catch (e) {
      setError(e.message || 'Error al enviar mensaje');
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: 'Lo siento, ocurrió un error. Intenta de nuevo.',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleNewConversation = () => {
    navigate('/chat');
    setMessages([]);
    setError(null);
    inputRef.current?.focus();
  };

  const handleDelete = async () => {
    if (!deleteModal) return;
    try {
      await deleteConversation(deleteModal);
      if (deleteModal === activeConv) {
        navigate('/chat');
        setMessages([]);
      }
      loadConversations();
    } catch (e) {
      setError('Error al eliminar');
    }
    setDeleteModal(null);
  };

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
      setRatingBusy(prev => { const next = { ...prev }; delete next[msgId]; return next; });
    }
  };

  // ── Render ───────────────────────────────────────────────

  return (
    <div className={`chat-layout ${pdfSource ? 'with-pdf' : ''}`}>
      {sidebarOpen && isMobile && (
        <div className="sidebar-overlay show" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`sidebar ${!sidebarOpen ? 'hidden' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-title">Conversaciones</span>
          <button className="btn-new" onClick={handleNewConversation}>+ Nueva</button>
          <button className="btn-close" onClick={() => setSidebarOpen(false)}>
            <X size={18} />
          </button>
        </div>

        <div className="conversations" ref={convListRef}>
          {conversations.map(c => (
            <div
              key={c.id}
              className={`conv-item ${c.id === activeConv ? 'active' : ''}`}
              onClick={() => navigate(`/chat/${c.id}`)}
            >
              <span className="conv-title">{c.title || `Conversacion ${c.id}`}</span>
              <button
                className="btn-delete"
                onClick={(e) => { e.stopPropagation(); setDeleteModal(c.id); }}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          {convLoadingMore && (
            <div className="conv-load-more">
              <div className="dots"><span></span><span></span><span></span></div>
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <span className="user-name">{user?.username || 'Usuario'}</span>
          <button className="btn-logout" onClick={onLogout}>Salir</button>
        </div>
      </aside>

      <main className="chat-main">
        <header className="chat-header">
          <button className="btn-menu" onClick={() => setSidebarOpen(true)}>
            <Menu size={20} />
          </button>
          <h1 className="chat-title">NISIRA Assistant</h1>
          {loading && <span className="chat-status">Procesando...</span>}
        </header>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={16} /> {error}
            <button onClick={() => setError(null)}><X size={16} /></button>
          </div>
        )}

        <div className="messages" ref={messagesContainerRef}>
          {msgLoadingOlder && (
            <div className="msg-load-older">
              <div className="dots"><span></span><span></span><span></span></div>
            </div>
          )}

          {messages.length === 0 && !loading && !msgLoadingOlder && (
            <div className="welcome">
              <div className="welcome-icon"><Bot size={64} strokeWidth={1.5} /></div>
              <h2>Hola! Soy NISIRA Assistant</h2>
              <p>Tu asistente inteligente. Preguntame lo que necesites.</p>
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
                <Send size={18} />
              </button>
            </div>
          </form>
        </div>
      </main>

      {deleteModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Eliminar conversacion?</h3>
            <p>Esta accion no se puede deshacer.</p>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setDeleteModal(null)}>Cancelar</button>
              <button className="btn btn-danger" onClick={handleDelete}>Eliminar</button>
            </div>
          </div>
        </div>
      )}

      {pdfSource && <PdfViewer source={pdfSource} onClose={() => setPdfSource(null)} />}
    </div>
  );
}
