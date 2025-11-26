import React, { useState } from 'react';
import { register } from '../services/api';
import '../styles/Login.css';

/**
 * Componente de Registro - Diseño limpio y simple
 */
export default function Register({ onRegister, onBackToLogin }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const { username, email, password, confirmPassword } = formData;

    // Validaciones
    if (!username.trim() || !email.trim() || !password || !confirmPassword) {
      setError('Todos los campos son requeridos');
      return;
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Ingresa un email válido');
      return;
    }

    setLoading(true);

    try {
      await register(username, email, password);
      setSuccess('¡Cuenta creada! Redirigiendo...');
      setFormData({ username: '', email: '', password: '', confirmPassword: '' });
      setTimeout(onBackToLogin, 2000);
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.message || 'Error al crear la cuenta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <header className="auth-header">
          <div className="auth-logo">✨</div>
          <h1 className="auth-title">Crear cuenta</h1>
          <p className="auth-subtitle">Únete a NISIRA Assistant</p>
        </header>

        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <div className="form-group">
            <label className="form-label" htmlFor="username">Usuario</label>
            <input
              id="username"
              name="username"
              type="text"
              className="form-input"
              placeholder="Elige un nombre de usuario"
              value={formData.username}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              className="form-input"
              placeholder="tu@email.com"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Contraseña</label>
            <input
              id="password"
              name="password"
              type="password"
              className="form-input"
              placeholder="Mínimo 6 caracteres"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="confirmPassword">Confirmar contraseña</label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              className="form-input"
              placeholder="Repite la contraseña"
              value={formData.confirmPassword}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <><span className="spinner" /> Creando...</> : 'Crear cuenta'}
          </button>

          <div className="divider">o</div>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={onBackToLogin}
            disabled={loading}
          >
            Volver al inicio de sesión
          </button>
        </form>
      </div>
    </div>
  );
}
