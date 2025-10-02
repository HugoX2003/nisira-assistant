import React, { useState } from "react";
import { login, tokenManager } from "../services/api";
import "../styles/Login.css";

/**
 * Componente de inicio de sesión
 * Permite a los usuarios autenticarse con username y password
 */
export default function Login({ onLogin, onShowRegister }) {
  // Estados del formulario de login
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Maneja el envío del formulario de login
   * Valida credenciales y autentica al usuario
   */
  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Validación básica del lado del cliente
    if (!username.trim() || !password) {
      setError("Por favor ingresa usuario y contraseña");
      setLoading(false);
      return;
    }

    try {
      // Enviar petición de login al backend
      const data = await login(username, password);
      
      // Guardar tokens usando el TokenManager
      tokenManager.setTokens(data.access, data.refresh);
      
      console.log('✅ Tokens guardados exitosamente');
      
      // Si el login es exitoso, notificar al componente padre
      onLogin();
    } catch (err) {
      // Manejar errores de autenticación
      if (err.response?.status === 401) {
        setError("Usuario o contraseña incorrectos");
      } else {
        setError("Error de conexión. Intenta nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login">
      <div className="app-container">
        {/* Fondo decorativo estilo GPT */}
        <div className="bg-grid" aria-hidden="true" />
        <div className="bg-glow" aria-hidden="true" />

        <form
          onSubmit={handleLogin}
          className="auth-form gpt-card"
          role="form"
          aria-labelledby="login-title"
        >
          <header className="form-header">
            {/* Logo moderno mejorado para login */}
            <div className="gpt-logo login-logo" aria-hidden="true">
              <svg viewBox="0 0 64 64" width="44" height="44">
                <circle
                  cx="32" cy="32" r="22"
                  fill="none"
                  stroke="url(#loginGradient)"
                  strokeWidth="2"
                  className="gpt-logo-orbit"
                />
                <circle
                  cx="32" cy="32" r="8"
                  fill="url(#loginGradientFill)"
                  className="gpt-logo-center"
                />
                <path
                  d="M32 12v8M32 44v8M12 32h8M44 32h8"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  className="gpt-logo-rays"
                />
                <defs>
                  <linearGradient id="loginGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#22d3ee" />
                    <stop offset="100%" stopColor="#a78bfa" />
                  </linearGradient>
                  <radialGradient id="loginGradientFill" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.6" />
                  </radialGradient>
                </defs>
              </svg>
            </div>

            <h2 id="login-title" className="title login-title">
              Bienvenido de vuelta
            </h2>
            <p className="subtitle">Accede a NISIRA Assistant</p>
          </header>

          {/* Campo de nombre de usuario */}
          <div className="input-group">
            <span className="icon login-user-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path
                  d="M12 2C14.21 2 16 3.79 16 6C16 8.21 14.21 10 12 10C9.79 10 8 8.21 8 6C8 3.79 9.79 2 12 2ZM12 4C10.9 4 10 4.9 10 6C10 7.1 10.9 8 12 8C13.1 8 14 7.1 14 6C14 4.9 13.1 4 12 4ZM4 19V16C4 14.67 4.67 14 6 14H18C19.33 14 20 14.67 20 16V19C20 20.11 19.11 21 18 21H6C4.89 21 4 20.11 4 19Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="username" className="sr-only">
              Nombre de usuario
            </label>
            <input
              id="username"
              type="text"
              placeholder="Ingresa tu nombre de usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field login-input"
              autoComplete="username"
              disabled={loading}
            />
          </div>

          {/* Campo de contraseña */}
          <div className="input-group">
            <span className="icon login-password-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path
                  d="M6 10V8C6 5.79 7.79 4 10 4H14C16.21 4 18 5.79 18 8V10H19C20.1 10 21 10.9 21 12V20C21 21.1 20.1 22 19 22H5C3.9 22 3 21.1 3 20V12C3 10.9 3.9 10 5 10H6ZM8 8V10H16V8C16 6.9 15.1 6 14 6H10C8.9 6 8 6.9 8 8ZM12 17C13.1 17 14 16.1 14 15C14 13.9 13.1 13 12 13C10.9 13 10 13.9 10 15C10 16.1 10.9 17 12 17Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="password" className="sr-only">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              placeholder="Ingresa tu contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field login-input"
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          {/* Botón de inicio de sesión */}
          <button type="submit" disabled={loading} className="btn-primary gpt-btn login-btn">
            {loading ? (
              <>
                <span className="loading-spinner" aria-hidden="true"></span>
                <span>Iniciando sesión...</span>
              </>
            ) : (
              <>
                <span className="btn-icon">🔑</span>
                <span>Iniciar Sesión</span>
              </>
            )}
          </button>

          <div className="divider">
            <span>o</span>
          </div>

          {/* Botón para ir al registro */}
          <button
            type="button"
            onClick={onShowRegister}
            className="btn-secondary ghost-btn register-link-btn"
            disabled={loading}
          >
            <span className="btn-icon">✨</span>
            <span>¿No tienes cuenta? Regístrate</span>
          </button>

          {/* Mostrar mensajes de error */}
          {error && <div className="error-message">{error}</div>}
        </form>
      </div>
    </div>
  );
}