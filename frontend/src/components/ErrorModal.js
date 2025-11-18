import React from 'react';
import '../styles/ErrorModal.css';

/**
 * Modal de Error Prominente
 * Muestra mensajes de error específicos con estilo visual llamativo
 */
function ErrorModal({ message, onClose, type = 'error' }) {
  if (!message) return null;

  const getIcon = () => {
    switch (type) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  const getTitle = () => {
    switch (type) {
      case 'error':
        return 'Error';
      case 'warning':
        return 'Advertencia';
      case 'info':
        return 'Información';
      default:
        return 'Error';
    }
  };

  return (
    <div className="error-modal-overlay" onClick={onClose}>
      <div className="error-modal" onClick={(e) => e.stopPropagation()}>
        <div className={`error-modal-icon ${type}`}>
          {getIcon()}
        </div>
        <h2 className="error-modal-title">{getTitle()}</h2>
        <p className="error-modal-message">{message}</p>
        <button className="error-modal-close" onClick={onClose}>
          Entendido
        </button>
      </div>
    </div>
  );
}

export default ErrorModal;
