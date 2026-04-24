import React, { useState } from 'react';
import { Bot } from 'lucide-react';
import { login, tokenManager } from '../services/api';
import '../styles/Login.css';

/**
 * Componente de Login - Diseño limpio y simple
 */
export default function Login({ onLogin, onShowRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!username.trim() || !password) {
      setError('Por favor completa todos los campos');
      return;
    }

    setLoading(true);

    try {
      const data = await login(username, password);
      tokenManager.setTokens(data.access, data.refresh);
      onLogin(data.user);
    } catch (err) {
      setError(
        err.response?.status === 401
          ? 'Usuario o contraseña incorrectos'
          : 'Error de conexión. Intenta nuevamente.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <header className="auth-header">
          <div className="auth-logo"><Bot size={48} strokeWidth={1.5} /></div>
          <h1 className="auth-title">Bienvenido</h1>
          <p className="auth-subtitle">Inicia sesión en NISIRA Assistant</p>
        </header>

        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label className="form-label" htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              className="form-input"
              placeholder="Tu nombre de usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="Tu contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <><span className="spinner" /> Iniciando...</> : 'Iniciar Sesión'}
          </button>

          <div className="divider">o</div>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={onShowRegister}
            disabled={loading}
          >
            Crear cuenta nueva
          </button>
        </form>
      </div>
    </div>
  );
}
