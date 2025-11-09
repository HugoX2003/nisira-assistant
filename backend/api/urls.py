from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    # Vistas básicas
    health_check,
    api_info,
    service_status,
    submit_rating,
    rating_summary,
    export_ratings,
    create_experiment_run,
    list_experiments,
    latest_experiment,
    guardrail_status,
    # Vistas de conversaciones
    get_conversations,
    create_conversation,
    get_messages,
    send_message,
    delete_conversation,
    # Vistas de autenticación
    register_user,
    custom_login,
    serve_document,
    # Vistas RAG
    rag_status,
    rag_initialize,
    rag_sync_documents,
    rag_query,
    rag_enhanced_chat,
    rag_system_status
)

# Importar vistas de admin
from .admin_views import (
    list_drive_files,
    upload_to_drive,
    delete_drive_file,
    sync_drive_documents,
    get_embeddings_status,
    generate_embeddings,
    verify_embeddings,
    clear_embeddings,
    get_embedding_progress,
    get_system_metrics,
    get_pipeline_status
)

# URLs de la API
urlpatterns = [
    # Autenticación JWT
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/login/", custom_login, name="custom_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/register/", register_user, name="register_user"),
    
    # API básica
    path("health/", health_check, name="health_check"),
    path("info/", api_info, name="api_info"),
    path("status/", service_status, name="service_status"),
    
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
    
    # Servir documentos
    path("documents/<str:filename>/", serve_document, name="serve_document"),

    # Calificaciones
    path("ratings/", submit_rating, name="submit_rating"),
    path("ratings/summary/", rating_summary, name="rating_summary"),
    path("ratings/export/", export_ratings, name="export_ratings"),

    # Experimentos y guardrails
    path("experiments/", list_experiments, name="list_experiments"),
    path("experiments/latest/", latest_experiment, name="latest_experiment"),
    path("experiments/create/", create_experiment_run, name="create_experiment_run"),
    path("guardrails/status/", guardrail_status, name="guardrail_status"),
    
    # Panel de Administración (solo admin)
    path("admin/drive/files/", list_drive_files, name="admin_list_drive_files"),
    path("admin/drive/upload/", upload_to_drive, name="admin_upload_to_drive"),
    path("admin/drive/delete/<str:file_id>/", delete_drive_file, name="admin_delete_drive_file"),
    path("admin/drive/sync/", sync_drive_documents, name="admin_sync_drive_documents"),
    path("admin/embeddings/status/", get_embeddings_status, name="admin_embeddings_status"),
    path("admin/embeddings/generate/", generate_embeddings, name="admin_generate_embeddings"),
    path("admin/embeddings/verify/", verify_embeddings, name="admin_verify_embeddings"),
    path("admin/embeddings/clear/", clear_embeddings, name="admin_clear_embeddings"),
    path("admin/embeddings/progress/", get_embedding_progress, name="admin_embedding_progress"),
    path("admin/metrics/", get_system_metrics, name="admin_get_metrics"),
    path("admin/pipeline/status/", get_pipeline_status, name="admin_pipeline_status"),
]
