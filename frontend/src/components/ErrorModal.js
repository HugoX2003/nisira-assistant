import React from 'react';
import { XCircle, AlertTriangle, Info } from 'lucide-react';
import '../styles/ErrorModal.css';

/**
 * Modal de Error Prominente
 * Muestra mensajes de error especificos con estilo visual llamativo
 */
function ErrorModal({ message, onClose, type = 'error' }) {
  if (!message) return null;

  const getIcon = () => {
    switch (type) {
      case 'error':
        return <XCircle size={48} strokeWidth={1.5} />;
      case 'warning':
        return <AlertTriangle size={48} strokeWidth={1.5} />;
      case 'info':
        return <Info size={48} strokeWidth={1.5} />;
      default:
        return <XCircle size={48} strokeWidth={1.5} />;
    }
  };

  const getTitle = () => {
    switch (type) {
      case 'error':
        return 'Error';
      case 'warning':
        return 'Advertencia';
      case 'info':
        return 'Informacion';
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
