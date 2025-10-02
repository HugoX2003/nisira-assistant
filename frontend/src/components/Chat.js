import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { ragEnhancedChat, getConversations, getMessages, getVectorStats, deleteConversation } from '../services/api';
import '../styles/Chat.css';

// Componente actualizado con nuevo diseño moderno

// Componente de mensaje optimizado
const Message = React.memo(({ message, isUser, timestamp, sources }) => (
  <div className={`message-item ${isUser ? 'user-message' : 'assistant-message'}`}>
    <div className="message-bubble">
      <div className="message-text">{message}</div>
      {sources && sources.length > 0 && (
        <div className="message-sources">
          <div className="sources-header">
            📋 Fuentes ({sources.length})
          </div>
          <div className="source-cards">
            {sources.map((source, idx) => (
              <div key={idx} className="source-card">
                <div className="source-title">{source.file_name || 'Documento'}</div>
                <div className="source-details">
                  {source.page && <span className="source-page">Página {source.page}</span>}
                  <span className="source-score">
                    {((source.similarity_score || 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
    <div className="message-timestamp">{timestamp}</div>
  </div>
));

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
    setMessages(prev => [...prev, message]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    setIsLoading,
    addMessage,
    clearMessages
  };
};

// Hook personalizado para conversaciones
const useConversations = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);

  const loadConversations = useCallback(async (autoSelectFirst = true) => {
    try {
      const res = await getConversations();
      const list = res.conversations || [];
      setConversations(list);
      if (list.length > 0 && !activeConversation && autoSelectFirst) {
        setActiveConversation(list[0].id);
      }
    } catch (error) {
      console.error('Error cargando conversaciones:', error);
    }
  }, [activeConversation]);

  return {
    conversations,
    activeConversation,
    setActiveConversation,
    loadConversations
  };
};

const Chat = ({ onLogout, user }) => {
  const [message, setMessage] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [error, setError] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ show: false, conversationId: null });
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { messages, isLoading, setIsLoading, addMessage, clearMessages } = useMessages();
  const { conversations, activeConversation, setActiveConversation, loadConversations } = useConversations();

  // Scroll automático optimizado
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Efecto para scroll cuando cambian los mensajes
  useEffect(() => {
    const timer = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timer);
  }, [messages, scrollToBottom]);

  // Cargar conversaciones al montar - SIN auto-seleccionar
  useEffect(() => {
    loadConversations(false);
  }, [loadConversations]);

  // Cargar mensajes cuando cambia la conversación activa
  useEffect(() => {
    if (!activeConversation) {
      clearMessages();
      return;
    }

    const loadMessages = async () => {
      try {
        setError(null);
        const res = await getMessages(activeConversation);
        const msgs = (res.messages || []).map(m => ({
          id: m.id,
          text: m.content, // Backend envía 'content'
          sender: m.is_user ? 'user' : 'bot', // Backend envía 'is_user'
          timestamp: new Date(m.timestamp).toLocaleTimeString(), // Backend envía 'timestamp'
          sources: m.sources || []
        }));
        clearMessages();
        msgs.forEach(addMessage);
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
    
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isLoading) return;

    // Limpiar mensaje inmediatamente
    setMessage('');
    setError(null);

    // Agregar mensaje del usuario inmediatamente a la UI
    const userMsg = {
      id: `temp-user-${Date.now()}`,
      text: trimmedMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      sources: []
    };
    addMessage(userMsg);
    
    setIsLoading(true);

    try {
      // Usar ragEnhancedChat que guarda automáticamente las conversaciones
      const response = await ragEnhancedChat(trimmedMessage, activeConversation);
      
      if (response && response.assistant_message) {
        // Agregar mensaje del asistente inmediatamente a la UI
        const assistantMsg = {
          id: response.assistant_message.id,
          text: response.assistant_message.content,
          sender: 'bot',
          timestamp: new Date(response.assistant_message.timestamp).toLocaleTimeString(),
          sources: response.sources || []
        };
        addMessage(assistantMsg);

        // Si se creó una nueva conversación, actualizarla
        if (!activeConversation && response.conversation_id) {
          setActiveConversation(response.conversation_id);
        }
        
        // Recargar conversaciones para mostrar la nueva en la sidebar
        // No auto-seleccionar la primera para no interferir con la vista actual
        loadConversations(false);
        
      } else {
        throw new Error(response?.error || 'No se generó respuesta');
      }
    } catch (error) {
      console.error('Error enviando mensaje:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: `Error: ${error.message || 'No se pudo procesar tu mensaje'}`,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        sources: []
      };
      
      addMessage(errorMessage);
      setError(error.message);
    } finally {
      setIsLoading(false);
      // Enfocar input después de procesar
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [message, isLoading, addMessage, activeConversation, setActiveConversation, loadConversations]);

  // Manejo de teclas optimizado
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  // Nueva conversación
  const handleNewConversation = useCallback(() => {
    setActiveConversation(null);
    clearMessages();
    setError(null);
    inputRef.current?.focus();
  }, [clearMessages, setActiveConversation]);

  // Cambiar conversación
  const handleConversationSelect = useCallback((conversationId) => {
    if (conversationId !== activeConversation) {
      setActiveConversation(conversationId);
      setError(null);
    }
  }, [activeConversation]);

  // Eliminar conversación - Mostrar diálogo
  const handleDeleteConversation = useCallback((conversationId, e) => {
    // Prevenir que se seleccione la conversación al hacer click en eliminar
    e.stopPropagation();
    
    // Mostrar diálogo de confirmación
    setDeleteDialog({ show: true, conversationId });
  }, []);

  // Confirmar eliminación
  const confirmDelete = useCallback(async () => {
    const conversationId = deleteDialog.conversationId;
    
    try {
      await deleteConversation(conversationId);
      
      // Si la conversación eliminada era la activa, limpiar vista
      if (conversationId === activeConversation) {
        setActiveConversation(null);
        clearMessages();
      }
      
      // Recargar lista de conversaciones sin auto-seleccionar
      // Esto mostrará la pantalla de bienvenida si se eliminó la conversación activa
      loadConversations(false);
      
      // Cerrar diálogo
      setDeleteDialog({ show: false, conversationId: null });
      
    } catch (error) {
      console.error('Error eliminando conversación:', error);
      setError('No se pudo eliminar la conversación');
      setDeleteDialog({ show: false, conversationId: null });
    }
  }, [deleteDialog.conversationId, activeConversation, clearMessages, loadConversations]);

  // Cancelar eliminación
  const cancelDelete = useCallback(() => {
    setDeleteDialog({ show: false, conversationId: null });
  }, []);

  // Componente de sidebar memoizado
  const Sidebar = useMemo(() => (
    <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
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
            <div className="conversation-content">
              <div className="conversation-title">{conv.title}</div>
              <div className="conversation-date">
                {new Date(conv.created_at).toLocaleDateString()}
              </div>
            </div>
            <button
              className="delete-conversation-btn"
              onClick={(e) => handleDeleteConversation(conv.id, e)}
              title="Eliminar conversación"
              aria-label="Eliminar conversación"
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
      
      <div className="sidebar-footer">
        <div className="user-info">
          <span>👤 {user?.username || 'Usuario'}</span>
        </div>
        <button className="logout-btn" onClick={onLogout}>
          Cerrar Sesión
        </button>
      </div>
    </div>
  ), [sidebarOpen, conversations, activeConversation, handleNewConversation, handleConversationSelect, user, onLogout]);

  return (
    <div className="chat chat-container">
      {/* Overlay para cerrar sidebar en móvil */}
      {sidebarOpen && (
        <div 
          className="sidebar-overlay" 
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {Sidebar}
      
      <div className="main-content">
        <div className="chat-header">
          {!sidebarOpen && (
            <button 
              className="sidebar-toggle"
              onClick={() => setSidebarOpen(true)}
              aria-label="Abrir sidebar"
            >
              ☰
            </button>
          )}
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

          {messages.map(msg => (
            <Message
              key={msg.id}
              message={msg.text}
              isUser={msg.sender === 'user'}
              timestamp={msg.timestamp}
              sources={msg.sources}
            />
          ))}

          {isLoading && <LoadingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <form className="input-form" onSubmit={handleSubmit}>
            <div className="input-wrapper">
              <textarea
                ref={inputRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Escribe tu pregunta aquí..."
                disabled={isLoading}
                rows={1}
                className="message-input"
                style={{ resize: 'none' }}
              />
              <button 
                type="submit" 
                disabled={!message.trim() || isLoading}
                className="send-button"
                title="Enviar mensaje"
              >
                {isLoading ? '⏳' : '📤'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Diálogo de confirmación de eliminación */}
      {deleteDialog.show && (
        <div className="delete-dialog-overlay" onClick={cancelDelete}>
          <div className="delete-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="delete-dialog-icon">🗑️</div>
            <h3 className="delete-dialog-title">Eliminar conversación</h3>
            <p className="delete-dialog-message">
              ¿Estás seguro de que quieres eliminar esta conversación? Esta acción no se puede deshacer.
            </p>
            <div className="delete-dialog-actions">
              <button 
                className="delete-dialog-btn delete-dialog-btn-cancel" 
                onClick={cancelDelete}
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