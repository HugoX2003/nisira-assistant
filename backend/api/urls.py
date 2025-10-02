from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    # Vistas básicas
    health_check,
    api_info,
    # Vistas de conversaciones
    get_conversations,
    create_conversation,
    get_messages,
    send_message,
    delete_conversation,
    # Vistas RAG
    rag_status,
    rag_initialize,
    rag_sync_documents,
    rag_query,
    rag_enhanced_chat,
    rag_system_status
)

# URLs de la API
urlpatterns = [
    # Autenticación JWT
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # API básica
    path("health/", health_check, name="health_check"),
    path("info/", api_info, name="api_info"),
    
    # Gestión de conversaciones
    path("conversations/", get_conversations, name="get_conversations"),
    path("conversations/create/", create_conversation, name="create_conversation"),
    path("conversations/<int:conversation_id>/messages/", get_messages, name="get_messages"),
    path("conversations/<int:conversation_id>/delete/", delete_conversation, name="delete_conversation"),
    
    # Chat básico
    path("chat/", send_message, name="send_message"),
    
    # Sistema RAG
    path("rag/status/", rag_status, name="rag_status"),
    path("rag/initialize/", rag_initialize, name="rag_initialize"),
    path("rag/sync/", rag_sync_documents, name="rag_sync_documents"),
    path("rag/query/", rag_query, name="rag_query"),
    path("rag/chat/", rag_enhanced_chat, name="rag_enhanced_chat"),
    path("rag/system-status/", rag_system_status, name="rag_system_status"),
]
