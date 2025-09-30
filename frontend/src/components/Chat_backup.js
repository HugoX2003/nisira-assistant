import React, { useState, useRef, useEffect } from 'react';
import { query as queryApi, getConversations, getMessages } from '../services/api';
import '../styles/Chat.css';

const Chat = ({ onLogout }) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  // Cargar conversaciones al montar
  useEffect(() => {
    (async () => {
      try {
        const res = await getConversations();
        const list = res.conversations || [];
        setConversations(list);
        if (list.length > 0) setActiveConversation(list[0].id);
      } catch (e) {
        console.error('No se pudieron cargar conversaciones', e);
      }
    })();
  }, []);

  // Cargar mensajes al cambiar de conversación
  useEffect(() => {
    if (!activeConversation) { setMessages([]); return; }
    (async () => {
      try {
        const res = await getMessages(activeConversation);
        const msgs = (res.messages || []).map(m => ({
          id: m.id,
          text: m.text,
          sender: m.sender,
          timestamp: new Date(m.created_at).toLocaleTimeString()
        }));
        setMessages(msgs);
      } catch (e) {
        console.error('No se pudieron cargar mensajes', e);
        setMessages([]);
      }
    })();
  }, [activeConversation]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: message,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);

    try {
      const response = await queryApi(message, 5, activeConversation || undefined);
      const botMessage = {
        id: Date.now() + 1,
        text: response.answer,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        sources: response.sources || []
      };
      setMessages(prev => [...prev, botMessage]);
      // Actualizar conversación activa si el backend la creó
      if (!activeConversation && response.conversation_id) {
        setActiveConversation(response.conversation_id);
        try {
          const r = await getConversations();
          setConversations(r.conversations || []);
        } catch {}
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Error al procesar la consulta. Intenta nuevamente.',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setActiveConversation(null);
  };

  return (
    <div className="chat">
      <div className={`chat-container ${!sidebarOpen ? 'sidebar-closed' : ''}`}>
        {/* Sidebar */}
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            <button
              className="toggle-sidebar"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? '◀' : '▶'}
            </button>

            {sidebarOpen && (
              <button className="new-chat-btn" onClick={startNewConversation}>
                Nueva Conversación
              </button>
            )}
          </div>

          {sidebarOpen && (
            <>
              <div className="conversations-section">
                <h4 className="sidebar-title">Chats</h4>
                <div className="conversations-list">
                  {conversations.map(conv => (
                    <div
                      key={conv.id}
                      className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                      onClick={() => setActiveConversation(conv.id)}
                      title={conv.title}
                    >
                      {conv.title}
                    </div>
                  ))}
                </div>
              </div>

              <div className="sidebar-footer">
                <button className="logout-btn" onClick={onLogout}>
                  Cerrar Sesión
                </button>
              </div>
            </>
          )}
        </aside>

        {/* Main Chat Area */}
        <main className="chat-main">
          <header className="chat-header">
            <div className="header-content">
              <div className="nisira-logo">
                <svg viewBox="0 0 100 100" width="40" height="40">
                  <defs>
                    <linearGradient id="flame1" x1="0%" y1="100%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#FF6B35" />
                      <stop offset="50%" stopColor="#FF8C42" />
                      <stop offset="100%" stopColor="#FFA726" />
                    </linearGradient>
                    <linearGradient id="flame2" x1="0%" y1="100%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#8BC34A" />
                      <stop offset="50%" stopColor="#9CCC65" />
                      <stop offset="100%" stopColor="#AED581" />
                    </linearGradient>
                    <linearGradient id="flame3" x1="0%" y1="100%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#FFD54F" />
                      <stop offset="50%" stopColor="#FFEB3B" />
                      <stop offset="100%" stopColor="#FFF176" />
                    </linearGradient>
                  </defs>
                  
                  {/* Llama naranja */}
                  <path d="M20 80 C20 60, 30 40, 45 30 C35 45, 40 65, 50 70 C45 75, 35 85, 20 80 Z" 
                        fill="url(#flame1)" className="flame flame1" />
                  
                  {/* Llama verde */}
                  <path d="M35 75 C35 55, 45 35, 60 25 C50 40, 55 60, 65 65 C60 70, 50 80, 35 75 Z" 
                        fill="url(#flame2)" className="flame flame2" />
                  
                  {/* Llama amarilla */}
                  <path d="M50 70 C50 50, 60 30, 75 20 C65 35, 70 55, 80 60 C75 65, 65 75, 50 70 Z" 
                        fill="url(#flame3)" className="flame flame3" />
                </svg>
              </div>
              <h1>NISIRA ASSISTANT</h1>
            </div>
          </header>

          <section className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <div className="welcome-icon nisira-welcome-logo">
                  <svg viewBox="0 0 100 100" width="80" height="80">
                    <defs>
                      <linearGradient id="welcomeFlame1" x1="0%" y1="100%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#FF6B35" />
                        <stop offset="50%" stopColor="#FF8C42" />
                        <stop offset="100%" stopColor="#FFA726" />
                      </linearGradient>
                      <linearGradient id="welcomeFlame2" x1="0%" y1="100%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#8BC34A" />
                        <stop offset="50%" stopColor="#9CCC65" />
                        <stop offset="100%" stopColor="#AED581" />
                      </linearGradient>
                      <linearGradient id="welcomeFlame3" x1="0%" y1="100%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#FFD54F" />
                        <stop offset="50%" stopColor="#FFEB3B" />
                        <stop offset="100%" stopColor="#FFF176" />
                      </linearGradient>
                    </defs>
                    
                    <path d="M20 80 C20 60, 30 40, 45 30 C35 45, 40 65, 50 70 C45 75, 35 85, 20 80 Z" 
                          fill="url(#welcomeFlame1)" className="welcome-flame welcome-flame1" />
                    
                    <path d="M35 75 C35 55, 45 35, 60 25 C50 40, 55 60, 65 65 C60 70, 50 80, 35 75 Z" 
                          fill="url(#welcomeFlame2)" className="welcome-flame welcome-flame2" />
                    
                    <path d="M50 70 C50 50, 60 30, 75 20 C65 35, 70 55, 80 60 C75 65, 65 75, 50 70 Z" 
                          fill="url(#welcomeFlame3)" className="welcome-flame welcome-flame3" />
                  </svg>
                </div>
                <h2>¡Hola! Soy NISIRA, tu asistente inteligente</h2>
                <p>Pregúntame lo que necesites sobre los documentos disponibles</p>
              </div>
            ) : (
              <>
                {messages.map(msg => (
                  <article key={msg.id} className={`message ${msg.sender}-message ${msg.isError ? 'error' : ''}`}>
                    <div className="message-avatar">
                      {msg.sender === 'user' ? '👤' : '🤖'}
                    </div>
                    <div className="message-bubble">
                      <div className="message-text">{msg.text}</div>

                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          <div className="sources-header" onClick={(e) => {
                            const list = e.target.nextElementSibling;
                            list.style.display = list.style.display === 'none' ? 'block' : 'none';
                            e.target.innerHTML = list.style.display === 'none' 
                              ? `📄 Fuentes consultadas (${msg.sources.length}) ▼`
                              : `📄 Fuentes consultadas (${msg.sources.length}) ▲`;
                          }}>
                            📄 Fuentes consultadas ({msg.sources.length}) ▼
                          </div>
                          <div className="sources-list">
                            {msg.sources.map((source, idx) => (
                              <div key={idx} className="source-item">
                                <div className="source-header">
                                  <span className="source-number">#{source.numero_fuente || idx + 1}</span>
                                  <span className="source-title">{source.title}</span>
                                  {source.similarity_score && (
                                    <span className="source-score">
                                      📊 {(source.similarity_score * 100).toFixed(1)}%
                                    </span>
                                  )}
                                </div>
                                <div className="source-snippet">{source.snippet}</div>
                                {source.page && (
                                  <div className="source-meta">
                                    📄 Fragmento: {source.page}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="message-meta">
                        <span className="message-time">⏰ {msg.timestamp}</span>
                        {msg.sender === 'bot' && !msg.isError && (
                          <span className="message-feedback">
                            ¿Te ayudó esta respuesta?
                            <button className="feedback-btn" type="button" aria-label="Me ayudó">👍</button>
                            <button className="feedback-btn" type="button" aria-label="No me ayudó">👎</button>
                          </span>
                        )}
                      </div>
                    </div>
                  </article>
                ))}

                {isLoading && (
                  <article className="message bot-message">
                    <div className="message-avatar">🤖</div>
                    <div className="message-bubble">
                      <div className="typing-indicator" aria-label="Escribiendo">
                        <span></span><span></span><span></span>
                      </div>
                    </div>
                  </article>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </section>

          <footer className="input-container">
            <form onSubmit={handleSubmit} className="input-form">
              <div className="input-wrapper">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ingresa tu consulta"
                  className="message-input"
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
                  disabled={isLoading || !message.trim()}
                  aria-label="Enviar"
                  title="Enviar"
                >
                  ✈️
                </button>
              </div>
            </form>
          </footer>
        </main>
      </div>
    </div>
  );
};

export default Chat;