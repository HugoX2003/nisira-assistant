# administración y revisión de los historiales de chat nativo de django admin
from django.contrib import admin
from .models import Conversation, Message, UploadedDocument

# Configuración de la vista para el modelo Conversation en el admin
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista
    list_display = ("id", "user", "title", "created_at", "updated_at")
    # Permite buscar por título y usuario
    search_fields = ("title", "user__username")

# Configuración de la vista para el modelo Message en el admin
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista
    list_display = ("id", "conversation", "sender", "created_at")
    # Permite filtrar por tipo de remitente (user/bot)
    list_filter = ("sender",)
    # Permite buscar por texto del mensaje
    search_fields = ("text",)

# Configuración para el modelo UploadedDocument
@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ("file_name", "uploaded_by", "file_size", "processed", "drive_uploaded", "uploaded_at")
    list_filter = ("processed", "drive_uploaded", "file_type")
    search_fields = ("file_name", "uploaded_by__username")
    readonly_fields = ("uploaded_at", "processed_at")

