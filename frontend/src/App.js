import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Login from "./components/Login";
import Register from "./components/Register";
import Chat from "./components/Chat";
import AdminPanel from "./components/AdminPanel";
import { getCurrentUser, clearUserData } from "./services/api";

/**
 * Ruta protegida: requiere usuario autenticado.
 * Opcionalmente requiere admin (adminOnly=true).
 */
function ProtectedRoute({ children, adminOnly = false }) {
  const token = localStorage.getItem('token');
  const isAuth = !!(token && token !== 'null' && token !== 'undefined' && token.trim() !== '');
  const u = getCurrentUser();
  const isAdmin = u && u.username === 'admin';

  if (!isAuth) {
    return <Navigate to="/login" replace />;
  }
  if (adminOnly && !isAdmin) {
    return <Navigate to="/chat" replace />;
  }
  return children;
}

/**
 * Pantalla raiz: redirige segun el rol del usuario logueado.
 */
function HomeRedirect() {
  const token = localStorage.getItem('token');
  const isAuth = !!(token && token !== 'null' && token !== 'undefined' && token.trim() !== '');
  if (!isAuth) return <Navigate to="/login" replace />;
  const u = getCurrentUser();
  if (u && u.username === 'admin') return <Navigate to="/admin" replace />;
  return <Navigate to="/chat" replace />;
}

/**
 * Wrappers para inyectar callbacks de navegacion a los componentes legacy.
 */
function LoginRoute() {
  const navigate = useNavigate();
  const handleLogin = (userData) => {
    if (userData && userData.username === 'admin') {
      navigate('/admin', { replace: true });
    } else {
      navigate('/chat', { replace: true });
    }
  };
  return <Login onLogin={handleLogin} onShowRegister={() => navigate('/register')} />;
}

function RegisterRoute() {
  const navigate = useNavigate();
  return (
    <Register
      onRegister={() => navigate('/login')}
      onBackToLogin={() => navigate('/login')}
    />
  );
}

function ChatRoute() {
  const navigate = useNavigate();
  const u = getCurrentUser();
  const handleLogout = () => {
    clearUserData();
    navigate('/login', { replace: true });
  };
  return <Chat user={u} onLogout={handleLogout} />;
}

function AdminRoute() {
  const navigate = useNavigate();
  const u = getCurrentUser();
  const handleLogout = () => {
    clearUserData();
    navigate('/login', { replace: true });
  };
  return <AdminPanel user={u} onLogout={handleLogout} />;
}

/**
 * Componente principal con BrowserRouter.
 * Rutas:
 *   /                          -> redirige segun rol
 *   /login, /register          -> publicas
 *   /chat, /chat/:id           -> usuario autenticado
 *   /admin, /admin/:tab        -> solo admin
 */
function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/register" element={<RegisterRoute />} />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatRoute />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat/:conversationId"
            element={
              <ProtectedRoute>
                <ChatRoute />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute adminOnly>
                <AdminRoute />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/:tabId"
            element={
              <ProtectedRoute adminOnly>
                <AdminRoute />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
