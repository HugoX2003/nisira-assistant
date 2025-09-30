import React, { useState } from "react";
import { register } from "../services/api";
import "../styles/Login.css";

/**
 * Componente de registro de usuarios
 * Permite crear nuevas cuentas conectando con el endpoint /auth/register del backend
 */
export default function Register({ onRegister, onBackToLogin }) {
  // Estados del formulario de registro
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Maneja el envío del formulario de registro
   * Valida los datos y envía la petición al backend
   */
  async function handleRegister(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    // Validaciones del lado del cliente
    if (!username.trim() || !email.trim() || !password || !confirmPassword) {
      setError("Todos los campos son requeridos");
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      setLoading(false);
      return;
    }

    // Validación básica de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Por favor ingresa un email válido");
      setLoading(false);
      return;
    }

    try {
      // Enviar petición de registro al backend
      await register(username, email, password);
      setSuccess("Usuario creado exitosamente. Ahora puedes iniciar sesión.");

      // Limpiar formulario después del registro exitoso
      setUsername("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");

      // Opcional: redirigir automáticamente al login después de 2 segundos
      setTimeout(() => {
        onBackToLogin();
      }, 2000);
    } catch (err) {
      // Manejar errores del servidor
      const errorMessage = err.response?.data?.error || "Error al crear la cuenta";
      setError(errorMessage);
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
          onSubmit={handleRegister}
          className="auth-form gpt-card"
          role="form"
          aria-labelledby="register-title"
        >
          <header className="form-header">
            {/* Logo moderno mejorado */}
            <div className="gpt-logo register-logo" aria-hidden="true">
              <svg viewBox="0 0 64 64" width="44" height="44">
                <circle
                  cx="32" cy="32" r="22"
                  fill="none"
                  stroke="url(#registerGradient)"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                  className="gpt-logo-circle"
                />
                <path
                  d="M32 18v28M18 32h28"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  className="gpt-logo-plus"
                />
                <defs>
                  <linearGradient id="registerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#22d3ee" />
                    <stop offset="100%" stopColor="#a78bfa" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            <h2 id="register-title" className="title register-title">
              Crear cuenta nueva
            </h2>
            <p className="subtitle">Únete a NISIRA Assistant</p>
          </header>

          {/* Campo de nombre de usuario */}
          <div className="input-group">
            <span className="icon user-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path
                  d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 4L13.5 7H10.5L9 4L3 7V9H21ZM21 10H3V12H21V10ZM3 13V22H8V16H16V22H21V13H3Z"
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
              placeholder="Elige tu nombre de usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field register-input"
              autoComplete="username"
              disabled={loading}
            />
          </div>

          {/* Campo de email */}
          <div className="input-group">
            <span className="icon email-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path
                  d="M22 6C22 4.9 21.1 4 20 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6ZM20 6L12 11L4 6H20ZM20 18H4V8L12 13L20 8V18Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="email" className="sr-only">
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              placeholder="Tu correo electrónico"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field register-input"
              autoComplete="email"
              disabled={loading}
            />
          </div>

          {/* Campo de contraseña */}
          <div className="input-group">
            <span className="icon password-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path
                  d="M18 8H20C21.1 8 22 8.9 22 10V20C22 21.1 21.1 22 20 22H4C2.9 22 2 21.1 2 20V10C2 8.9 2.9 8 4 8H6V6C6 3.8 7.8 2 10 2H14C16.2 2 18 3.8 18 6V8ZM16 8V6C16 4.9 15.1 4 14 4H10C8.9 4 8 4.9 8 6V8H16ZM12 17C13.1 17 14 16.1 14 15C14 13.9 13.1 13 12 13C10.9 13 10 13.9 10 15C10 16.1 10.9 17 12 17Z"
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
              placeholder="Crea una contraseña segura (min. 6 caracteres)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field register-input"
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          {/* Campo de confirmación de contraseña */}
          <div className="input-group">
            <span className="icon confirm-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path
                  d="M18 8H20C21.1 8 22 8.9 22 10V20C22 21.1 21.1 22 20 22H4C2.9 22 2 21.1 2 20V10C2 8.9 2.9 8 4 8H6V6C6 3.8 7.8 2 10 2H14C16.2 2 18 3.8 18 6V8ZM16 8V6C16 4.9 15.1 4 14 4H10C8.9 4 8 4.9 8 6V8H16ZM10.5 16.2L16.2 10.5L15.5 9.8L10.5 14.8L8.5 12.8L7.8 13.5L10.5 16.2Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="confirmPassword" className="sr-only">
              Confirmar contraseña
            </label>
            <input
              id="confirmPassword"
              type="password"
              placeholder="Confirma tu contraseña"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input-field register-input"
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          {/* Botón de registro */}
          <button type="submit" disabled={loading} className="btn-primary gpt-btn register-btn">
            {loading ? (
              <>
                <span className="loading-spinner" aria-hidden="true"></span>
                <span>Creando tu cuenta...</span>
              </>
            ) : (
              <>
                <span className="btn-icon">🚀</span>
                <span>Crear mi cuenta</span>
              </>
            )}
          </button>

          <div className="divider">
            <span>o</span>
          </div>

          {/* Botón para volver al login */}
          <button
            type="button"
            onClick={onBackToLogin}
            className="btn-secondary ghost-btn back-btn"
            disabled={loading}
          >
            <span className="btn-icon">←</span>
            <span>¿Ya tienes cuenta? Inicia sesión</span>
          </button>

          {/* Mostrar mensajes de error / éxito */}
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}
        </form>
      </div>
    </div>
  );
}