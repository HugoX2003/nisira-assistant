import React, { useState, useEffect } from "react";
import Login from "./components/Login";
import Register from "./components/Register";
import Chat from "./components/Chat";
import { getCurrentUser, clearUserData } from "./services/api";

/**
 * Componente principal de la aplicación
 * Maneja la navegación entre las pantallas de login, registro y chat
 */
function App() {
  // Verificar si hay un token en localStorage al iniciar
  const checkAuth = () => {
    const token = localStorage.getItem('token');
    const isValid = token && token !== 'null' && token !== 'undefined' && token.trim() !== '';
    console.log('🔍 Verificando autenticación:', { 
      hasToken: !!token, 
      isValid, 
      tokenLength: token ? token.length : 0 
    });
    return isValid;
  };

  // Estados para controlar qué pantalla mostrar
  const [currentView, setCurrentView] = useState(checkAuth() ? "chat" : "login");
  const [loggedIn, setLoggedIn] = useState(checkAuth());
  const [user, setUser] = useState(getCurrentUser());

  // Verificar autenticación al montar el componente
  useEffect(() => {
    const isAuthenticated = checkAuth();
    const currentUser = getCurrentUser();
    setLoggedIn(isAuthenticated);
    setUser(currentUser);
    setCurrentView(isAuthenticated ? "chat" : "login");
  }, []);

  /**
   * Función que se ejecuta cuando el usuario se loguea exitosamente
   * Cambia el estado para mostrar la pantalla de chat
   */
  function handleLogin(userData) {
    setLoggedIn(true);
    setUser(userData);
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
    setUser(null);
    setCurrentView("login");
    clearUserData();
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
        <Chat onLogout={handleLogout} user={user} />
      )}
    </div>
  );
}

export default App;
