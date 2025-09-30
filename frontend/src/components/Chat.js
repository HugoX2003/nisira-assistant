import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { query as queryApi, getConversations, getMessages } from '../services/api';
import '../styles/Chat.css';

// Componente de mensaje optimizado
const Message = React.memo(({ message, isUser, timestamp, sources }) => (
  <div className={`message ${isUser ? 'user' : 'bot'}`}>
    <div className="message-content">
      <div className="message-text">{message}</div>
      {sources && sources.length > 0 && (
        <div className="message-sources">
          <details>
            <summary>Fuentes ({sources.length})</summary>
            <ul>
              {sources.map((source, idx) => (
                <li key={idx}>
                  <strong>{source.archivo}</strong> - Relevancia: {(source.similarity_score * 100).toFixed(1)}%
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
    <div className="message-timestamp">{timestamp}</div>
  </div>
));

// Componente de loading optimizado
const LoadingIndicator = React.memo(() => (
  <div className="message bot">
    <div className="message-content">
      <div className="loading-dots">
        <span></span>
        <span></span>
        <span></span>
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

  const loadConversations = useCallback(async () => {
    try {
      const res = await getConversations();
      const list = res.conversations || [];
      setConversations(list);
      if (list.length > 0 && !activeConversation) {
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

  // Cargar conversaciones al montar
  useEffect(() => {
    loadConversations();
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
          text: m.text,
          sender: m.sender,
          timestamp: new Date(m.created_at).toLocaleTimeString(),
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

    // Agregar mensaje del usuario
    const userMessage = {
      id: Date.now(),
      text: trimmedMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      sources: []
    };
    
    addMessage(userMessage);
    setIsLoading(true);

    try {
      const response = await queryApi(trimmedMessage);
      
      if (response.success) {
        const botMessage = {
          id: Date.now() + 1,
          text: response.data.response,
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString(),
          sources: response.data.search_results || []
        };
        
        addMessage(botMessage);
        
        // Recargar conversaciones si es necesario
        if (response.data.conversation_id && !activeConversation) {
          await loadConversations();
        }
      } else {
        throw new Error(response.message || 'Error en la respuesta');
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
  }, [message, isLoading, addMessage, activeConversation, loadConversations]);

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
  }, [clearMessages]);

  // Cambiar conversación
  const handleConversationSelect = useCallback((conversationId) => {
    if (conversationId !== activeConversation) {
      setActiveConversation(conversationId);
      setError(null);
    }
  }, [activeConversation]);

  // Componente de sidebar memoizado
  const Sidebar = useMemo(() => (
    <div className={`chat-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <h3>Conversaciones</h3>
        <button 
          className="new-conversation-btn"
          onClick={handleNewConversation}
          title="Nueva conversación"
        >
          + Nueva
        </button>
      </div>
      
      <div className="conversations-list">
        {conversations.map(conv => (
          <div
            key={conv.id}
            className={`conversation-item ${conv.id === activeConversation ? 'active' : ''}`}
            onClick={() => handleConversationSelect(conv.id)}
          >
            <div className="conversation-title">{conv.title}</div>
            <div className="conversation-date">
              {new Date(conv.created_at).toLocaleDateString()}
            </div>
            <div className="conversation-meta">
              {conv.message_count} mensajes
            </div>
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
    <div className="chat-container">
      {Sidebar}
      
      <div className="chat-main">
        <div className="chat-header">
          <button 
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
          <h2>RAG Assistant</h2>
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

        <div className="chat-messages">
          {messages.length === 0 && !isLoading && (
            <div className="welcome-message">
              <h3>¡Bienvenido al RAG Assistant! 🤖</h3>
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

        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className="input-container">
            <textarea
              ref={inputRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe tu pregunta aquí... (Enter para enviar, Shift+Enter para nueva línea)"
              disabled={isLoading}
              rows={1}
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
          
          <div className="input-help">
            <small>
              💡 Tip: Sé específico en tus preguntas para obtener mejores resultados
            </small>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Chat;