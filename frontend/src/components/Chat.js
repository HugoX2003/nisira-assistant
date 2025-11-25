import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ragEnhancedChat, getConversations, getMessages, getVectorStats, deleteConversation, submitRating } from '../services/api';
import '../styles/Chat.css';

// Componente actualizado con nuevo diseño moderno

// Componente especializado para renderizar texto con Markdown
const MarkdownRenderer = React.memo(({ content }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      // Párrafos con mejor espaciado
      p: ({ children }) => (
        <p style={{ 
          margin: '0.8em 0', 
          lineHeight: '1.7',
          fontSize: '0.95rem'
        }}>
          {children}
        </p>
      ),
      
      // Texto en negrita
      strong: ({ children }) => (
        <strong style={{ 
          fontWeight: '600',
          color: 'inherit'
        }}>
          {children}
        </strong>
      ),
      
      // Texto en cursiva
      em: ({ children }) => (
        <em style={{ 
          fontStyle: 'italic',
          opacity: '0.95'
        }}>
          {children}
        </em>
      ),
      
      // Código inline
      code: ({ children, className }) => {
        const isBlock = className?.includes('language-');
        if (isBlock) {
          return (
            <pre style={{
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              padding: '1rem',
              borderRadius: '8px',
              overflow: 'auto',
              margin: '1em 0',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <code style={{
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                fontSize: '0.9em',
                color: 'inherit'
              }}>
                {children}
              </code>
            </pre>
          );
        }
        return (
          <code style={{
            backgroundColor: 'rgba(255, 255, 255, 0.12)',
            padding: '3px 6px',
            borderRadius: '4px',
            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
            fontSize: '0.9em',
            fontWeight: '500',
            color: 'inherit',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            {children}
          </code>
        );
      },
      
      // Listas ordenadas
      ol: ({ children }) => (
        <ol style={{
          paddingLeft: '1.5em',
          margin: '1.2em 0',
          lineHeight: '1.7'
        }}>
          {children}
        </ol>
      ),
      
      // Listas no ordenadas
      ul: ({ children }) => (
        <ul style={{
          paddingLeft: '1.5em',
          margin: '1.2em 0',
          lineHeight: '1.7'
        }}>
          {children}
        </ul>
      ),
      
      // Items de lista
      li: ({ children }) => (
        <li style={{
          margin: '0.8em 0',
          lineHeight: '1.7',
          display: 'list-item',
          listStylePosition: 'outside',
          paddingLeft: '0.3em'
        }}>
          {children}
        </li>
      ),
      
      // Encabezados
      h1: ({ children }) => (
        <h1 style={{
          fontSize: '1.3em',
          fontWeight: '700',
          margin: '1.5em 0 0.8em 0',
          color: 'inherit',
          borderBottom: '2px solid rgba(255, 255, 255, 0.2)',
          paddingBottom: '0.3em'
        }}>
          {children}
        </h1>
      ),
      
      h2: ({ children }) => (
        <h2 style={{
          fontSize: '1.2em',
          fontWeight: '650',
          margin: '1.4em 0 0.7em 0',
          color: 'inherit'
        }}>
          {children}
        </h2>
      ),
      
      h3: ({ children }) => (
        <h3 style={{
          fontSize: '1.1em',
          fontWeight: '600',
          margin: '1.2em 0 0.6em 0',
          color: 'inherit'
        }}>
          {children}
        </h3>
      ),
      
      h4: ({ children }) => (
        <h4 style={{
          fontSize: '1.05em',
          fontWeight: '600',
          margin: '1em 0 0.5em 0',
          color: 'inherit'
        }}>
          {children}
        </h4>
      ),
      
      // Citas en bloque
      blockquote: ({ children }) => (
        <blockquote style={{
          borderLeft: '4px solid rgba(255, 255, 255, 0.3)',
          paddingLeft: '1rem',
          margin: '1em 0',
          fontStyle: 'italic',
          opacity: '0.9',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          padding: '0.8rem 1rem',
          borderRadius: '0 8px 8px 0'
        }}>
          {children}
        </blockquote>
      ),
      
      // Separadores horizontales
      hr: () => (
        <hr style={{
          border: 'none',
          borderTop: '1px solid rgba(255, 255, 255, 0.2)',
          margin: '2em 0'
        }} />
      ),
      
      // Eliminar enlaces azules
      a: ({ children, href }) => (
        <span style={{
          color: 'inherit',
          textDecoration: 'underline',
          textDecorationColor: 'rgba(255, 255, 255, 0.5)'
        }}>
          {children}
        </span>
      ),
      
      // Tablas
      table: ({ children }) => (
        <div style={{ overflowX: 'auto', margin: '1em 0' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            {children}
          </table>
        </div>
      ),
      
      th: ({ children }) => (
        <th style={{
          padding: '0.6rem',
          textAlign: 'left',
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          fontWeight: '600'
        }}>
          {children}
        </th>
      ),
      
      td: ({ children }) => (
        <td style={{
          padding: '0.6rem',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          {children}
        </td>
      )
    }}
  >
    {content}
  </ReactMarkdown>
));

// Componente de fuentes mejorado con lista desplegable
const SourcesDropdown = React.memo(({ sources }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  console.log('SourcesDropdown renderizado con:', sources);
  
  if (!sources || sources.length === 0) {
    console.log('No hay fuentes para mostrar');
    return null;
  }
  
  const handleSourceClick = async (source) => {
    try {
      if (source.file_name) {
        // Construir URL del documento usando la misma lógica que adminApi.js
        const rawBaseUrl = process.env.REACT_APP_API_URL || process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8000';
        const trimmedBaseUrl = rawBaseUrl.replace(/\/+$/, '');
        const API_BASE_URL = trimmedBaseUrl.endsWith('/api') ? trimmedBaseUrl : `${trimmedBaseUrl}/api`;
        
        const token = localStorage.getItem('token');
        
        if (!token) {
          alert('Necesitas estar logueado para ver los documentos');
          return;
        }
        
        // Abrir documento en nueva ventana
        const documentUrl = `${API_BASE_URL}/documents/${encodeURIComponent(source.file_name)}/`;
        console.log('📄 Abriendo documento:', documentUrl);
        const newWindow = window.open('', '_blank');
        
        // Crear iframe con autenticación
        newWindow.document.write(`
          <html>
            <head>
              <title>${source.file_name}</title>
              <style>
                body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
                iframe { width: 100%; height: 100vh; border: none; }
                .loading { text-align: center; padding: 50px; }
                .error { color: red; text-align: center; padding: 50px; }
              </style>
            </head>
            <body>
              <div class="loading">Cargando documento...</div>
              <script>
                fetch('${documentUrl}', {
                  headers: {
                    'Authorization': 'Bearer ${token}'
                  }
                })
                .then(response => {
                  console.log('Response status:', response.status);
                  if (response.ok) {
                    return response.blob();
                  }
                  throw new Error('Error al cargar el documento (HTTP ' + response.status + ')');
                })
                .then(blob => {
                  const url = URL.createObjectURL(blob);
                  document.body.innerHTML = '<iframe src="' + url + '"></iframe>';
                })
                .catch(error => {
                  console.error('Error:', error);
                  document.body.innerHTML = '<div class="error">Error: ' + error.message + '</div>';
                });
              </script>
            </body>
          </html>
        `);
        newWindow.document.close();
      } else {
        // Fallback: mostrar información del documento
        alert(`Documento: ${source.file_name || 'Documento sin nombre'}
Página: ${source.page || 'N/A'}
Relevancia: ${((source.similarity_score || 0) * 100).toFixed(1)}%`);
      }
    } catch (error) {
      console.error('Error abriendo documento:', error);
      alert('Error al abrir el documento. Inténtalo de nuevo.');
    }
  };

  return (
    <div className="sources-dropdown">
      <button 
        className="sources-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className="sources-icon">📚</span>
        <span className="sources-text">Fuentes consultadas ({sources.length})</span>
        <span className={`sources-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </button>
      
      {isOpen && (
        <div className="sources-content">
          {sources.map((source, idx) => (
            <div 
              key={idx} 
              className="source-item"
              onClick={() => handleSourceClick(source)}
              role="button"
              tabIndex={0}
            >
              <div className="source-header">
                <span className="source-icon">📄</span>
                <div className="source-info">
                  <div className="source-title">
                    {source.file_name || `Documento ${idx + 1}`}
                  </div>
                  <div className="source-meta">
                    {source.page && <span className="source-page">Página {source.page}</span>}
                    <span className="source-relevance">
                      Relevancia: {((source.similarity_score || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
              <div className="source-preview">
                {source.content ? source.content.substring(0, 200) + (source.content.length > 200 ? '...' : '') : 
                 source.text ? source.text.substring(0, 200) + (source.text.length > 200 ? '...' : '') :
                 'Vista previa no disponible'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

// Componente de mensaje optimizado
const MessageFeedback = React.memo(({ value, disabled, onChange }) => {
  const isLikeActive = value === 'like';
  const isDislikeActive = value === 'dislike';

  return (
    <div className="message-feedback" role="group" aria-label="Califica la respuesta">
      <button
        type="button"
        className={`feedback-btn feedback-like ${isLikeActive ? 'active' : ''}`}
        onClick={() => onChange(isLikeActive ? 'clear' : 'like')}
        disabled={disabled}
        aria-pressed={isLikeActive}
        aria-label={isLikeActive ? 'Quitar "me gusta"' : 'Marcar como útil'}
      >
        <span aria-hidden="true">👍</span>
        <span className="feedback-label">Útil</span>
      </button>
      <button
        type="button"
        className={`feedback-btn feedback-dislike ${isDislikeActive ? 'active' : ''}`}
        onClick={() => onChange(isDislikeActive ? 'clear' : 'dislike')}
        disabled={disabled}
        aria-pressed={isDislikeActive}
        aria-label={isDislikeActive ? 'Quitar "no útil"' : 'Marcar como no útil'}
      >
        <span aria-hidden="true">👎</span>
        <span className="feedback-label">No útil</span>
      </button>
    </div>
  );
});

const Message = React.memo(({ message, isUser, timestamp, sources, rating, onRate, ratingBusy }) => {
  console.log('Renderizando mensaje:', { message: message?.substring(0, 50), isUser, sourcesCount: sources?.length });
  
  return (
    <div className={`message-item ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-bubble">
        <div className="message-text">
          {isUser ? (
            message
          ) : (
            <MarkdownRenderer content={message || ''} />
          )}
        </div>
        {!isUser && sources && sources.length > 0 && (
          <SourcesDropdown sources={sources} />
        )}
        {!isUser && onRate && (
          <MessageFeedback value={rating} onChange={onRate} disabled={ratingBusy} />
        )}
      </div>
      <div className="message-timestamp">{timestamp}</div>
    </div>
  );
});

// Componente de loading optimizado
const LoadingIndicator = React.memo(() => (
  <div className="message-item assistant-message">
    <div className="message-bubble">
      <div className="loading-indicator">
        <span>Pensando</span>
        <div className="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  </div>
));

// Hook personalizado para manejo de mensajes
const useMessages = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const addMessage = useCallback((message) => {
    console.log('Agregando mensaje:', message);
    setMessages(prev => {
      // Evitar duplicados basados en ID
      if (prev.some(m => m.id === message.id)) {
        console.log('Mensaje duplicado detectado, ignorando');
        return prev;
      }
      const newMessages = [...prev, message];
      console.log('Nuevo estado de mensajes:', newMessages.length);
      return newMessages;
    });
  }, []);

  const clearMessages = useCallback(() => {
    console.log('Limpiando mensajes');
    setMessages([]);
  }, []);

  const updateMessage = useCallback((backendId, updates) => {
    if (!backendId) {
      return;
    }

    setMessages(prev => prev.map(msg => {
      if (msg.backendId !== backendId) {
        return msg;
      }

      const patch = typeof updates === 'function' ? updates(msg) : updates;
      return { ...msg, ...patch };
    }));
  }, []);

  return {
    messages,
    isLoading,
    setIsLoading,
    addMessage,
    clearMessages,
    updateMessage
  };
};

// Hook personalizado para manejo de conversaciones
const useConversations = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);

  const loadConversations = useCallback(async (autoSelect = true) => {
    try {
      console.log('📋 Cargando conversaciones...');
      const response = await getConversations();
      const conversationsList = response.conversations || [];
      console.log('📋 Conversaciones recibidas:', conversationsList.length, conversationsList);
      setConversations(conversationsList);
      
      // Solo auto-seleccionar si se especifica Y hay conversaciones
      if (autoSelect && conversationsList.length > 0) {
        console.log('🎯 Auto-seleccionando conversación:', conversationsList[0].id);
        setActiveConversation(conversationsList[0].id);
      } else {
        console.log('⏭️ No auto-seleccionar (autoSelect:', autoSelect, ', count:', conversationsList.length, ')');
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
      setConversations([]);
    }
  }, []);

  return {
    conversations,
    activeConversation,
    setActiveConversation,
    loadConversations,
    setConversations
  };
};

const Chat = ({ onLogout, user }) => {
  const [message, setMessage] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 1024);
  const [error, setError] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ show: false, conversationId: null });
  const [ratingBusy, setRatingBusy] = useState({});
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { messages, isLoading, setIsLoading, addMessage, clearMessages, updateMessage } = useMessages();
  const { conversations, activeConversation, setActiveConversation, loadConversations } = useConversations();

  // Manejar cambios de tamaño de ventana
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 1024) {
        setSidebarOpen(true);
      } else {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Toggle sidebar para móvil
  const toggleSidebar = useCallback(() => {
    setSidebarOpen(prev => !prev);
  }, []);

  // Scroll automático optimizado
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Efecto para scroll cuando cambian los mensajes
  useEffect(() => {
    console.log('Mensajes cambiaron, total:', messages.length);
    const timer = setTimeout(scrollToBottom, 200);
    return () => clearTimeout(timer);
  }, [messages, scrollToBottom]);

  // Efecto adicional para forzar re-renderizado después de agregar mensajes
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage && lastMessage.sender === 'bot' && lastMessage.sources?.length > 0) {
        console.log('Mensaje del bot con fuentes detectado, forzando re-renderizado');
        // Pequeño delay para asegurar que el DOM se actualice
        setTimeout(() => {
          // Trigger re-render si es necesario
        }, 100);
      }
    }
  }, [messages]);

  // Cargar conversaciones al montar - SIN auto-seleccionar
  useEffect(() => {
    loadConversations(false);
  }, [loadConversations]);

  // Cargar mensajes cuando cambia la conversación activa
  useEffect(() => {
    if (!activeConversation) {
      clearMessages();
      setRatingBusy({});
      return;
    }

    const loadMessages = async () => {
      try {
        setError(null);
        setRatingBusy({});
        const res = await getMessages(activeConversation);
        const msgs = (res.messages || []).map(m => ({
          id: `loaded-${m.id}`,
          backendId: m.id,
          text: m.content || '',
          sender: m.is_user ? 'user' : 'bot',
          timestamp: new Date(m.timestamp).toLocaleTimeString(),
          sources: m.sources || [],
          rating: m.rating || null,
        }));
        
        console.log('Mensajes cargados:', msgs);
        clearMessages();
        
        // Agregar mensajes uno por uno para asegurar el renderizado correcto
        msgs.forEach((msg, index) => {
          setTimeout(() => {
            addMessage(msg);
          }, index * 10);
        });
        
      } catch (error) {
        console.error('Error cargando mensajes:', error);
        setError('Error cargando mensajes');
        clearMessages();
      }
    };

    loadMessages();
  }, [activeConversation, clearMessages, addMessage]);

  // Manejo optimizado del envío de mensajes
  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage('');
    
    // Agregar mensaje del usuario inmediatamente
    const userMsg = {
      id: `user-${Date.now()}`,
      backendId: null,
      text: userMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      sources: [],
      rating: null,
    };
    
    addMessage(userMsg);
    setIsLoading(true);
    setError(null);

    try {
      // Enviar al sistema RAG
      const response = await ragEnhancedChat(userMessage, activeConversation);
      
      console.log('Respuesta del backend:', response);
      
      // Asegurar que la respuesta esté completa antes de agregar
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Agregar respuesta del asistente con ID único
      const assistantMsg = {
        id: `bot-${Date.now()}`,
        backendId: response.assistant_message?.id || null,
        text: response.assistant_message?.content || response.response || '',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        sources: response.sources || [],
        rating: response.assistant_message?.rating || null,
      };
      
      console.log('Mensaje del asistente creado:', assistantMsg);
      addMessage(assistantMsg);
      
      // Actualizar conversación activa si se creó una nueva
      if (response.conversation_id && response.conversation_id !== activeConversation) {
        console.log('🔄 Nueva conversación creada, ID:', response.conversation_id);
        setActiveConversation(response.conversation_id);
      }
      
      // SIEMPRE recargar lista de conversaciones después de enviar mensaje
      // Esto asegura que las nuevas conversaciones aparezcan inmediatamente
      await loadConversations(false);
      console.log('✅ Lista de conversaciones actualizada');
      
    } catch (error) {
      console.error('Error en chat:', error);
      setError(error.message || 'Error al enviar mensaje');
      
      // Agregar mensaje de error
      const errorMsg = {
        id: `error-${Date.now()}`,
        text: 'Lo siento, ocurrió un error. Por favor intenta de nuevo.',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        sources: []
      };
      
      addMessage(errorMsg);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [message, isLoading, activeConversation, addMessage, loadConversations]);

  // Manejo de nueva conversación
  const handleNewConversation = useCallback(() => {
    // Limpiar para nueva conversación
    setActiveConversation(null);
    clearMessages();
    setError(null);
    setRatingBusy({});
    inputRef.current?.focus();
  }, [clearMessages, setRatingBusy, setActiveConversation]);

  // Manejo de selección de conversación
  const handleConversationSelect = useCallback((conversationId) => {
    if (conversationId !== activeConversation) {
      setActiveConversation(conversationId);
    }
  }, [activeConversation]);

  // Manejo de eliminación de conversación
  const handleDeleteConversation = useCallback(async (conversationId, event) => {
    if (event) {
      event.stopPropagation();
    }
    
    setDeleteDialog({ show: true, conversationId });
  }, []);

  const confirmDelete = useCallback(async () => {
    const { conversationId } = deleteDialog;
    
    try {
      await deleteConversation(conversationId);
      
      // Si es la conversación activa, limpiar
      if (conversationId === activeConversation) {
        setActiveConversation(null);
        clearMessages();
        setRatingBusy({});
      }
      
      // Recargar conversaciones
      await loadConversations(false);
      setDeleteDialog({ show: false, conversationId: null });
      
    } catch (error) {
      console.error('Error al eliminar conversación:', error);
      setError('Error al eliminar conversación');
    }
  }, [deleteDialog, activeConversation, clearMessages, loadConversations]);

  const handleRateMessage = useCallback(async (backendId, targetValue) => {
    if (!backendId || !targetValue) {
      return;
    }

    setRatingBusy(prev => ({ ...prev, [backendId]: true }));
    try {
      const result = await submitRating({ messageId: backendId, value: targetValue });
      updateMessage(backendId, {
        rating: result?.value || null,
        ratingUpdatedAt: result?.updated_at || null,
      });
    } catch (error) {
      console.error('Error guardando calificación:', error);
      setError(error.message || 'No se pudo guardar la calificación');
    } finally {
      setRatingBusy(prev => {
        const next = { ...prev };
        delete next[backendId];
        return next;
      });
    }
  }, [updateMessage]);

  const handleRateToggle = useCallback((backendId, currentValue, requestedValue) => {
    const nextValue = currentValue === requestedValue ? 'clear' : requestedValue;
    handleRateMessage(backendId, nextValue);
  }, [handleRateMessage]);

  return (
    <div className="chat chat-container">
      {/* Overlay para cerrar sidebar en móvil */}
      {sidebarOpen && window.innerWidth <= 1024 && (
        <div 
          className="sidebar-overlay show" 
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      <div className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <h3>Conversaciones</h3>
          <div className="sidebar-header-actions">
            <button 
              className="new-conversation-btn"
              onClick={handleNewConversation}
              title="Nueva conversación"
            >
              + Nueva
            </button>
            <button 
              className="sidebar-close-btn"
              onClick={() => setSidebarOpen(false)}
              title="Cerrar sidebar"
              aria-label="Cerrar sidebar"
            >
              ✕
            </button>
          </div>
        </div>
        
        <div className="conversations-list">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`conversation-item ${conv.id === activeConversation ? 'active' : ''}`}
              onClick={() => handleConversationSelect(conv.id)}
            >
              <div className="conversation-title">
                {conv.title || `Conversación ${conv.id}`}
              </div>
              <div className="conversation-actions">
                <button
                  className="delete-conversation-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteDialog({ show: true, conversationId: conv.id });
                  }}
                  title="Eliminar conversación"
                  aria-label="Eliminar conversación"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-name">{user?.username || 'Usuario'}</span>
            <button 
              className="logout-btn"
              onClick={onLogout}
              title="Cerrar sesión"
            >
              🚪 Salir
            </button>
          </div>
        </div>
      </div>
      
      <div className="main-content">
        <div className="chat-header">
          <button 
            className="menu-toggle"
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
          <h2>NISIRA Assistant</h2>
          <div className="chat-status">
            {isLoading ? 'Procesando...' : 'Listo'}
          </div>
        </div>

        {error && (
          <div className="error-banner">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        <div className="messages-container">
          {messages.length === 0 && !isLoading && (
            <div className="welcome-message">
              <h3>¡Bienvenido al NISIRA Assistant! 🤖</h3>
              <p>Pregúntame sobre cualquier tema de los documentos disponibles.</p>
              <div className="example-questions">
                <p><strong>Ejemplos:</strong></p>
                <ul>
                  <li>"¿Qué es el machine learning?"</li>
                  <li>"Explícame sobre las redes neuronales"</li>
                  <li>"¿Cómo funciona el procesamiento de lenguaje natural?"</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map((msg, index) => {
            console.log(`Renderizando mensaje ${index}:`, { id: msg.id, text: msg.text?.substring(0, 30), sources: msg.sources?.length });
            return (
              <Message
                key={`${msg.id}-${index}`}
                message={msg.text}
                isUser={msg.sender === 'user'}
                timestamp={msg.timestamp}
                sources={msg.sources}
                rating={msg.rating}
                onRate={msg.sender === 'bot' ? (value) => handleRateToggle(msg.backendId, msg.rating, value) : null}
                ratingBusy={Boolean(msg.backendId && ratingBusy[msg.backendId])}
              />
            );
          })}

          {isLoading && <LoadingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-wrapper">
              <textarea
                ref={inputRef}
                className="message-input"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Escribe tu pregunta aquí..."
                disabled={isLoading}
                rows="1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <button
                type="submit"
                className="send-button"
                disabled={!message.trim() || isLoading}
                title="Enviar mensaje"
              >
                ➤
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Dialog de confirmación de eliminación */}
      {deleteDialog.show && (
        <div className="delete-dialog-overlay">
          <div className="delete-dialog">
            <h3>Confirmar eliminación</h3>
            <p>¿Estás seguro de que quieres eliminar esta conversación?</p>
            <div className="delete-dialog-actions">
              <button 
                className="delete-dialog-btn delete-dialog-btn-cancel"
                onClick={() => setDeleteDialog({ show: false, conversationId: null })}
              >
                Cancelar
              </button>
              <button 
                className="delete-dialog-btn delete-dialog-btn-confirm"
                onClick={confirmDelete}
              >
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;