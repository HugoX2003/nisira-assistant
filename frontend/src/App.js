import React, { useState, useEffect } from "react";
import Login from "./components/Login";
import Register from "./components/Register";
import Chat from "./components/Chat";

/**
 * Componente principal de la aplicación
 * Maneja la navegación entre las pantallas de login, registro y chat
 */
function App() {
  // Verificar si hay un token en localStorage al iniciar
  const checkAuth = () => {
    const token = localStorage.getItem('token');
    return token && token !== 'null' && token !== 'undefined';
  };

  // Estados para controlar qué pantalla mostrar
  const [currentView, setCurrentView] = useState(checkAuth() ? "chat" : "login");
  const [loggedIn, setLoggedIn] = useState(checkAuth());

  // Verificar autenticación al montar el componente
  useEffect(() => {
    const isAuthenticated = checkAuth();
    setLoggedIn(isAuthenticated);
    setCurrentView(isAuthenticated ? "chat" : "login");
  }, []);

  /**
   * Función que se ejecuta cuando el usuario se loguea exitosamente
   * Cambia el estado para mostrar la pantalla de chat
   */
  function handleLogin() {
    setLoggedIn(true);
    setCurrentView("chat");
  }

  /**
   * Función para navegar a la pantalla de registro
   */
  function showRegister() {
    setCurrentView("register");
  }

  /**
   * Función para volver a la pantalla de login
   */
  function showLogin() {
    setCurrentView("login");
  }

  /**
   * Función que se ejecuta cuando el usuario se registra exitosamente
   * Por ahora redirige al login, pero podría auto-loguearlo
   */
  function handleRegister() {
    // Después del registro exitoso, volver al login
    setCurrentView("login");
  }

  /**
   * Función para cerrar sesión (logout)
   * Vuelve al estado inicial y muestra la pantalla de login
   */
  function handleLogout() {
    setLoggedIn(false);
    setCurrentView("login");
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh');
    } catch {}
  }

  // Renderizar la pantalla correspondiente según el estado actual
  return (
    <div className="app-container">
      {currentView === "login" && (
        <Login 
          onLogin={handleLogin} 
          onShowRegister={showRegister}
        />
      )}
      
      {currentView === "register" && (
        <Register 
          onRegister={handleRegister}
          onBackToLogin={showLogin}
        />
      )}
      
      {currentView === "chat" && loggedIn && (
        <Chat onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;
